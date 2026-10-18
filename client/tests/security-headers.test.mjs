// client/tests/security-headers.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CLIENT_ROOT = path.resolve(__dirname, '..');

test('Client Middleware - Enforces CSP with per-request nonces', () => {
  const middlewarePath = path.join(CLIENT_ROOT, 'src', 'middleware.ts');
  assert.ok(fs.existsSync(middlewarePath), 'middleware.ts must exist');

  const content = fs.readFileSync(middlewarePath, 'utf8');

  // Verify nonce generation
  assert.match(content, /crypto\.randomUUID\(\)/, 'Must generate cryptographically secure UUID for nonce');
  assert.match(content, /nonce-\$\{nonce\}/, 'Must inject per-request nonce into CSP script-src');
  assert.match(content, /'x-nonce',\s*nonce/, 'Must inject x-nonce into request/response headers');

  // Verify required security headers
  assert.match(content, /frame-ancestors 'none'/, 'CSP must contain frame-ancestors none');
  assert.match(content, /X-Frame-Options', 'DENY'/, 'Must set X-Frame-Options: DENY');
  assert.match(content, /X-Content-Type-Options', 'nosniff'/, 'Must set X-Content-Type-Options: nosniff');
  assert.match(content, /Referrer-Policy', 'strict-origin-when-cross-origin'/, 'Must set Referrer-Policy: strict-origin-when-cross-origin');
  assert.match(content, /Permissions-Policy'/, 'Must set Permissions-Policy');
  assert.match(content, /Strict-Transport-Security'/, 'Must set Strict-Transport-Security');
});

test('Client Error Boundaries - Generic error and global-error components exist', () => {
  const errorPagePath = path.join(CLIENT_ROOT, 'src', 'app', 'error.tsx');
  const globalErrorPath = path.join(CLIENT_ROOT, 'src', 'app', 'global-error.tsx');

  assert.ok(fs.existsSync(errorPagePath), 'src/app/error.tsx must exist');
  assert.ok(fs.existsSync(globalErrorPath), 'src/app/global-error.tsx must exist');

  const errorContent = fs.readFileSync(errorPagePath, 'utf8');
  assert.match(errorContent, /'use client'/, 'error.tsx must be a client component');
  assert.match(errorContent, /Something went wrong/, 'Must provide user-friendly generic error message');
  assert.match(errorContent, /reset/, 'Must provide retry/reset function');

  const globalContent = fs.readFileSync(globalErrorPath, 'utf8');
  assert.match(globalContent, /<html/, 'global-error.tsx must render root html');
  assert.match(globalContent, /<body/, 'global-error.tsx must render root body');
});
