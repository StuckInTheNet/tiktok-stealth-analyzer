#!/usr/bin/env python3
"""
Setup Verification Script
Test tokens, proxies, and configuration before production use
"""

import asyncio
import json
import sys
from pathlib import Path

def test_token_extraction():
    """Test 1: Token Extraction"""
    print("🔐 Testing Token Extraction...")
    
    try:
        from tiktok_token_extractor import TikTokTokenExtractor
        extractor = TikTokTokenExtractor()
        
        # Try to load existing tokens
        tokens = extractor.load_tokens()
        
        if tokens and tokens.get('msToken'):
            print(f"✅ Found saved tokens: {len(tokens)} tokens")
            print(f"   msToken: {tokens.get('msToken', '')[:20]}...")
            return True, tokens
        else:
            print("⚠️  No saved tokens found")
            print("   Run: python tiktok_token_extractor.py")
            return False, {}
            
    except Exception as e:
        print(f"❌ Token extraction failed: {e}")
        return False, {}

async def test_proxy_manager():
    """Test 2: Proxy Infrastructure"""
    print("\n🌐 Testing Proxy Manager...")
    
    try:
        from proxy_manager import StealthProxyManager
        
        # Test with sample proxies (will fail but tests code)
        sample_proxies = ['http://test.proxy.com:8080']
        manager = StealthProxyManager(sample_proxies)
        
        print(f"✅ Proxy manager initialized with {len(manager.proxies)} proxies")
        
        # Test proxy validation (will show failures for fake proxies)
        await manager.validate_all_proxies()
        working = len(manager.get_working_proxies())
        
        if working > 0:
            print(f"✅ Found {working} working proxies")
            return True
        else:
            print("⚠️  No working proxies found")
            print("   Add real proxy URLs to test connectivity")
            return False
            
    except Exception as e:
        print(f"❌ Proxy manager failed: {e}")
        return False

def test_configuration():
    """Test 3: Configuration System"""
    print("\n⚙️  Testing Configuration...")
    
    try:
        config_path = Path("config.json")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print("✅ Configuration file loaded")
            
            # Validate key sections
            required_sections = ['rate_limits', 'stealth', 'analysis']
            missing = [s for s in required_sections if s not in config]
            
            if not missing:
                print("✅ All required configuration sections present")
                
                # Show key settings
                rate_limits = config.get('rate_limits', {})
                print(f"   Rate limit: {rate_limits.get('requests_per_hour', 50)}/hour")
                
                stealth = config.get('stealth', {})
                print(f"   Delay range: {stealth.get('min_delay', 3)}-{stealth.get('max_delay', 12)}s")
                
                return True, config
            else:
                print(f"⚠️  Missing sections: {missing}")
                return False, config
        else:
            print("❌ config.json not found")
            return False, {}
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False, {}

async def test_stealth_analyzer():
    """Test 4: Main Analyzer (API test)"""
    print("\n🎯 Testing Stealth Analyzer...")
    
    try:
        from tiktok_stealth_analyzer import TikTokStealthAnalyzer
        
        analyzer = TikTokStealthAnalyzer()
        print("✅ Analyzer initialized")
        
        # Test API initialization (will likely fail without valid tokens/proxies)
        success = await analyzer.initialize_api()
        
        if success:
            print("✅ TikTok API initialized successfully")
            return True
        else:
            print("⚠️  TikTok API initialization failed (expected without valid tokens)")
            print("   This is normal for testing - API will work with proper setup")
            return False
            
    except Exception as e:
        print(f"❌ Analyzer test failed: {e}")
        return False

def check_dependencies():
    """Test 5: Dependencies"""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        'TikTokApi',
        'playwright', 
        'aiohttp',
        'pandas',
        'browser_cookie3'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - missing")
            missing.append(package)
    
    if not missing:
        print("✅ All dependencies installed")
        return True
    else:
        print(f"\n⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False

async def run_full_test():
    """Run complete setup verification"""
    print("🧪 TikTok Stealth Analyzer - Setup Verification")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Dependencies
    results['dependencies'] = check_dependencies()
    
    # Test 2: Configuration
    results['config'], config_data = test_configuration()
    
    # Test 3: Token extraction
    results['tokens'], token_data = test_token_extraction()
    
    # Test 4: Proxy manager
    results['proxies'] = await test_proxy_manager()
    
    # Test 5: Main analyzer
    results['analyzer'] = await test_stealth_analyzer()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SETUP VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():15} {status}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    # Recommendations
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your setup is ready for production use.")
    else:
        print(f"\n⚠️  {total - passed} issues found. Recommendations:")
        
        if not results['dependencies']:
            print("   1. Run: pip install -r requirements.txt")
            
        if not results['tokens']:
            print("   2. Run: python tiktok_token_extractor.py")
            
        if not results['proxies']:
            print("   3. Add real proxy URLs and test connectivity")
            
        if not results['config']:
            print("   4. Check config.json format and required sections")
            
        if not results['analyzer']:
            print("   5. Fix tokens/proxies - analyzer needs valid credentials")
    
    # Next steps
    print("\n📋 NEXT STEPS:")
    if results['tokens'] and results['config']:
        print("1. Add your proxy list to the configuration")
        print("2. Run: python tiktok_stealth_analyzer.py")  
        print("3. Monitor stealth scores and adjust as needed")
    else:
        print("1. Fix the failed tests above")
        print("2. Follow the SETUP_GUIDE.md for detailed instructions")
        print("3. Re-run this test when issues are resolved")

if __name__ == "__main__":
    asyncio.run(run_full_test())