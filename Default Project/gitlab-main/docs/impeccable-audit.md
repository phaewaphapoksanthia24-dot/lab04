# Impeccable UI audit — Lab 04

## Tool / command

Impeccable was installed into this project with the OpenCode provider:

```bash
npx impeccable install -y --providers=opencode --scope=project
npx impeccable detect --json http://127.0.0.1:5000/lab4
```

The scan targets the real rendered Flask page while the ngspice-enabled server is
running, so it sees the same DOM/CSS that the browser acceptance checks use.

## Before (first findings, reported before editing)

Saved raw output: `docs/impeccable-before.json`

| Rule | Severity | Element | Finding |
|---|---|---|---|
| `side-tab` | warning | `div.notice.provenance` | A 4 px left accent bar was combined with rounded corners. |
| `first-viewport-column-overflow` | warning | `div.lab4-grid` | On a wide viewport the input column ran far past the fold while the short circuit column ended early, leaving dead space. |

Screenshot: `docs/images/lab04-ui-before.png`

## Change made

Only `static/lab4.css` was changed:

- `.notice` now uses a full 1 px border and a softer radius instead of a side tab.
- On viewports `>= 1241px`, the input panel is capped to the first viewport with
  internal scrolling and the reference-circuit panel becomes `position: sticky`.
- No Python, JavaScript, route, netlist, parser, or calculation code was touched.

## After

Saved raw output: `docs/impeccable-after.json`

```json
[]
```

`npx impeccable detect --json http://127.0.0.1:5000/lab4` exited `0` with no findings.

Screenshot: `docs/images/lab04-ui-after.png`

## Non-regression check

The same B2 DC run was repeated in the browser after the CSS edit and still reports
`ngspice 41`, `success · DC`, `VB 1.9491 V`, `VE 1.2895 V`, `VC 9.1894 V`,
`VCE 7.9000 V`, `IC 1.2775 mA`, `IB 11.913 µA`. The full suite also remains
`Ran 68 tests / OK`. UI polish therefore did not change calculation output.

## Limitation

The in-app browser exposed a narrow 800×609 viewport but no phone viewport
emulation, so the B8 evidence is a real narrow-viewport screenshot rather than a
phone-device emulation. This is recorded honestly in `docs/validation.md`.
