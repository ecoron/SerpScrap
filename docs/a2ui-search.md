```{eval-rst}
:orphan:
```

# Search Provider Consent and Live Browser-Flow Plan

## Status

Implementation slices 1-4 are complete, including the controlled browser
diagnostic follow-up. This document records the plan and
verification gates for enabling Google and Ecosia after the 2026-08-07 live
investigation. The consent controls work in a real browser, while Google and
Ecosia still apply separate headless-browser access controls after consent.

This is an internal engineering plan. It is intentionally excluded from the
published Read the Docs navigation together with the other `a2ui-*.md` plans.

## Evidence and Current Diagnosis

The investigation used the project Pipenv environment, Selenium 4.46, Chrome
151, and a locally cached ChromeDriver. It verified the following:

- Google exposes a visible German `Alle ablehnen` button. Clicking it removes
  the visible dialog and allows a normal search in the in-app browser.
- Ecosia exposes a visible `Nicht essenzielle Cookies ablehnen` button in its
  Didomi dialog. Clicking it removes the visible overlay and allows a normal
  search in the in-app browser.
- The local Selenium run emits `consent_cleared` for both providers, but the
  subsequent homepage classification returns `consent_required`.
- The current implementation reclassifies the page with the complete
  `page_source` after consent. Hidden dialog nodes remain in that source even
  though no consent dialog is displayed.
- When the consent reclassification is bypassed experimentally, Google reaches
  `/sorry/index` and Ecosia returns a `Nur einen Moment…` challenge in the
  headless Selenium session. These are access-control outcomes, not consent
  failures.
- After the implementation fix, the complete local Pipenv flow emits
  `consent_cleared`, reaches `homepage_ready`, and reports both providers as
  typed `blocked` outcomes during the low-volume live smoke.

The primary defect was therefore in the post-consent state boundary. The
secondary live-smoke result is provider protection and remains typed rather
than bypassed.

The browser identity follow-up now resolves the effective User-Agent from the
installed Chrome major through Selenium Manager's cross-platform browser
detection. A generic executable version command remains as a fallback. A
stale explicit Chrome major is normalized to the detected major. An optional
disposable profile directory is available for controlled repeatability tests;
it is never enabled by default.

## Objective

Make the homepage flow distinguish a verified, cleared consent overlay from a
consent page that is still blocking search, then preserve honest provider
outcomes when Google or Ecosia applies an access-control challenge.

## Solution Decision

| Option | Decision | Rationale |
| --- | --- | --- |
| Reclassify consent after the click from rendered visible state | **Required** | Matches the successful verification already used by `_apply_consent()` and ignores hidden stale DOM nodes. |
| Delete consent nodes with JavaScript | Rejected | Hides provider state without proving that the provider accepted the choice. |
| Inject guessed Google/Ecosia cookies | Rejected | Values and semantics are region-, version-, and session-dependent. |
| Reuse an isolated opt-in profile | Conditional fallback | Useful for repeatable smoke tests, but it must never contain personal data or become the default success path. |
| Retry or evade `/sorry` and Ecosia challenges | Rejected | These are access-control outcomes; the browser flow must report them and stop. |

## Implementation Slices

1. **Fix the post-consent classification boundary**

   - Add a dedicated helper for post-consent homepage verification.
   - Classify provider block/rate-limit states from the rendered visible text.
   - Verify that every configured homepage consent selector has no visible
     usable element.
   - Do not pass raw `page_source` into the consent-cleared decision.
   - Keep the existing `_apply_consent()` explicit waits and
     `consent_cleared` progress event.

2. **Strengthen provider state precedence**

   - Preserve `blocked` and `rate_limited` precedence over generic consent text.
   - Avoid treating footer links, hidden markup, or stale dialog nodes as an
     active consent state.
   - Keep `consent_required` when no visible, semantic rejection control can
     be found or the overlay cannot be verified as gone.

3. **Run the real homepage flow after consent**

   - Locate and use the search field only after the new post-consent check.
   - Submit one low-volume query per provider.
   - Classify Google `/sorry` as `blocked` and Ecosia challenge pages as
     `blocked` or a more specific typed access-control state if the existing
     provider contract supports it.
   - Do not retry these states under the transient retry policy.

4. **Add opt-in live-smoke configuration**

   - Keep live checks outside the default test gate.
   - Use a disposable, provider-scoped Chrome profile when persistence is
     needed for repeated smoke runs.
   - Never store profile directories, cookies, local storage, query text, or
     raw provider pages in the repository or CI artifacts.
   - Record only date, country/language, selector decision, terminal state,
     sanitized URL shape, and correlation ID.
   - Keep the effective User-Agent consistent with the installed Chrome
     major; use `--visible` and an isolated profile only for controlled
     headless/headful comparison runs.
   - Use the bounded `interaction_settle_delay` for provider autocomplete and
     form validation; do not alter `navigator.webdriver` or other WebDriver
     automation signals.

5. **Update operational documentation**

   - Document Chrome/ChromeDriver setup for local Pipenv runs.
   - Document that consent success and SERP access success are separate gates.
   - Explain that `blocked` after `consent_cleared` is an honest provider
     outcome, not evidence that consent handling failed.

The live smoke also confirmed that the current Ecosia homepage uses a
`textarea[name='q']` search control and that Google may require keyboard
submission when its autocomplete layer intercepts the submit button. Both
provider-specific contract updates are now implemented and fixture/regression
covered.

## Test Plan

### Deterministic tests

- Add a regression test where the consent dialog remains in `page_source` but
  is hidden after the click; the flow must continue past homepage consent.
- Add tests for Google and Ecosia visible-overlay removal using the existing
  fixtures and mocked WebDriver.
- Add tests proving that visible provider challenges after consent become
  `blocked` and are not retried as consent failures.
- Keep tests for unmatched rejection labels, timeout, hidden nodes, and
  partial multi-provider success.

### Opt-in live smoke

- Run one Google and one Ecosia search in a fresh, headless Selenium session.
- Record consent progress states and the final typed provider outcome.
- Repeat only with explicit approval when investigating selector drift or a
  new country/language combination.
- Treat successful consent followed by `/sorry` or a challenge as a valid
  diagnostic result, not as a failed consent implementation.

## Acceptance Gates

- After a visible consent action and verified overlay disappearance, the
  homepage flow does not return `consent_required` solely because hidden DOM
  nodes remain in `page_source`.
- Google and Ecosia consent fixtures and mocked-browser tests pass.
- The full offline test suite, Ruff, package build, and Sphinx warning-as-error
  build pass.
- Live smoke output distinguishes `consent_cleared` from `blocked`,
  `rate_limited`, `selector_drift`, and `consent_required`.
- No provider JavaScript shortcut, guessed cookie, CAPTCHA bypass, or access
  control evasion is introduced.

## Next TODO

- Run the same low-volume Google/Ecosia query once headless and once with
  `--visible`, using the same disposable provider-scoped profile, User-Agent,
  network, language, and interaction settle delay. Compare consent events,
  browser startup, terminal provider state, and sanitized navigation outcome.
- Keep the comparison opt-in and diagnostic; do not suppress WebDriver signals
  or retry provider access-control challenges.
- Google and Ecosia are enabled by default only after dated live evidence shows
  both consent completion and an acceptable SERP access outcome for the
  supported market.

## Deferred Scope

Provider-specific API integrations, Google Custom Search, third-party SERP
APIs, Consent-O-Matic, and automatic cookie/state injection remain separate
experiments. They are not part of the default Selenium success path.
