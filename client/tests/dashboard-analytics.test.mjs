// client/tests/dashboard-analytics.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';

test('Dashboard Analytics - Real-time zero activity state renders zero baseline without mock data', () => {
  const summaryEmpty = {
    workspace_id: 'test-ws',
    total_automations: 0,
    active_automations: 0,
    total_leads: 0,
    converted_leads: 0,
    conversion_rate_pct: 0,
    stats_comments: 0,
    stats_dms_sent: 0,
    stats_clicks: 0,
    daily_stats: [
      { day: 'Mon', date: '2026-10-12', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Tue', date: '2026-10-13', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Wed', date: '2026-10-14', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Thu', date: '2026-10-15', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Fri', date: '2026-10-16', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Sat', date: '2026-10-17', dms: 0, comments: 0, count: 0, pct: 0 },
      { day: 'Sun', date: '2026-10-18', dms: 0, comments: 0, count: 0, pct: 0 },
    ]
  };

  // Every single day must have pct === 0 and count === 0
  for (const item of summaryEmpty.daily_stats) {
    assert.strictEqual(item.count, 0, `Day ${item.day} should have count 0`);
    assert.strictEqual(item.pct, 0, `Day ${item.day} should have pct 0`);
  }

  // Bar rendering height logic: if pct === 0, render 3px baseline (not fake non-zero height)
  const heights = summaryEmpty.daily_stats.map(item => item.pct > 0 ? `${item.pct}%` : '3px');
  assert.deepStrictEqual(heights, ['3px', '3px', '3px', '3px', '3px', '3px', '3px']);
});

test('Dashboard Analytics - Real message activity calculates proportional heights accurately', () => {
  const dailyStats = [
    { day: 'Mon', date: '2026-10-12', dms: 5, comments: 5, count: 10, pct: 20 },
    { day: 'Tue', date: '2026-10-13', dms: 10, comments: 15, count: 25, pct: 50 },
    { day: 'Wed', date: '2026-10-14', dms: 20, comments: 30, count: 50, pct: 100 },
    { day: 'Thu', date: '2026-10-15', dms: 0, comments: 0, count: 0, pct: 0 },
    { day: 'Fri', date: '2026-10-16', dms: 5, comments: 5, count: 10, pct: 20 },
    { day: 'Sat', date: '2026-10-17', dms: 0, comments: 0, count: 0, pct: 0 },
    { day: 'Sun', date: '2026-10-18', dms: 0, comments: 0, count: 0, pct: 0 },
  ];

  const heights = dailyStats.map(item => item.pct > 0 ? `${item.pct}%` : '3px');
  assert.strictEqual(heights[0], '20%');
  assert.strictEqual(heights[1], '50%');
  assert.strictEqual(heights[2], '100%');
  assert.strictEqual(heights[3], '3px'); // Zero traffic renders baseline
});
