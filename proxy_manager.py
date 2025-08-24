#!/usr/bin/env python3
"""
Proxy Manager for TikTok Analysis
Handles proxy rotation, validation, and stealth techniques
"""

import asyncio
import aiohttp
import random
import time
import json
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class ProxyInfo:
    """Proxy information container"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'
    last_used: float = 0
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0
    is_working: bool = True

class ProxyManager:
    """Manage proxy rotation and validation for stealth operations"""
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxies: List[ProxyInfo] = []
        self.current_proxy_index = 0
        self.logger = logging.getLogger(__name__)
        self.test_url = 'https://httpbin.org/ip'
        self.max_failures_per_proxy = 5
        self.cooldown_period = 300  # 5 minutes
        
        if proxy_list:
            self.load_proxy_list(proxy_list)
    
    def load_proxy_list(self, proxy_list: List[str]):
        """Load proxy list from strings or file"""
        for proxy_str in proxy_list:
            proxy_info = self.parse_proxy_string(proxy_str)
            if proxy_info:
                self.proxies.append(proxy_info)
        
        self.logger.info(f"Loaded {len(self.proxies)} proxies")
    
    def parse_proxy_string(self, proxy_str: str) -> Optional[ProxyInfo]:
        """Parse proxy string into ProxyInfo object"""
        try:
            # Handle different formats:
            # http://username:password@host:port
            # http://host:port
            # host:port
            
            if not proxy_str.startswith(('http://', 'https://', 'socks5://')):
                proxy_str = f'http://{proxy_str}'
            
            parsed = urlparse(proxy_str)
            
            return ProxyInfo(
                host=parsed.hostname,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
                protocol=parsed.scheme
            )
        except Exception as e:
            self.logger.error(f"Failed to parse proxy {proxy_str}: {e}")
            return None
    
    async def validate_proxy(self, proxy: ProxyInfo) -> Tuple[bool, float]:
        """Test if a proxy is working"""
        try:
            start_time = time.time()
            
            # Create proxy URL
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            else:
                proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        data = await response.json()
                        
                        # Log the IP we're appearing from
                        self.logger.info(f"Proxy {proxy.host}:{proxy.port} working. IP: {data.get('origin', 'unknown')}")
                        return True, response_time
                    else:
                        return False, 0
                        
        except Exception as e:
            self.logger.warning(f"Proxy {proxy.host}:{proxy.port} failed: {e}")
            return False, 0
    
    async def validate_all_proxies(self):
        """Validate all proxies and update their status"""
        self.logger.info("Validating all proxies...")
        
        tasks = []
        for proxy in self.proxies:
            tasks.append(self.validate_proxy(proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        working_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.proxies[i].is_working = False
                self.proxies[i].failure_count += 1
            else:
                is_working, response_time = result
                self.proxies[i].is_working = is_working
                if is_working:
                    self.proxies[i].success_count += 1
                    self.proxies[i].avg_response_time = response_time
                    working_count += 1
                else:
                    self.proxies[i].failure_count += 1
        
        self.logger.info(f"Proxy validation complete: {working_count}/{len(self.proxies)} working")
    
    def get_working_proxies(self) -> List[ProxyInfo]:
        """Get list of currently working proxies"""
        current_time = time.time()
        
        working_proxies = []
        for proxy in self.proxies:
            # Check if proxy is working and not in cooldown
            if (proxy.is_working and 
                proxy.failure_count < self.max_failures_per_proxy and
                (current_time - proxy.last_used) > (proxy.failure_count * 60)):  # Progressive backoff
                
                working_proxies.append(proxy)
        
        # Sort by success rate and response time
        working_proxies.sort(key=lambda p: (p.success_count / max(1, p.success_count + p.failure_count), -p.avg_response_time), reverse=True)
        
        return working_proxies
    
    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get the next proxy in rotation"""
        working_proxies = self.get_working_proxies()
        
        if not working_proxies:
            self.logger.warning("No working proxies available")
            return None
        
        # Use weighted random selection favoring better proxies
        if len(working_proxies) > 1:
            # Give more weight to better performing proxies
            weights = []
            for proxy in working_proxies:
                success_rate = proxy.success_count / max(1, proxy.success_count + proxy.failure_count)
                weight = success_rate * (1 / max(0.1, proxy.avg_response_time))  # Favor faster proxies
                weights.append(weight)
            
            # Weighted random selection
            selected_proxy = random.choices(working_proxies, weights=weights)[0]
        else:
            selected_proxy = working_proxies[0]
        
        selected_proxy.last_used = time.time()
        return selected_proxy
    
    def mark_proxy_success(self, proxy: ProxyInfo, response_time: float):
        """Mark a proxy as successful"""
        proxy.success_count += 1
        proxy.avg_response_time = (proxy.avg_response_time + response_time) / 2
        proxy.is_working = True
    
    def mark_proxy_failure(self, proxy: ProxyInfo):
        """Mark a proxy as failed"""
        proxy.failure_count += 1
        
        # Disable proxy if it has too many failures
        if proxy.failure_count >= self.max_failures_per_proxy:
            proxy.is_working = False
            self.logger.warning(f"Proxy {proxy.host}:{proxy.port} disabled due to failures")
    
    def get_proxy_url(self, proxy: ProxyInfo) -> str:
        """Get formatted proxy URL for use with aiohttp"""
        if proxy.username and proxy.password:
            return f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        else:
            return f"{proxy.protocol}://{proxy.host}:{proxy.port}"
    
    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        total_proxies = len(self.proxies)
        working_proxies = len(self.get_working_proxies())
        
        total_success = sum(p.success_count for p in self.proxies)
        total_failures = sum(p.failure_count for p in self.proxies)
        
        avg_response_time = sum(p.avg_response_time for p in self.proxies if p.avg_response_time > 0)
        avg_response_time = avg_response_time / max(1, len([p for p in self.proxies if p.avg_response_time > 0]))
        
        return {
            'total_proxies': total_proxies,
            'working_proxies': working_proxies,
            'success_rate': total_success / max(1, total_success + total_failures),
            'avg_response_time': avg_response_time,
            'top_performers': sorted(self.proxies, key=lambda p: p.success_count, reverse=True)[:5]
        }
    
    def save_proxy_stats(self, filename: str = 'proxy_stats.json'):
        """Save proxy statistics to file"""
        stats = self.get_stats()
        
        # Convert ProxyInfo objects to dict for JSON serialization
        stats['top_performers'] = [
            {
                'host': p.host,
                'port': p.port,
                'success_count': p.success_count,
                'failure_count': p.failure_count,
                'avg_response_time': p.avg_response_time
            }
            for p in stats['top_performers']
        ]
        
        filepath = f"/Users/matth/{filename}"
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"Proxy stats saved to {filepath}")

class StealthProxyManager(ProxyManager):
    """Enhanced proxy manager with additional stealth features"""
    
    def __init__(self, proxy_list: List[str] = None):
        super().__init__(proxy_list)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.request_delays = {
            'min_delay': 2.0,
            'max_delay': 8.0,
            'burst_delay': 15.0  # Delay after multiple rapid requests
        }
        
        self.last_request_time = 0
        self.request_count = 0
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent for stealth"""
        return random.choice(self.user_agents)
    
    async def get_stealth_delay(self) -> float:
        """Calculate appropriate delay for stealth"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Base delay
        delay = random.uniform(self.request_delays['min_delay'], self.request_delays['max_delay'])
        
        # Add burst protection
        if time_since_last < 5.0 and self.request_count > 5:
            delay += self.request_delays['burst_delay']
            self.logger.info("Applying burst protection delay")
        
        self.last_request_time = current_time
        self.request_count += 1
        
        # Reset request count periodically
        if self.request_count > 50:
            self.request_count = 0
        
        return delay
    
    def get_stealth_headers(self) -> Dict[str, str]:
        """Generate realistic headers for stealth"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

# Example proxy lists (placeholder - replace with actual proxies)
SAMPLE_PROXY_LISTS = {
    'free': [
        # Free proxies (often unreliable)
        '104.207.52.54:8080',
        '45.77.55.173:8080'
    ],
    'premium': [
        # Premium proxy format examples
        # 'http://username:password@proxy1.provider.com:8080',
        # 'http://username:password@proxy2.provider.com:8080'
    ],
    'residential': [
        # Residential proxy format examples  
        # 'http://user:pass@residential.provider.com:8000',
    ]
}

async def test_proxy_manager():
    """Test the proxy manager functionality"""
    print("🌐 Testing Proxy Manager")
    print("=" * 40)
    
    # Initialize with sample proxies (replace with real ones)
    manager = StealthProxyManager(SAMPLE_PROXY_LISTS['free'])
    
    if not manager.proxies:
        print("⚠️  No proxies loaded. Add real proxies to test.")
        return
    
    # Validate proxies
    await manager.validate_all_proxies()
    
    # Get stats
    stats = manager.get_stats()
    print(f"📊 Proxy Stats:")
    print(f"  Total: {stats['total_proxies']}")
    print(f"  Working: {stats['working_proxies']}")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    
    # Test proxy rotation
    for i in range(3):
        proxy = manager.get_next_proxy()
        if proxy:
            print(f"🔄 Using proxy: {proxy.host}:{proxy.port}")
            delay = await manager.get_stealth_delay()
            print(f"⏱️  Stealth delay: {delay:.2f}s")
            await asyncio.sleep(1)  # Reduced for testing
        else:
            print("❌ No working proxies available")
    
    # Save stats
    manager.save_proxy_stats()
    print("💾 Stats saved")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    asyncio.run(test_proxy_manager())