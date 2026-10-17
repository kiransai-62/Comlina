import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# --- Workspace Schemas ---
class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceOut(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_tier: str
    plan_status: str
    max_automations: int
    max_accounts: int
    created_at: datetime

# --- Instagram Account Schemas ---
class InstagramAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    ig_user_id: str
    username: str
    account_type: str
    follower_count: int
    profile_pic_url: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_active: bool
    connected_at: datetime

class ConnectAccountRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=1024)
    redirect_uri: Optional[str] = Field(None, max_length=2048)
    state: str = Field(..., min_length=1, max_length=512)

# --- Automation Schemas ---
class FlowDefinitionSchema(BaseModel):
    trigger: Dict[str, Any]
    conditions: Optional[List[Dict[str, Any]]] = []
    actions: List[Dict[str, Any]] = Field(..., min_length=1, max_length=50)
    nodes: Optional[List[Dict[str, Any]]] = []

class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    instagram_account_id: uuid.UUID
    trigger_type: str = Field(..., pattern=r"^(COMMENT|DM|STORY_REPLY|MENTION)$")
    flow_definition: FlowDefinitionSchema

class AutomationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|ACTIVE|PAUSED|ARCHIVED)$")
    flow_definition: Optional[FlowDefinitionSchema] = None

class AutomationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    instagram_account_id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    trigger_type: str
    flow_definition: Dict[str, Any]
    version: int
    stats_comments: int
    stats_dms_sent: int
    stats_clicks: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

# --- Contact Schemas ---
class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    instagram_account_id: uuid.UUID
    username: str
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    follower_status: str
    is_converted: bool
    interaction_count: int
    tags: List[str]
    notes: Optional[str]
    last_interaction_at: datetime
    created_at: datetime

class ContactCreate(BaseModel):
    instagram_account_id: uuid.UUID
    username: str = Field(..., min_length=1, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)
    follower_status: Optional[str] = Field("UNKNOWN", pattern=r"^(UNKNOWN|FOLLOWING|NOT_FOLLOWING|CHECK_UNAVAILABLE)$")
    tags: Optional[List[str]] = ["lead"]
    notes: Optional[str] = Field(None, max_length=5000)

# --- Conversation & Message Schemas ---
class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    media_url: Optional[str] = None

class SendMessageRequest(MessageCreate):
    pass

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_type: str
    text: str
    media_url: Optional[str]
    created_at: datetime

class InstagramMediaItem(BaseModel):
    id: str
    caption: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    permalink: Optional[str] = None
    timestamp: Optional[str] = None
    like_count: Optional[int] = None
    comments_count: Optional[int] = None

class InstagramMediaPage(BaseModel):
    data: List[InstagramMediaItem]
    next_cursor: Optional[str] = None

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contact_id: uuid.UUID
    status: str
    last_message_text: Optional[str] = None
    last_message_at: datetime
    unread_count: int
    contact: Optional[ContactOut] = None
    contact_username: Optional[str] = None
    name: Optional[str] = None
    followers: Optional[int] = None
    followed_you: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    first_seen: Optional[datetime] = None

# --- Webhook Schemas ---
class WebhookChallengeQuery(BaseModel):
    hub_mode: Optional[str] = Field(None, alias="hub.mode")
    hub_challenge: Optional[str] = Field(None, alias="hub.challenge")
    hub_verify_token: Optional[str] = Field(None, alias="hub.verify_token")
