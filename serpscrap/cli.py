"""Click-based command-line interface for SerpScrap."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

import click

from scrapcore.scraper.browser import ChromeDriverFactory
from serpscrap import Config, SerpScrap
from serpscrap.topic_service import TopicService
from serpscrap.topics import TopicRequest

LOG_LEVELS = click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False)


def _echo_json(payload: Any) -> None:
    """Write result JSON without failing on a legacy Windows console codec."""
    stream = getattr(sys, "stdout", None)
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError):
            pass
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        click.echo(rendered)
    except UnicodeEncodeError:
        # Some embedded runners expose an immutable cp1252 stream.  Escaped
        # UTF-8 keeps the JSON valid and guarantees that the command exits.
        click.echo(rendered.encode("utf-8", errors="backslashreplace").decode("ascii"))


class JsonLogFormatter(logging.Formatter):
    """Emit one compact JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if getattr(record, "progress_event", None) is not None:
            payload["event"] = record.progress_event
        return json.dumps(payload, ensure_ascii=False)


class ClickLogHandler(logging.Handler):
    """Route Python log records through Click's stderr handling."""

    _serpscrap_click_handler = True

    def emit(self, record: logging.LogRecord) -> None:
        try:
            click.echo(self.format(record), err=True)
        except Exception:
            self.handleError(record)


def configure_logging(level: str, log_format: str) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [
        handler
        for handler in root.handlers
        if not getattr(handler, "_serpscrap_click_handler", False)
    ]
    handler = ClickLogHandler()
    if log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--log-level", type=LOG_LEVELS, default="INFO", show_default=True)
@click.option(
    "--log-format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
def main(log_level: str, log_format: str) -> None:
    """Retrieve structured SERPs from configured search engines."""

    configure_logging(log_level, log_format)


@main.command("search")
@click.option(
    "-k",
    "--keyword",
    "--keywords",
    "keywords",
    multiple=True,
    required=True,
    help="Query to run; repeat the option for multiple queries.",
)
@click.option("--pages", type=click.IntRange(min=1), default=None)
@click.option("--workers", type=click.IntRange(min=1), default=None)
@click.option(
    "--engine",
    "engines",
    multiple=True,
    help="Search engine ID; repeat for parallel engines (default: google).",
)
@click.option(
    "--country",
    "country_code",
    type=click.STRING,
    default=None,
    help="ISO 3166-1 alpha-2 result market.",
)
@click.option(
    "--search-type",
    type=click.Choice(["normal", "image", "news", "shopping", "videos"]),
    default=None,
)
@click.option("--visible", is_flag=True, default=None, help="Show the Chrome window.")
@click.option("--screenshots", is_flag=True, default=None, help="Save diagnostic screenshots.")
@click.option("--scrape-urls", is_flag=True, default=None, help="Also fetch parsed result pages.")
@click.option(
    "--output",
    type=click.Path(path_type=str, dir_okay=False),
    help="Atomically save the result array to a local .json file.",
)
@click.option(
    "--overwrite", is_flag=True, default=False, help="Replace an existing JSON output file."
)
@click.option("--no-cache", is_flag=True, default=None, help="Disable the local HTML cache.")
@click.option("--no-history", is_flag=True, default=None, help="Disable persistent SQLite history.")
@click.option(
    "--consent-action",
    type=click.Choice(["necessary", "reject", "accept", "disabled"]),
    default=None,
    help="Handle consent dialogs using the privacy-preserving rejection action.",
)
@click.option("--progress/--no-progress", default=True, help="Show per-engine progress on stderr.")
@click.option(
    "--progress-format",
    type=click.Choice(["text", "jsonl"]),
    default="text",
    show_default=True,
    help="Progress event format; JSON Lines is written to stderr.",
)
@click.option(
    "--diagnostic-html",
    is_flag=True,
    default=False,
    help="Save redacted rendered HTML under the diagnostic directory.",
)
@click.option(
    "--diagnostic-dir",
    type=click.Path(path_type=str, file_okay=False),
    default=None,
    help="Diagnostic artifact directory.",
)
def search(
    keywords: tuple[str, ...],
    pages: int | None,
    workers: int | None,
    engines: tuple[str, ...],
    country_code: str | None,
    search_type: str | None,
    visible: bool | None,
    screenshots: bool | None,
    scrape_urls: bool | None,
    output: str | None,
    overwrite: bool,
    no_cache: bool | None,
    no_history: bool | None,
    consent_action: str | None,
    progress: bool,
    progress_format: str,
    diagnostic_html: bool,
    diagnostic_dir: str | None,
) -> None:
    """Run one or more configured search queries and write JSON to stdout."""

    logger = logging.getLogger("serpscrap.cli")
    config = Config()
    overrides: dict[str, Any] = {}
    if pages is not None:
        overrides["num_pages_for_keyword"] = pages
    if workers is not None:
        overrides["num_workers"] = workers
    if engines:
        overrides["search_engines"] = list(engines)
    if country_code is not None:
        overrides["country_code"] = country_code.upper()
    if search_type is not None:
        overrides["search_type"] = search_type
    if visible is not None:
        overrides["chrome_headless"] = not visible
    if screenshots is not None:
        overrides["screenshot"] = screenshots
    if scrape_urls is not None:
        overrides["scrape_urls"] = scrape_urls
    if no_cache:
        overrides["do_caching"] = False
    if no_history:
        overrides["store_history"] = False
    if consent_action is not None:
        overrides["consent_action"] = consent_action
    overrides["progress"] = progress
    overrides["progress_format"] = progress_format
    overrides["diagnostic_html"] = diagnostic_html
    if diagnostic_dir is not None:
        overrides["diagnostic_dir"] = diagnostic_dir
    config.apply(overrides)
    effective_workers = config.get().get("num_workers", 1)
    logger.info("Starting %d query job(s) with %d worker(s)", len(keywords), effective_workers)
    scraper = SerpScrap()
    try:
        results = scraper.search(
            list(keywords),
            config=config,
            output=output,
            overwrite=overwrite,
        )
    except Exception as exc:
        logger.exception("Search failed")
        raise click.ClickException(str(exc)) from exc
    for failure in scraper.get_failures():
        logger.warning(
            "Partial failure [%s] correlation_id=%s page=%s retryable=%s: %s",
            failure["category"],
            failure["correlation_id"],
            failure["page_number"],
            failure["retryable"],
            failure["message"],
        )
    logger.info("Search completed with %d parsed result(s)", len(results))
    _echo_json(results)


@main.command("topic-search")
@click.argument("topic", type=click.Choice(["news", "shopping"]))
@click.argument("query")
@click.option("--source", "sources", multiple=True)
@click.option("--country", default=None)
@click.option("--language", default=None)
@click.option("--since", default=None, help="ISO timestamp or relative value such as 24h.")
def topic_search(
    topic: str,
    query: str,
    sources: tuple[str, ...],
    country: str | None,
    language: str | None,
    since: str | None,
) -> None:
    """Run a News or Shopping query through the shared TopicService."""
    try:
        report = TopicService(config=Config().get()).execute(
            TopicRequest.create(
                query, topic=topic, sources=sources, country=country, language=language, since=since
            )
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    _echo_json(report.to_dict())


@main.command("browser-check")
@click.option("--visible", is_flag=True, help="Show the Chrome window.")
def browser_check(visible: bool) -> None:
    """Start Chrome, print its version, and terminate it without network access."""

    logger = logging.getLogger("serpscrap.cli")
    config = Config().get()
    config["chrome_headless"] = not visible
    driver = None
    try:
        logger.info("Starting Chrome health check")
        driver = ChromeDriverFactory.from_config(config).create()
        version = driver.capabilities.get("browserVersion", "unknown")
        click.echo(f"Chrome {version}")
        logger.info("Chrome health check completed")
    except Exception as exc:
        logger.exception("Chrome health check failed")
        raise click.ClickException(str(exc)) from exc
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()
