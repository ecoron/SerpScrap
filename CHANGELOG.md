# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Added the Phase 6 plan for reproducible Read-the-Docs documentation builds and Sphinx configuration alignment.
- Added a root-level Read the Docs version-2 build configuration, reproducible Sphinx requirements, MyST Markdown support, and warning-clean build settings.
- Aligned the local documentation Makefile/navigation and removed the obsolete Jekyll configuration.
- Added a dedicated CI job for the warning-as-error Sphinx HTML build.
- Completed Phase 5 production integration for the registered multi-engine plugins, including validated readiness/capability metadata, per-engine concurrency ceilings, versioned country-aware cache identities, atomic cache writes, and explainable deterministic fusion report metadata.
- Added documentation examples for multi-engine searches capped at four concurrent requests.
- CLI searches now inherit all omitted option values from ``serpscrap/config.py``; ``search -k`` no longer replaces configured defaults.
- Added the direct ``SerpScrap.search()`` API with canonical JSON-compatible ``list[dict]`` results.
- Added atomic UTF-8 JSON file output and CLI ``--output``/``--overwrite`` options.
- Made HTML caching and SQLite history independently optional.
- Moved optional SQLite history behind a post-assembly repository so persistence failures retain successful in-memory results.
- Removed CSV output, duplicate result writers, and the unreachable legacy scraping workflow.
- Added current Chrome identity resolution, paced Google navigation, bounded transient retries, access-control/rate-limit classification, and a run circuit breaker.
- Added canonical parsing and vertical routing for organic, image, news, shopping, and video result formats.
- Hardened URL enrichment with explicit headers, limits, classified failures, and atomic identity-aware caching.

## [0.14.0] - 2025-10-26
### Changed
- Removed support for Firefox and PhantomJS. Only Chrome is supported.
- Updated dependencies and improved error handling.
- Refactored cache management and Selenium integration.
- Modernized Dockerfile (now based on python:3.10-slim).
- Updated documentation and README for pipenv and Docker usage.
- Added clear pipenv CLI usage examples to README and docs.

## [0.13.0]
### Changed
- Updated dependencies: chromedriver >= 76.0.3809.68, sqlalchemy>=1.3.7
- Minor changes to install_chrome.sh

## [0.12.0]
### Changed
- Update and cleanup of selectors to fetch results
- New result type: videos

## [0.11.0]
### Changed
- Chrome headless is now the default browser, PhantomJS is no longer supported
- Chromedriver is installed on the first run (Linux, Windows, Mac OS)
- Scraping of raw text contents from SERP URLs and given URLs improved
- Scraping of SERP results and contents can be run at once
- CSV output format changed (now tab-separated and quoted)

## [0.10.0]
### Changed
- Support for headless Chrome, adjusted default time between scrapes

## [0.9.0]
### Added
- Result types added (news, shopping, image)
- Image search is supported

## [0.8.0]
### Changed
- Text processing tools removed
- Fewer requirements
