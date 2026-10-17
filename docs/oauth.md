# Meta Instagram Graph API OAuth Guide

## 1. Required Meta Graph Permissions

To automate Instagram comments and Direct Messages, your Meta App must request:

- `instagram_basic`: Read profile info and follower metrics.
- `instagram_manage_messages`: Send and receive direct messages and automated private replies.
- `instagram_manage_comments`: Read comments and post automated public replies.
- `pages_show_list`: Associate Instagram professional accounts with Facebook Pages.
- `pages_read_engagement`: Monitor post comments and mentions.

## 2. Authorization Flow

1. User clicks **"Connect Instagram Account"** in Comlina.
2. Comlina redirects user to:

   ```text
   https://www.facebook.com/v21.0/dialog/oauth?client_id=...&redirect_uri=...&scope=...
   ```

3. User logs in, selects Instagram Business / Creator accounts, and grants permissions.
4. Meta redirects to `/connect/instagram?code=...`.
5. Comlina backend exchanges authorization code for short-lived user token.
6. Comlina exchanges short-lived token for 60-day long-lived page access token:

   ```http
   GET /oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token=...
   ```

7. Encrypted token is stored in `instagram_accounts` table linked to the current `workspace_id`.
