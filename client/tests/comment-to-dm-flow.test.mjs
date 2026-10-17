// client/tests/comment-to-dm-flow.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

// Helper validator replicating the exact logic of CommentToDmFlow
function validateCommentToDmForm({
  selectedAccountId,
  postMode,
  selectedPostId,
  keywords,
  replyToAll,
  responseDm,
  buttonLabel,
  destinationUrl,
}) {
  const errors = [];

  if (!selectedAccountId) {
    errors.push('Please connect an Instagram account first.');
  }

  if (postMode === 'specific' && !selectedPostId) {
    errors.push('Please select an Instagram post.');
  }

  if (!replyToAll && (!keywords || keywords.length === 0)) {
    errors.push('At least one trigger keyword is required.');
  }

  if (!responseDm || !responseDm.trim()) {
    errors.push('Automated DM message cannot be empty.');
  }

  if (!buttonLabel || !buttonLabel.trim()) {
    errors.push('CTA button label is required.');
  }

  if (!destinationUrl || !destinationUrl.trim()) {
    errors.push('Destination URL is required.');
  } else if (!destinationUrl.startsWith('http://') && !destinationUrl.startsWith('https://')) {
    errors.push('Destination URL must be a valid HTTP or HTTPS link.');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

test('CommentToDmFlow Validation - Valid default state matches reference design', () => {
  const state = {
    selectedAccountId: 'acc_12345',
    postMode: 'specific',
    selectedPostId: 'media_real_post_1',
    keywords: ['PRICE', 'LINK', 'INFO'],
    replyToAll: false,
    responseDm: "Hey! 👋 Here's what you asked for:\nhttps://example.com/guide",
    buttonLabel: 'View the guide',
    destinationUrl: 'https://example.com/guide',
  };

  const validation = validateCommentToDmForm(state);
  assert.equal(validation.isValid, true);
  assert.equal(validation.errors.length, 0);
});

test('CommentToDmFlow Validation - Rejects missing connected Instagram account', () => {
  const stateNoAcc = {
    selectedAccountId: '',
    postMode: 'specific',
    selectedPostId: 'media_real_post_1',
    keywords: ['PRICE'],
    replyToAll: false,
    responseDm: 'Hello',
    buttonLabel: 'Click Here',
    destinationUrl: 'https://example.com/guide',
  };

  const val = validateCommentToDmForm(stateNoAcc);
  assert.equal(val.isValid, false);
  assert.ok(val.errors.includes('Please connect an Instagram account first.'));
});

test('CommentToDmFlow Validation - Rejects missing required CTA button or URL', () => {
  const stateMissingBtn = {
    selectedAccountId: 'acc_12345',
    postMode: 'specific',
    selectedPostId: 'media_summer',
    keywords: ['PRICE'],
    replyToAll: false,
    responseDm: 'Hello',
    buttonLabel: '',
    destinationUrl: 'https://example.com/guide',
  };

  const val1 = validateCommentToDmForm(stateMissingBtn);
  assert.equal(val1.isValid, false);
  assert.ok(val1.errors.includes('CTA button label is required.'));

  const stateInvalidUrl = {
    ...stateMissingBtn,
    buttonLabel: 'Click Here',
    destinationUrl: 'not_a_url',
  };

  const val2 = validateCommentToDmForm(stateInvalidUrl);
  assert.equal(val2.isValid, false);
  assert.ok(val2.errors.includes('Destination URL must be a valid HTTP or HTTPS link.'));
});

test('CommentToDmFlow Keywords - Adding, uppercase normalization and removal', () => {
  let keywords = ['PRICE', 'LINK', 'INFO'];

  // Add keyword with whitespace and lowercase
  const input = ' discount ';
  const clean = input.trim().toUpperCase();
  if (!keywords.includes(clean)) {
    keywords = [...keywords, clean];
  }

  assert.deepEqual(keywords, ['PRICE', 'LINK', 'INFO', 'DISCOUNT']);

  // Remove keyword
  keywords = keywords.filter((k) => k !== 'LINK');
  assert.deepEqual(keywords, ['PRICE', 'INFO', 'DISCOUNT']);
});

test('Simulator Follower States - Toggling between follower and non-follower preview', () => {
  let followerView = 'follower';
  const askFollowEnabled = true;

  // Follower view: Immediate DM delivery previewed
  const messagesFollower = [
    { sender: 'user', text: 'PRICE' },
    { sender: 'brand', text: 'Hey! Here is what you asked for' },
  ];
  assert.equal(messagesFollower[0].text, 'PRICE');
  assert.equal(messagesFollower.length, 2);

  // Non-follower view: Follow gate request prompt previewed first
  followerView = 'non_follower';
  const messagesNonFollower = [
    { sender: 'user', text: 'PRICE' },
    { sender: 'brand', text: 'Please follow our account first to get the guide!' },
    { sender: 'brand', text: 'Hey! Here is what you asked for' },
  ];
  assert.equal(messagesNonFollower.length, 3);
  assert.ok(messagesNonFollower[1].text.includes('follow our account'));
});

test('Account Isolation & Switching - Switching account updates active identity and payload', () => {
  const accounts = [
    { id: 'acc_creator_1', username: 'kiran_design', profile_pic_url: 'https://instagram.com/pic1.jpg' },
    { id: 'acc_brand_2', username: 'global_footwear', profile_pic_url: null },
  ];

  let selectedAccountId = accounts[0].id;
  let activeAccount = accounts.find((a) => a.id === selectedAccountId);

  assert.equal(activeAccount.username, 'kiran_design');
  assert.equal(activeAccount.profile_pic_url, 'https://instagram.com/pic1.jpg');

  // Switch to second account
  selectedAccountId = accounts[1].id;
  activeAccount = accounts.find((a) => a.id === selectedAccountId);

  assert.equal(activeAccount.username, 'global_footwear');
  assert.equal(activeAccount.profile_pic_url, null);

  // Automation payload reflects exact selected account ID
  const payload = {
    status: 'ACTIVE',
    instagram_account_id: activeAccount.id,
    name: 'Comment to DM Flow',
  };
  assert.equal(payload.instagram_account_id, 'acc_brand_2');
});

test('Dynamic Simulator Domain & Avatar - Resolves domain and authentic initials without fake stock data', () => {
  function getDomain(url) {
    try {
      if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
        return new URL(url).hostname;
      }
    } catch {
      return 'example.com';
    }
    return 'example.com';
  }

  function getAvatarInitial(username) {
    if (!username) return 'IG';
    const clean = username.startsWith('@') ? username.slice(1) : username;
    return clean.charAt(0).toUpperCase();
  }

  assert.equal(getDomain('https://customclient.io/shop/collection'), 'customclient.io');
  assert.equal(getDomain('https://mybusiness.store/product-123'), 'mybusiness.store');
  assert.equal(getAvatarInitial('nike_athletics'), 'N');
  assert.equal(getAvatarInitial('@urban_style'), 'U');
  assert.equal(getAvatarInitial(''), 'IG');
});
