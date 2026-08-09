```{eval-rst}
:orphan:
```

# Alpha 2.0.0 Configuration UI Development Plan

## Status

Implementation complete. This plan extends the existing Configuration page so
that it represents the complete effective `serpscrap.config.Config` surface,
persists validated settings in the database, and remains understandable for
users who only need common search defaults.

The implementation is delivered through the schema-driven configuration
service, the versioned configuration API, grouped progressive-disclosure UI,
database persistence/reset workflow, redaction rules, and deterministic
service/UI contract tests.

## Objective

Provide one reliable configuration workspace with three guarantees:

1. On first load, the UI shows the initial values from `serpscrap.config.Config`.
2. After saving, the validated configuration is persisted in the existing
   database configuration record and is used for future searches.
3. Reset removes the persisted override and restores the initial `Config`
   values, with an explicit confirmation and a visible success state.

Existing search runs are immutable. A configuration change affects new runs
only and must display that scope next to the save status.

## Research Findings

The plan was checked with bounded `mcp-serpscrap` searches for settings-page
information architecture, progressive disclosure, search/application
configuration, and accessible form validation.

The relevant patterns were:

- show the most important and frequently used settings first;
- group related settings by user task, not by internal variable name;
- move low-frequency or risky settings into an Advanced area;
- show the current value, default value, effect, and validation requirements;
- use explicit labels and helper text instead of relying on placeholders;
- validate inline at the right time and summarize errors near the save action;
- make reset-to-defaults reversible through confirmation and a clear source
  indicator (`Initial defaults` versus `Saved override`).

Discovery references:

- [UI Patterns settings pattern](https://ui-patterns.com/patterns/settings)
- [Material settings guidance](https://m1.material.io/patterns/settings.html)
- [Progressive disclosure in SaaS dashboards](https://pixxen.com/blog/progressive-disclosure-saas/)
- [Application settings UX](https://www.toptal.com/designers/ux/settings-ux)
- [Accessible forms guidance](https://accessibility.build/guides/accessible-forms)
- [WAI form validation](https://www.w3.org/WAI/tutorials/forms/validation/)

## Configuration Inventory and Grouping

The API must expose a field schema so the UI does not hard-code validation,
labels, defaults, or visibility rules independently from the service.

### Search behavior

Common and high-frequency settings:

- `search_engines`
- `country_code`
- `search_type`
- `num_pages_for_keyword`
- `num_results_per_page`
- `results_age`
- `language`
- `use_own_ip`
- `searxng_enabled`
- `searxng_url`
- `searxng_fallback`
- `searxng_engines`

The provider selector remains registry-backed. Unsupported or disabled engines
are visible with a reason but cannot be selected. Direct SerpScrap providers
and SearXNG's grouped no-key sources are rendered in one overview; the global
SearXNG toggle remains a separate setting. Search-type options must be derived
from the selected engine intersection; incompatible selections must be
explained before save.

### Ranking and fusion

Advanced result-combination settings:

- `engine_workers`
- `engine_workers_by_engine`
- `engine_weights`
- `other_market_share`
- `ranking.rrf_k`
- `ranking.provider_family_cap`
- `fusion_snapshot_id`

Render simple controls for the common case and JSON-like structured editors or
repeatable rows for per-engine maps. Never require users to edit raw JSON for a
normal provider-weight or worker override.

### Browser and scraping

Operational settings affecting browser execution:

- `scrape_method`
- `sel_browser`
- `chrome_headless`
- `chrome_no_sandbox`
- `window_width`, `window_height`
- `page_load_timeout`, `wait_timeout`
- `user_agent`
- `request_delay_min`, `request_delay_max`
- `request_retry_limit`
- `retryable_engine_categories`
- `request_backoff_base`, `request_backoff_max`
- `block_threshold`

Put this group behind an Advanced disclosure. Explain operational impact and
show safe ranges. Environment-resolved binary paths are read-only unless the
deployment explicitly permits editing them.

### Network and proxy

- `url_connect_timeout`, `url_read_timeout`
- `url_max_redirects`, `url_max_response_bytes`
- `proxy_file`
- `proxy_check_url`, `proxy_info_url`
- `check_proxies`
- `headers`

Use a dedicated proxy section with a clear privacy/security warning. Headers
are not displayed as an unstructured secret-bearing text area by default. If
editing is supported, use a key/value editor, redact sensitive values, and
validate URLs, sizes, and header names. Sensitive values must never be echoed
in success notifications, logs, exports, or browser markup.

### Storage, cache, and history

- `do_caching`
- `cachedir`
- `clean_cache_after`
- `minimize_caching_files`
- `database_name`
- `store_history`
- `scrape_urls`

Show destructive or data-retention consequences next to the control. Changing
database location or disabling history requires a warning and confirmation.
The UI must distinguish “history disabled for future runs” from deleting the
existing archive.

### Diagnostics and execution

- `diagnostic_html`
- `diagnostic_dir`
- `diagnostic_max_bytes_per_file`
- `diagnostic_max_total_bytes`
- `diagnostic_max_artifacts_per_job`
- `url_threads`
- `num_workers`
- `progress`
- `progress_format`
- `log_level`
- `consent_action`

Keep diagnostics collapsed by default. Add concise explanations for storage,
privacy, and performance impact.

### Runtime and read-only information

These values are returned for transparency but are not freely editable in the
first implementation:

- `supported_search_engines`
- `today`
- environment-derived `chrome_binary` and `executable_path` when supplied by
  the deployment environment;
- deployment capability/readiness and provider disable reasons.

Read-only fields must be visually and semantically marked as such, with a
reason instead of a disabled control that provides no explanation.

## Information Architecture

The page uses a two-level structure:

1. **Common defaults**: Search behavior and provider selection visible on load.
2. **Advanced settings**: Ranking/fusion, browser/scraping, network/proxy,
   storage/history, and diagnostics/execution as collapsible groups.

Each group contains:

- a short purpose statement;
- fields in task order, not alphabetic key order;
- a label, current value, unit or range, and one-line helper text;
- a default badge or “changed from initial default” marker;
- inline validation linked with `aria-describedby` and `aria-errormessage`;
- a group-level error summary when a field cannot be saved.

The page header shows `Initial defaults` or `Saved override`, revision,
last-updated time, and “Applies to new searches”. A sticky action bar contains
`Save changes`, `Reset changes`, and `Reset to initial defaults`.

## API and Persistence Contract

Extend the existing additive API without changing the existing endpoint names:

```text
GET  /api/v1/configuration
PUT  /api/v1/configuration
POST /api/v1/configuration/reset
GET  /api/v1/engines
```

`GET /configuration` must return:

```json
{
  "schema_version": 2,
  "source": "defaults|persisted",
  "revision": 0,
  "updated_at": null,
  "configuration": {},
  "initial_defaults": {},
  "groups": [],
  "fields": [],
  "capabilities": {}
}
```

`fields` is the authoritative UI schema. Each field includes `key`, `group`,
`label`, `description`, `type`, `default`, `value`, `editable`, `sensitive`,
`required`, and bounded validation metadata. `groups` includes order, title,
description, and default-expanded state.

The existing database JSON record remains the persistence mechanism, but the
payload must gain a schema version and validated full-config shape. Save is
atomic: validate the complete proposed configuration, then replace the
persisted payload and increment the revision. Partial updates are optional,
but if supported they must be merged and validated server-side.

Reset deletes the persisted record and returns the same schema as GET with
`source=defaults`, `revision=0`, and the initial values from a fresh
`Config().get()` filtered through deployment capability rules.

## Validation and Safety Rules

- The server is the only source of truth for defaults and validation.
- Unknown keys are rejected or explicitly ignored with a response warning;
  they must never silently become executable settings.
- Cross-field rules are validated together: page size/range, engine/search-type
  compatibility, delay min/max, timeout ordering, worker bounds, proxy URL
  validity, and retention/storage constraints.
- Sensitive values are redacted in API responses and never placed in HTML
  data attributes or notifications.
- Save and reset use revision-aware responses so the UI can display the exact
  persisted revision.
- Existing runs and existing history are never changed by saving settings.

## Implementation Slices

### Slice 1: Inventory and schema

- Derive the initial default payload from `Config().get()`.
- Define grouped field metadata, editability, sensitivity, labels, units,
  defaults, and bounded validators.
- Add schema-versioned response examples and migration behavior for the
  current five-key persisted payload.

### Slice 2: Configuration service

- Expand `_default_payload`, `_validate`, `get`, `save`, and `reset` to cover
  the complete supported configuration surface.
- Add cross-field validation and redaction.
- Keep registry capability filtering and search-engine compatibility checks.
- Add atomic persistence and revision behavior tests.

### Slice 3: API contract

- Return `initial_defaults`, `fields`, `groups`, capabilities, and source
  metadata from GET/save/reset.
- Add bounded error payloads with field-level and group-level errors.
- Update MCP configuration schemas only if the public MCP contract is also
  intentionally expanded; do not expose secrets through MCP.

### Slice 4: Configuration UI

- Replace the single compact form with grouped sections and progressive
  disclosure.
- Render fields from the API schema while retaining registry-backed engine
  cards and disabled-provider explanations.
- Add default badges, helper text, units, read-only markers, inline errors,
  dirty tracking, revision/source status, and sticky actions.

### Slice 5: Save/reset workflow

- Load effective configuration and initial defaults on page entry.
- Detect unsaved changes and warn before navigation or reset.
- Validate locally for immediate feedback, then submit the full payload for
  authoritative server validation.
- On save, replace the local form with the server response and show revision.
- On reset, require confirmation, call the reset endpoint, and repopulate all
  groups from the returned initial defaults.

### Slice 6: Accessibility and responsive behavior

- Use semantic `fieldset`/`legend` groupings and explicit labels.
- Keep error summaries keyboard reachable and associate errors with fields.
- Ensure the advanced sections work with keyboard and screen readers.
- Stack groups and action bars on narrow screens without hiding save/reset
  actions.
- Do not rely on color alone for changed, read-only, warning, or error states.

### Slice 7: Tests and documentation

- Add service/API tests for every field group, defaults, persistence,
  migration, reset, cross-field validation, redaction, and revision behavior.
- Add UI contract tests for every group, field schema rendering, dirty state,
  error summary, reset confirmation, and responsive/accessibility markers.
- Update `docs/configuration.rst`, this plan, and `CHANGELOG.md` together.

## Acceptance Criteria

- A fresh database shows all editable `Config` values from initial defaults.
- Every supported configuration key is either editable, explicitly read-only,
  or explicitly deferred with a documented reason.
- Settings are grouped by user task and common settings are understandable
  without reading source-code key names.
- The UI shows source, revision, last update, default values, and new-search
  scope.
- Save persists the complete validated configuration atomically.
- Reset restores a fresh `Config().get()` default payload and removes the DB
  override.
- Invalid and cross-field values produce accessible field/group errors without
  partial persistence.
- Sensitive values are redacted and never leaked into UI markup or logs.
- Existing search-engine selection behavior remains compatible.
- Deterministic API, service, UI contract, accessibility, and documentation
  tests pass.

## Deferred or Restricted

- Editing deployment-only paths and arbitrary HTTP headers remains restricted
  until a safe environment policy exists.
- No per-user configuration profiles or scheduled configuration changes in
  this increment.
- No automatic migration of unknown legacy keys into executable settings.
