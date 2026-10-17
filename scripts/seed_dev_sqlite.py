# pyright: reportMissingImports=none
# pyright: reportMissingModuleSource=none
"""
Comlina Dev Seeder - Connects Instagram Accounts, Automations, Contacts, and Conversations
across all workspaces in server/comlina_dev.db.
"""
import sys
import os
import uuid
import json
import hashlib
from datetime import datetime, timedelta, timezone

# Ensure python path includes server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

try:
    from server.app.core.config import settings
    from server.app.core.encryption import encrypt_token
    from server.app.models import (
        User, Workspace, WorkspaceMember, InstagramAccount,
        Automation, AutomationVersion, Contact, Conversation, Message,
        WebhookEvent, AnalyticsEvent
    )
except ImportError:
    from app.core.config import settings  # type: ignore
    from app.core.encryption import encrypt_token  # type: ignore
    from app.models import (  # type: ignore
        User, Workspace, WorkspaceMember, InstagramAccount,
        Automation, AutomationVersion, Contact, Conversation, Message,
        WebhookEvent, AnalyticsEvent
    )

def run_seed():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server", "comlina_dev.db"))
    engine = create_engine(f"sqlite:///{db_path}")

    with Session(engine) as session:
        workspaces = session.execute(select(Workspace)).scalars().all()
        if not workspaces:
            print("No workspaces found. Creating default workspace...")
            # Default dev password: Password123!
            salt = os.urandom(32)
            pw_hash = hashlib.pbkdf2_hmac("sha256", "Password123!".encode("utf-8"), salt, 100_000)
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                email="kiran@example.com",
                full_name="Kiran Sai",
                timezone=f"pbkdf2:{salt.hex()}:{pw_hash.hex()}"
            )
            session.add(user)
            session.flush()

            ws = Workspace(
                id=uuid.uuid4(),
                name="Kiran Studio",
                slug="kiran-studio",
                plan_tier="PRO",
                plan_status="ACTIVE"
            )
            session.add(ws)
            session.flush()

            member = WorkspaceMember(
                workspace_id=ws.id,
                user_id=user.id,
                role="OWNER"
            )
            session.add(member)
            session.commit()
            workspaces = [ws]

        demo_token = encrypt_token(os.getenv("DEV_IG_ACCESS_TOKEN", "EAAG_demo_access_token_comlina_2026"))

        for ws in workspaces:
            print(f"Connecting resources for workspace {ws.name} ({ws.id})...")

            # 1. Instagram Account
            existing_acc = session.execute(
                select(InstagramAccount).where(InstagramAccount.workspace_id == ws.id)
            ).scalars().first()

            if not existing_acc:
                acc = InstagramAccount(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    ig_user_id="29500779709524479",
                    username="aiworkbench.lab",
                    account_type="MEDIA_CREATOR",
                    profile_pic_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&auto=format&fit=crop&q=80",
                    follower_count=19400,
                    access_token_encrypted=demo_token,
                    token_expires_at=datetime.now(timezone.utc) + timedelta(days=60),
                    is_active=True,
                    permissions=["instagram_business_basic", "instagram_business_manage_messages", "instagram_business_manage_comments"]
                )
                session.add(acc)
                session.flush()
            else:
                acc = existing_acc
                acc.is_active = True
                session.flush()

            # 2. Automations
            existing_autos = session.execute(
                select(Automation).where(Automation.workspace_id == ws.id)
            ).scalars().all()

            if not existing_autos:
                auto1 = Automation(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    instagram_account_id=acc.id,
                    name="Guide DM + Follow Gate",
                    description="Sends playbook PDF when user comments GUIDE with follower check",
                    status="ACTIVE",
                    trigger_type="COMMENT",
                    flow_definition={
                        "trigger": {"type": "COMMENT", "keywords": ["GUIDE", "PLAYBOOK"]},
                        "conditions": [{"type": "FOLLOWER_STATUS", "expected": "FOLLOWING", "fallback_action": "SEND_FOLLOW_GATE"}],
                        "actions": [
                            {"type": "PUBLIC_REPLY", "text": "Thanks @{username}! Sent the free guide link to your DMs 📩"},
                            {"type": "PRIVATE_DM", "text": "Hey {first_name}! Here is your direct link to the 2026 AI Playbook: https://comlina.com/guide/ai"},
                            {"type": "TAG_CONTACT", "tag": "guide-lead"}
                        ]
                    },
                    version=1,
                    stats_comments=312,
                    stats_dms_sent=284,
                    stats_clicks=142,
                    published_at=datetime.now(timezone.utc) - timedelta(days=7)
                )
                auto2 = Automation(
                    id=uuid.uuid4(),
                    workspace_id=ws.id,
                    instagram_account_id=acc.id,
                    name="Story Mention VIP Reward",
                    description="Sends exclusive 20% discount code to users who mention in Stories",
                    status="ACTIVE",
                    trigger_type="STORY_MENTION",
                    flow_definition={
                        "trigger": {"type": "STORY_MENTION", "keywords": []},
                        "conditions": [],
                        "actions": [
                            {"type": "PRIVATE_DM", "text": "Thank you for the shoutout @{username}! Here is your 20% off code: VIP20"},
                            {"type": "TAG_CONTACT", "tag": "story-advocate"}
                        ]
                    },
                    version=1,
                    stats_comments=0,
                    stats_dms_sent=98,
                    stats_clicks=64,
                    published_at=datetime.now(timezone.utc) - timedelta(days=5)
                )
                session.add_all([auto1, auto2])
                session.flush()
            else:
                auto1 = existing_autos[0]

            # 3. Contacts
            contacts_data = [
                {
                    "ig_user_id": "ig_user_201",
                    "username": "sarah_designs",
                    "full_name": "Sarah Jenkins",
                    "email": "sarah@designcraft.co",
                    "follower_status": "FOLLOWING",
                    "is_converted": True,
                    "tags": ["lead", "vip", "guide-lead"],
                    "notes": "Highly engaged UI/UX designer, requested the AI Playbook."
                },
                {
                    "ig_user_id": "ig_user_202",
                    "username": "david_ux",
                    "full_name": "David Miller",
                    "email": "david@uxhub.io",
                    "follower_status": "FOLLOWING",
                    "is_converted": False,
                    "tags": ["lead", "price-inquiry"],
                    "notes": "Inquiring about enterprise tier integrations."
                },
                {
                    "ig_user_id": "ig_user_203",
                    "username": "elena_creator",
                    "full_name": "Elena Rostova",
                    "email": "elena@aetherix.studio",
                    "follower_status": "FOLLOWING",
                    "is_converted": True,
                    "tags": ["vip", "creator", "story-advocate"],
                    "notes": "Mentioned product in story with 50k views."
                }
            ]

            for c_info in contacts_data:
                contact = session.execute(
                    select(Contact).where(
                        Contact.workspace_id == ws.id,
                        Contact.ig_user_id == c_info["ig_user_id"]
                    )
                ).scalars().first()

                if not contact:
                    contact = Contact(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        instagram_account_id=acc.id,
                        ig_user_id=c_info["ig_user_id"],
                        username=c_info["username"],
                        full_name=c_info["full_name"],
                        email=c_info["email"],
                        follower_status=c_info["follower_status"],
                        is_converted=c_info["is_converted"],
                        tags=c_info["tags"],
                        notes=c_info["notes"],
                        last_interaction_at=datetime.now(timezone.utc) - timedelta(minutes=25)
                    )
                    session.add(contact)
                    session.flush()

                # 4. Conversation
                conv = session.execute(
                    select(Conversation).where(
                        Conversation.workspace_id == ws.id,
                        Conversation.contact_id == contact.id
                    )
                ).scalars().first()

                if not conv:
                    last_msg = f"Hey {contact.full_name.split()[0]}! Welcome to Comlina."
                    conv = Conversation(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        instagram_account_id=acc.id,
                        contact_id=contact.id,
                        status="OPEN" if not contact.is_converted else "REPLIED",
                        last_message_text=last_msg,
                        last_message_at=datetime.now(timezone.utc) - timedelta(minutes=25),
                        unread_count=1 if not contact.is_converted else 0
                    )
                    session.add(conv)
                    session.flush()

                    # Messages
                    m1 = Message(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        conversation_id=conv.id,
                        sender_type="CONTACT",
                        text="Hi! Saw your post about the new automated flows. How does it work?",
                        created_at=datetime.now(timezone.utc) - timedelta(minutes=30)
                    )
                    m2 = Message(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        conversation_id=conv.id,
                        sender_type="INSTAGRAM_ACCOUNT",
                        text=last_msg,
                        created_at=datetime.now(timezone.utc) - timedelta(minutes=25)
                    )
                    session.add_all([m1, m2])

            # 5. Webhook Events for Analytics Health
            webhook_count = session.execute(
                select(WebhookEvent).where(WebhookEvent.workspace_id == ws.id)
            ).scalars().all()

            if not webhook_count:
                for i in range(10):
                    ev = WebhookEvent(
                        id=uuid.uuid4(),
                        workspace_id=ws.id,
                        instagram_account_id=acc.id,
                        provider_event_id=f"evt_seed_{ws.id}_{i}",
                        event_type="COMMENT" if i % 2 == 0 else "MESSAGING",
                        payload={"entry": [{"id": acc.ig_user_id}]},
                        status="COMPLETED",
                        received_at=datetime.now(timezone.utc) - timedelta(minutes=60 - i * 5),
                        processed_at=datetime.now(timezone.utc) - timedelta(minutes=60 - i * 5 - 1)
                    )
                    session.add(ev)

        session.commit()
        print("Successfully seeded all workspaces with connected Instagram accounts, automations, contacts, and conversations!")

if __name__ == "__main__":
    run_seed()
