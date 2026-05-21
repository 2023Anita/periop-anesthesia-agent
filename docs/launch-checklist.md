# GitHub Launch Checklist

Use this checklist before announcing or republishing the project.

## Repository Surface

- [ ] README renders correctly on GitHub.
- [ ] Language navigation links work: English, Chinese, Japanese, Korean, French, German.
- [ ] `docs/assets/demo.gif` loads in the README.
- [ ] Generated explainer images load from `docs/assets/generated/`.
- [ ] License is shown as MIT.
- [ ] Repository description is concise and developer-facing.
- [ ] Topics include `clinical-ai`, `healthcare-ai`, `openai-agents-sdk`, `human-in-the-loop`, `fastapi`, `react`, `sqlite`.

## Local Validation

- [ ] Backend tests pass:

  ```bash
  cd "backend"
  ".venv/bin/python" -m pytest
  ```

- [ ] Frontend build passes:

  ```bash
  cd "frontend"
  npm run build
  ```

- [ ] The app starts locally.
- [ ] `Load sample case` creates a report.
- [ ] Markdown export works.
- [ ] UI language selection persists after refresh.

## Safety and Privacy

- [ ] No `.env` file is tracked.
- [ ] No API key or private key is present in tracked files.
- [ ] No real patient data appears in examples, tests, screenshots, GIFs, or generated images.
- [ ] README states that this is not a production medical device.
- [ ] App copy avoids surgery clearance, dosing, emergency instructions, or patient-specific advice.

## Profile and Distribution

- [ ] Pin the repository on the GitHub profile.
- [ ] Keep the public positioning aligned with clinical AI developer tooling.
- [ ] Share with a short demo-first description and the GitHub URL.
