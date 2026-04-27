import requests

API_URL = "https://tele.alreadytaken.me"
TARGET_CHANNEL = "-1003737951848"

endpoints = [
    f"{API_URL}/api/send",
    f"{API_URL}/api/text",
    f"{API_URL}/api/messages",
    f"{API_URL}/api/mirror/send",
    f"{API_URL}/api/v1/send"
]

payload = {
    "channel_id": TARGET_CHANNEL,
    "text": "🤖 **TEST LOG**\nTesting endpoints..."
}

for url in endpoints:
    try:
        r = requests.post(url, json=payload, timeout=3)
        print(f"URL: {url} | Status: {r.status_code} | Response: {r.text[:50]}")
    except Exception as e:
        print(f"URL: {url} | Error: {e}")
