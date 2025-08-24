#!/usr/bin/env python3
"""
TikTok Stealth Analyzer - Production Ready
Enhanced version with authentication, proxies, and request randomization
For authorized red team security assessment
"""

import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from collections import Counter
import logging
import aiohttp
from pathlib import Path

# Import our custom modules
from tiktok_token_extractor import TikTokTokenExtractor
from proxy_manager import StealthProxyManager, ProxyInfo
from TikTokApi import TikTokApi

class TikTokStealthAnalyzer:
    """
    Production-ready TikTok trend analyzer with full stealth capabilities
    """
    
    def __init__(self, config_file: str = None):
        """Initialize with configuration"""
        self.config = self.load_config(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.api = None
        self.token_extractor = TikTokTokenExtractor()
        self.proxy_manager = None
        self.tokens = {}
        
        # Request patterns and randomization
        self.request_patterns = {
            'human_delays': [2.5, 3.2, 4.1, 5.3, 6.8, 8.2, 12.1],  # Fibonacci-like delays
            'burst_patterns': [(3, 15), (5, 30), (2, 45)],  # (requests, delay_after)
            'session_duration': random.randint(300, 1800),  # 5-30 minutes
            'break_duration': random.randint(600, 3600)     # 10-60 minutes
        }
        
        # Analysis data
        self.trend_data = {
            'videos': [],
            'hashtags': [],
            'users': [],
            'temporal_snapshots': [],
            'session_metadata': {
                'start_time': datetime.now().isoformat(),
                'requests_made': 0,
                'proxies_used': [],
                'tokens_rotated': 0
            }
        }
        
        self.session_start_time = time.time()
        self.requests_this_session = 0
        
    def load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'rate_limits': {
                'requests_per_hour': 50,
                'requests_per_session': 100,
                'session_duration_minutes': 30
            },
            'stealth': {
                'min_delay': 3.0,
                'max_delay': 12.0,
                'randomize_user_agents': True,
                'rotate_proxies': True,
                'human_behavior_simulation': True
            },
            'analysis': {
                'max_videos_per_request': 30,
                'hashtag_analysis_depth': 50,
                'export_formats': ['json', 'csv']
            },
            'security': {
                'log_requests': True,
                'save_tokens': True,
                'validate_responses': True
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config {config_file}: {e}")
        
        return default_config
    
    async def initialize(self, proxy_list: List[str] = None, force_token_refresh: bool = False):
        """Initialize all components"""
        self.logger.info("🚀 Initializing TikTok Stealth Analyzer...")
        
        # Initialize proxy manager
        if proxy_list:
            self.proxy_manager = StealthProxyManager(proxy_list)
            await self.proxy_manager.validate_all_proxies()
            working_proxies = len(self.proxy_manager.get_working_proxies())
            self.logger.info(f"📡 Proxy manager initialized: {working_proxies} working proxies")
        
        # Get authentication tokens
        if force_token_refresh or not self.tokens:
            self.tokens = self.token_extractor.get_best_tokens(use_manual_fallback=True)
            
        if not self.tokens.get('msToken'):
            self.logger.warning("⚠️  No valid tokens available. Limited functionality expected.")
        else:
            self.logger.info("🔑 Authentication tokens loaded")
        
        # Initialize TikTok API
        success = await self.initialize_api()
        if not success:
            self.logger.error("❌ Failed to initialize TikTok API")
            return False
        
        self.logger.info("✅ Initialization complete")
        return True
    
    async def initialize_api(self) -> bool:
        """Initialize TikTok API with stealth configuration"""
        try:
            # Get proxy configuration
            proxy_config = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_next_proxy()
                if proxy:
                    proxy_config = self.proxy_manager.get_proxy_url(proxy)
                    self.logger.info(f"Using proxy: {proxy.host}:{proxy.port}")
            
            # Initialize API with available tokens
            ms_token = self.tokens.get('msToken')
            
            self.api = TikTokApi()
            
            # Create sessions with configuration
            await self.api.create_sessions(
                ms_tokens=[ms_token] if ms_token else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
                proxy=proxy_config
            )
            
            self.logger.info("TikTok API initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"API initialization failed: {e}")
            return False
    
    async def human_delay(self, base_delay: float = None) -> float:
        """Implement human-like delays with randomization"""
        if base_delay is None:
            base_delay = random.uniform(
                self.config['stealth']['min_delay'],
                self.config['stealth']['max_delay']
            )
        
        # Add random variation (±20%)
        variation = base_delay * 0.2
        delay = base_delay + random.uniform(-variation, variation)
        
        # Occasionally add longer pauses (simulate reading/thinking)
        if random.random() < 0.15:  # 15% chance
            delay += random.uniform(5, 15)
            self.logger.info("🤔 Adding thinking pause...")
        
        # Track session patterns
        self.requests_this_session += 1
        
        # Implement burst control
        if self.requests_this_session % 10 == 0:
            burst_delay = random.uniform(20, 60)
            delay += burst_delay
            self.logger.info(f"🔄 Burst control: adding {burst_delay:.1f}s delay")
        
        await asyncio.sleep(delay)
        return delay
    
    async def rotate_session(self):
        """Rotate proxy and potentially refresh tokens"""
        if self.proxy_manager:
            new_proxy = self.proxy_manager.get_next_proxy()
            if new_proxy:
                self.logger.info(f"🔄 Rotating to proxy: {new_proxy.host}:{new_proxy.port}")
                self.trend_data['session_metadata']['proxies_used'].append(f"{new_proxy.host}:{new_proxy.port}")
                
                # Re-initialize API with new proxy
                await self.initialize_api()
        
        # Occasionally refresh tokens (every 50 requests)
        if self.requests_this_session % 50 == 0:
            self.logger.info("🔑 Refreshing authentication tokens...")
            new_tokens = self.token_extractor.get_best_tokens(use_manual_fallback=False)
            if new_tokens:
                self.tokens.update(new_tokens)
                self.trend_data['session_metadata']['tokens_rotated'] += 1
    
    async def get_trending_videos_stealth(self, count: int = 30) -> List[Dict]:
        """Fetch trending videos with full stealth measures"""
        if not self.api:
            await self.initialize_api()
        
        self.logger.info(f"📈 Fetching {count} trending videos with stealth...")
        
        trending_videos = []
        video_count = 0
        
        try:
            async for video in self.api.trending.videos(count=count):
                if video_count >= count:
                    break
                
                # Apply human delay before processing each video
                await self.human_delay()
                
                # Rotate session periodically
                if video_count > 0 and video_count % 15 == 0:
                    await self.rotate_session()
                
                # Extract video data
                video_data = await self.extract_video_data_stealth(video)
                if video_data:
                    trending_videos.append(video_data)
                    video_count += 1
                    
                    if video_count % 10 == 0:
                        self.logger.info(f"📊 Processed {video_count}/{count} videos")
                
                # Update session metadata
                self.trend_data['session_metadata']['requests_made'] += 1
                
        except Exception as e:
            self.logger.error(f"Error in stealth video fetching: {e}")
            
            # Mark proxy as failed if we have proxy manager
            if self.proxy_manager:
                current_proxy = self.proxy_manager.get_next_proxy()
                if current_proxy:
                    self.proxy_manager.mark_proxy_failure(current_proxy)
        
        self.trend_data['videos'].extend(trending_videos)
        self.logger.info(f"✅ Successfully fetched {len(trending_videos)} videos")
        
        return trending_videos
    
    async def extract_video_data_stealth(self, video) -> Optional[Dict]:
        """Extract video data with additional stealth measures"""
        try:
            # Simulate reading time
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            video_data = {
                'id': getattr(video, 'id', None),
                'desc': getattr(video, 'desc', ''),
                'create_time': getattr(video, 'create_time', None),
                'hashtags': self.extract_hashtags(getattr(video, 'desc', '')),
                'timestamp': datetime.now().isoformat(),
                'collection_metadata': {
                    'proxy_used': self.get_current_proxy_info(),
                    'session_request_number': self.requests_this_session,
                    'collection_delay': random.uniform(1.0, 3.0)  # Simulate processing time
                }
            }
            
            # Safely extract nested data
            if hasattr(video, 'author') and video.author:
                video_data['author'] = {
                    'unique_id': getattr(video.author, 'unique_id', ''),
                    'nickname': getattr(video.author, 'nickname', ''),
                    'follower_count': getattr(video.author, 'follower_count', 0)
                }
            
            if hasattr(video, 'stats') and video.stats:
                video_data['stats'] = {
                    'digg_count': getattr(video.stats, 'digg_count', 0),
                    'share_count': getattr(video.stats, 'share_count', 0),
                    'comment_count': getattr(video.stats, 'comment_count', 0),
                    'play_count': getattr(video.stats, 'play_count', 0)
                }
            
            if hasattr(video, 'music') and video.music:
                video_data['music'] = {
                    'id': getattr(video.music, 'id', None),
                    'title': getattr(video.music, 'title', ''),
                    'author': getattr(video.music, 'author', '')
                }
            
            return video_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting video data: {e}")
            return None
    
    def get_current_proxy_info(self) -> Optional[str]:
        """Get current proxy information for metadata"""
        if self.proxy_manager:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                return f"{proxy.host}:{proxy.port}"
        return None
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        if not text:
            return []
        
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag.lower() for tag in hashtags]
    
    async def search_hashtag_stealth(self, hashtag: str, count: int = 20) -> List[Dict]:
        """Search hashtag with stealth measures"""
        self.logger.info(f"🏷️  Searching #{hashtag} with stealth...")
        
        if not self.api:
            await self.initialize_api()
        
        try:
            # Apply delay before hashtag search
            await self.human_delay()
            
            hashtag_videos = []
            tag = self.api.hashtag(name=hashtag)
            
            video_count = 0
            async for video in tag.videos(count=count):
                if video_count >= count:
                    break
                
                # Human-like processing delay
                await self.human_delay(base_delay=2.0)
                
                video_data = await self.extract_video_data_stealth(video)
                if video_data:
                    video_data['searched_hashtag'] = hashtag
                    hashtag_videos.append(video_data)
                    video_count += 1
            
            self.logger.info(f"✅ Found {len(hashtag_videos)} videos for #{hashtag}")
            return hashtag_videos
            
        except Exception as e:
            self.logger.error(f"Error searching #{hashtag}: {e}")
            return []
    
    def analyze_trends_advanced(self, videos: List[Dict]) -> Dict:
        """Advanced trend analysis with enhanced metrics"""
        if not videos:
            return {}
        
        hashtag_data = {}
        engagement_data = {}
        temporal_data = {}
        author_data = {}
        
        # Analyze each video
        for video in videos:
            # Hashtag analysis
            for hashtag in video.get('hashtags', []):
                if hashtag not in hashtag_data:
                    hashtag_data[hashtag] = {
                        'count': 0,
                        'total_engagement': 0,
                        'videos': [],
                        'avg_engagement': 0,
                        'peak_engagement': 0
                    }
                
                hashtag_data[hashtag]['count'] += 1
                hashtag_data[hashtag]['videos'].append(video['id'])
                
                # Calculate engagement
                stats = video.get('stats', {})
                engagement = (
                    stats.get('digg_count', 0) * 1 +
                    stats.get('share_count', 0) * 3 +
                    stats.get('comment_count', 0) * 5
                )
                
                hashtag_data[hashtag]['total_engagement'] += engagement
                hashtag_data[hashtag]['peak_engagement'] = max(
                    hashtag_data[hashtag]['peak_engagement'], engagement
                )
            
            # Author analysis
            author = video.get('author', {})
            if author.get('unique_id'):
                author_id = author['unique_id']
                if author_id not in author_data:
                    author_data[author_id] = {
                        'video_count': 0,
                        'total_engagement': 0,
                        'follower_count': author.get('follower_count', 0)
                    }
                
                author_data[author_id]['video_count'] += 1
                author_data[author_id]['total_engagement'] += engagement
        
        # Calculate averages
        for hashtag in hashtag_data:
            if hashtag_data[hashtag]['count'] > 0:
                hashtag_data[hashtag]['avg_engagement'] = (
                    hashtag_data[hashtag]['total_engagement'] / hashtag_data[hashtag]['count']
                )
        
        # Sort and rank
        top_hashtags = sorted(
            hashtag_data.items(),
            key=lambda x: x[1]['total_engagement'],
            reverse=True
        )[:20]
        
        top_authors = sorted(
            author_data.items(),
            key=lambda x: x[1]['total_engagement'],
            reverse=True
        )[:10]
        
        return {
            'hashtag_analysis': {
                'total_unique_hashtags': len(hashtag_data),
                'top_hashtags': [(tag, data['count'], data['total_engagement']) 
                                for tag, data in top_hashtags],
                'detailed_hashtag_data': dict(top_hashtags)
            },
            'author_analysis': {
                'total_unique_authors': len(author_data),
                'top_performing_authors': top_authors
            },
            'engagement_summary': {
                'total_videos_analyzed': len(videos),
                'total_engagement_calculated': sum(
                    video.get('stats', {}).get('digg_count', 0) +
                    video.get('stats', {}).get('share_count', 0) +
                    video.get('stats', {}).get('comment_count', 0)
                    for video in videos
                ),
                'avg_engagement_per_video': sum(
                    video.get('stats', {}).get('digg_count', 0) +
                    video.get('stats', {}).get('share_count', 0) +
                    video.get('stats', {}).get('comment_count', 0)
                    for video in videos
                ) / len(videos) if videos else 0
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def export_comprehensive_data(self, filename_prefix: str = None) -> Dict[str, str]:
        """Export all collected data in multiple formats"""
        if not filename_prefix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = f"tiktok_stealth_analysis_{timestamp}"
        
        exported_files = {}
        
        # JSON export (complete data)
        json_file = f"/Users/matth/{filename_prefix}.json"
        with open(json_file, 'w') as f:
            json.dump(self.trend_data, f, indent=2, default=str)
        exported_files['json'] = json_file
        
        # CSV export (flattened video data)
        if self.trend_data['videos']:
            csv_file = f"/Users/matth/{filename_prefix}.csv"
            video_records = []
            
            for video in self.trend_data['videos']:
                record = {
                    'video_id': video.get('id', ''),
                    'description': video.get('desc', ''),
                    'author_id': video.get('author', {}).get('unique_id', ''),
                    'author_nickname': video.get('author', {}).get('nickname', ''),
                    'likes': video.get('stats', {}).get('digg_count', 0),
                    'shares': video.get('stats', {}).get('share_count', 0),
                    'comments': video.get('stats', {}).get('comment_count', 0),
                    'plays': video.get('stats', {}).get('play_count', 0),
                    'hashtags': ', '.join(video.get('hashtags', [])),
                    'collection_timestamp': video.get('timestamp', ''),
                    'proxy_used': video.get('collection_metadata', {}).get('proxy_used', '')
                }
                video_records.append(record)
            
            df = pd.DataFrame(video_records)
            df.to_csv(csv_file, index=False)
            exported_files['csv'] = csv_file
        
        # Analysis report
        if self.trend_data['videos']:
            analysis = self.analyze_trends_advanced(self.trend_data['videos'])
            report_file = f"/Users/matth/{filename_prefix}_analysis_report.json"
            with open(report_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            exported_files['analysis'] = report_file
        
        self.logger.info(f"📁 Data exported to {len(exported_files)} files")
        return exported_files
    
    async def run_comprehensive_stealth_analysis(
        self, 
        target_hashtags: List[str] = None, 
        max_videos: int = 50
    ) -> Dict:
        """Run complete stealth analysis workflow"""
        self.logger.info("🎯 Starting comprehensive stealth analysis...")
        
        start_time = time.time()
        
        try:
            # Get trending videos with stealth
            trending_videos = await self.get_trending_videos_stealth(count=max_videos)
            
            # Search specific hashtags if provided
            if target_hashtags:
                for hashtag in target_hashtags[:3]:  # Limit to avoid over-requesting
                    await self.human_delay(base_delay=10.0)  # Longer delay between hashtag searches
                    hashtag_videos = await self.search_hashtag_stealth(hashtag, count=15)
                    self.trend_data['videos'].extend(hashtag_videos)
            
            # Perform advanced analysis
            analysis_results = self.analyze_trends_advanced(self.trend_data['videos'])
            
            # Export all data
            exported_files = self.export_comprehensive_data()
            
            # Generate final report
            execution_time = time.time() - start_time
            
            report = {
                'execution_summary': {
                    'start_time': datetime.fromtimestamp(start_time).isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'execution_time_seconds': execution_time,
                    'total_videos_collected': len(self.trend_data['videos']),
                    'requests_made': self.trend_data['session_metadata']['requests_made'],
                    'proxies_used': len(set(self.trend_data['session_metadata']['proxies_used'])),
                    'tokens_rotated': self.trend_data['session_metadata']['tokens_rotated']
                },
                'analysis_results': analysis_results,
                'exported_files': exported_files,
                'stealth_metrics': {
                    'avg_delay_per_request': execution_time / max(1, self.requests_this_session),
                    'stealth_score': self.calculate_stealth_score()
                }
            }
            
            self.logger.info(f"✅ Analysis completed in {execution_time:.2f} seconds")
            return report
            
        except Exception as e:
            error_report = {
                'error': str(e),
                'partial_data': {
                    'videos_collected': len(self.trend_data['videos']),
                    'requests_made': self.trend_data['session_metadata']['requests_made']
                }
            }
            self.logger.error(f"❌ Analysis failed: {e}")
            return error_report
    
    def calculate_stealth_score(self) -> float:
        """Calculate stealth effectiveness score (0-100)"""
        score = 100.0
        
        # Deduct for high request rate
        if self.requests_this_session > 0:
            request_rate = self.requests_this_session / max(1, time.time() - self.session_start_time)
            if request_rate > 0.5:  # More than 1 request per 2 seconds
                score -= min(20, (request_rate - 0.5) * 40)
        
        # Add points for proxy usage
        if self.proxy_manager and len(self.trend_data['session_metadata']['proxies_used']) > 0:
            score += 10
        
        # Add points for token rotation
        if self.trend_data['session_metadata']['tokens_rotated'] > 0:
            score += 5
        
        return max(0, min(100, score))

# Configuration and testing
async def main():
    """Main execution function"""
    print("🎯 TikTok Stealth Analyzer - Production Version")
    print("=" * 60)
    
    # Sample configuration
    sample_proxies = [
        # Add your proxy list here
        # 'http://username:password@proxy1.com:8080',
        # 'proxy2.com:3128'
    ]
    
    # Initialize analyzer
    analyzer = TikTokStealthAnalyzer()
    
    # Initialize with proxy support
    success = await analyzer.initialize(proxy_list=sample_proxies if sample_proxies else None)
    
    if not success:
        print("❌ Initialization failed")
        return
    
    # Run comprehensive analysis
    target_hashtags = ['viral', 'trending', 'fyp']
    results = await analyzer.run_comprehensive_stealth_analysis(
        target_hashtags=target_hashtags,
        max_videos=30  # Reduced for testing
    )
    
    print("\n📊 Analysis Results:")
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
    else:
        summary = results.get('execution_summary', {})
        print(f"✅ Videos collected: {summary.get('total_videos_collected', 0)}")
        print(f"🕐 Execution time: {summary.get('execution_time_seconds', 0):.2f}s")
        print(f"🔄 Requests made: {summary.get('requests_made', 0)}")
        print(f"🌐 Proxies used: {summary.get('proxies_used', 0)}")
        print(f"🎯 Stealth score: {results.get('stealth_metrics', {}).get('stealth_score', 0):.1f}/100")
        
        exported = results.get('exported_files', {})
        print(f"📁 Files exported: {len(exported)}")
        for file_type, filepath in exported.items():
            print(f"  - {file_type.upper()}: {filepath}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())