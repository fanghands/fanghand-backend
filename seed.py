"""Seed the database with initial hands and a platform user."""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, engine
from app.models.base import Base
from app.models.user import User
from app.models.hand import Hand, HandType, HandStatus, HandCategory


PLATFORM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
COMMUNITY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

HANDS_DATA = [
    {
        "slug": "collector-hand",
        "name": "collector-hand",
        "description": "OSINT-style intelligence collector. monitors targets 24/7 with change detection, sentiment tracking, and knowledge graph construction.",
        "type": HandType.official,
        "status": HandStatus.live,
        "category": HandCategory.intelligence,
        "tags": ["crypto", "research"],
        "icon_emoji": "\U0001f50d",
        "author_id": PLATFORM_USER_ID,
        "total_activations": 312,
        "avg_rating": 4.2,
        "review_count": 47,
        "version": "1.0.0",
        "hand_toml_url": '[hand]\nname = "collector-hand"\nversion = "1.0.0"\n\n[schedule]\nfrequency = "6h"\n\n[settings]\nsources_per_cycle = 50\nsentiment = true',
        "published_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
    },
    {
        "slug": "researcher-hand",
        "name": "researcher-hand",
        "description": "fact-checking engine. cross-references sources using the CRAAP methodology. generates cited reports with confidence scores.",
        "type": HandType.official,
        "status": HandStatus.live,
        "category": HandCategory.research,
        "tags": ["research"],
        "icon_emoji": "\U0001f4da",
        "author_id": PLATFORM_USER_ID,
        "total_activations": 289,
        "avg_rating": 4.5,
        "review_count": 38,
        "version": "1.0.0",
        "hand_toml_url": '[hand]\nname = "researcher-hand"\nversion = "1.0.0"\n\n[schedule]\nfrequency = "daily"\n\n[output]\nformat = "markdown"\ncitations = true',
        "published_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
    },
    {
        "slug": "twitter-hand",
        "name": "twitter-hand",
        "description": "autonomous social media operator. posts 3x/day, engages with target accounts, tracks narrative shifts in the crypto/AI space.",
        "type": HandType.official,
        "status": HandStatus.live,
        "category": HandCategory.social,
        "tags": ["social", "automation"],
        "icon_emoji": "\U0001f426",
        "author_id": PLATFORM_USER_ID,
        "total_activations": 246,
        "avg_rating": 4.0,
        "review_count": 31,
        "version": "1.0.0",
        "hand_toml_url": '[hand]\nname = "twitter-hand"\nversion = "1.0.0"\n\n[schedule]\nposts_per_day = 3\n\n[settings]\napproval_mode = true\nstyle = "provocative"',
        "published_at": datetime(2026, 2, 15, tzinfo=timezone.utc),
    },
    {
        "slug": "analyst-hand",
        "name": "analyst-hand",
        "description": "synthesizes collector + researcher outputs into actionable recommendations. generates the weekly mission briefing for community vote.",
        "type": HandType.official,
        "status": HandStatus.review,
        "category": HandCategory.research,
        "tags": ["research", "crypto"],
        "icon_emoji": "\U0001f4ca",
        "author_id": PLATFORM_USER_ID,
        "total_activations": 0,
        "avg_rating": 0,
        "review_count": 0,
        "version": "0.9.0",
        "hand_toml_url": '[hand]\nname = "analyst-hand"\nversion = "0.9.0"\nstatus = "pending_activation"\n\n[dependencies]\nrequires = ["collector-hand", "researcher-hand"]',
    },
    {
        "slug": "orchestrator",
        "name": "orchestrator",
        "description": "CEO Hand. coordinates all other Hands, manages task routing, resolves conflicts, and ensures mission coherence across the agent team.",
        "type": HandType.official,
        "status": HandStatus.review,
        "category": HandCategory.automation,
        "tags": ["automation"],
        "icon_emoji": "\U0001f3af",
        "author_id": PLATFORM_USER_ID,
        "total_activations": 0,
        "avg_rating": 0,
        "review_count": 0,
        "version": "0.8.0",
        "hand_toml_url": '[hand]\nname = "orchestrator"\nversion = "0.8.0"\nstatus = "pending_activation"\n\n[role]\ntier = "supervisor"\ncontrols = ["all"]',
    },
    {
        "slug": "hyperliquid-intel-hand",
        "name": "hyperliquid-intel-hand",
        "description": "monitors Hyperliquid ecosystem 24/7. tracks builder code volumes, new protocol deployments, and fee distribution changes.",
        "type": HandType.community,
        "status": HandStatus.live,
        "category": HandCategory.intelligence,
        "tags": ["crypto", "research"],
        "icon_emoji": "\U0001f4a7",
        "author_id": COMMUNITY_USER_ID,
        "total_activations": 143,
        "avg_rating": 3.9,
        "review_count": 19,
        "price_monthly_cents": 200,
        "version": "1.1.0",
        "hand_toml_url": '[hand]\nname = "hyperliquid-intel-hand"\nversion = "1.1.0"\n\n[schedule]\nfrequency = "1h"\n\n[targets]\nchain = "hyperliquid"\ntrack = ["builders", "tvl", "fees"]',
        "published_at": datetime(2026, 2, 20, tzinfo=timezone.utc),
    },
    {
        "slug": "solana-narrative-hand",
        "name": "solana-narrative-hand",
        "description": "tracks narrative shifts across Solana Twitter, Discord, and on-chain activity. surfaces emerging meta before it goes mainstream.",
        "type": HandType.community,
        "status": HandStatus.live,
        "category": HandCategory.social,
        "tags": ["crypto", "social"],
        "icon_emoji": "\U0001f30a",
        "author_id": COMMUNITY_USER_ID,
        "total_activations": 98,
        "avg_rating": 4.1,
        "review_count": 14,
        "price_monthly_cents": 300,
        "version": "1.0.2",
        "hand_toml_url": '[hand]\nname = "solana-narrative-hand"\nversion = "1.0.2"\n\n[schedule]\nfrequency = "2h"\n\n[sources]\nplatforms = ["twitter", "discord", "on-chain"]',
        "published_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
    },
    {
        "slug": "defi-yield-hand",
        "name": "defi-yield-hand",
        "description": "scans DeFi protocols for yield opportunities. compares APYs, assesses smart contract risk, and generates daily opportunity briefings.",
        "type": HandType.community,
        "status": HandStatus.live,
        "category": HandCategory.finance,
        "tags": ["crypto", "automation"],
        "icon_emoji": "\U0001f4b0",
        "author_id": COMMUNITY_USER_ID,
        "total_activations": 67,
        "avg_rating": 3.7,
        "review_count": 9,
        "price_monthly_cents": 500,
        "version": "0.9.1",
        "hand_toml_url": '[hand]\nname = "defi-yield-hand"\nversion = "0.9.1"\n\n[schedule]\nfrequency = "4h"\n\n[scope]\nchains = ["solana", "ethereum", "base"]',
        "published_at": datetime(2026, 3, 5, tzinfo=timezone.utc),
    },
]


async def seed():
    async with async_session_factory() as session:
        # Create platform user if not exists
        for uid, wallet, username in [
            (PLATFORM_USER_ID, "FNG1111111111111111111111111111111111111111", "@fanghandx"),
            (COMMUNITY_USER_ID, "COM1111111111111111111111111111111111111111", "@community_builder"),
        ]:
            existing = await session.execute(select(User).where(User.id == uid))
            if existing.scalar_one_or_none() is None:
                user = User(id=uid, wallet_address=wallet, username=username)
                session.add(user)
        await session.flush()

        # Seed hands
        for hand_data in HANDS_DATA:
            existing = await session.execute(
                select(Hand).where(Hand.slug == hand_data["slug"])
            )
            if existing.scalar_one_or_none() is None:
                hand = Hand(id=uuid.uuid4(), **hand_data)
                session.add(hand)

        await session.commit()
        print(f"Seeded {len(HANDS_DATA)} hands successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
