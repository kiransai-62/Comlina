import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, Text, UniqueConstraint, Index, Uuid, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base

# Universal JSON type that automatically uses native JSONB on PostgreSQL and JSON on SQLite
JSONType = JSON().with_variant(JSONB, "postgresql")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)



class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    # Dedicated column for PBKDF2-HMAC-SHA256 password hash (format: "pbkdf2:<salt_hex>:<hash_hex>").
    # Auth previously (incorrectly) stored this in `timezone`; new accounts use this column.
    # Migration: _apply_schema_patches() adds this column; login falls back to timezone if
    # password_hash is empty and timezone starts with "pbkdf2:" for backward compatibility.
    password_hash: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    workspaces = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(32), default="FREE")
    plan_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    max_automations: Mapped[int] = mapped_column(Integer, default=10)
    max_accounts: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    instagram_accounts = relationship("InstagramAccount", back_populates="workspace", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), default="MEMBER")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")


class InstagramAccount(Base):
    __tablename__ = "instagram_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ig_user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(32), default="BUSINESS")
    profile_pic_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_method: Mapped[str] = mapped_column(String(64), default="META_INSTAGRAM_OAUTH")
    connection_status: Mapped[str] = mapped_column(String(32), default="CONNECTED", index=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    permissions: Mapped[Any] = mapped_column(JSONType, default=["instagram_manage_messages", "instagram_manage_comments"])
    webhook_subscription_status: Mapped[Optional[str]] = mapped_column(String(32), default="UNKNOWN", nullable=True)
    webhook_subscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (UniqueConstraint("ig_user_id", name="uq_ig_accounts_ig_user_id"),)

    workspace = relationship("Workspace", back_populates="instagram_accounts")
    user = relationship("User")
    automations = relationship("Automation", back_populates="instagram_account")


class Automation(Base):
    __tablename__ = "automations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    flow_definition: Mapped[Any] = mapped_column(JSONType, nullable=False, default={})
    version: Mapped[int] = mapped_column(Integer, default=1)
    stats_comments: Mapped[int] = mapped_column(Integer, default=0)
    stats_dms_sent: Mapped[int] = mapped_column(Integer, default=0)
    stats_clicks: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    workspace = relationship("Workspace", back_populates="automations")
    instagram_account = relationship("InstagramAccount", back_populates="automations")
    versions = relationship("AutomationVersion", back_populates="automation", cascade="all, delete-orphan")


class AutomationVersion(Base):
    __tablename__ = "automation_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    automation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("automations.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    flow_definition: Mapped[Any] = mapped_column(JSONType, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    published_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (UniqueConstraint("automation_id", "version", name="uq_automation_version"),)

    automation = relationship("Automation", back_populates="versions")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), index=True)
    ig_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_pic_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # 4 explicit states: UNKNOWN, FOLLOWING, NOT_FOLLOWING, CHECK_UNAVAILABLE
    follower_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    automation_state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default=None, index=True)
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    interaction_count: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[Any] = mapped_column(JSONType, default=["lead"])
    custom_fields: Mapped[Any] = mapped_column(JSONType, default={})
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_interaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (UniqueConstraint("workspace_id", "instagram_account_id", "ig_user_id", name="uq_workspace_ig_contact"),)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    last_message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (UniqueConstraint("workspace_id", "instagram_account_id", "contact_id", name="uq_workspace_conversation"),)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_type: Mapped[str] = mapped_column(String(16), nullable=False) # CONTACT, INSTAGRAM_ACCOUNT, BOT
    text: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    automation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("automations.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    instagram_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="SET NULL"), nullable=True)
    provider_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Any] = mapped_column(JSONType, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), index=True)
    automation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("automations.id", ondelete="SET NULL"), index=True)
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metadata_: Mapped[Any] = mapped_column("metadata", JSONType, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class PostUsage(Base):
    __tablename__ = "post_usage"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    instagram_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=True)
    ig_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    media_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    dms_delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    max_dms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (UniqueConstraint("workspace_id", "media_id", name="uq_post_usage_workspace_media"),)


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan_tier: Mapped[str] = mapped_column(String(32), nullable=False)  # PREMIUM, PRO
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)  # 19900, 39900
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    razorpay_order_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    razorpay_signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="CREATED", index=True)  # CREATED, PAID, FAILED, EXPIRED
    billing_period: Mapped[str] = mapped_column(String(32), default="MONTHLY")
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[Any] = mapped_column("metadata", JSONType, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    instagram_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    ig_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    automation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("automations.id", ondelete="CASCADE"), nullable=True, index=True)
    automation_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("automation_versions.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    meta_error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta_error_subcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


