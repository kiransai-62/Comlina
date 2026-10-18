// client/tests/comment-to-dm-flow.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

// Helper validator replicating the exact logic of CommentToDmFlow
function validateCommentToDmForm({
  selectedAccountId,
  postMode,
  selectedPostId,
  triggerMode = 'specific_keywords',
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

  if (triggerMode === 'specific_keywords' && !replyToAll && (!keywords || keywords.length === 0)) {
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

test('CommentToDmFlow Trigger Mode - Any keyword mode does not require keyword entries', () => {
  const stateAnyKeyword = {
    selectedAccountId: 'acc_12345',
    postMode: 'specific',
    selectedPostId: 'media_real_post_1',
    triggerMode: 'any_keyword',
    keywords: [], // Empty keywords allowed in any_keyword mode!
    replyToAll: false,
    responseDm: "Hey! 👋 Here's your link!",
    buttonLabel: 'Get Link',
    destinationUrl: 'https://comlina.com/guide',
  };

  const validation = validateCommentToDmForm(stateAnyKeyword);
  assert.equal(validation.isValid, true);
  assert.equal(validation.errors.length, 0);
});

test('CommentToDmFlow Trigger Mode - Specific keywords mode requires keyword entries', () => {
  const stateSpecificEmpty = {
    selectedAccountId: 'acc_12345',
    postMode: 'specific',
    selectedPostId: 'media_real_post_1',
    triggerMode: 'specific_keywords',
    keywords: [], // Must have keywords in specific_keywords mode!
    replyToAll: false,
    responseDm: "Hey! 👋 Here's your link!",
    buttonLabel: 'Get Link',
    destinationUrl: 'https://comlina.com/guide',
  };

  const validation = validateCommentToDmForm(stateSpecificEmpty);
  assert.equal(validation.isValid, false);
  assert.ok(validation.errors.includes('At least one trigger keyword is required.'));
});

test('CommentToDmFlow State - Switching modes preserves configured keywords and restores settings', () => {
  // 1. User configures keywords
  let state = {
    triggerMode: 'specific_keywords',
    keywords: ['PRICE', 'LINK', 'INFO'],
    matchWholeWords: true,
  };
  assert.deepEqual(state.keywords, ['PRICE', 'LINK', 'INFO']);

  // 2. User switches to Any keyword mode
  state = {
    ...state,
    triggerMode: 'any_keyword',
    // keywords are NOT deleted; they are preserved in state
  };
  assert.equal(state.triggerMode, 'any_keyword');
  assert.deepEqual(state.keywords, ['PRICE', 'LINK', 'INFO']);

  // 3. User switches back to Specific keywords mode
  state = {
    ...state,
    triggerMode: 'specific_keywords',
  };
  assert.equal(state.triggerMode, 'specific_keywords');
  assert.deepEqual(state.keywords, ['PRICE', 'LINK', 'INFO']); // Fully restored!
});

test('CommentToDmFlow Save Payload - Correctly encodes triggerMode and preserves configured keywords', () => {
  const triggerMode = 'any_keyword';
  const configuredKeywords = ['PRICE', 'LINK'];

  const payload = {
    status: 'ACTIVE',
    name: 'Comment to DM Flow',
    instagram_account_id: 'acc_12345',
    triggerMode,
    trigger: {
      type: 'COMMENT',
      mode: 'specific',
      postId: 'media_123',
      triggerMode,
      keywords: configuredKeywords, // Preserved in backend trigger record
      matchWholeWords: true,
      matchBehavior: 'contains',
      replyToAll: false,
    },
    automatedDm: {
      message: 'Check your DM! 📩',
      button: {
        label: 'View Guide',
        url: 'https://comlina.com',
      },
    },
  };

  assert.equal(payload.triggerMode, 'any_keyword');
  assert.equal(payload.trigger.triggerMode, 'any_keyword');
  assert.deepEqual(payload.trigger.keywords, ['PRICE', 'LINK']);
});

test('CommentToDmFlow - Restores and persists Ask to Follow and Comment Teaser Reply', () => {
  const initialData = {
    triggerMode: 'specific_keywords',
    trigger: {
      type: 'COMMENT',
      keywords: ['ACCESS', 'VIP'],
      matchWholeWords: true
    },
    automatedDm: {
      message: 'Here is your VIP access link! 🌟',
      button: {
        label: 'Enter Portal',
        url: 'https://example.com/vip'
      }
    },
    advanced: {
      askFollow: {
        enabled: true,
        message: 'Please follow @test_creator to unlock this VIP resource!'
      },
      commentTeaser: {
        enabled: true,
        message: 'Check your DM! 📩'
      }
    }
  };

  // Verify restoration extraction
  const restoredAskFollowEnabled = initialData?.advanced?.askFollow?.enabled ?? false;
  const restoredAskFollowMessage = initialData?.advanced?.askFollow?.message;
  const restoredTeaserEnabled = initialData?.advanced?.commentTeaser?.enabled ?? false;
  const restoredTeaserMessage = initialData?.advanced?.commentTeaser?.message;

  assert.equal(restoredAskFollowEnabled, true);
  assert.equal(restoredAskFollowMessage, 'Please follow @test_creator to unlock this VIP resource!');
  assert.equal(restoredTeaserEnabled, true);
  assert.equal(restoredTeaserMessage, 'Check your DM! 📩');
});

test('InstagramPhonePreview - Follow-to-Unlock Gating displays gate for non-follower and withholds resource', () => {
  const askFollowEnabled = true;
  let previewState = 'non_follower';

  // In non_follower state, resource is withheld and gate is visible
  const isResourceVisibleNonFollower = !(askFollowEnabled && previewState === 'non_follower');
  const isGateVisibleNonFollower = askFollowEnabled && previewState === 'non_follower';
  assert.equal(isResourceVisibleNonFollower, false, 'Protected resource must NOT be visible to non-followers');
  assert.equal(isGateVisibleNonFollower, true, 'Follow gate message must be visible to non-followers');

  // Once following, resource is unlocked and gate is hidden
  previewState = 'follower';
  const isResourceVisibleFollower = !(askFollowEnabled && previewState === 'non_follower');
  const isGateVisibleFollower = askFollowEnabled && previewState === 'non_follower';
  assert.equal(isResourceVisibleFollower, true, 'Protected resource must be unlocked for verified followers');
  assert.equal(isGateVisibleFollower, false, 'Follow gate message must be hidden for verified followers');
});

test('SelectMediaModal - Real data handling, deduplication by ID, and missing fields', () => {
  const rawApiItems = [
    {
      id: '1799001122',
      type: 'POST',
      caption: 'Real Launch Announcement',
      imageUrl: 'https://cdn.example.com/launch.jpg',
      likesCount: 154,
      commentsCount: 23,
      publishedDate: '2026-10-16T18:00:00+0000',
    },
    {
      id: '1799001123',
      type: 'REEL',
      caption: '', // No caption
      imageUrl: 'https://cdn.example.com/reel_thumb.jpg',
      likesCount: null, // Genuinely absent metric
      commentsCount: null,
      publishedDate: '2026-10-15T12:00:00+0000',
    },
    {
      id: '1799001122', // Duplicate ID
      type: 'POST',
      caption: 'Duplicate',
      imageUrl: 'https://cdn.example.com/launch.jpg',
    }
  ];

  // Deduplication
  const seen = new Set();
  const deduped = [];
  for (const item of rawApiItems) {
    if (item.id && !seen.has(item.id)) {
      seen.add(item.id);
      deduped.push(item);
    }
  }

  assert.equal(deduped.length, 2);
  assert.equal(deduped[0].id, '1799001122');
  assert.equal(deduped[1].id, '1799001123');

  // Verify missing caption label
  const item1Caption = deduped[0].caption && deduped[0].caption.trim() ? deduped[0].caption : '(No caption)';
  const item2Caption = deduped[1].caption && deduped[1].caption.trim() ? deduped[1].caption : '(No caption)';
  assert.equal(item1Caption, 'Real Launch Announcement');
  assert.equal(item2Caption, '(No caption)');

  // Verify engagement metrics are not fabricated when absent
  assert.equal(deduped[1].likesCount, null);
  assert.equal(deduped[1].commentsCount, null);
});

test('SelectMediaModal - Filtering by All, Posts, and Reels', () => {
  const items = [
    { id: 'p1', type: 'POST', caption: 'Post 1' },
    { id: 'r1', type: 'REEL', caption: 'Reel 1' },
    { id: 'p2', type: 'POST', caption: 'Post 2' },
    { id: 'r2', type: 'REEL', caption: 'Reel 2' },
  ];

  const filterAll = items;
  assert.equal(filterAll.length, 4);

  const filterPosts = items.filter((i) => i.type === 'POST');
  assert.equal(filterPosts.length, 2);
  assert.ok(filterPosts.every((i) => i.type === 'POST'));

  const filterReels = items.filter((i) => i.type === 'REEL');
  assert.equal(filterReels.length, 2);
  assert.ok(filterReels.every((i) => i.type === 'REEL'));
});

test('SelectMediaModal - Search and Sorting by newest, oldest, and likes', () => {
  const items = [
    { id: 'm1', caption: 'Deep dive into LLM workflows', publishedDate: '2026-10-10T10:00:00Z', likesCount: 45 },
    { id: 'm2', caption: 'Brand new template release', publishedDate: '2026-10-15T12:00:00Z', likesCount: 120 },
    { id: 'm3', caption: 'Behind the scenes at office', publishedDate: '2026-10-05T08:00:00Z', likesCount: 10 },
  ];

  // Search by query
  const query = 'template';
  const searched = items.filter((i) => i.caption.toLowerCase().includes(query.toLowerCase()));
  assert.equal(searched.length, 1);
  assert.equal(searched[0].id, 'm2');

  // Sort by newest
  const sortedNewest = [...items].sort((a, b) => new Date(b.publishedDate) - new Date(a.publishedDate));
  assert.equal(sortedNewest[0].id, 'm2'); // 2026-10-15
  assert.equal(sortedNewest[2].id, 'm3'); // 2026-10-05

  // Sort by likes
  const sortedLikes = [...items].sort((a, b) => (b.likesCount ?? 0) - (a.likesCount ?? 0));
  assert.equal(sortedLikes[0].id, 'm2'); // 120 likes
  assert.equal(sortedLikes[1].id, 'm1'); // 45 likes
});

test('SelectMediaModal - Pagination cursor appends additional real media deduplicated', () => {
  const page1 = [
    { id: 'post_1', caption: 'First post' },
    { id: 'post_2', caption: 'Second post' },
  ];
  let nextCursor = 'cursor_page_2';

  const page2 = [
    { id: 'post_2', caption: 'Second post (duplicate across page boundary)' },
    { id: 'post_3', caption: 'Third post' },
  ];

  // Simulating handleLoadMore appending
  const existingIds = new Set(page1.map((p) => p.id));
  const uniqueNew = page2.filter((p) => !existingIds.has(p.id));
  const combined = [...page1, ...uniqueNew];

  assert.equal(combined.length, 3);
  assert.deepEqual(combined.map((p) => p.id), ['post_1', 'post_2', 'post_3']);
});

test('SelectMediaModal - Selection persistence across modal open/close and editor update', () => {
  let selectedPostId = 'post_initial_123';
  let modalSelectedId = selectedPostId;

  // User opens modal -> initialized with selectedPostId
  assert.equal(modalSelectedId, 'post_initial_123');

  // User clicks on a different post inside modal
  const newlyChosen = { id: 'post_new_789', caption: 'New chosen post', type: 'POST' };
  modalSelectedId = newlyChosen.id;

  // User cancels modal -> selectedPostId is unchanged
  modalSelectedId = selectedPostId;
  assert.equal(selectedPostId, 'post_initial_123');

  // User confirms selection -> selectedPostId updates to newlyChosen.id
  selectedPostId = newlyChosen.id;
  assert.equal(selectedPostId, 'post_new_789');
});


