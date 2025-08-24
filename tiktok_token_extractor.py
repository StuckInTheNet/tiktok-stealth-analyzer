#!/usr/bin/env python3
"""
TikTok Token Extractor
Extracts authentication tokens from browser sessions for red team analysis
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import browser_cookie3
import logging
from datetime import datetime

class TikTokTokenExtractor:
    """Extract TikTok authentication tokens from browser sessions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tokens = {}
        
    def extract_from_chrome(self) -> Dict[str, str]:
        """Extract tokens from Chrome browser"""
        try:
            cookies = browser_cookie3.chrome(domain_name='tiktok.com')
            tokens = {}
            
            for cookie in cookies:
                if cookie.name in ['msToken', 'tt_webid', 'tt_webid_v2', 'sessionid']:
                    tokens[cookie.name] = cookie.value
                    self.logger.info(f"Extracted {cookie.name} from Chrome")
                    
            return tokens
        except Exception as e:
            self.logger.error(f"Failed to extract from Chrome: {e}")
            return {}
    
    def extract_from_firefox(self) -> Dict[str, str]:
        """Extract tokens from Firefox browser"""
        try:
            cookies = browser_cookie3.firefox(domain_name='tiktok.com')
            tokens = {}
            
            for cookie in cookies:
                if cookie.name in ['msToken', 'tt_webid', 'tt_webid_v2', 'sessionid']:
                    tokens[cookie.name] = cookie.value
                    self.logger.info(f"Extracted {cookie.name} from Firefox")
                    
            return tokens
        except Exception as e:
            self.logger.error(f"Failed to extract from Firefox: {e}")
            return {}
    
    def extract_from_safari(self) -> Dict[str, str]:
        """Extract tokens from Safari browser"""
        try:
            cookies = browser_cookie3.safari(domain_name='tiktok.com')
            tokens = {}
            
            for cookie in cookies:
                if cookie.name in ['msToken', 'tt_webid', 'tt_webid_v2', 'sessionid']:
                    tokens[cookie.name] = cookie.value
                    self.logger.info(f"Extracted {cookie.name} from Safari")
                    
            return tokens
        except Exception as e:
            self.logger.error(f"Failed to extract from Safari: {e}")
            return {}
    
    def extract_all_browsers(self) -> Dict[str, Dict[str, str]]:
        """Extract tokens from all available browsers"""
        all_tokens = {
            'chrome': self.extract_from_chrome(),
            'firefox': self.extract_from_firefox(),
            'safari': self.extract_from_safari()
        }
        
        # Find the most complete token set
        best_browser = max(all_tokens.keys(), key=lambda k: len(all_tokens[k]))
        
        if all_tokens[best_browser]:
            self.logger.info(f"Best token source: {best_browser}")
            self.tokens = all_tokens[best_browser]
        
        return all_tokens
    
    def manual_token_input(self) -> Dict[str, str]:
        """Allow manual token input for cases where automatic extraction fails"""
        print("\n🔑 Manual Token Input")
        print("To get tokens manually:")
        print("1. Open TikTok.com in your browser")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Application/Storage tab")
        print("4. Find Cookies for tiktok.com")
        print("5. Look for: msToken, tt_webid, tt_webid_v2")
        print()
        
        tokens = {}
        required_tokens = ['msToken', 'tt_webid', 'tt_webid_v2']
        
        for token_name in required_tokens:
            value = input(f"Enter {token_name} (or press Enter to skip): ").strip()
            if value:
                tokens[token_name] = value
        
        return tokens
    
    def save_tokens(self, tokens: Dict[str, str], filename: str = 'tiktok_tokens.json'):
        """Save tokens to file for reuse"""
        filepath = f"/Users/matth/{filename}"
        
        token_data = {
            'tokens': tokens,
            'extracted_at': datetime.now().isoformat(),
            'expires_note': 'Tokens may expire. Re-extract if analysis fails.'
        }
        
        with open(filepath, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        self.logger.info(f"Tokens saved to {filepath}")
        return filepath
    
    def load_tokens(self, filename: str = 'tiktok_tokens.json') -> Dict[str, str]:
        """Load previously saved tokens"""
        filepath = f"/Users/matth/{filename}"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            tokens = data.get('tokens', {})
            extracted_at = data.get('extracted_at', 'Unknown')
            
            self.logger.info(f"Loaded tokens from {filepath} (extracted: {extracted_at})")
            return tokens
            
        except FileNotFoundError:
            self.logger.warning(f"Token file not found: {filepath}")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load tokens: {e}")
            return {}
    
    def validate_tokens(self, tokens: Dict[str, str]) -> bool:
        """Basic validation of extracted tokens"""
        required = ['msToken']  # msToken is most critical
        
        for req in required:
            if req not in tokens or not tokens[req]:
                self.logger.warning(f"Missing required token: {req}")
                return False
        
        # Check token format (basic validation)
        ms_token = tokens.get('msToken', '')
        if len(ms_token) < 50:  # msTokens are typically longer
            self.logger.warning("msToken appears too short")
            return False
        
        self.logger.info("Token validation passed")
        return True
    
    def get_best_tokens(self, use_manual_fallback: bool = True) -> Dict[str, str]:
        """Get the best available tokens with fallback options"""
        
        # Try loading existing tokens first
        tokens = self.load_tokens()
        if tokens and self.validate_tokens(tokens):
            self.logger.info("Using previously saved tokens")
            return tokens
        
        # Try automatic extraction
        self.logger.info("Attempting automatic token extraction...")
        all_browser_tokens = self.extract_all_browsers()
        
        # Find best token set
        for browser, browser_tokens in all_browser_tokens.items():
            if browser_tokens and self.validate_tokens(browser_tokens):
                self.logger.info(f"Using tokens from {browser}")
                self.save_tokens(browser_tokens)
                return browser_tokens
        
        # Manual fallback if automatic extraction fails
        if use_manual_fallback:
            self.logger.warning("Automatic extraction failed. Trying manual input...")
            manual_tokens = self.manual_token_input()
            if manual_tokens and self.validate_tokens(manual_tokens):
                self.save_tokens(manual_tokens)
                return manual_tokens
        
        self.logger.error("No valid tokens found")
        return {}

def main():
    """Test the token extractor"""
    print("🔑 TikTok Token Extractor")
    print("=" * 40)
    
    extractor = TikTokTokenExtractor()
    tokens = extractor.get_best_tokens()
    
    if tokens:
        print("✅ Successfully extracted tokens:")
        for token_name, token_value in tokens.items():
            print(f"  {token_name}: {token_value[:20]}...")
        print(f"\n💾 Tokens saved for use in analyzer")
    else:
        print("❌ Failed to extract tokens")
        print("Manual extraction may be required")
    
    return tokens

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()