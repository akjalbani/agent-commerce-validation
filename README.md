# Agent Commerce Validation Laboratory

Open-source synthetic research prototype supporting the paper **Financial Infrastructure for Autonomous AI-Agent Commerce: A Reference Architecture for Authorisation, Settlement, Liquidity, and Risk**.

**Scope:** demonstration and validation of selected rail-neutral payment *policy* rules. No real payments, real credentials, blockchains, bank integrations, cryptographic proofs, fraud detection, or settlement occur. Simulated card, bank, stablecoin and payment-channel rails are labels only.

## Quick start: GitHub Pages (public interactive website)

1. Create a public GitHub repository, e.g. `agent-commerce-validation`.
2. Upload **all repository files**, retaining the `docs/` folder and its `index.html`, `style.css`, `app.js`, and `.nojekyll`.
3. In GitHub open **Settings > Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**, select `main` and `/docs`, then **Save**.
5. When GitHub publishes the site, open `https://YOUR-USERNAME.github.io/agent-commerce-validation/`.

GitHub Pages runs **only the browser JavaScript model**. GitHub Pages does not execute Python or Flask. The browser model uses equivalent named synthetic cases, but its code is separate from Python and must not be described as the Flask backend running online.

## Run locally with Flask

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000`. The interface is browser-based and the Flask API is available under `/api/` for independent Python experiments.

### Python API

- `GET /api/health` indicates simulation mode.
- `GET /api/scenarios` returns the 11 single-request scenarios.
- `GET /api/suite` executes the 16-case Python reference suite.
- `POST /api/simulate` runs an independent scenario: `{"request":{"txn":"C1","principal":"research-user","payee":"approved-api","asset":"USD","amount":"30","rail":"card","quote_expiry":150,"terms_hash":"example"},"now":100}`.
- `POST /api/session/reset` clears global in-memory state.
- `POST /api/session/authorize` sends `{"request": { ... }, "now":100}` to the stateful demo.
- `POST /api/session/transition` sends `{"txn":"C1", "action":"submit"}`; actions: `submit`, `uncertain`, `confirm`, `fail`.

**Caution:** The stateful API is intentionally shared and in-memory, with no user authentication. It is for a controlled local lab only, not public multiuser use. For internet-facing use, host only the static `docs/` site. Never add real credentials to the app.

## Reproduce Python tests

```bash
python -m unittest discover -s tests -v
python legacy_validation_18_tests.py
```

The original 18-test study script is provided unchanged as `legacy_validation_18_tests.py` so prior manuscript results remain reproducible. The new 16-case demonstrator suite is **separate**. Do not combine counts or report browser tests as executions of Python code. A GitHub Actions workflow is configured to rerun both checks on every push and pull request. The Flask integration tests require installation of `requirements.txt`.

## Evidence for publication

Suggested reporting: "An open-source demonstrator was implemented in Python/Flask with a separate browser simulation for public access. The Python reference model was checked against 16 synthetic scenario expectations, and the previously reported 18 unit tests remain available as a separate script. These results evaluate selected logical mandate, budget and transaction-state controls only. No real payment adapter or live settlement was tested."

Report the actual command output, repository commit identifier, Python version, test date, and test results when using the software in a paper. A hosted GitHub Pages link does not itself establish validation of deployed payment infrastructure.

## Architecture

1. Principal mandate and policy: fixed synthetic scope and limits.
2. Agent request: scenario inputs, not a deployed LLM.
3. Orchestration: deterministic allow/reject decisions and budget reservation.
4. Settlement adapters: symbolic rail labels only, with simulated provider outcomes.
5. Evidence and recourse: immutable-in-execution event sequence; no durable records or actual dispute process.

## Known limitations

- The web and Python engines are independent implementations; numeric handling differs, especially beyond two decimal places. The documented shared cases are restricted to two-decimal USD amounts.
- No independent signature validation or cryptographic hash verification. The `terms_hash` field is non-empty string checking only.
- No persistent transaction store, crash recovery, isolation of concurrent web users, bank/card provider contract testing, or genuine adversarial security assessment.
- Simulated clock values are numbers, not real timestamps, and scenario payments use abstract units.
- Flask's built-in server is for local development only; production Python deployments require a suitable WSGI server and authentication, isolation and durable storage.

## Licence

MIT; see `LICENSE`.

## Local verification status

The original 18 unittest checks, six core-model unittest checks, the 16-scenario Python reference suite, the 16-scenario browser reference suite in Node.js, and JavaScript syntax were executed successfully in the creation environment. Flask itself was not installed in that environment and installation was blocked, so Flask route tests were supplied but **not executed locally**. GitHub Actions is configured to install Flask and execute those API tests after upload. No GitHub Pages deployment has yet been performed.
