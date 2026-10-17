import sys
sys.path.insert(0, 'server')
from app.core.config import settings
import jwt
import time
import json

exp = int(time.time()) + 86400 * 7
payload = {
    'sub': '00000000-0000-0000-0000-000000000001',
    'email': 'qa@comlina.com',
    'role': 'authenticated',
    'aud': 'authenticated',
    'exp': exp
}
token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')
session = {
    'access_token': token,
    'token_type': 'bearer',
    'expires_in': 86400 * 7,
    'expires_at': exp,
    'refresh_token': 'qa_refresh_token_comlina',
    'user': {
        'id': '00000000-0000-0000-0000-000000000001',
        'aud': 'authenticated',
        'role': 'authenticated',
        'email': 'qa@comlina.com',
        'user_metadata': {'full_name': 'QA Engineer'}
    }
}

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>QA Session Setup</title>
</head>
<body style="font-family: sans-serif; padding: 2rem;">
  <h1>QA Session Setup</h1>
  <p>Logged in as: <strong>qa@comlina.com</strong></p>
  <button id="goBtn" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #004020; color: white; border: none; border-radius: 8px;">Go to Dashboard</button>
  <script>
    const sessionData = {json.dumps(session)};
    function setSessionAndGo() {{
      try {{
        localStorage.setItem('sb-vrfwgoigtmixkkunvrnw-auth-token', JSON.stringify(sessionData));
        document.cookie = 'sb-vrfwgoigtmixkkunvrnw-auth-token=' + encodeURIComponent(JSON.stringify(sessionData)) + '; path=/; max-age=604800; SameSite=Lax';
        sessionStorage.setItem('comlina_qa_auth', 'true');
        console.log('Session set successfully in localStorage and cookie');
        window.location.href = '/dashboard';
      }} catch (err) {{
        alert('Error setting session: ' + err);
      }}
    }}
    document.getElementById('goBtn').addEventListener('click', setSessionAndGo);
    // Auto-run if requested
    if (window.location.search.includes('auto=1')) {{
      setSessionAndGo();
    }}
  </script>
</body>
</html>
"""

with open('client/public/qa-login.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Created client/public/qa-login.html")
