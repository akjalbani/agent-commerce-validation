# Agent Commerce Validation Laboratory

Open-source synthetic research prototype supporting the paper:

> Jalbani, A.; Weerawarna, R.; Jain, A. **A Rail-Neutral Payment Architecture for Autonomous AI Agents: Authority, Settlement, Liquidity, and Risk Controls.** Submitted to *Future Internet* (MDPI), 2026.

**Live demonstration:** https://akjalbani.github.io/agent-commerce-validation/

**Scope:** demonstration and validation of selected rail-neutral payment *policy* rules. No real payments, real credentials, blockchains, bank integrations, cryptographic proofs, fraud detection, or settlement occur. Simulated card, bank, stablecoin and payment-channel rails are labels only.

## What is in this repository

| Path | Purpose |
|---|---|
| `legacy_validation_18_tests.py` | Original 18-test policy-control suite reported in the paper (standard library only). |
| `simulator/` | Python reference model (mandate checks, budget reservation, transaction states). |
| `tests/` | Core-model unit tests, the 16-scenario Python reference suite, and Flask API tests. |
| `app.py` | Local Flask application exposing the Python model through `/api/`. |
| `docs/` | Static browser simulator published through GitHub Pages (JavaScript only). |
| `validation_report.json` | Example exported results. |
| `.github/workflows/tests.yml` | Continuous integration: runs all Python test suites on every push. |

## Test suites: keep the counts separate

| Suite | Implementation | Cases | Command |
|---|---|---|---|
| Original policy-control suite (reported in the paper) | Python | 18 | `python legacy_validation_18_tests.py` |
| Core-model and 16-scenario reference suite | Python | see test output | `python -m unittest discover -s tests -v` |
| Browser scenario suite | JavaScript (GitHub Pages) | 16 | Run in the web interface |

The Python and browser suites are **independent implementations** of comparable logic. Agreement between them is not evidence that identical code was executed. Do not add the counts together, and do not report browser results as executions of the Python code.

## Quick start: run the tests locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS:        source .venv/bin/activate
pip install -r requirements.txt
python legacy_validation_18_tests.py
python -m unittest discover -s tests -v
```

## Run the Flask application locally

```bash
python app.py
```

Visit `http://127.0.0.1:5000`. API endpoints:

- `GET /api/health`: indicates simulation mode.
- `GET /api/scenarios`: returns the 11 single-request scenarios.
- `GET /api/suite`: executes the 16-case Python reference suite.
- `POST /api/simulate`: runs an independent scenario, e.g. `{"request":{"txn":"C1","principal":"research-user","payee":"approved-api","asset":"USD","amount":"30","rail":"card","quote_expiry":150,"terms_hash":"example"},"now":100}`.
- `POST /api/session/reset`: clears global in-memory state.
- `POST /api/session/authorize`: sends `{"request": { ... }, "now":100}` to the stateful demo.
- `POST /api/session/transition`: sends `{"txn":"C1", "action":"submit"}`; actions: `submit`, `uncertain`, `confirm`, `fail`.

**Caution:** the stateful API is shared, in-memory and unauthenticated. It is for a controlled local lab only. For internet-facing use, host only the static `docs/` site. Never add real credentials.

## GitHub Pages

The public site is served from the `docs/` folder on the `main` branch (Settings → Pages → Deploy from a branch → `main` / `/docs`). GitHub Pages runs **only the browser JavaScript model**; it does not execute Python or Flask.

## Reference model

1. **Mandate and policy:** fixed synthetic scope and limits (principal `research-user`, payee `approved-api`, asset `USD`, 50-unit single-payment cap, 80-unit aggregate allowance, simulated expiry at clock 200).
2. **Agent request:** scenario inputs, not a deployed LLM.
3. **Orchestration:** deterministic allow/reject decisions and atomic budget reservation.
4. **Settlement adapters:** symbolic rail labels only, with simulated provider outcomes.
5. **Evidence and recourse:** in-execution event sequence; no durable records or real dispute process.

## Known limitations

- The web and Python engines are independent implementations; numeric handling differs beyond two decimal places. Shared cases use two-decimal USD amounts.
- No signature validation or cryptographic hash verification; `terms_hash` is checked only as a non-empty string.
- No persistent transaction store, crash recovery, isolation of concurrent web users, provider contract testing, or adversarial security assessment.
- The unrecoverable-exposure limit, route selection and disputed state described in the paper are specified but **not implemented** in this model.
- Simulated clock values are numbers, not timestamps; amounts are abstract units.
- Flask's built-in server is for local development only.

## Reporting results in a publication

Report, at minimum: the release tag and commit identifier, Python version, test date, and the actual command output of each suite. A hosted GitHub Pages link does not by itself establish validation of deployed payment infrastructure.

## Citation

If you use this software, please cite it using the metadata in `CITATION.cff` (GitHub shows a "Cite this repository" button). The archived release DOI will be added here once the release is deposited.

## Licence

MIT; see `LICENSE`.
