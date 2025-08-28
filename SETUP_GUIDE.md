# Production Setup Guide
## Getting TikTok Tokens, Proxies, and Configuration

---

## 🔐 1. Getting Valid TikTok Tokens

### Method A: Automatic Extraction (Recommended)
```bash
# Run the token extractor
python tiktok_token_extractor.py
```

**What it does:**
- Scans Chrome, Firefox, Safari for TikTok cookies
- Extracts `msToken`, `tt_webid`, `tt_webid_v2`
- Saves tokens for reuse

### Method B: Manual Extraction
If automatic extraction fails:

1. **Open TikTok.com in your browser**
2. **Log in** (optional but improves token quality)
3. **Open Developer Tools** (F12)
4. **Go to Application/Storage tab**
5. **Navigate to Cookies → tiktok.com**
6. **Copy these values:**
   - `msToken` (most critical)
   - `tt_webid`
   - `tt_webid_v2`
   - `sessionid` (if logged in)

**Manual input:**
```bash
python tiktok_token_extractor.py
# Follow prompts to enter tokens manually
```

### Method C: Browser Extension (Advanced)
For continuous token refresh:

```javascript
// Chrome DevTools Console
// Extract current tokens
const tokens = {};
document.cookie.split(';').forEach(cookie => {
    const [name, value] = cookie.trim().split('=');
    if (['msToken', 'tt_webid', 'tt_webid_v2', 'sessionid'].includes(name)) {
        tokens[name] = value;
    }
});
console.log(JSON.stringify(tokens, null, 2));
```

---

## 🌐 2. Proxy Infrastructure Setup

### Recommended Proxy Providers

#### **Tier 1: Premium Residential** (Best for red team)
- **Smartproxy**: `https://smartproxy.com`
  - Price: $7-12/GB
  - Features: 40M+ IPs, session control
  - Setup: HTTP/SOCKS5 endpoints

- **Bright Data** (formerly Luminati): `https://brightdata.com`
  - Price: $15-20/GB
  - Features: 72M+ IPs, enterprise grade
  - Best for: Large-scale operations

- **ProxyEmpire**: `https://proxyempire.io`
  - Price: $2.5-7/GB  
  - Features: Rotating residential IPs
  - Good for: Budget-conscious operations

#### **Tier 2: Datacenter Proxies** (Moderate detection risk)
- **MyPrivateProxy**: `https://myprivateproxy.net`
  - Price: $1-3/proxy/month
  - Features: Fast, dedicated IPs
  - Risk: Higher detection rate

- **Rayobyte**: `https://rayobyte.com`
  - Price: $2-5/proxy/month
  - Features: US-based, good speeds

#### **Tier 3: Free/Public** (High detection risk)
- Use only for testing
- Very limited functionality expected

### Proxy Setup Steps

#### **1. Sign up with provider**
Choose based on budget and scale:
- **Small scale**: 1-5GB/month residential
- **Medium scale**: 10-50GB/month residential  
- **Large scale**: 100GB+ with dedicated account manager

#### **2. Get credentials**
Most providers give you:
```
Username: user123
Password: pass456
Endpoint: rotating.provider.com:8000
```

#### **3. Configure in your code**
```python
proxy_list = [
    'http://user123:pass456@rotating.provider.com:8000',
    'http://user123:pass456@session1.provider.com:8001',
    'http://user123:pass456@session2.provider.com:8002'
]

analyzer = TikTokStealthAnalyzer()
await analyzer.initialize(proxy_list=proxy_list)
```

### Proxy Testing
```bash
# Test proxy connectivity
python proxy_manager.py
```

---

## ⚙️ 3. Configuration Tuning

### Basic Configuration (config.json)

#### **Conservative Setup** (Low detection risk)
```json
{
  "rate_limits": {
    "requests_per_hour": 30,
    "requests_per_session": 50
  },
  "stealth": {
    "min_delay": 5.0,
    "max_delay": 20.0,
    "thinking_pause_chance": 0.25
  }
}
```

#### **Aggressive Setup** (Higher throughput, more risk)
```json
{
  "rate_limits": {
    "requests_per_hour": 100,
    "requests_per_session": 200
  },
  "stealth": {
    "min_delay": 2.0,
    "max_delay": 8.0,
    "thinking_pause_chance": 0.10
  }
}
```

#### **Red Team Optimized** (Balanced for assessments)
```json
{
  "rate_limits": {
    "requests_per_hour": 50,
    "requests_per_session": 100,
    "session_duration_minutes": 30
  },
  "stealth": {
    "min_delay": 3.0,
    "max_delay": 12.0,
    "burst_delay": 25.0,
    "thinking_pause_chance": 0.15,
    "rotate_proxies": true,
    "human_behavior_simulation": true
  },
  "analysis": {
    "max_videos_per_request": 30,
    "hashtag_analysis_depth": 50
  }
}
```

### Environment-Specific Tuning

#### **Corporate Environment**
```json
{
  "proxy_configuration": {
    "rotation_strategy": "round_robin",
    "health_check_interval": 180,
    "max_failures_per_proxy": 3
  },
  "security": {
    "log_requests": true,
    "anonymize_user_data": true,
    "secure_token_storage": true
  }
}
```

#### **Cloud Deployment**
```json
{
  "output": {
    "base_directory": "/app/data",
    "compress_exports": true
  },
  "compliance": {
    "data_retention_days": 7,
    "respect_robots_txt": true
  }
}
```

---

## 🚀 Quick Setup Commands

### Complete Setup Sequence
```bash
# 1. Clone and install
git clone https://github.com/StuckInTheNet/tiktok-stealth-analyzer.git
cd tiktok-stealth-analyzer
pip install -r requirements.txt
python -m playwright install

# 2. Extract tokens
python tiktok_token_extractor.py

# 3. Test proxy connectivity (add your proxies)
python proxy_manager.py

# 4. Run analysis
python tiktok_stealth_analyzer.py
```

### Production Checklist
- [ ] Valid `msToken` extracted and saved
- [ ] Proxy provider account configured  
- [ ] At least 3 working proxies verified
- [ ] Configuration tuned for use case
- [ ] Rate limits appropriate for timeline
- [ ] Logging and monitoring enabled
- [ ] Data export directory configured

---

## 💰 Cost Estimates

### Monthly Operational Costs

| Scale | Proxy Cost | Requests/Day | Detection Risk |
|-------|------------|-------------|----------------|
| **Small** | $20-50 | 500-1000 | Low |
| **Medium** | $100-300 | 2000-5000 | Low-Medium |
| **Large** | $500-1500 | 10000+ | Medium |

### ROI for Red Team
- **Traditional manual analysis**: 40+ hours
- **With this toolkit**: 2-4 hours
- **Time savings**: 90%+
- **Data quality**: Significantly higher

---

## 🔧 Troubleshooting

### Common Issues

#### **"No valid tokens found"**
```bash
# Solution 1: Manual extraction
python tiktok_token_extractor.py
# Follow manual input prompts

# Solution 2: Fresh browser session
# 1. Clear TikTok cookies
# 2. Visit tiktok.com
# 3. Re-extract tokens
```

#### **"All proxies failed"**
```bash
# Test connectivity
curl --proxy http://user:pass@proxy.com:8000 https://httpbin.org/ip

# Check proxy format
# Correct: http://user:pass@proxy.com:8000
# Incorrect: proxy.com:8000 (missing protocol)
```

#### **"Rate limit exceeded"**
- Reduce `requests_per_hour` in config
- Increase delays in `stealth` section
- Add more proxies for rotation

### Getting Help
1. Check logs in `tiktok_analysis.log`
2. Validate configuration with test runs
3. Monitor stealth scores during operation
4. Adjust parameters based on detection feedback

---

## 🛡️ Security Best Practices

1. **Never commit tokens to git**
2. **Use different proxy pools for different targets**
3. **Rotate tokens regularly (every 24-48 hours)**
4. **Monitor for detection indicators**
5. **Keep request patterns randomized**
6. **Use VPN + residential proxies for maximum stealth**

---

*Ready for production deployment with proper tokens, proxies, and configuration!*