"""Registry for thematic source plugins."""

from __future__ import annotations

from collections.abc import Iterable

from serpscrap.topics import TopicPlugin


class TopicPluginRegistry:
    def __init__(self, plugins: Iterable[TopicPlugin] = ()) -> None:
        self._plugins: dict[str, TopicPlugin] = {}
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: TopicPlugin) -> None:
        errors = plugin.validate_contract()
        if errors:
            raise ValueError(f"invalid topic plugin {plugin.topic_id!r}: {'; '.join(errors)}")
        source_id = plugin.source_id or plugin.topic_id
        if source_id in self._plugins:
            raise ValueError(f"duplicate topic source: {source_id}")
        self._plugins[source_id] = plugin

    def get(self, topic_id: str) -> TopicPlugin:
        try:
            return self._plugins[topic_id]
        except KeyError as exc:
            matches = [plugin for plugin in self._plugins.values() if plugin.topic_id == topic_id]
            if matches:
                return matches[0]
            raise KeyError(f"unknown topic or source: {topic_id}") from exc

    def find(
        self,
        *,
        topic: str | None = None,
        country: str | None = None,
        language: str | None = None,
        transport: str | None = None,
    ) -> list[TopicPlugin]:
        result = list(self._plugins.values())
        result = [
            p
            for p in result
            if getattr(p.capabilities.readiness, "value", p.capabilities.readiness) != "disabled"
        ]
        if topic:
            result = [p for p in result if p.topic_id == topic]
        if country:
            result = [
                p
                for p in result
                if not p.capabilities.supported_countries
                or country.upper() in p.capabilities.supported_countries
            ]
        if language:
            result = [
                p
                for p in result
                if not p.capabilities.supported_languages
                or language.lower() in p.capabilities.supported_languages
            ]
        if transport:
            result = [p for p in result if p.capabilities.transport == transport]
        return result

    def metadata(self) -> list[dict]:
        return [plugin.metadata() for plugin in self._plugins.values()]
