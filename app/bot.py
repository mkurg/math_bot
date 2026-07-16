from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.content.loader import ContentCatalog
from app.core.topics.registry import TopicRegistry
from app.services.invitations import InvitationService


@dataclass(slots=True)
class Application:
    settings: Settings
    sessions: async_sessionmaker[AsyncSession]
    registry: TopicRegistry
    content: ContentCatalog
    invitations: InvitationService

    def text(self, key: str, topic_id: str | None = None, **values: object) -> str:
        """Resolve student-facing text from the assigned topic, then fall back to core."""
        if topic_id is not None:
            try:
                return self.registry.get(topic_id).content(key, **values)
            except KeyError:
                pass
        return self.content.get(key, **values)
