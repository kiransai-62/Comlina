import sys
import os
import time
import json
import hmac
import hashlib
import base64
import urllib.request
import urllib.error
import urllib.parse

sys.path.insert(0, 'server')
from app.core.config import settings
import jwt

print("=== COMLINA BACKEND QA TEST SUITE ===")

# 1. Generate auth token
exp = int(time.time()) + 86400
payload = {
    'sub': '00000000-0000-0000-0000-000000000001',
    'email': 'qa@comlina.com',
    'role': 'authenticated',
    'aud': 'authenticated',
    'exp': exp
}
token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')
auth_header = {'Authorization': f'Bearer {token}'}

# --- Item 24: GET /api/analytics/summary ---
print("\n--- ITEM 24: GET /api/analytics/summary ---")
expected_keys = {
    'workspace_id', 'total_automations', 'active_automations',
    'total_leads', 'converted_leads', 'conversion_rate_pct',
    'stats_comments', 'stats_dms_sent', 'stats_clicks'
}
req = urllib.request.Request('http://localhost:8000/api/analytics/summary', headers=auth_header)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"Status: {resp.status}")
        print(f"Keys returned: {list(data.keys())}")
        missing_keys = expected_keys - set(data.keys())
        if not missing_keys:
            print("ITEM 24 RESULT: PASS - All expected keys present.")
        else:
            print(f"ITEM 24 RESULT: FAIL - Missing keys: {missing_keys}")
except Exception as e:
    print(f"ITEM 24 RESULT: FAIL - {e}")

# --- Item 25: GET /api/instagram/media ---
print("\n--- ITEM 25: GET /api/instagram/media ---")
# 25a: Without token
req_no_auth = urllib.request.Request('http://localhost:8000/api/instagram/media')
try:
    urllib.request.urlopen(req_no_auth)
    print("25a (no token): FAIL - Expected 401 but got 200")
except urllib.error.HTTPError as e:
    if e.code == 401:
        print("25a (no token): PASS - Got 401 Unauthorized")
    else:
        print(f"25a (no token): FAIL - Expected 401, got {e.code}")

# 25b: With token and fake account
req_auth = urllib.request.Request('http://localhost:8000/api/instagram/media', headers=auth_header)
try:
    with urllib.request.urlopen(req_auth) as resp:
        print(f"25b (with token): Got {resp.status}: {resp.read().decode()}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if 400 <= e.code < 600:
        print(f"25b (with token): PASS - Got clear {e.code} JSON error: {body}")
    else:
        print(f"25b (with token): FAIL - Unexpected status {e.code}: {body}")

# --- Item 26: POST /webhooks/instagram (signature verification & idempotency) ---
print("\n--- ITEM 26: POST /webhooks/instagram ---")
webhook_payload = json.dumps({
    "object": "instagram",
    "entry": [
        {
            "id": "17841400000000000",
            "time": int(time.time()),
            "changes": [
                {
                    "field": "comments",
                    "value": {
                        "id": "item26_test_comment_unique_1",
                        "text": "test price please",
                        "from": {"id": "user_123", "username": "test_user"},
                        "media": {"id": "media_456"}
                    }
                }
            ]
        }
    ]
}).encode('utf-8')

def sign_payload(body: bytes, secret: str) -> str:
    h = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    return f"sha256={h}"

valid_sig = sign_payload(webhook_payload, settings.META_APP_SECRET)
bad_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

# 26a: Bad signature -> 403
req_bad = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram',
    data=webhook_payload,
    headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': bad_sig}
)
try:
    urllib.request.urlopen(req_bad)
    print("26a (bad signature): FAIL - Expected 403, got 200")
except urllib.error.HTTPError as e:
    if e.code == 403:
        print("26a (bad signature): PASS - Got 403 Forbidden")
    else:
        print(f"26a (bad signature): FAIL - Expected 403, got {e.code}")

# 26b: Valid signature -> 200
req_valid1 = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram',
    data=webhook_payload,
    headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': valid_sig}
)
try:
    with urllib.request.urlopen(req_valid1) as resp:
        print(f"26b (first delivery): Status {resp.status} - {resp.read().decode()}")
except urllib.error.HTTPError as e:
    print(f"26b (first delivery): Error {e.code} - {e.read().decode()}")

# 26c: Same delivery second time (idempotency) -> accepted / deduplicated
req_valid2 = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram',
    data=webhook_payload,
    headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': valid_sig}
)
try:
    with urllib.request.urlopen(req_valid2) as resp:
        print(f"26c (second delivery): Status {resp.status} - {resp.read().decode()}")
except urllib.error.HTTPError as e:
    print(f"26c (second delivery): Error {e.code} - {e.read().decode()}")

# --- Item 27: POST /webhooks/instagram/data-deletion & /deauthorize ---
print("\n--- ITEM 27: Meta Data Deletion & Deauthorize ---")

def build_signed_request(payload_dict: dict, secret: str) -> str:
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode('utf-8')).decode('utf-8').rstrip('=')
    sig = hmac.new(secret.encode('utf-8'), encoded_payload.encode('utf-8'), hashlib.sha256).digest()
    encoded_sig = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')
    return f"{encoded_sig}.{encoded_payload}"

valid_signed_req = build_signed_request({"user_id": "17841400000000000", "algorithm": "HMAC-SHA256"}, settings.META_APP_SECRET)
bad_signed_req = "badsig.eyJ1c2VyX2lkIjoiMTIzNCJ9"

# 27a: Data deletion bad signature -> 400
form_bad = urllib.parse.urlencode({"signed_request": bad_signed_req}).encode('utf-8')
req_del_bad = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram/data-deletion',
    data=form_bad,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
try:
    urllib.request.urlopen(req_del_bad)
    print("27a (deletion bad sig): FAIL - Expected 400, got 200")
except urllib.error.HTTPError as e:
    if e.code == 400:
        print("27a (deletion bad sig): PASS - Got 400 Bad Request")
    else:
        print(f"27a (deletion bad sig): FAIL - Expected 400, got {e.code}")

# 27b: Data deletion valid signature -> 200 with url and confirmation_code
form_valid = urllib.parse.urlencode({"signed_request": valid_signed_req}).encode('utf-8')
req_del_valid = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram/data-deletion',
    data=form_valid,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
try:
    with urllib.request.urlopen(req_del_valid) as resp:
        body = json.loads(resp.read().decode())
        print(f"27b (deletion valid sig): Status {resp.status} - url={body.get('url')}, confirmation_code={body.get('confirmation_code')}")
        if 'url' in body and 'confirmation_code' in body:
            print("27b (deletion valid sig): PASS - Both url and confirmation_code returned.")
        else:
            print("27b (deletion valid sig): FAIL - Missing url or confirmation_code in response.")
except urllib.error.HTTPError as e:
    print(f"27b (deletion valid sig): FAIL - Status {e.code}: {e.read().decode()}")

# 27c: Deauthorize valid signature -> 200
req_deauth = urllib.request.Request(
    'http://localhost:8000/webhooks/instagram/deauthorize',
    data=form_valid,
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
try:
    with urllib.request.urlopen(req_deauth) as resp:
        print(f"27c (deauthorize valid sig): PASS - Status {resp.status} - {resp.read().decode()}")
except urllib.error.HTTPError as e:
    print(f"27c (deauthorize valid sig): FAIL - Status {e.code}: {e.read().decode()}")

print("\n=== BACKEND QA TEST SUITE COMPLETED ===")
