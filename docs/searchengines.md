# Search Engines for Refactoring Phase 7

Last researched: 2026-08-02. Market snapshot: Europe, all devices, July 2026.

This document is the operational registry input for the Phase 7 browser-flow and plugin set. It is not a promise that undocumented query parameters or CSS selectors are stable. Every engine is independently disableable and is enabled only while its homepage flow, URL/country mapping, pagination, response classification, and parsing behavior remain covered by sanitized offline fixtures.

## Phase 7 plugin status matrix

| Engine | Readiness | Plugin version | Search types | Pagination | Provider family | Disable reason |
|---|---|---:|---|---|---|---|
| Google | enabled | 1 | normal, image, news, shopping, videos | offset | google | — |
| Bing | enabled | 1 | normal | offset | bing | — |
| Yandex | enabled | 1 | normal | page | yandex | — |
| Yahoo | enabled | 1 | normal | offset | bing | — |
| DuckDuckGo | enabled | 1 | normal | offset | bing | — |
| Ecosia | enabled | 1 | normal | page | mixed | — |
| Qwant | enabled | 1 | normal | provider-defined | bing | — |
| Startpage | enabled | 1 | normal | provider-defined | google | — |
| Brave | enabled | 1 | normal | offset | brave | — |
| Swisscows | enabled | 1 | normal | page | bing | — |
| Mojeek | enabled | 1 | normal | offset | mojeek | — |

The matrix is also exposed through `default_registry().metadata()` for diagnostics. A provider can be switched to `experimental` or `disabled` without removing its importable plugin or fixtures.

## Selection Method

[StatCounter Global Stats](https://gs.statcounter.com/search-engine-market-share/all/europe/) is the primary comparable source for European search-engine share across all devices. Its July 2026 view reports only six engines separately. Together they account for 99.37% after rounding; every other engine is combined into `Other` and therefore has no defensible individual StatCounter percentage.

The initial cohort consequently uses two evidence levels:

1. **Measured European leaders:** Google, Bing, Yandex, Yahoo, DuckDuckGo, and Ecosia, ordered by StatCounter's July 2026 share.
2. **Supplementary European alternatives:** Qwant, Startpage, Brave Search, Swisscows, and Mojeek. These are not claimed to be positions 7-11 by measured European market share. They were selected because they are established general web-search options for European users, appear in browser/search choice material, cover European privacy-oriented services and independent indexes, and expose a usable public web SERP. Google's [Android choice-screen list](https://www.android.com/choicescreen-winners/) supplies country-specific evidence for Brave, Ecosia, Mojeek, and Qwant alongside the measured leaders. Mojeek's [search-choice documentation](https://www.mojeek.com/preferences?tab=search) lists Brave, Ecosia, Qwant, Startpage, Swisscows, Yandex, Bing, DuckDuckGo, and Google and publishes their search URL templates.

This produces ten alternatives plus Google:

`bing`, `yandex`, `yahoo`, `duckduckgo`, `ecosia`, `qwant`, `startpage`, `brave`, `swisscows`, `mojeek`, and `google`.

## European Market-Share Snapshot

| Engine | July 2026 Europe share | Weight status | Evidence |
|---|---:|---|---|
| Google | 89.07% | measured | StatCounter |
| Bing | 5.00% | measured | StatCounter |
| Yandex | 2.50% | measured | StatCounter |
| Yahoo | 1.47% | measured | StatCounter |
| DuckDuckGo | 0.85% | measured | StatCounter |
| Ecosia | 0.48% | measured | StatCounter |
| Qwant | not individually reported | `Other` fallback or operator override | supplementary cohort |
| Startpage | not individually reported | `Other` fallback or operator override | supplementary cohort |
| Brave Search | not individually reported | `Other` fallback or operator override | supplementary cohort |
| Swisscows | not individually reported | `Other` fallback or operator override | supplementary cohort |
| Mojeek | not individually reported | `Other` fallback or operator override | supplementary cohort |

The six displayed values sum to 99.37%; the 0.63 percentage-point remainder is the rounded aggregate for all other engines, not a measurement for these five supplementary engines. Phase 4 must store `{source, region, device_scope, period, retrieved_at}` with the values. For reproducible ranking, a run freezes a weight snapshot. The initial fallback may divide the `Other` remainder equally among the configured unreported engines (0.126 percentage points each only when all five are active), but this is a ranking prior, not an observed market share. Operators can override it, and report metadata must expose the fallback.

Raw market-share weighting would make a single Google result dominate broad alternative-engine agreement. Phase 4 therefore has to test and document whether production uses normalized raw share, a bounded/log transform, or provider-family caps. Whatever is chosen must still be deterministic, versioned, explainable, and covered by ranking fixtures; it must not be tuned invisibly.

## Search Entry Points and SERP Reconnaissance

`{query}` means percent-encoded UTF-8 text. Parameter names below are discovery baselines, not permission to automate a provider and not a substitute for fixture verification. The common target for Phase 4 is an organic web result with title, target URL, visible URL/domain, snippet, page, and rank. Ads, AI answers, knowledge panels, shopping blocks, and other modules must not be mistaken for organic results.

| Engine | Baseline web-search URL | Pagination/country reconnaissance | Result-page notes for plugin discovery |
|---|---|---|---|
| Google | `https://www.google.com/search?q={query}` | `start` is the result offset; `gl` and `hl` influence country/language | Dynamic HTML with several organic layouts; retain the Phase 3 ordered selector fallbacks, redirect decoding, and explicit CAPTCHA/consent/rate classification. |
| Bing | `https://www.bing.com/search?q={query}` | `first` is a one-based offset; investigate `cc` and `setlang` per ISO country | Organic cards are commonly list items in the web-results area; separate ads, answer modules, and redirect/tracking links before assigning rank. |
| Yandex | `https://yandex.com/search/?text={query}` | `p` is normally zero-based; `lr` uses Yandex region IDs and needs an explicit ISO-to-provider map | Dynamic/localized SERP; identify organic `serp-item` cards, redirect URLs, empty state, CAPTCHA, and consent from fixtures. |
| Yahoo | `https://search.yahoo.com/search?p={query}` | `b` is commonly a one-based offset; country may also depend on host/locale | Organic `algo` cards coexist with sponsored and answer modules; test Yahoo redirect decoding and Bing-syndicated overlap. |
| DuckDuckGo | `https://html.duckduckgo.com/html/?q={query}` | Region commonly uses `kl`; continuation can be form/token based and must be captured rather than guessed | Prefer the documented no-JavaScript HTML surface for a fixture-friendly plugin if current provider policy permits it; organic `result` cards contain redirect links that require safe decoding. |
| Ecosia | `https://www.ecosia.org/search?q={query}` | Page/cursor and region parameters require current fixture discovery | Hydrated result page with organic cards plus ads/features. Results may come from Microsoft Bing, Google, or European Search Perspective depending on region/device, so record provider-family uncertainty. |
| Qwant | `https://www.qwant.com/?q={query}&t=web` | Country/search region and pagination require current fixture discovery | JavaScript-backed categorized SERP; target only Web organic cards and classify unavailable/consent states separately. Qwant documents `t=all` for browser integration and Web as the default search category. |
| Startpage | `https://www.startpage.com/sp/search?q={query}` | Pagination and region can depend on form state/preferences; do not invent a numeric offset | Server/form-driven privacy SERP; identify organic web cards, sponsored blocks, anonymous-view links, and bot responses in fixtures. |
| Brave Search | `https://search.brave.com/search?q={query}` | Validate `source=web`, country, language, and continuation behavior from fixtures | Hydrated HTML over Brave's independent index; exclude AI answers, discussions, videos, and ads from the initial organic parser. Brave also offers a supported Search API, which should be evaluated before relying on browser capture. |
| Swisscows | `https://swisscows.com/en/web?query={query}` | Language appears in the path; region/pagination mapping requires fixture discovery | Dynamic web cards backed by an upstream index; distinguish organic results, previews, and block/empty states. |
| Mojeek | `https://www.mojeek.com/search?q={query}` | `s` is a candidate result offset; location/language preferences require fixture discovery | Mostly server-rendered organic result list over Mojeek's own index; verify standard cards, infobox/news additions, pagination, and no-result state. |

## Phase 7 Browser Entry Points and Selector Baseline

The following matrix is the starting point for the homepage-driven Selenium flow. It records selector candidates to verify against sanitized fixtures and an opt-in live observation; it is intentionally not a claim that these selectors are stable provider APIs. `Enter` is the preferred submit fallback when no stable submit control is available. A result-ready selector must be combined with URL/state-change detection and the provider's empty/consent/block classifiers.

| Engine | Homepage | Search input candidates | Submit candidates | SERP-ready / organic-card candidates | Status |
|---|---|---|---|---|---|
| Google | `https://www.google.com/` | `textarea[name="q"]`, `input[name="q"]` | `button[name="btnK"]`, `input[name="btnK"]`, Enter | `div#search`, `div.MjjYud`, `a h3` | candidate; retain ordered fallbacks |
| Bing | `https://www.bing.com/` | `textarea#sb_form_q`, `input[name="q"]` | `form#sb_form button[type="submit"]`, Enter | `ol#b_results`, `li.b_algo`, `li.b_algo h2 a` | candidate; verify hydrated variants |
| Yandex | `https://yandex.com/` | `input[name="text"]`, `input[type="search"]` | `form[action*="/search"] button[type="submit"]`, Enter | `[data-serp-item]`, `.serp-item`, `h2 a` within the organic card | candidate; region IDs require mapping |
| Yahoo | `https://search.yahoo.com/` | `input[name="p"]`, `input[type="search"]` | `form[action*="/search"] button[type="submit"]`, Enter | `div#web`, `div.algo`, `div.algo h3 a` | candidate; consent may precede form |
| DuckDuckGo | `https://html.duckduckgo.com/html/` | `input[name="q"]` | `form[action="/html/"] input[type="submit"]`, Enter | `div.results`, `.result`, `.result__a` | candidate; HTML surface preferred |
| Ecosia | `https://www.ecosia.org/` | `input[name="q"]`, `input[type="search"]` | `form[action*="/search"] button[type="submit"]`, Enter | `main`, `article`, provider-verified organic result link | candidate; hydration/provider-family review required |
| Qwant | `https://www.qwant.com/` | `input[name="q"]`, `input[type="search"]` | `button[type="submit"]`, Enter | Web-result container and card `data-testid`/role attributes from fixture | candidate; generated classes prohibited |
| Startpage | `https://www.startpage.com/` | `input[name="query"]`, `input[type="search"]` | `form[action*="/sp/search"] button[type="submit"]`, Enter | `a.result-title`, `h2`, `p.description` | fixture-verified from 2026-08-02 artifact; generated suffixes excluded |
| Brave Search | `https://search.brave.com/` | `textarea#searchbox`, `textarea[name="q"]`, `input[name="q"]`, `input[type="search"]` | `form button[type="submit"]`, Enter | `.snippet`, `div.title`, `.generic-snippet .content` | fixture-verified from 2026-08-02 artifact; exclude AI/discussions |
| Swisscows | `https://swisscows.com/en/web` | `input[name="query"]`, `input[type="search"]` | `form button[type="submit"]`, Enter | `article.item.web-page`, `h1.title` | wait for organic cards; `.web-results` alone is not readiness |
| Mojeek | `https://www.mojeek.com/` | `input[name="q"]`, `input[placeholder*="Search"]` | `form button[type="submit"]`, Enter | `ul.results-standard > li[class^="r"]`, `h2.title`, `p.s` | fixture-verified from 2026-08-02 artifact; verify infobox/news exclusions |

### Selector Verification Rules

- Each candidate is promoted to `fixture-verified` only after a sanitized homepage/SERP fixture and a selector-specific test pass. `live-smoke-verified` additionally requires a dated, low-volume opt-in observation.
- The adapter must wait for the homepage input to be visible and enabled, clear it, enter the keyword, and verify the submitted value before submitting. The submit wait must observe a URL change, a DOM state change, or a provider-specific result/empty state.
- A broad container selector is only a readiness signal. Organic extraction must use a narrower card selector and explicitly exclude ads, sponsored cards, AI answers, knowledge panels, navigation, related searches, and duplicate sitelinks.
- If a candidate fails, try the next documented candidate only within the same page state. Do not broaden to arbitrary `a`, `li`, or generated class selectors.
- Record `observed_at`, country/language, viewport, browser identity, provider/plugin version, and the fixture filename in adapter metadata. Refresh the observation at least quarterly and after a selector failure.
- A missing input, missing submit control, missing result-ready state, or zero cards on a known non-empty fixture is a typed `selector_drift`/`malformed` failure. It must not be converted into an empty successful result.

## Phase 7.2 Artifact Findings and Current Status

The latest diagnostic run is recorded in `docs/phase7.log`; its manifest and
rendered HTML are stored below `logs/phase7/<run_id>/` when diagnostic capture
is enabled. The current findings are:

Google consent dialogs are detected with `div[role="dialog"][aria-modal="true"]`.
The default `consent_action="necessary"` selects the privacy-preserving
`Alle ablehnen` action. `reject` is an explicit alias; `disabled` leaves the
dialog untouched and reports `consent_required`.

Known TODO for a later phase: Google and Ecosia consent controls are loaded or
exposed dynamically in the current browser environment. If the configured
action cannot be confirmed and the dialog remains present, the safe terminal
state is `consent_required`; the flow does not continue with an ambiguous
search.

| Engine | Current status | Next adapter action |
|---|---|---|
| Brave | blocked challenge/CAPTCHA before input | classify the homepage as `blocked`; do not broaden input selectors |
| Ecosia | consent overlay before input | classify the homepage as `consent_required`; verify overlay markers |
| Bing | SERP cards present but raw markup caused false rate-limit classification | classify visible state and parse `#b_results`/`li.b_algo` before incidental script text |
| Yandex | `.serp-item` cards present but raw markup caused false rate-limit classification | classify visible state and parse `.serp-item` before incidental script text |
| Qwant | homepage retained after submit with challenge/consent signals | record post-submit URL/state and classify explicitly |
| Startpage | `/sp/search` reached with challenge/consent response | distinguish route from blocked response |
| Swisscows | explicit `too many requests` mixed with privacy text | give rate-limit evidence deterministic precedence |
| DuckDuckGo, Yahoo, Mojeek | SERP reached in the latest run | retain fixture coverage and monitor provider drift |

Do not promote a selector based only on a raw artifact. Remove queries,
tracking parameters, cookies, tokens, and unrelated content before promoting a
page to `tests/fixtures/searchengines/<engine>/`.

## Phase 7.3 Runtime Outcome Semantics

The browser flow reports one typed terminal outcome per engine/page. A
recognized SERP with organic cards is parsed normally. A page with an explicit
provider empty marker is reported as `empty`; a page that reaches a result
route but has neither recognized cards nor an empty marker is `malformed`.
When the post-submit URL/state cannot be recognized, the flow reports
`navigation_state` instead of hiding the observation behind a generic timeout.

The configured retry policy defaults to transient `timeout`,
`navigation_state`, and `network` failures. Provider controls (`blocked`,
`consent_required`, `rate_limited`) and parser/selector outcomes are not
retried by default. Override this only deliberately through
`retryable_engine_categories`, for example:

.. code-block:: python

   config = {
       "search_engines": ["bing", "mojeek"],
       "retryable_engine_categories": ["timeout", "navigation_state"],
       "progress": True,
   }

The final report metadata contains `terminal_summaries` and `outcome_counts`.
Each summary includes engine, page, category/state, result count, final URL
path, and correlation ID. This preserves healthy results when another engine
returns `empty`, `malformed`, `blocked`, `consent_required`, or
`navigation_state`.

### Phase 7.3 Artifact Corrections

The run `1761a92d6e7d459e` verified the following current structures:

| Engine | Artifact finding | Implemented contract |
|---|---|---|
| Brave | Normal localized homepage exposes `textarea#searchbox`; current SERP cards use `.snippet`, `div.title`, and `.generic-snippet .content` | ordered input selector and artifact-backed SERP parser are documented; normal selector drift remains distinguishable from `blocked` |
| Qwant | Result page reports `vorübergehend nicht verfügbar` and `(HTTP 403)` | provider-specific visible markers classify the response as `blocked` |
| Startpage | Current result links are `a.result-title` with an `h2` title; the `.w-gl` wrapper is not consistently present | readiness and parsing use `a.result-title`; dynamic CSS suffixes are excluded |
| Swisscows | Current run exposes `.web-results` but no organic `article.item.web-page` cards | readiness now waits for organic cards; an empty wrapper is not accepted as a SERP |
| Mojeek | Organic cards are `ul.results-standard > li.r1...`, with `h2.title` and `p.s` | class-prefix card selector and provider-specific title/snippet selectors |

The corresponding sanitized fixtures are stored under
`tests/fixtures/searchengines/<engine>/`. Raw rendered pages remain local under
`logs/phase7/` and are not promoted to source control.

Published template evidence is strongest for Bing, Brave, DuckDuckGo, Ecosia, Google, Qwant, Startpage, Swisscows, and Yandex in [Mojeek's search settings](https://www.mojeek.com/preferences?tab=search). Qwant also publishes `https://www.qwant.com/?q={searchTerms}&t=all` in its [Chrome deployment guidance](https://help.qwant.com/wp-content/uploads/sites/2/2023/02/PREP-Chrome-200223-1449-232.pdf) and describes Web, News, Images, Videos, Shopping, Maps, Social, and Music categories in [Qwant search help](https://help.qwant.com/en/docs/qwant-search/searching/how-to-search-with-qwant/). Yahoo's help confirms Yahoo Search browser integration and the public search host in its [mobile setup guidance](https://help.yahoo.com/kb/yahoo-search-mobile-device-sln15524.html).

## Index and Provider-Family Notes

Engine occurrence is useful evidence, but multiple branded SERPs can draw from the same upstream provider. Counting them as fully independent votes may overstate consensus.

- Brave states that it serves an [independent search index](https://brave.com/search/).
- Ecosia states that current results can come from [Microsoft Bing, Google, and European Search Perspective](https://support.ecosia.org/article/579-search-results-providers), depending on region and device.
- Mojeek describes itself as `Crawler/Index/Rank` in its [search-choice comparison](https://blog.mojeek.com/2023/06/new-pathways-with-expanded-search-choices.html).
- DuckDuckGo, Yahoo, Qwant, Startpage, and Swisscows require a dated provider-family review during implementation; provider relationships can change and should not be hard-coded from memory.

The ranking input should therefore retain both the user-facing engine ID and an optional provider-family label with provenance and review date. The primary score can cap duplicate contributions per family or expose `independent_provider_count` alongside ordinary `engine_match_count`; Phase 4 tests must settle the exact behavior before release.

## Country Codes

The public `country_code` is uppercase ISO 3166-1 alpha-2, for example `DE`, `FR`, or `GB`. It always means the requested result market. It is not inferred from proxy IP after the request and is not silently replaced by browser language.

Each plugin owns a tested mapping from the public code to provider parameters, host, path locale, language header, cookie/form state, or provider-specific region ID. If an engine cannot honor the requested country, the plugin returns an `unsupported_country` failure or declares a documented neutral-search capability; it must not emit a misleading country code. The captured page and every parsed row retain both `search_engine` and `country_code`.

## Pre-Implementation Checklist per Engine

- Review current terms, robots guidance where relevant, official API availability, request limits, and access-control behavior; store the review date.
- Verify the query URL, correct percent encoding, result count, pagination/cursor behavior, and ISO country mapping using one low-volume opt-in capture.
- Sanitize and save normal, localized, empty, blocked/consent, and selector-fallback HTML fixtures.
- Identify organic card boundaries and exclude ads, AI summaries, answer modules, navigation, and duplicate sitelinks.
- Decode only recognized provider redirect formats, accept only HTTP(S) targets, and test malicious/ambiguous redirect parameters.
- Define result-ready, empty, consent, CAPTCHA/block, rate-limit, malformed, and timeout states with a clear precedence.
- Pass the shared plugin conformance suite and installed-wheel discovery test before the engine is enabled by default.

## Research Limitations and Refresh Policy

Market-share services use different measurement panels and taxonomies, and StatCounter's displayed percentages are rounded. Its `Other` bucket prevents a defensible numerical ranking among the five supplementary engines. Search pages, parameters, upstream providers, terms, and access controls can change without notice. Consequently:

- refresh this document and the machine-readable weight snapshot for each scheduled release or at least quarterly;
- retain old snapshots so cached/historical runs remain reproducible;
- record direct observation dates in fixture metadata;
- never promote reconnaissance selectors or parameters to supported behavior without offline tests; and
- disable a drifting plugin independently rather than weakening parsing or bypassing provider controls.
