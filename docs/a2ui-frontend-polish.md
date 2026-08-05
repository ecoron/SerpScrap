```{eval-rst}
:orphan:
```

# Alpha 2.0.0 Frontend Polish Plan

## Objective

Make the existing Flask/Jinja, CSS, and native ES-module frontend reliable,
responsive, accessible, and visually consistent without adding a framework or
chart dependency.

## Research Basis

The plan was checked with bounded `mcp-serpscrap` searches for responsive
dashboard CSS, JavaScript request lifecycle patterns, accessible charts/tables,
and dashboard loading/error states. The useful patterns were:

- fluid `minmax()`/intrinsic grids with a small number of intentional layout
  breakpoints;
- semantic HTML tables as the exact alternative to visual charts;
- `AbortController` for cancelling superseded fetches and preventing stale
  results from winning a race;
- explicit loading, empty, timeout, partial, and error states with a recovery
  action;
- focus-visible treatment, reduced-motion behavior, and status indicators
  that do not rely on color alone.

Discovery references:

- [MDN responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)
- [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort)
- [Accessible charts guidance](https://www.adacompliancepros.com/blog/accessible-charts)
- [Accessible tables](https://www.thewcag.com/examples/tables)
- [Carbon empty-state pattern](https://v10.carbondesignsystem.com/patterns/empty-states-pattern/)

## Implementation Plan

1. **Token and base layer**: add consistent spacing, typography, surface,
   focus, status, and motion tokens; make global focus and reduced motion
   behavior explicit.
2. **Responsive layout**: make the shell, toolbars, metric cards, filter
   groups, tables, compare panels, and result cards usable from 320px upward.
3. **History presentation**: improve hierarchy, scope metadata, table density,
   state cards, provider status badges, and compare readability.
4. **JavaScript lifecycle**: add request timeout/abort support, preserve the
   latest-request-wins invariant, avoid duplicate listeners, and render empty
   charts safely.
5. **Accessible data display**: add chart descriptions, exact table captions,
   non-color status text, focus order, and polite live-region updates.
6. **Verification**: add deterministic static UI-contract tests, run the full
   non-browser suite and Ruff, build Sphinx, and record any unavailable visual
   smoke checks.

## Acceptance Criteria

- No horizontal page overflow at 320px; wide tables scroll inside their panel.
- Focus-visible controls remain obvious against light and dark surfaces.
- Reduced-motion users receive no shimmer, transform, or smooth-scroll motion.
- A superseded History request cannot overwrite the latest scope.
- API timeout, abort, empty, partial, and error states are distinguishable.
- Every chart has a labelled semantic table with exact values.
- Provider states use text labels in addition to color.
- All deterministic tests, Ruff, and Sphinx checks pass.
