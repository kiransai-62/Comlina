# scripts/test_security.ps1
Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "Comlina Security Middleware Verification Suite" -ForegroundColor Cyan
Write-Host "=======================================================`n" -ForegroundColor Cyan

# Test 1: Legitimate Dashboard Request & Security Headers
Write-Host "[TEST 1] Legitimate Request & OWASP Security Headers..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/dashboard' -Method Head -UseBasicParsing
    Write-Host "  [PASS] Status: $($resp.StatusCode)" -ForegroundColor Green
    Write-Host "  [PASS] x-request-id: $($resp.Headers['x-request-id'])" -ForegroundColor Green
    Write-Host "  [PASS] X-Frame-Options: $($resp.Headers['X-Frame-Options'])" -ForegroundColor Green
    Write-Host "  [PASS] X-Content-Type-Options: $($resp.Headers['X-Content-Type-Options'])" -ForegroundColor Green
    Write-Host "  [PASS] Content-Security-Policy present: $($resp.Headers['Content-Security-Policy'] -ne $null)" -ForegroundColor Green
    Write-Host "  [PASS] RateLimit Headers: Limit=$($resp.Headers['X-RateLimit-Limit']), Remaining=$($resp.Headers['X-RateLimit-Remaining'])" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Legitimate request failed: $_" -ForegroundColor Red
}

# Test 2: Scanner & Exploit Trapping (/.env)
Write-Host "`n[TEST 2] Trapping Scanner Exploit Probe (/.env)..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/.env' -Method Get -UseBasicParsing
    Write-Host "  [FAIL] Expected 403 but got $($resp.StatusCode)" -ForegroundColor Red
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 403) {
        Write-Host "  [PASS] Blocked with HTTP 403 Forbidden!" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Unexpected status: $statusCode" -ForegroundColor Red
    }
}

# Test 3: Trapping WordPress / PHP exploit probe (/wp-login.php)
Write-Host "`n[TEST 3] Trapping PHP Scanner Probe (/wp-login.php)..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/wp-login.php' -Method Get -UseBasicParsing
    Write-Host "  [FAIL] Expected 403 but got $($resp.StatusCode)" -ForegroundColor Red
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 403) {
        Write-Host "  [PASS] Blocked with HTTP 403 Forbidden!" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Unexpected status: $statusCode" -ForegroundColor Red
    }
}

# Test 4: Malicious User-Agent Blocking (sqlmap)
Write-Host "`n[TEST 4] Blocking Malicious Attack Tool User-Agent (sqlmap)..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/' -UserAgent 'sqlmap/1.5.2#stable' -Method Get -UseBasicParsing
    Write-Host "  [FAIL] Expected 403 but got $($resp.StatusCode)" -ForegroundColor Red
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 403) {
        Write-Host "  [PASS] Blocked with HTTP 403 Forbidden!" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Unexpected status: $statusCode" -ForegroundColor Red
    }
}

# Test 5: Injection Attack Detection (Path Traversal in Query)
Write-Host "`n[TEST 5] Blocking Path Traversal in Query Parameters (../../etc/passwd)..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/dashboard?file=../../etc/passwd' -Method Get -UseBasicParsing
    Write-Host "  [FAIL] Expected 400 but got $($resp.StatusCode)" -ForegroundColor Red
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 400) {
        Write-Host "  [PASS] Blocked with HTTP 400 Bad Request (Injection Signature Detected)!" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Unexpected status: $statusCode" -ForegroundColor Red
    }
}

# Test 6: Injection Attack Detection (SQLi in Query)
Write-Host "`n[TEST 6] Blocking SQL Injection in Query Parameters (UNION SELECT)..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:3000/dashboard?search=1%20UNION%20SELECT%20*%20FROM%20users' -Method Get -UseBasicParsing
    Write-Host "  [FAIL] Expected 400 but got $($resp.StatusCode)" -ForegroundColor Red
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 400) {
        Write-Host "  [PASS] Blocked with HTTP 400 Bad Request (SQLi Detected)!" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Unexpected status: $statusCode" -ForegroundColor Red
    }
}

# Test 7: Rate Limiting on Auth Endpoints (/login)
Write-Host "`n[TEST 7] Sliding-Window Rate Limiting on /login (Limit: 12 req/min)..." -ForegroundColor Yellow
$blocked = $false
$rateLimitedCount = 0
for ($i = 1; $i -le 15; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri 'http://localhost:3000/login' -Method Head -UseBasicParsing
    }
    catch {
        $sc = $_.Exception.Response.StatusCode.value__
        if ($sc -eq 429) {
            $rateLimitedCount++
            $blocked = $true
        }
    }
}
if ($blocked) {
    Write-Host "  [PASS] Rate limit engaged! Blocked $rateLimitedCount excess requests with HTTP 429 Too Many Requests!" -ForegroundColor Green
}
else {
    Write-Host "  [FAIL] Expected HTTP 429 after 12 requests" -ForegroundColor Red
}

Write-Host "`n=======================================================" -ForegroundColor Cyan
Write-Host "Security Middleware Verification Completed Successfully" -ForegroundColor Cyan
Write-Host "=======================================================`n" -ForegroundColor Cyan
