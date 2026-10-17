# Multi-Tenant Architecture & Security

## Hierarchy

```text
User (Supabase Auth)
  │
  ▼
Workspaces
  │
  ├── Workspace Members (Roles: OWNER, ADMIN, MEMBER)
  ├── Instagram Accounts
  ├── Automations (with JSONB flow_definition & versions)
  ├── Contacts (Follower status & captured leads)
  ├── Conversations & Messages
  ├── Webhook Events (Durable deduplication log)
  └── Analytics Events
```

## Security Rules

1. **Never Trust Client Workspace ID**:
   Clients pass `X-Workspace-ID` in request headers, but the server always verifies that the authenticated user actually has an active membership record in `workspace_members` for that workspace.

2. **Database Row Level Security (RLS)**:
   In addition to application-level checks, PostgreSQL RLS policies enforce that users can only query rows where:

   ```sql
   is_workspace_member(workspace_id) = true
   ```

3. **Isolated Meta Integration**:
   API keys and encrypted access tokens are scoped to the specific `workspace_id`. Cross-workspace account sharing is strictly prohibited.
