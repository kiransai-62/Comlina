// client/tests/loading-animation.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const globalsCssPath = path.resolve(__dirname, '../src/styles/globals.css');
const componentPath = path.resolve(__dirname, '../src/components/ComlinaLoadingOverlay.tsx');

test('Comlina Loading Animation - CSS Color Tokens', () => {
  const css = fs.readFileSync(globalsCssPath, 'utf8');

  assert.ok(css.includes('--comlina-purple: #8B3DFF;'), 'Defines canonical purple token #8B3DFF');
  assert.ok(css.includes('--comlina-pink: #F50087;'), 'Defines canonical pink token #F50087');
  assert.ok(css.includes('--comlina-orange: #FF8A00;'), 'Defines canonical orange token #FF8A00');
  assert.ok(css.includes('--comlina-background: #FAFAF8;'), 'Defines canonical background token #FAFAF8');
});

test('Comlina Loading Animation - Backdrop Glassmorphism & Fixed Overlay', () => {
  const css = fs.readFileSync(globalsCssPath, 'utf8');

  assert.ok(css.includes('.comlina-loading-backdrop'), 'Includes .comlina-loading-backdrop class');
  assert.ok(css.includes('backdrop-filter: blur(14px);'), 'Applies 14px blur to underlying UI');
  assert.ok(css.includes('-webkit-backdrop-filter: blur(14px);'), 'Includes webkit prefix for iOS Safari');
  assert.ok(css.includes('z-index: 9999;'), 'Ensures top-level overlay stacking above all UI');
});

test('Comlina Loading Animation - Three-Dot Sequential Pulse Order', () => {
  const css = fs.readFileSync(globalsCssPath, 'utf8');

  // Verify Dot 1 (Purple)
  assert.ok(css.includes('.comlina-loading-dot:nth-child(1)'), 'Targets first dot');
  assert.ok(css.includes('animation: comlina-dot-pulse-purple'), 'Uses purple pulse animation');

  // Verify Dot 2 (Pink)
  assert.ok(css.includes('.comlina-loading-dot:nth-child(2)'), 'Targets second dot');
  assert.ok(css.includes('animation: comlina-dot-pulse-pink'), 'Uses pink pulse animation');

  // Verify Dot 3 (Orange)
  assert.ok(css.includes('.comlina-loading-dot:nth-child(3)'), 'Targets third dot');
  assert.ok(css.includes('animation: comlina-dot-pulse-orange'), 'Uses orange pulse animation');

  // Check exact phases: exactly one dot bright at a time
  assert.ok(css.includes('@keyframes comlina-dot-pulse-purple'), 'Purple keyframes exist');
  assert.ok(css.includes('@keyframes comlina-dot-pulse-pink'), 'Pink keyframes exist');
  assert.ok(css.includes('@keyframes comlina-dot-pulse-orange'), 'Orange keyframes exist');
});

test('Comlina Loading Animation - Accessibility and Reduced Motion', () => {
  const css = fs.readFileSync(globalsCssPath, 'utf8');

  assert.ok(css.includes('@media (prefers-reduced-motion: reduce)'), 'Contains prefers-reduced-motion query');
  assert.ok(css.includes('animation: none !important;'), 'Disables pulse animation for reduced motion users');
});

test('Comlina Loading Overlay Component - Structure and Spec Compliance', () => {
  const componentSrc = fs.readFileSync(componentPath, 'utf8');

  // Must reuse BrandLogo variant="mark"
  assert.ok(componentSrc.includes('variant="mark"'), 'Reuses Comlina brand mark icon without wordmark');
  assert.ok(!componentSrc.includes('variant="wordmark"'), 'Must not render wordmark');
  assert.ok(!componentSrc.includes('variant="horizontal"'), 'Must not render horizontal logo with text');

  // Must have exactly 3 dots
  const dotCount = (componentSrc.match(/className="comlina-loading-dot"/g) || []).length;
  assert.equal(dotCount, 3, 'Renders exactly 3 sequential loading dots');

  // Must not have textual clutter
  assert.ok(!componentSrc.includes('Loading...</div>'), 'Does not render visible loading text');
  assert.ok(!componentSrc.includes('Turn Conversations into Growth'), 'Does not render brand tagline');

  // Must be accessible with screen reader description and ARIA status
  assert.ok(componentSrc.includes('role="status"'), 'Includes ARIA role=status');
  assert.ok(componentSrc.includes('aria-live="polite"'), 'Includes ARIA polite region');
  assert.ok(componentSrc.includes('sr-only'), 'Includes screen reader accessible label');

  // Body scroll locking
  assert.ok(componentSrc.includes('document.body.style.overflow'), 'Locks and restores document body scroll');
});
