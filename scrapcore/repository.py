"""Optional SQLite history adapter."""

from __future__ import annotations

from typing import Any

from scrapcore.database import (
    Link,
    RelatedKeyword,
    ScraperSearch,
    SearchEngineResultsPage,
    fixtures,
    get_session,
)


def _column_values(entity: Any, *, excluded: set[str]) -> dict[str, Any]:
    return {
        column.name: getattr(entity, column.name)
        for column in entity.__table__.columns
        if column.name not in excluded
    }


class SqliteHistoryRepository:
    """Persist a detached copy without owning application result assembly."""

    def persist(self, config: dict[str, Any], search: ScraperSearch) -> None:
        session = get_session(config)()
        try:
            fixtures(config, session)
            stored_search = ScraperSearch(
                **_column_values(search, excluded={"id"}),
            )
            for serp in search.serps:
                stored_serp = SearchEngineResultsPage(
                    **_column_values(serp, excluded={"id"}),
                )
                stored_search.serps.append(stored_serp)
                for link in serp.links:
                    Link(
                        **_column_values(link, excluded={"id", "serp_id"}),
                        serp=stored_serp,
                    )
                for keyword in serp.related_keywords:
                    RelatedKeyword(
                        **_column_values(keyword, excluded={"id", "serp_id"}),
                        serp=stored_serp,
                    )
            session.add(stored_search)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
