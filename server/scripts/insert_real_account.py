import sqlite3
import uuid
import datetime
import json
from app.core.encryption import encrypt_token

token = 'IGAANs2PQCNp5BZAGFxTzBIbWdsSTlvTGlnZAC1PeEttSjJZAUmc0LUZAlZAkRmb3FOZAmFPTnpaa25fOXNnSTdEV0ptT19RZATdDang2OTdxR3B4RXB3c0lUR2VmSWxfdzlQUzRtMndSa1hfclRvY0hISW1INkxiZA1owR0pCNWRSZAVVjWQZDZD'
enc = encrypt_token(token)

con = sqlite3.connect('c:/PROJECTS/Comlina/server/comlina_dev.db')
cur = con.cursor()

ws_rows = cur.execute('SELECT id FROM workspaces').fetchall()
now = datetime.datetime.now(datetime.UTC).isoformat()
expires = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=60)).isoformat()
perms = json.dumps(["instagram_business_basic", "instagram_manage_messages", "instagram_manage_comments"])

for (ws_id,) in ws_rows:
    existing = cur.execute('SELECT id FROM instagram_accounts WHERE workspace_id = ? AND username = ?', (ws_id, 'aiworkbench.lab')).fetchone()
    if not existing:
        acc_id = uuid.uuid4().hex
        cur.execute('''
            INSERT INTO instagram_accounts (
                id, workspace_id, ig_user_id, username, account_type, 
                follower_count, profile_pic_url, access_token_encrypted, 
                token_expires_at, is_active, permissions, connected_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        ''', (acc_id, ws_id, '29500779709524479', 'aiworkbench.lab', 'MEDIA_CREATOR', 1250, 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80', enc, expires, perms, now, now))
        print(f'Inserted aiworkbench.lab into workspace {ws_id}')

con.commit()
print('Success! Accounts in DB:', cur.execute('SELECT id, workspace_id, username, is_active FROM instagram_accounts').fetchall())
con.close()
