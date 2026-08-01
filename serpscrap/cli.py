"""Click-based command-line interface for SerpScrap."""

from __future__ import annotations

import json
import logging
from typing import Any

import click

from scrapcore.scraper.browser import ChromeDriverFactory
from serpscrap import Config, SerpScrap

LOG_LEVELS = click.Choice(
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
)


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
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
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
    """Retrieve structured Google SERPs with headless Chrome."""

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
@click.option("--pages", type=click.IntRange(min=1), default=1, show_default=True)
@click.option("--workers", type=click.IntRange(min=1), default=1, show_default=True)
@click.option(
    "--search-type",
    type=click.Choice(["normal", "image", "news", "shopping", "videos"]),
    default="normal",
    show_default=True,
)
@click.option("--visible", is_flag=True, help="Show the Chrome window.")
@click.option("--screenshots", is_flag=True, help="Save diagnostic screenshots.")
@click.option("--scrape-urls", is_flag=True, help="Also fetch parsed result pages.")
@click.option(
    "--output",
    type=click.Path(path_type=str, dir_okay=False),
    help="Atomically save the result array to a local .json file.",
)
@click.option("--overwrite", is_flag=True, help="Replace an existing JSON output file.")
@click.option("--no-cache", is_flag=True, help="Disable the local HTML cache.")
@click.option("--no-history", is_flag=True, help="Disable persistent SQLite history.")
def search(
    keywords: tuple[str, ...],
    pages: int,
    workers: int,
    search_type: str,
    visible: bool,
    screenshots: bool,
    scrape_urls: bool,
    output: str | None,
    overwrite: bool,
    no_cache: bool,
    no_history: bool,
) -> None:
    """Run one or more Google search queries and write JSON results to stdout."""

    logger = logging.getLogger("serpscrap.cli")
    config = Config()
    config.apply(
        {
            "num_pages_for_keyword": pages,
            "num_workers": workers,
            "search_type": search_type,
            "chrome_headless": not visible,
            "screenshot": screenshots,
            "scrape_urls": scrape_urls,
            "do_caching": not no_cache,
            "store_history": not no_history,
        }
    )
    logger.info("Starting %d query job(s) with %d worker(s)", len(keywords), workers)
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
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


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
