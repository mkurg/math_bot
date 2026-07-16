from __future__ import annotations

from app.core.topics.contracts import TopicModule


class TopicRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, TopicModule] = {}
        self._enabled: tuple[str, ...] = ()

    def register(self, module: TopicModule) -> None:
        topic_id = module.metadata.topic_id
        if topic_id in self._modules:
            raise ValueError(f"duplicate topic ID: {topic_id}")
        errors = module.validate()
        if errors:
            raise ValueError(f"invalid topic {topic_id}: {'; '.join(errors)}")
        self._modules[topic_id] = module

    def configure(self, enabled_topic_ids: tuple[str, ...], default_topic_id: str) -> None:
        missing = set(enabled_topic_ids).difference(self._modules)
        if missing:
            raise ValueError(f"enabled topics are not registered: {sorted(missing)}")
        if default_topic_id not in enabled_topic_ids:
            raise ValueError("default topic must be enabled")
        self._enabled = enabled_topic_ids

    def get(self, topic_id: str) -> TopicModule:
        try:
            return self._modules[topic_id]
        except KeyError as exc:
            raise LookupError(f"unknown topic: {topic_id}") from exc

    def enabled_topics(self) -> tuple[TopicModule, ...]:
        return tuple(self._modules[topic_id] for topic_id in self._enabled)
