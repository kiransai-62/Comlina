-- 001_seed_data.sql
-- WARNING: STRICTLY FOR LOCAL DEVELOPMENT AND TESTING ONLY.
-- DO NOT RUN IN STAGING OR PRODUCTION ENVIRONMENTS.

-- Insert Demo User
INSERT INTO users (id, email, full_name, timezone)
VALUES ('a0000000-0000-0000-0000-000000000001', 'kiran.sai@comlina.com', 'Kiran Sai', 'Asia/Kolkata')
ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

-- Insert Demo Workspace
INSERT INTO workspaces (id, name, slug, plan_tier, plan_status, max_automations)
VALUES ('b0000000-0000-0000-0000-000000000001', 'Kiran Studio', 'kiran-studio', 'PRO', 'ACTIVE', 100)
ON CONFLICT (id) DO NOTHING;

-- Link Member
INSERT INTO workspace_members (workspace_id, user_id, role)
VALUES ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'OWNER')
ON CONFLICT (workspace_id, user_id) DO NOTHING;

-- Insert Connected Instagram Account
INSERT INTO instagram_accounts (id, workspace_id, ig_user_id, username, account_type, follower_count, access_token_encrypted)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    '17841400123456789',
    '@kiran.creator',
    'BUSINESS',
    18400,
    'enc_token_demo_sample_meta_graph_api_key'
)
ON CONFLICT (workspace_id, ig_user_id) DO NOTHING;

-- Insert Automations
INSERT INTO automations (id, workspace_id, instagram_account_id, name, description, status, trigger_type, flow_definition, version, stats_comments, stats_dms_sent, stats_clicks)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'Guide DM + Follow Gate',
    'Sends comprehensive guide PDF when user comments GUIDE with follower check',
    'ACTIVE',
    'COMMENT',
    '{
        "trigger": { "type": "COMMENT", "keywords": ["GUIDE", "PLAYBOOK"] },
        "conditions": [
            { "type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallback_action": "SEND_FOLLOW_GATE" }
        ],
        "actions": [
            { "type": "PUBLIC_REPLY", "text": "Thanks @{username}! Sent the free guide link to your DMs 📩" },
            { "type": "PRIVATE_DM", "text": "Hey {first_name}! Here is your direct link to the 2026 AI Playbook: https://comlina.com/guide/ai" },
            { "type": "TAG_CONTACT", "tag": "guide-lead" }
        ]
    }'::jsonb,
    1,
    248,
    214,
    92
)
ON CONFLICT (id) DO NOTHING;

-- Insert Version Snapshot
INSERT INTO automation_versions (automation_id, workspace_id, version, trigger_type, flow_definition, published_by)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    1,
    'COMMENT',
    '{
        "trigger": { "type": "COMMENT", "keywords": ["GUIDE", "PLAYBOOK"] },
        "conditions": [
            { "type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallback_action": "SEND_FOLLOW_GATE" }
        ],
        "actions": [
            { "type": "PUBLIC_REPLY", "text": "Thanks @{username}! Sent the free guide link to your DMs 📩" },
            { "type": "PRIVATE_DM", "text": "Hey {first_name}! Here is your direct link to the 2026 AI Playbook: https://comlina.com/guide/ai" },
            { "type": "TAG_CONTACT", "tag": "guide-lead" }
        ]
    }'::jsonb,
    'a0000000-0000-0000-0000-000000000001'
)
ON CONFLICT (automation_id, version) DO NOTHING;

-- Insert Sample Contacts
INSERT INTO contacts (id, workspace_id, instagram_account_id, ig_user_id, username, full_name, email, follower_status, is_converted, tags)
VALUES
(
    'e0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'ig_user_101',
    '@sarah_designs',
    'Sarah Jenkins',
    'sarah@designcraft.co',
    'FOLLOWING',
    true,
    '["lead", "vip", "guide-lead"]'::jsonb
),
(
    'e0000000-0000-0000-0000-000000000002',
    'b0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'ig_user_102',
    '@david_ux',
    'David Miller',
    'david@uxhub.io',
    'NOT_FOLLOWING',
    false,
    '["lead", "price-inquiry"]'::jsonb
)
ON CONFLICT (workspace_id, instagram_account_id, ig_user_id) DO NOTHING;
