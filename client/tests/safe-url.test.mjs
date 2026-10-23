// client/tests/safe-url.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const securityTsPath = path.resolve(__dirname, '../src/lib/security.ts');

const ALLOWED_PROTOCOLS = new Set(['https:', 'http:', 'mailto:', 'tel:']);

function safeUrl(url, fallback = '#') {
  if (!url || typeof url !== 'string') {
    return fallback;
  }

  const trimmed = url.trim();
  if (!trimmed) {
    return fallback;
  }

  if (trimmed.startsWith('/') && !trimmed.startsWith('//') && !trimmed.startsWith('/\\')) {
    return trimmed;
  }

  if (trimmed.startsWith('#')) {
    return trimmed;
  }

  try {
    const parsed = new URL(trimmed);
    const protocol = parsed.protocol.toLowerCase();

    if (ALLOWED_PROTOCOLS.has(protocol)) {
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        if (!parsed.hostname || parsed.hostname.includes('javascript:') || parsed.hostname.includes('data:')) {
          return fallback;
        }
      }
      return trimmed;
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function isSafeUrl(url) {
  return safeUrl(url, '') !== '';
}

function safeExternalLinkProps(url) {
  const sanitized = safeUrl(url, '#');
  const isExternal = sanitized.startsWith('http:') || sanitized.startsWith('https:');

  return {
    href: sanitized,
    ...(isExternal ? { target: '_blank', rel: 'noopener noreferrer' } : {}),
  };
}

function sanitizeText(text, maxLength = 2000) {
  if (!text || typeof text !== 'string') {
    return '';
  }
  const sanitized = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
  return sanitized.trim().slice(0, maxLength);
}

test('security.ts - Source file exists and exports all security utilities', () => {
  assert.ok(fs.existsSync(securityTsPath), 'src/lib/security.ts must exist');
  const content = fs.readFileSync(securityTsPath, 'utf-8');
  assert.ok(content.includes('export function safeUrl'), 'must export safeUrl');
  assert.ok(content.includes('export function isSafeUrl'), 'must export isSafeUrl');
  assert.ok(content.includes('export function safeExternalLinkProps'), 'must export safeExternalLinkProps');
  assert.ok(content.includes('export function sanitizeText'), 'must export sanitizeText');
});

test('safeUrl - Blocks dangerous protocol execution', () => {
  const dangerousVectors = [
    'javascript:alert(1)',
    'JAVASCRIPT:alert(document.cookie)',
    'javascript:/*--></title></style></textarea></script><svg/onload=alert(1)>',
    'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
    'vbscript:msgbox("XSS")',
    'file:///etc/passwd',
    '//malicious-domain.com/phish',
    '/\\malicious-domain.com',
  ];

  for (const vector of dangerousVectors) {
    const result = safeUrl(vector);
    assert.equal(result, '#', `Failed to neutralize dangerous vector: ${vector}`);
    assert.equal(isSafeUrl(vector), false, `isSafeUrl must return false for ${vector}`);
  }
});

test('safeUrl - Permits legitimate URLs and relative paths', () => {
  const safeUrls = [
    'https://comlina.ai',
    'https://comlina.ai/playbook?ref=test&id=123',
    'http://localhost:3000/dashboard',
    '/dashboard/automations',
    '#section-1',
    'mailto:support@comlina.ai',
    'tel:+1234567890',
  ];

  for (const url of safeUrls) {
    const result = safeUrl(url);
    assert.equal(result, url, `Legitimate URL was incorrectly modified: ${url}`);
    assert.equal(isSafeUrl(url), true, `isSafeUrl must return true for ${url}`);
  }
});

test('safeUrl - Handles null, undefined, empty string, and whitespace with fallback', () => {
  assert.equal(safeUrl(null), '#');
  assert.equal(safeUrl(undefined), '#');
  assert.equal(safeUrl(''), '#');
  assert.equal(safeUrl('   '), '#');
  assert.equal(safeUrl(null, '/default'), '/default');
  assert.equal(safeUrl('javascript:alert(1)', '/safe-fallback'), '/safe-fallback');
});

test('safeExternalLinkProps - Applies noopener noreferrer to external links', () => {
  const externalProps = safeExternalLinkProps('https://instagram.com/comlina');
  assert.equal(externalProps.href, 'https://instagram.com/comlina');
  assert.equal(externalProps.target, '_blank');
  assert.equal(externalProps.rel, 'noopener noreferrer');

  const internalProps = safeExternalLinkProps('/dashboard');
  assert.equal(internalProps.href, '/dashboard');
  assert.equal(internalProps.target, undefined);
  assert.equal(internalProps.rel, undefined);
});

test('sanitizeText - Strips control characters and enforces length bound', () => {
  const dirty = 'Hello\x00World\x08Test\x1F';
  assert.equal(sanitizeText(dirty), 'HelloWorldTest');

  const longText = 'a'.repeat(3000);
  assert.equal(sanitizeText(longText, 100).length, 100);
});
