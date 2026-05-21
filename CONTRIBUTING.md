# Contributing

Thanks for helping improve `periop-anesthesia-agent`.

This repository is a local clinical AI developer template. Please keep changes small, reviewable, and conservative about medical claims.

## Good First Contributions

- Improve documentation for setup, safety boundaries, or demo flow.
- Add synthetic sample cases with no real patient data.
- Add tests for extraction, report export, and safety guardrails.
- Improve frontend empty, loading, and error states.
- Refine clinician-facing copy without making autonomous medical claims.

## Boundaries

Do not add features that:

- Decide whether a patient can have surgery.
- Provide anesthesia or medication doses.
- Give emergency rescue instructions.
- Produce patient-facing individualized medical advice.
- Use real patient data in examples, screenshots, tests, or fixtures.

## Local Checks

Backend:

```bash
cd "backend"
".venv/bin/python" -m pytest
```

Frontend:

```bash
cd "frontend"
npm run build
```

## Pull Request Style

- Keep PRs focused on one behavior or documentation improvement.
- Include tests when changing backend logic.
- Include screenshots or GIFs when changing UI behavior.
- State explicitly when a change affects safety boundaries.
