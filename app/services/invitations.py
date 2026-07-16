from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import InviteToken


class InvitationService:
    def __init__(self, signing_secret: str, bot_username: str) -> None:
        self._secret = signing_secret.encode()
        self._bot_username = bot_username

    def _signature(self, token_id: int) -> str:
        message = str(token_id).encode()
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()[:20]

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def rotate(self, session: AsyncSession, created_by_user_id: int) -> str:
        await session.execute(
            update(InviteToken)
            .where(InviteToken.is_active.is_(True))
            .values(is_active=False, invalidated_at=datetime.now(UTC))
        )
        record = InviteToken(
            token_hash=hashlib.sha256(
                f"pending:{datetime.now(UTC).isoformat()}".encode()
            ).hexdigest(),
            created_by_user_id=created_by_user_id,
        )
        session.add(record)
        await session.flush()
        raw = f"{record.id}_{self._signature(record.id)}"
        record.token_hash = self._hash(raw)
        return self.link(raw)

    async def current_link(self, session: AsyncSession) -> str | None:
        active = await session.scalar(
            select(InviteToken.id).where(InviteToken.is_active.is_(True)).limit(1)
        )
        if active is None:
            return None
        raw = f"{active}_{self._signature(active)}"
        return self.link(raw)

    async def validate(self, session: AsyncSession, raw: str) -> bool:
        parts = raw.split("_")
        if len(parts) != 2:
            return False
        try:
            token_id = int(parts[0])
        except ValueError:
            return False
        signature = parts[1]
        if not hmac.compare_digest(signature, self._signature(token_id)):
            return False
        record = await session.get(InviteToken, token_id)
        return bool(
            record and record.is_active and hmac.compare_digest(record.token_hash, self._hash(raw))
        )

    def link(self, raw: str) -> str:
        return f"https://t.me/{self._bot_username}?start=join_{raw}"
