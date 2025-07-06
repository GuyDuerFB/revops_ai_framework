#!/usr/bin/env python3
"""
Test Slack-Bedrock Integration
"""

import json
import time
import hmac
import hashlib
import requests

# Test configuration
API_GATEWAY_URL = "https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events"
SIGNING_SECRET = "7649bbaf1ac9ca3a971484ba76b36504"

def create_slack_signature(timestamp, body, secret):
    """Create Slack signature for request verification"""
    sig_basestring = f'v0:{timestamp}:{body}'
    signature = 'v0=' + hmac.new(
        secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_url_verification():
    """Test URL verification challenge"""
    print("🧪 Testing URL Verification...")
    
    challenge = "test_challenge_123"
    payload = {
        "type": "url_verification",
        "challenge": challenge
    }
    
    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = create_slack_signature(timestamp, body, SIGNING_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': signature
    }
    
    try:
        response = requests.post(API_GATEWAY_URL, data=body, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.text == challenge:
            print("✅ URL Verification: PASSED")
            return True
        else:
            print(f"❌ URL Verification: FAILED - {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ URL Verification: ERROR - {e}")
        return False

def test_app_mention():
    """Test app mention event (simulated)"""
    print("🧪 Testing App Mention Event...")
    
    payload = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "user": "U123456789",
            "text": "<@UBOT123456> What workflows are available?",
            "channel": "C123456789",
            "ts": str(time.time())
        },
        "team_id": "T123456789",
        "api_app_id": "A094GD826SD"
    }
    
    body = json.dumps(payload)
    timestamp = str(int(time.time()))
    signature = create_slack_signature(timestamp, body, SIGNING_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': signature
    }
    
    try:
        response = requests.post(API_GATEWAY_URL, data=body, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ App Mention Event: ACCEPTED")
            print(f"   Response: {response.text}")
            return True
        else:
            print(f"❌ App Mention Event: FAILED - {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ App Mention Event: ERROR - {e}")
        return False

def main():
    print("🚀 RevBot Slack Integration Test")
    print("=" * 50)
    
    # Test URL verification
    url_test = test_url_verification()
    
    print()
    
    # Test app mention
    mention_test = test_app_mention()
    
    print()
    print("📊 Test Results:")
    print(f"   URL Verification: {'✅ PASS' if url_test else '❌ FAIL'}")
    print(f"   App Mention: {'✅ PASS' if mention_test else '❌ FAIL'}")
    
    if url_test and mention_test:
        print("\n🎉 Integration is ready! You can now test in Slack:")
        print("   • Mention @RevBot in a channel")
        print("   • Send a DM to RevBot")
        print("   • Ask: 'What workflows are available for deal assessment?'")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and try again.")

if __name__ == "__main__":
    main()