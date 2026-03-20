# Notes

---

## Testing Approach

### Chat: 


This document lays out the recommended testing structure and CI workflow for our Python repos that deploy through:

`Bitbucket Pipeline -> Helm pipe -> EKS`

The goals are:

1. Make it easy for us to write and maintain tests.
2. Make PR review much better by showing clearly that a feature has passed tests.
3. Keep the setup lightweight and consistent across repos.
4. Separate fast PR-time checks from slower environment/deployment checks.
5. Publish richer human-readable test reports via Allure in S3.

---

#### High-Level Recommendation

We will use the following stack:

- **pytest** as the test runner
- **pytest markers** to separate test categories
- **JUnit XML** as the canonical CI-readable output for Bitbucket
- **Allure** as the richer human-readable report
- **Bitbucket Pipelines** to run tests and attach artifacts
- **S3** to host/persist Allure report output for review/debugging
- optionally **coverage.py + pytest-cov** later for coverage gates and trend reporting

The basic idea is:

- **PR pipeline**
  - run `unit` + small `contract/api` tests
  - emit `junit.xml`
  - emit Allure raw results
  - generate/publish Allure HTML to S3
  - fail the PR if tests fail

- **main branch pipeline**
  - run `unit` + `contract` + `integration`
  - publish same artifacts
  - optionally deploy to dev/uat
  - optionally run smoke tests after deploy

- **post-deploy pipeline / environment validation**
  - run `smoke` tests against deployed service in EKS

- **nightly or scheduled pipeline**
  - run `slow`, broader `integration`, or `e2e`

---

#### Guiding Principles

##### 1) Keep the suite structure boring
Every repo should have the same testing layout and the same marker names.

##### 2) Make PR tests fast
If PR tests are slow, people stop trusting them and start bypassing them mentally.

##### 3) Separate application logic tests from infrastructure/deployment validation
A deployment to EKS should not be the only way we validate core code correctness.

##### 4) Treat JUnit XML as the canonical CI output
Bitbucket and other CI tools understand it well.

##### 5) Treat Allure as the human-friendly drilldown UI
Bitbucket tells us pass/fail. Allure tells us what happened.

---

#### Recommended Test Taxonomy

We will standardize on these buckets:

- `unit`
- `contract`
- `integration`
- `smoke`
- `slow`

Optional only where truly needed:

- `e2e`

##### Definitions

###### unit
Fast, deterministic, isolated tests.

Examples:

- pure transformation logic
- validation logic
- serializers/parsers
- utility functions
- business rules
- orchestration logic with dependencies mocked

These should:

- not hit network
- not require a running DB/Redis/Kafka
- not depend on AWS/EKS
- generally run in milliseconds

###### contract
Tests around service boundaries and request/response contracts.

Examples:

- FastAPI route tests with `TestClient`
- API schema validation
- input/output payload shape tests
- consumer/producer message schema tests
- serialization contracts for Kafka messages

These are still PR-safe and usually fast.

###### integration
Tests with real or near-real dependencies.

Examples:

- PostgreSQL integration
- Redis integration
- Kafka/Redpanda integration
- repository/data access tests
- startup wiring against realistic dependencies

These may use:

- docker service containers in CI
- ephemeral test infra
- test databases/topics/buckets

###### smoke
Minimal high-value checks against a deployed environment.

Examples:

- service starts
- health endpoint works
- one representative API call works
- one representative write/read path works

These should be small in number and high signal.

###### slow
Anything expensive enough that we do not want it on every PR.

Examples:

- large dataset tests
- long-running integration tests
- broad scenario matrices

###### e2e
Only if we truly own end-to-end product behavior in that repo.
Avoid adding this everywhere by default.

---

#### Standard File Structure

Every Python service repo should roughly follow this structure:

```text
repo/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ api/
│  ├─ services/
│  ├─ repositories/
│  ├─ clients/
│  ├─ models/
│  └─ settings.py
│
├─ tests/
│  ├─ conftest.py
│  ├─ fixtures/
│  │  ├─ __init__.py
│  │  ├─ api.py
│  │  ├─ db.py
│  │  ├─ redis.py
│  │  ├─ kafka.py
│  │  └─ factories.py
│  │
│  ├─ unit/
│  │  ├─ services/
│  │  ├─ repositories/
│  │  ├─ api/
│  │  └─ test_settings.py
│  │
│  ├─ contract/
│  │  ├─ api/
│  │  ├─ schemas/
│  │  └─ messaging/
│  │
│  ├─ integration/
│  │  ├─ db/
│  │  ├─ redis/
│  │  ├─ kafka/
│  │  └─ api/
│  │
│  ├─ smoke/
│  │  └─ test_health.py
│  │
│  └─ e2e/
│     └─ ...
│
├─ pyproject.toml
├─ pytest.ini
├─ requirements-dev.txt
├─ bitbucket-pipelines.yml
├─ scripts/
│  ├─ run_tests.sh
│  ├─ build_allure_report.sh
│  └─ publish_allure_to_s3.sh
└─ README.md
```

---

#### Naming Conventions

##### Test file naming
Use:

- `test_<thing>.py`

Examples:

- `test_health.py`
- `test_trade_allocator.py`
- `test_offer_serializer.py`

##### Test function naming
Use descriptive names:

```python
def test_allocate_offer_returns_empty_list_when_no_accounts_are_eligible():
    ...

def test_post_trade_import_returns_401_payload_when_downstream_auth_fails():
    ...
```

Avoid vague names like:

- `test_1`
- `test_basic`
- `test_happy_path`

---

#### Marker Policy

We will use markers consistently. Every test should belong to one primary bucket.

##### pytest.ini

```ini
[pytest]
minversion = 8.0
addopts = -ra
testpaths = tests
pythonpath = .
markers =
    unit: fast isolated tests
    contract: API/schema/message contract tests
    integration: tests using real external dependencies
    smoke: post-deploy environment validation tests
    slow: long-running tests excluded from normal PR runs
    e2e: end-to-end workflow tests
filterwarnings =
    error
    ignore::DeprecationWarning:pkg_resources.*
```

##### Example usage

```python
import pytest

@pytest.mark.unit
def test_normalize_cusip_trims_and_uppercases():
    ...

@pytest.mark.contract
def test_post_offer_route_returns_expected_response_shape():
    ...

@pytest.mark.integration
def test_offer_repository_round_trip_insert_and_fetch(db_session):
    ...

@pytest.mark.smoke
def test_health_endpoint_returns_200(base_url):
    ...
```

---

#### Recommended Local Developer Workflow

##### Fast loop during development

Developers should usually run:

```bash
pytest -m "unit or contract" -q
```

Or a specific file:

```bash
pytest tests/unit/services/test_allocator.py -q
```

Or a specific test:

```bash
pytest tests/unit/services/test_allocator.py -k eligible -q
```

##### Before opening a PR

Recommended local command:

```bash
pytest -m "unit or contract" --junit-xml=.tmp/junit.xml
```

If working in an area that touches integration points:

```bash
pytest -m "unit or contract or integration" -q
```

---

#### Recommended Fixture Strategy

We should avoid putting everything into one giant `conftest.py`.

##### Good pattern
- keep `tests/conftest.py` small
- place reusable fixtures under `tests/fixtures/`
- import shared fixtures into `conftest.py`

##### Example `tests/conftest.py`

```python
pytest_plugins = [
    "tests.fixtures.api",
    "tests.fixtures.db",
    "tests.fixtures.redis",
    "tests.fixtures.kafka",
    "tests.fixtures.factories",
]
```

##### Example `tests/fixtures/api.py`

```python
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def base_url():
    return os.getenv("SMOKE_BASE_URL", "http://localhost:8000")
```

##### Example `tests/fixtures/db.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
```

Notes:

- For true DB integration tests, use real Postgres in CI.
- For unit tests, an in-memory DB or mocking is fine if it is genuinely testing logic rather than driver behavior.

---

#### Example Test Layout by Layer

##### Example unit test

```python
import pytest
from app.services.eligibility import is_account_eligible

@pytest.mark.unit
def test_is_account_eligible_returns_false_when_state_is_disallowed():
    account = {"allowed_states": {"WA", "CA"}}
    offer = {"state": "NY"}

    result = is_account_eligible(account, offer)

    assert result is False
```

##### Example contract test for FastAPI route

```python
import pytest

@pytest.mark.contract
def test_health_route_returns_expected_shape(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "service" in payload
```

##### Example integration test

```python
import pytest
from app.repositories.offer_repository import OfferRepository

@pytest.mark.integration
def test_offer_repository_can_insert_and_fetch(db_session):
    repo = OfferRepository(db_session)

    repo.insert_offer(cusip="123456AB7", price=101.25)
    offer = repo.get_offer("123456AB7")

    assert offer is not None
    assert offer.cusip == "123456AB7"
    assert offer.price == 101.25
```

##### Example smoke test

```python
import os
import pytest
import requests

@pytest.mark.smoke
def test_healthcheck_in_deployed_env():
    base_url = os.environ["SMOKE_BASE_URL"]
    response = requests.get(f"{base_url}/health", timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

#### What Should Run in PRs vs Main vs Post-Deploy

##### PR pipeline
Run:

- `unit`
- `contract`
- optionally a very small subset of `integration` if fast/stable

Command:

```bash
pytest -m "unit or contract" \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### Main branch pipeline
Run:

- `unit`
- `contract`
- `integration`

Command:

```bash
pytest -m "unit or contract or integration" \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### Post-deploy smoke
Run:

- `smoke`

Command:

```bash
pytest -m "smoke" \
  --junit-xml=test-results/junit-smoke.xml \
  --alluredir=test-results/allure-results-smoke
```

##### Nightly
Run:

- `slow`
- broader `integration`
- `e2e` if applicable

---

#### Dev Dependencies

Recommended `requirements-dev.txt`:

```txt
pytest
pytest-xdist
pytest-cov
allure-pytest
requests
```

Notes:

- `pytest-xdist` is useful for speeding up large test suites
- `pytest-cov` is useful later if we add coverage gating
- `allure-pytest` writes Allure result files
- `requests` is useful for smoke tests against deployed URLs

---

#### Example `pyproject.toml` Snippet

If we want to keep tooling config in `pyproject.toml`, something like:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra"
testpaths = ["tests"]
pythonpath = ["."]
markers = [
  "unit: fast isolated tests",
  "contract: API/schema/message contract tests",
  "integration: tests using real external dependencies",
  "smoke: post-deploy environment validation tests",
  "slow: long-running tests excluded from normal PR runs",
  "e2e: end-to-end workflow tests"
]
```

We can use either `pytest.ini` or `pyproject.toml`. I prefer `pytest.ini` for visibility and simplicity.

---

#### Allure Usage

##### Why Allure
Bitbucket/JUnit gives us pass/fail and machine-readable results.
Allure gives us a cleaner UI for:

- failed test drilldown
- captured logs/details
- attachments
- screenshots/payloads if we choose to add them
- browsing historical artifacts if we persist reports

##### Basic command
Pytest writes Allure raw results like this:

```bash
pytest -m "unit or contract" \
  --alluredir=test-results/allure-results
```

Then the raw results must be turned into HTML with the Allure CLI.

##### Local example
If the Allure CLI is installed locally:

```bash
allure generate test-results/allure-results \
  --clean \
  -o test-results/allure-report
```

That creates static HTML files under `test-results/allure-report/`.

---

#### Scripts We Should Standardize

##### `scripts/run_tests.sh`

```bash
####!/usr/bin/env bash
set -euo pipefail

MARK_EXPR="${1:-unit or contract}"

mkdir -p test-results

pytest -m "${MARK_EXPR}" \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### `scripts/build_allure_report.sh`

```bash
####!/usr/bin/env bash
set -euo pipefail

RESULTS_DIR="${1:-test-results/allure-results}"
REPORT_DIR="${2:-test-results/allure-report}"

rm -rf "${REPORT_DIR}"
mkdir -p "${REPORT_DIR}"

allure generate "${RESULTS_DIR}" --clean -o "${REPORT_DIR}"
```

##### `scripts/publish_allure_to_s3.sh`

```bash
####!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${1:-test-results/allure-report}"
S3_DEST="${2:?Must provide S3 destination, e.g. s3://my-bucket/my-repo/pr-123/}"

aws s3 sync "${REPORT_DIR}" "${S3_DEST}" --delete
```

Make sure scripts are executable:

```bash
chmod +x scripts/*.sh
```

---

#### Bitbucket Pipeline Example

Below is an example `bitbucket-pipelines.yml` we can use as a starting point.

Adjust:

- image
- caches
- service containers
- deployment steps
- helm pipe details
- AWS auth approach
- bucket names

##### Example pipeline

```yaml
image: python:3.12

definitions:
  caches:
    pip: ~/.cache/pip

  services:
    postgres:
      image: postgres:15
      environment:
        POSTGRES_DB: test_db
        POSTGRES_USER: test_user
        POSTGRES_PASSWORD: test_pass

pipelines:
  pull-requests:
    "**":
      - step:
          name: PR Tests
          caches:
            - pip
          script:
            - python -V
            - pip install --upgrade pip
            - pip install -r requirements.txt
            - pip install -r requirements-dev.txt
            - mkdir -p test-results
            - pytest -m "unit or contract" --junit-xml=test-results/junit.xml --alluredir=test-results/allure-results
          artifacts:
            - test-results/**

      - step:
          name: Build Allure Report and Upload to S3
          caches:
            - pip
          script:
            - apt-get update && apt-get install -y default-jre wget unzip
            - wget -q https://github.com/allure-framework/allure2/releases/download/2.34.1/allure-2.34.1.zip
            - unzip -q allure-2.34.1.zip
            - export PATH="$PWD/allure-2.34.1/bin:$PATH"
            - python -V
            - pip install --upgrade pip
            - pip install awscli
            - test -d test-results/allure-results
            - allure generate test-results/allure-results --clean -o test-results/allure-report
            - aws s3 sync test-results/allure-report "s3://${ALLURE_BUCKET}/${BITBUCKET_REPO_SLUG}/pr-${BITBUCKET_PR_ID}/" --delete
          artifacts:
            - test-results/**

  branches:
    main:
      - step:
          name: Main Branch Tests
          caches:
            - pip
          services:
            - postgres
          script:
            - python -V
            - pip install --upgrade pip
            - pip install -r requirements.txt
            - pip install -r requirements-dev.txt
            - mkdir -p test-results
            - pytest -m "unit or contract or integration" --junit-xml=test-results/junit.xml --alluredir=test-results/allure-results
          artifacts:
            - test-results/**

      - step:
          name: Build Allure Report and Upload to S3
          caches:
            - pip
          script:
            - apt-get update && apt-get install -y default-jre wget unzip
            - wget -q https://github.com/allure-framework/allure2/releases/download/2.34.1/allure-2.34.1.zip
            - unzip -q allure-2.34.1.zip
            - export PATH="$PWD/allure-2.34.1/bin:$PATH"
            - pip install awscli
            - allure generate test-results/allure-results --clean -o test-results/allure-report
            - aws s3 sync test-results/allure-report "s3://${ALLURE_BUCKET}/${BITBUCKET_REPO_SLUG}/main-${BITBUCKET_BUILD_NUMBER}/" --delete
          artifacts:
            - test-results/**

      - step:
          name: Deploy to EKS
          script:
            - echo "helm pipe deployment step goes here"

      - step:
          name: Post-Deploy Smoke Tests
          caches:
            - pip
          script:
            - pip install --upgrade pip
            - pip install -r requirements.txt
            - pip install -r requirements-dev.txt
            - mkdir -p test-results
            - export SMOKE_BASE_URL="${DEV_SERVICE_URL}"
            - pytest -m "smoke" --junit-xml=test-results/junit-smoke.xml --alluredir=test-results/allure-results-smoke
          artifacts:
            - test-results/**
```

---

#### Notes on the Pipeline

##### Why two outputs?
Every test step should emit:

- `test-results/junit.xml` for Bitbucket / CI visibility
- `test-results/allure-results/` for rich reporting

##### Why upload Allure to S3?
Because raw CI artifacts are okay, but S3 lets us:

- keep reports around longer
- share a stable link
- browse failures after the build
- compare runs more easily if we organize paths well

##### Recommended S3 key pattern
Use something like:

```text
s3://<bucket>/<repo>/<context>/
```

Examples:

```text
s3://team-allure-reports/pragma-api-backend/pr-142/
s3://team-allure-reports/pragma-api-backend/main-387/
s3://team-allure-reports/pragma-api-backend/smoke-dev-388/
```

---

#### Suggested S3 Layout Convention

```text
s3://team-allure-reports/
└─ pragma-api-backend/
   ├─ pr-142/
   ├─ pr-143/
   ├─ main-387/
   ├─ main-388/
   ├─ smoke-dev-388/
   └─ nightly-2026-03-19/
```

This makes it obvious where to look.

---

#### Optional: Post a Report Link Back to the PR

If we want better reviewer ergonomics, we should consider a small script that posts a comment or status link back into the PR with something like:

- test summary
- number passed/failed/skipped
- link to Allure report in S3

Even without fancy API integration, a plain PR comment from CI is already useful.

Format example:

```text
PR test results:
- unit/contract tests passed
- 184 passed, 3 skipped, 0 failed
- Allure report: <link>
```

This is worth doing because I review a lot of PRs and I want one obvious place to click.

---

#### Recommended Environment Variables

We should standardize the following env vars where relevant:

```text
ALLURE_BUCKET
AWS_DEFAULT_REGION
SMOKE_BASE_URL
APP_ENV
DATABASE_URL
REDIS_URL
KAFKA_BOOTSTRAP_SERVERS
```

For smoke tests, `SMOKE_BASE_URL` is especially useful.

---

#### Recommended AWS / S3 Access Pattern

The pipeline needs permission to upload to the bucket.
How we do that depends on our Bitbucket/AWS setup.

At a minimum the pipeline needs:

- `s3:PutObject`
- `s3:DeleteObject`
- `s3:ListBucket`

scoped to the relevant report prefix/bucket.

If possible, keep the bucket private and expose reports via:

- presigned URLs
- CloudFront + auth
- or internal-only access pattern

I would avoid making the bucket publicly readable unless there is a very good reason.

---

#### Example Allure-Enriched Test

One of Allure’s advantages is that we can attach useful context to failures.

##### Example

```python
import json
import allure
import pytest

@pytest.mark.contract
def test_trade_import_response_shape(client):
    payload = {
        "account": "ABC123",
        "cusip": "123456AB7",
        "par": 100000,
    }

    with allure.step("Submit trade import request"):
        response = client.post("/trade-import", json=payload)

    allure.attach(
        json.dumps(payload, indent=2),
        name="request_payload",
        attachment_type=allure.attachment_type.JSON,
    )

    allure.attach(
        response.text,
        name="response_body",
        attachment_type=allure.attachment_type.JSON,
    )

    assert response.status_code == 200
```

This is especially useful for API/contract/integration tests where the payload matters.

---

#### Coverage Recommendation

Coverage is useful, but I do **not** want us to start with “chase a huge global percentage.”
That usually produces junk tests.

Recommended approach:

##### Phase 1
Do not block on coverage yet.
Just get:

- real unit tests
- real contract tests
- stable PR gating
- visible reports

##### Phase 2
Add coverage reporting:

```bash
pytest -m "unit or contract" \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### Phase 3
Potential gate:

- set a modest floor
- or better: require coverage not to drop materially
- or best: use diff coverage for changed files

I do **not** want a blunt policy like “85% or bust” on day one.

---

#### What We Should Enforce in PR Review

CI alone is not enough. We should also make PR expectations explicit.

##### PR checklist recommendation
Every PR should answer:

- What test bucket covers this change?
- Were tests added or updated?
- If no tests were added, why not?
- Did the PR pipeline pass?
- Is there any follow-up test debt?

Example PR template section:

```text
##### Testing
- [ ] Unit tests added/updated
- [ ] Contract tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] No tests added, and explanation provided below

Testing notes:
- Marker bucket(s):
- Local commands run:
- Any known gaps:
```

This matters because I want to quickly tell whether a feature only “passed existing tests” versus actually introduced meaningful new test coverage.

---

#### Anti-Patterns We Want to Avoid

##### 1) One giant `test_everything.py`
Split tests by domain and layer.

##### 2) Integration tests pretending to be unit tests
If it hits real infra, mark it `integration`.

##### 3) Massive fixture spaghetti
Keep fixtures composable and local where possible.

##### 4) PR pipelines that take forever
PR pipeline should be biased toward speed and signal.

##### 5) Deployment-dependent correctness
Core logic should be testable without deploying to EKS.

##### 6) Brittle snapshot-style tests everywhere
Use them selectively, not as the default.

##### 7) Chasing vanity coverage
Prefer meaningful coverage over inflated coverage.

---

#### Repo Bootstrap Checklist

For a new repo, the initial setup should be:

##### 1) Add dev dependencies
```text
pytest
pytest-xdist
pytest-cov
allure-pytest
requests
```

##### 2) Add `pytest.ini`
with standardized markers

##### 3) Add `tests/` structure
```text
tests/
  conftest.py
  fixtures/
  unit/
  contract/
  integration/
  smoke/
```

##### 4) Add pipeline step
Run:
```bash
pytest -m "unit or contract" \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### 5) Add Allure build/upload step
Generate HTML and upload to S3

##### 6) Add 3-5 high-value starter tests
Not dozens of filler tests

Suggested starter set:

- one core service unit test
- one route contract test
- one repo integration test
- one smoke health test

---

#### Minimal Starter Example

##### `pytest.ini`

```ini
[pytest]
minversion = 8.0
addopts = -ra
testpaths = tests
pythonpath = .
markers =
    unit: fast isolated tests
    contract: API/schema/message contract tests
    integration: tests using real external dependencies
    smoke: post-deploy environment validation tests
    slow: long-running tests excluded from normal PR runs
    e2e: end-to-end workflow tests
```

##### `tests/unit/test_example.py`

```python
import pytest

@pytest.mark.unit
def test_example():
    assert 2 + 2 == 4
```

##### `tests/contract/test_health.py`

```python
import pytest

@pytest.mark.contract
def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200
```

##### `tests/smoke/test_health_smoke.py`

```python
import os
import pytest
import requests

@pytest.mark.smoke
def test_health_smoke():
    base_url = os.environ["SMOKE_BASE_URL"]
    response = requests.get(f"{base_url}/health", timeout=5)
    assert response.status_code == 200
```

##### local run

```bash
pytest -m "unit or contract" \
  --junit-xml=test-results/junit.xml \
  --alluredir=test-results/allure-results
```

##### generate Allure report

```bash
allure generate test-results/allure-results --clean -o test-results/allure-report
```

##### publish

```bash
aws s3 sync test-results/allure-report "s3://${ALLURE_BUCKET}/${BITBUCKET_REPO_SLUG}/pr-${BITBUCKET_PR_ID}/" --delete
```

---

#### Recommended Team Policy

My recommendation for the team is:

##### Required on every PR
- unit + contract tests pass
- JUnit XML emitted
- Allure results emitted
- Allure report uploaded to S3
- PR includes testing notes

##### Required on main
- unit + contract + integration pass
- deployment proceeds only after those pass

##### Required post-deploy
- smoke tests pass against deployed env

##### Nightly
- slow/integration/e2e as needed

---

#### Final Practical Take

If we want something pragmatic that works well with our workflow, this is the setup I recommend:

1. Use **pytest markers** to separate test categories.
2. Keep **PR pipelines fast** with `unit + contract`.
3. Emit **JUnit XML** for Bitbucket visibility.
4. Emit **Allure raw results** during test execution.
5. Build static **Allure HTML** in CI.
6. Publish the report to **S3** using a clean repo/build/PR path convention.
7. Add a **PR link/comment/status** pointing reviewers to the report.
8. Keep test structure standardized across all repos.

This gives us:

- clean PR gating
- better reviewer visibility
- richer debugging when something fails
- minimal extra infrastructure
- a testing setup that matches how we actually develop and deploy

---

### Claude:

#### Overview

This document lays out how we're structuring our pytest suites, integrating them into our Bitbucket Pipeline → Helm → EKS deployment workflow, and generating human-readable test reports. The goals are:

1. **Every PR must show test results at review time.** I shouldn't have to ask "did tests pass?" — it should be visible on the PR itself.
2. **Test reports should be rich and browsable**, not raw terminal output. We'll use Allure for this.
3. **We need clear test tiers** so the pipeline runs the right tests at the right stage.
4. **PRs should surface whether new tests were added** for new features/fixes.

---

#### 1. Repository Test Structure

Every repo follows this layout:

```
repo-root/
├── src/
│   └── ...                          # application code
├── tests/
│   ├── conftest.py                  # shared fixtures: mock K8s clients, DB sessions,
│   │                                #   streaming test harnesses, etc.
│   ├── unit/
│   │   ├── conftest.py              # unit-specific fixtures (lightweight mocks)
│   │   ├── test_portfolio_opt.py
│   │   ├── test_signal_pipeline.py
│   │   └── ...
│   ├── integration/
│   │   ├── conftest.py              # integration fixtures (testcontainers, docker-compose refs)
│   │   ├── test_kafka_consumer.py
│   │   ├── test_db_writes.py
│   │   └── ...
│   └── e2e/
│       ├── conftest.py              # e2e fixtures (real cluster clients, health check helpers)
│       ├── test_deployment_smoke.py
│       └── ...
├── pyproject.toml
├── bitbucket-pipelines.yml
├── scripts/
│   ├── post_allure_link.py          # posts Allure report URL as PR comment
│   ├── check_new_tests.py           # diffs collected tests vs main branch
│   └── push_allure_to_s3.sh         # uploads Allure HTML to S3
└── allure-config/
    └── categories.json              # custom Allure failure categories
```

##### Why this structure

- **`conftest.py` at each level** keeps fixtures scoped appropriately. Unit fixtures shouldn't pull in Docker dependencies; integration fixtures shouldn't assume a live cluster.
- **`scripts/`** holds our pipeline helper scripts. These are not application code — they exist to make CI output useful.
- **`allure-config/`** lets us customize how Allure categorizes failures (product defect vs. test defect vs. infra flake).

---

#### 2. pytest Configuration

All pytest config lives in `pyproject.toml`. No `pytest.ini`, no `setup.cfg` — one source of truth.

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: fast, isolated, no infra dependencies",
    "integration: requires service dependencies (docker-compose / testcontainers)",
    "e2e: post-deploy smoke tests against live EKS cluster",
    "slow: tests that take >10s (can overlap with any tier)",
]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--junitxml=test-results/results.xml",
    "--alluredir=allure-results",
    "-v",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
junit_family = "xunit2"
```

##### Key flags

| Flag | Why |
|---|---|
| `--strict-markers` | Typos in marker names become errors, not silent passes. Non-negotiable. |
| `--junitxml=test-results/results.xml` | Bitbucket Pipelines natively parses JUnit XML and renders a **Tests** tab on each pipeline run. Free visibility with zero effort. |
| `--alluredir=allure-results` | Raw Allure data gets dumped here. We generate the HTML report from this in a later pipeline step. |
| `--tb=short` | Keeps pipeline logs readable. Full tracebacks live in the Allure report. |
| `junit_family = "xunit2"` | Required for modern JUnit XML schema. Bitbucket and Allure both expect this. |

---

#### 3. Marker Registration and Usage

Every test function or class **must** have a tier marker. The `--strict-markers` flag enforces that only registered markers are used.

```python
### tests/unit/test_portfolio_opt.py

import pytest
import numpy as np

@pytest.mark.unit
class TestMeanVarianceOptimizer:
    """Tests for the MVO engine. No network, no DB, no K8s."""

    def test_efficient_frontier_shape(self, sample_returns):
        frontier = compute_efficient_frontier(sample_returns, n_points=50)
        assert frontier.shape == (50, 2)  # (risk, return) pairs

    def test_constraint_violation_raises(self, sample_returns):
        with pytest.raises(ConstraintViolationError):
            optimize(sample_returns, max_weight=0.0)  # impossible constraint

    @pytest.mark.slow
    def test_large_universe_convergence(self, large_universe_returns):
        """5000-asset universe. Takes ~15s. Skip in quick feedback loops."""
        result = optimize(large_universe_returns)
        assert result.converged
```

```python
### tests/integration/test_kafka_consumer.py

import pytest
from testcontainers.kafka import KafkaContainer

@pytest.fixture(scope="module")
def kafka_broker():
    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()

@pytest.mark.integration
class TestSignalConsumer:
    """Requires a real Kafka broker (via testcontainers)."""

    def test_consumes_signal_message(self, kafka_broker, sample_signal):
        producer = create_producer(kafka_broker)
        producer.send("signals", sample_signal)
        consumed = consumer.poll(timeout=5.0)
        assert consumed is not None
        assert consumed["signal_id"] == sample_signal["signal_id"]
```

```python
### tests/e2e/test_deployment_smoke.py

import pytest
import requests

@pytest.mark.e2e
class TestDeploymentHealth:
    """Runs against live EKS after helm deploy. Keep these fast and read-only."""

    def test_health_endpoint(self, cluster_base_url):
        resp = requests.get(f"{cluster_base_url}/health", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_model_version_matches_deployment(self, cluster_base_url, expected_model_version):
        resp = requests.get(f"{cluster_base_url}/model/info", timeout=10)
        assert resp.json()["version"] == expected_model_version
```

---

#### 4. Allure Setup

##### Installation

```bash
### python plugin (in your test requirements)
pip install allure-pytest

### allure CLI (for generating HTML from raw results)
### in pipeline, install via npm or direct binary:
npm install -g allure-commandline
### or
curl -sL https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz \
  | tar -xz -C /opt/ && ln -s /opt/allure-2.27.0/bin/allure /usr/local/bin/allure
```

##### Adding detail to tests

Allure gets much more useful when tests carry metadata. This is optional but strongly encouraged for anything non-trivial:

```python
import allure

@allure.epic("Portfolio Construction")
@allure.feature("Mean-Variance Optimization")
@allure.story("Constraint Handling")
@pytest.mark.unit
def test_turnover_constraint_respected(portfolio_state, target_weights):
    """Verify turnover constraint limits total trade notional."""
    with allure.step("Compute optimal trades with 10% turnover cap"):
        result = optimize(
            current=portfolio_state,
            target=target_weights,
            max_turnover=0.10,
        )

    with allure.step("Assert turnover is within constraint"):
        assert result.turnover <= 0.10 + 1e-9  # float tolerance

    # attach useful debug info to the report
    allure.attach(
        str(result.trade_summary),
        name="Trade Summary",
        attachment_type=allure.attachment_type.TEXT,
    )
```

This gives you a navigable hierarchy in the Allure UI: **Epic → Feature → Story → Test** with expandable steps and attachments.

##### Custom failure categories

Create `allure-config/categories.json` so failures get classified meaningfully:

```json
[
  {
    "name": "Infrastructure Flakes",
    "matchedStatuses": ["broken"],
    "messageRegex": ".*(timeout|connection refused|socket|DNS).*"
  },
  {
    "name": "Assertion Failures (Product Defects)",
    "matchedStatuses": ["failed"],
    "messageRegex": ".*AssertionError.*"
  },
  {
    "name": "Test Code Errors",
    "matchedStatuses": ["broken"],
    "messageRegex": ".*"
  }
]
```

Copy this into the allure-results directory before generating the report:

```bash
cp allure-config/categories.json allure-results/categories.json
allure generate allure-results -o allure-report --clean
```

---

#### 5. S3 Hosting for Allure Reports

Each pipeline run pushes its Allure report to S3 as a static site. Reports are keyed by repo + branch + build number so they don't collide.

##### S3 bucket setup (one-time)

```bash
aws s3 mb s3://invesco-fi-test-reports --region us-east-1

### enable static website hosting
aws s3 website s3://invesco-fi-test-reports \
  --index-document index.html

### bucket policy: restrict to VPN/internal CIDR (adjust to your network)
### or use CloudFront + WAF if you want broader but controlled access
```

##### Upload script: `scripts/push_allure_to_s3.sh`

```bash
###!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="${BITBUCKET_REPO_SLUG}"
BRANCH="${BITBUCKET_BRANCH}"
BUILD_NUM="${BITBUCKET_BUILD_NUMBER}"
S3_BUCKET="s3://invesco-fi-test-reports"
REPORT_PATH="${REPO_SLUG}/${BRANCH}/${BUILD_NUM}"

echo "Uploading Allure report to ${S3_BUCKET}/${REPORT_PATH}/"
aws s3 sync allure-report/ "${S3_BUCKET}/${REPORT_PATH}/" \
  --delete \
  --cache-control "max-age=3600"

REPORT_URL="http://invesco-fi-test-reports.s3-website-us-east-1.amazonaws.com/${REPORT_PATH}/index.html"
echo "Report URL: ${REPORT_URL}"

### export for downstream steps
echo "${REPORT_URL}" > .allure_report_url
```

---

#### 6. PR Comment Automation

##### Post Allure link as PR comment: `scripts/post_allure_link.py`

Uses Bitbucket REST API to comment on the PR with the report link.

```python
###!/usr/bin/env python3
"""Post Allure report link as a PR comment on Bitbucket."""

import os
import requests

def main():
    workspace = os.environ["BITBUCKET_WORKSPACE"]
    repo_slug = os.environ["BITBUCKET_REPO_SLUG"]
    pr_id = os.environ.get("BITBUCKET_PR_ID")

    if not pr_id:
        print("Not a PR build, skipping comment.")
        return

    with open(".allure_report_url") as f:
        report_url = f.read().strip()

    # read junit results for a quick summary
    passed, failed, errors = parse_junit_summary("test-results/results.xml")

    status_emoji = "✅" if (failed + errors) == 0 else "❌"

    comment_body = f"""
{status_emoji} **Test Results**

| Passed | Failed | Errors |
|--------|--------|--------|
| {passed} | {failed} | {errors} |

📊 [**View Full Allure Report**]({report_url})
"""

    url = (
        f"https://api.bitbucket.org/2.0/repositories/"
        f"{workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
    )

    resp = requests.post(
        url,
        json={"content": {"raw": comment_body}},
        auth=(os.environ["BB_USER"], os.environ["BB_APP_PASSWORD"]),
    )
    resp.raise_for_status()
    print(f"Posted PR comment with report link.")


def parse_junit_summary(xml_path: str) -> tuple[int, int, int]:
    """Quick and dirty JUnit XML summary parse."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # handle both single <testsuite> and <testsuites> wrapper
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    else:
        suites = [root]

    passed = failed = errors = 0
    for suite in suites:
        total = int(suite.get("tests", 0))
        f = int(suite.get("failures", 0))
        e = int(suite.get("errors", 0))
        s = int(suite.get("skipped", 0))
        failed += f
        errors += e
        passed += total - f - e - s
    return passed, failed, errors


if __name__ == "__main__":
    main()
```

##### Detect new tests in PR: `scripts/check_new_tests.py`

```python
###!/usr/bin/env python3
"""
Diff collected test IDs between the feature branch and main.
Posts a PR comment listing newly added tests (or warns if none were added).
"""

import os
import subprocess
import requests


def collect_test_ids() -> set[str]:
    """Run pytest --collect-only and return set of test node IDs."""
    result = subprocess.run(
        ["python", "-m", "pytest", "--collect-only", "-q", "--no-header"],
        capture_output=True, text=True,
    )
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if "::" in line  # valid test node IDs contain ::
    }


def main():
    pr_id = os.environ.get("BITBUCKET_PR_ID")
    if not pr_id:
        print("Not a PR build, skipping.")
        return

    # collect tests on feature branch
    feature_tests = collect_test_ids()

    # stash changes, collect on main, restore
    current_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    subprocess.run(["git", "fetch", "origin", "main"], check=True)
    subprocess.run(["git", "checkout", "origin/main"], check=True)
    main_tests = collect_test_ids()
    subprocess.run(["git", "checkout", current_branch], check=True)

    new_tests = sorted(feature_tests - main_tests)
    removed_tests = sorted(main_tests - feature_tests)

    if new_tests:
        test_list = "\n".join(f"  - `{t}`" for t in new_tests)
        body = f"🆕 **New tests added in this PR ({len(new_tests)}):**\n\n{test_list}"
    else:
        body = (
            "⚠️ **No new tests detected in this PR.**\n\n"
            "If this PR adds or modifies functionality, please add corresponding tests."
        )

    if removed_tests:
        removed_list = "\n".join(f"  - `{t}`" for t in removed_tests)
        body += f"\n\n🗑️ **Tests removed ({len(removed_tests)}):**\n\n{removed_list}"

    # post comment
    workspace = os.environ["BITBUCKET_WORKSPACE"]
    repo_slug = os.environ["BITBUCKET_REPO_SLUG"]
    url = (
        f"https://api.bitbucket.org/2.0/repositories/"
        f"{workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
    )
    resp = requests.post(
        url,
        json={"content": {"raw": body}},
        auth=(os.environ["BB_USER"], os.environ["BB_APP_PASSWORD"]),
    )
    resp.raise_for_status()
    print(f"Posted new-test diff comment.")


if __name__ == "__main__":
    main()
```

---

#### 7. Bitbucket Pipelines Configuration

This is the full `bitbucket-pipelines.yml` tying everything together.

```yaml
image: python:3.11-slim

definitions:
  caches:
    pip: ~/.cache/pip

  steps:
    - step: &install-deps
        name: Install Dependencies
        caches:
          - pip
        script:
          - pip install -r requirements.txt -r requirements-test.txt
          - npm install -g allure-commandline

    - step: &run-unit-tests
        name: Unit Tests
        caches:
          - pip
        script:
          - pip install -r requirements.txt -r requirements-test.txt
          - python -m pytest tests/unit -m unit
            --junitxml=test-results/unit-results.xml
            --alluredir=allure-results
            --cov=src --cov-report=xml:coverage.xml
        artifacts:
          - test-results/**
          - allure-results/**
          - coverage.xml

    - step: &run-integration-tests
        name: Integration Tests
        caches:
          - pip
        services:
          - docker
        script:
          - pip install -r requirements.txt -r requirements-test.txt
          - python -m pytest tests/integration -m integration
            --junitxml=test-results/integration-results.xml
            --alluredir=allure-results
        artifacts:
          - test-results/**
          - allure-results/**

    - step: &generate-allure-report
        name: Generate & Upload Allure Report
        caches:
          - pip
        script:
          - npm install -g allure-commandline
          - pip install requests
          - cp allure-config/categories.json allure-results/ || true
          - allure generate allure-results -o allure-report --clean
          - bash scripts/push_allure_to_s3.sh
          - python scripts/post_allure_link.py
        artifacts:
          - allure-report/**

    - step: &check-new-tests
        name: Check for New Tests
        caches:
          - pip
        script:
          - pip install -r requirements.txt -r requirements-test.txt requests
          - python scripts/check_new_tests.py

    - step: &helm-deploy
        name: Helm Deploy to EKS
        deployment: staging
        script:
          - curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
          - aws eks update-kubeconfig --name $EKS_CLUSTER --region $AWS_REGION
          - helm upgrade --install $SERVICE_NAME ./helm/
            --namespace $K8S_NAMESPACE
            --set image.tag=$BITBUCKET_COMMIT
            --wait --timeout 300s

    - step: &run-e2e-tests
        name: E2E Smoke Tests
        script:
          - pip install -r requirements.txt -r requirements-test.txt
          - python -m pytest tests/e2e -m e2e
            --junitxml=test-results/e2e-results.xml
            --base-url=$STAGING_URL
        artifacts:
          - test-results/**

pipelines:
  # ──────────────────────────────────────────────
  # Every push to any branch: unit tests only
  # ──────────────────────────────────────────────
  default:
    - step: *run-unit-tests

  # ──────────────────────────────────────────────
  # Pull requests: full test suite + reporting
  # ──────────────────────────────────────────────
  pull-requests:
    "**":
      - step: *run-unit-tests
      - step: *run-integration-tests
      - parallel:
          - step: *generate-allure-report
          - step: *check-new-tests

  # ──────────────────────────────────────────────
  # Main branch: deploy + e2e
  # ──────────────────────────────────────────────
  branches:
    main:
      - step: *run-unit-tests
      - step: *run-integration-tests
      - step: *generate-allure-report
      - step: *helm-deploy
      - step: *run-e2e-tests
```

##### Pipeline environment variables to set

Set these in Bitbucket → Repository Settings → Pipeline → Environment Variables:

| Variable | Description | Secured? |
|---|---|---|
| `BB_USER` | Bitbucket username for API calls | No |
| `BB_APP_PASSWORD` | Bitbucket app password with PR comment scope | **Yes** |
| `AWS_ACCESS_KEY_ID` | For S3 upload + EKS access | **Yes** |
| `AWS_SECRET_ACCESS_KEY` | For S3 upload + EKS access | **Yes** |
| `AWS_REGION` | e.g. `us-east-1` | No |
| `EKS_CLUSTER` | EKS cluster name | No |
| `K8S_NAMESPACE` | Target namespace | No |
| `SERVICE_NAME` | Helm release name | No |
| `STAGING_URL` | Base URL for e2e tests | No |

---

#### 8. What This Looks Like at PR Review Time

When I open a PR, I should see:

1. **Bitbucket Tests tab** — native JUnit rendering showing pass/fail counts for unit + integration.
2. **PR comment: test results + Allure link** — clickable link to the full interactive report on S3. Shows passed/failed/error summary inline.
3. **PR comment: new test diff** — lists every new test added in the PR, or warns if none were added.
4. **Allure report (click-through)** — full breakdown by epic/feature/story, expandable steps, attachments, failure categorization, duration stats.

This means I never have to ask "did you run the tests" or "did you add tests" — it's all automated and visible.

---

#### 9. Test Requirements File

Keep test deps separate from app deps. `requirements-test.txt`:

```
pytest>=8.0
pytest-cov>=5.0
pytest-xdist>=3.5        # parallel test execution: pytest -n auto
allure-pytest>=2.13
testcontainers>=4.0       # for integration tests
requests                  # for helper scripts
```

---

#### 10. Local Development Workflow

Devs should be able to run tests locally with the same markers:

```bash
### quick unit feedback loop
pytest tests/unit -m unit -x --tb=short

### run everything except e2e
pytest tests/ -m "not e2e"

### generate local allure report for debugging
pytest tests/unit -m unit --alluredir=allure-results
allure serve allure-results  # opens browser with live report

### check what tests you've added vs main
python scripts/check_new_tests.py  # (will skip PR comment if no PR_ID set)
```

The `allure serve` command is especially useful — it generates and opens the report in one shot with hot reload. Great for iterating on test structure.

---

#### Action Items

- [ ] Add `requirements-test.txt` to all repos
- [ ] Add `pyproject.toml` pytest config to all repos
- [ ] Create S3 bucket + IAM policy for report uploads
- [ ] Set pipeline environment variables in Bitbucket
- [ ] Add `scripts/` directory + helper scripts to repo template
- [ ] Add `allure-config/categories.json` to repo template
- [ ] Update `bitbucket-pipelines.yml` in all repos
- [ ] Verify PR comment bot works on a test PR

## Cloud Migration Playbook: On-Prem Python Apps → AWS EKS

Cloud Migration Framework for Python Apps: Shared Drive / Excel → S3 or PostgreSQL, AutoSys/.jil → Airflow, On-Prem → EKS

---

### Chat:

#### Executive Summary

Your proposed migration shape is sound:

1. **First decide the system of record** for data currently living in Excel/network-drive files.
2. **Add dual-write capability in the current on-prem production pipeline** so the existing AutoSys-driven process continues to run while also publishing to the future-state storage layer.
3. **Build the cloud-native version on a feature branch** against that future-state storage layer.
4. **Cut over readers/consumers before cutting over writers**, then retire the old shared-drive dependency.
5. **Move orchestration from AutoSys/.jil to Airflow** only after job boundaries, inputs/outputs, retries, and idempotency are clearly defined.

My strong default recommendation is:

- Use **PostgreSQL for structured business data and state**
- Use **S3 for files, extracts, raw drops, archives, large artifacts, and audit snapshots**
- Avoid trying to force everything into only one of them

In other words: **do not frame this as S3 _or_ Postgres unless your workloads are unusually simple**. In most enterprise Python pipelines, the right answer is **both, with clear boundaries**.

---

#### 1. The Core Decision: S3 vs PostgreSQL

##### Recommended decision rule

Use **PostgreSQL** when the data is:

- relational
- queried by key, date, account, status, or other dimensions
- updated incrementally
- used for joins / filtering / downstream application logic
- subject to data quality constraints
- part of an operational workflow
- needed for concurrency-safe reads/writes
- required to support auditability at the row/state-transition level

Use **S3** when the data is:

- naturally a file or blob
- an inbound/outbound artifact (CSV, XLSX, PDF, Parquet, JSON, email attachment, report)
- append-only or immutable
- large and rarely updated in place
- used for archival / replay / backfill / raw landing
- a convenient interchange boundary between systems
- something users still genuinely need in file form

##### Practical enterprise recommendation

For your case, I would generally model the future state as:

- **Postgres**
  - canonical operational data
  - reference/config tables previously represented in Excel
  - run metadata
  - job status / control tables
  - normalized or well-defined denormalized business entities
  - email-recipient/config tables
  - migration reconciliation tables

- **S3**
  - raw file drops from legacy processes
  - exported reports
  - copies of original Excel inputs
  - bulk snapshots
  - backfill payloads
  - artifacts that need retention
  - large staged inputs/outputs between jobs when file format still makes sense

##### Anti-pattern to avoid

Do **not** simply replace “shared drive Excel files” with “S3 Excel files” and call the migration complete unless there is a strong business reason those files must remain files. That usually preserves the same fragility with better infrastructure.

A better pattern is:

- treat Excel as an **ingest format**, not a system of record
- parse and validate into **Postgres tables**
- generate Excel only as an **output artifact** when humans actually need it

---

#### 2. Decision Matrix

| Question | Lean PostgreSQL | Lean S3 |
|---|---|---|
| Do you query subsets of the data often? | Yes | No |
| Do multiple jobs depend on consistent current state? | Yes | No |
| Do you need joins, constraints, transactions? | Yes | No |
| Is the source fundamentally a file artifact? | Sometimes | Yes |
| Do users need the original file preserved? | Optional | Yes |
| Is it a large immutable dump/snapshot? | Sometimes | Yes |
| Do you need row-level lineage / validation? | Yes | No |
| Is the current Excel mainly standing in for tables? | Yes | No |

If many current Excel files are really “poor man’s tables,” move them to **Postgres**.

If some current Excel files are really “deliverables” or “externally supplied artifacts,” keep them in **S3** and optionally materialize parsed contents into **Postgres** too.

---

#### 3. Suggested Target Architecture

##### Control plane

- **Airflow** for orchestration
- **Git-based DAG deployment**
- **EKS** for containerized task execution
- **Secrets Manager / Kubernetes secrets / IRSA-based access**
- **CloudWatch / Splunk / central logging** for logs and alerts

##### Data plane

- **Postgres** for operational state and structured business data
- **S3** for file/object storage
- Optional:
  - **SES** or existing SMTP relay for outbound email
  - **Lambda only where it is clearly useful**, not because Airflow requires it
  - **SQS/EventBridge** later if event-driven triggers become useful

##### Workload execution pattern

Each legacy job becomes:

1. extract / receive input
2. validate
3. persist to target storage
4. transform
5. publish outputs
6. send email / notifications
7. write run metadata and status

---

#### 4. Airflow Thoughts for Your Situation

##### Does Airflow require Lambda?

No. Airflow does **not** require Lambda.

For your setup, the more natural fit is usually:

- **Airflow running on Kubernetes / EKS**
- tasks executed as Python tasks or containerized jobs
- optionally launching dedicated pods per task for isolation

Lambda can still be useful for very small auxiliary tasks, but it is not the default answer for Python batch pipelines with dependencies, file movement, validation, database I/O, and email sending.

##### What likely fits best

You likely want one of these:

###### Option A: Self-managed Airflow on EKS
Best if:

- your team is already comfortable with EKS/Kubernetes
- you want full control
- you already operate platform components in-cluster
- custom dependencies/images are common

###### Option B: Amazon MWAA
Best if:

- you want less operational burden for Airflow itself
- you can live within the managed service shape
- your org prefers managed services over operating Airflow directly

###### My default lean for you

Because you already operate EKS and seem comfortable with containerized Python services, **Airflow on EKS is a very reasonable default**, especially if your jobs already package cleanly into Docker images.

That said, if your team does **not** want another stateful platform to own, **MWAA is worth serious consideration**.

---

#### 5. Migration Strategy: The Safest Way

##### Phase 0: Inventory and classify everything

Before touching storage, create a migration inventory.

For each application/job, document:

- current AutoSys job name / schedule / dependencies
- script entrypoint
- source inputs
- output files/tables/emails
- shared-drive paths used
- Excel files read
- Excel files written
- downstream consumers
- SLA / runtime / frequency
- retry behavior
- idempotency characteristics
- secrets used
- environment-specific behavior
- failure notification behavior
- data retention expectations

Also classify each file as one of:

- **reference/config**
- **raw input**
- **working/intermediate**
- **output/report**
- **archive**
- **user-maintained spreadsheet**
- **system-generated spreadsheet pretending to be a table**

This inventory will make the S3/Postgres decision much clearer.

##### Phase 1: Define target contracts, not just target infrastructure

For each dataset/job boundary, define:

- authoritative source
- schema
- required validations
- freshness expectations
- retry behavior
- idempotency key
- backfill strategy
- ownership

This is the point where many teams save months of pain. Migrating unclear job boundaries into Airflow just recreates legacy ambiguity in a nicer UI.

##### Phase 2: Add dual-write to current on-prem production

Your idea here is very good.

While the on-prem pipeline still runs under AutoSys:

- keep existing shared-drive outputs intact
- add **S3 put** and/or **Postgres insert/upsert**
- add run logging around both
- compare old and new outputs
- do not yet change downstream consumers unless necessary

Important: dual-write only works safely if the writes are designed to be idempotent.

Examples:

- S3 key naming includes run date / partition / version
- Postgres uses `INSERT ... ON CONFLICT ... DO UPDATE` where appropriate
- each run has a unique `run_id`
- reconciliation checks compare row counts/hashes/business aggregates

##### Phase 3: Build cloud-native readers first

Before cutting over the whole pipeline:

- build cloud-native consumers that read from Postgres/S3
- validate they reproduce the same business result
- run them in parallel on a feature branch or shadow mode

This reduces cutover risk dramatically.

##### Phase 4: Replace orchestration

Only after storage and job contracts are stable:

- translate `.jil` schedules/dependencies into Airflow DAGs
- preserve dependency semantics explicitly
- keep tasks small and observable
- avoid giant PythonOperators that hide all logic in one step

##### Phase 5: Controlled cutover

Cut over in this order:

1. cloud writes in parallel
2. cloud reads in shadow mode
3. primary consumers switch to cloud storage
4. orchestration switches from AutoSys to Airflow
5. shared-drive writes downgraded to fallback only
6. shared-drive dependency removed

##### Phase 6: Decommission legacy paths

Only after:

- reconciliation passes over multiple cycles
- support playbooks are updated
- rollback plan exists
- downstream consumers are confirmed

---

#### 6. Strong Recommendation: Use a “Bronze / Silver / Gold” Data Mindset Even If You Do Not Call It That

A simple pattern:

##### Bronze
- raw source files exactly as received
- stored in S3
- immutable
- timestamped / versioned

##### Silver
- parsed, cleaned, validated structured data
- stored in Postgres
- standardized schema
- business rules applied

##### Gold
- curated outputs for applications, reports, emails, APIs
- could live in Postgres, S3, or both depending on consumer needs

This helps avoid conflating “input artifact preservation” with “operational truth.”

---

#### 7. What to Do About Excel Specifically

##### Split Excel use cases into 3 buckets

###### A. Excel as human-maintained configuration
Examples:

- mappings
- thresholds
- distribution lists
- exceptions
- business overrides

Recommendation:

- move to **Postgres-backed config tables** with admin tooling later
- in the short term, allow controlled upload of Excel → validation → Postgres load
- preserve original file in S3

###### B. Excel as system-generated intermediate data
Recommendation:

- eliminate this
- replace with Postgres tables or Parquet/CSV in S3 as appropriate

###### C. Excel as final user deliverable
Recommendation:

- keep generating it if users genuinely need it
- write generated files to S3
- optionally email link/attachment
- do not use the output workbook as the next job’s source of truth

---

#### 8. Postgres Design Guidance

##### Use Postgres for operational truth, but design it intentionally

Good practices:

- separate schemas by domain / app if helpful
- use proper primary keys
- add unique constraints that support idempotent upserts
- track `created_at`, `updated_at`, `run_id`, `source_file`, `source_version`
- distinguish current-state tables vs historical tables
- make soft-delete / active flags explicit where needed
- store original raw payload references for traceability

##### Common table patterns

###### Reference/config tables
- relatively small
- business-managed
- may come from spreadsheets initially

###### Staging tables
- one load/run at a time
- used for validation and reconciliation
- truncated/partitioned as appropriate

###### Current-state tables
- latest active state used by applications

###### History/audit tables
- append-only or slowly changing
- critical for migration validation and rollback confidence

##### Avoid

- giant JSONB dumping-ground designs unless the data is truly semi-structured
- over-normalization that makes simple batch processes painful
- under-modeling business keys

---

#### 9. S3 Design Guidance

##### Treat S3 as an object store with conventions

Use consistent key structure, for example:

`app_name/dataset/env/YYYY/MM/DD/run_id/file_name.ext`

or

`domain/dataset/version=1/business_date=YYYY-MM-DD/run_id=.../artifact.parquet`

##### Recommended S3 usage

- raw inbound files
- source Excel preservation
- generated reports
- backfill drops
- manifests/checksums
- large extracts
- archival snapshots

##### Add these from day 1

- bucket versioning where appropriate
- lifecycle rules
- SSE encryption
- clear naming conventions
- metadata or manifest files for lineage
- checksum/hash logging for important files

---

#### 10. Airflow DAG Design Principles for This Migration

##### Make tasks represent business boundaries

Good task boundaries:

- fetch input
- validate input
- load staging
- transform/load target
- produce report
- send email
- publish success marker

Bad task boundary:

- one monolithic Python function that does all of the above

##### Favor idempotent tasks

A rerun should not create corrupt duplication or inconsistent state.

Use:

- deterministic partitions
- upserts
- run IDs
- “already processed?” checks
- write temp then promote patterns for files

##### Separate orchestration from business logic

Airflow should orchestrate, not contain all the logic.

Preferred pattern:

- reusable Python package / CLI / container
- Airflow task invokes a clear entrypoint
- the same code can be run locally, in tests, or by Airflow

##### Support backfills explicitly

Every job should define:

- business date
- run date
- partition/date-range arguments
- replay behavior
- overwrite vs merge semantics

---

#### 11. Translating AutoSys/.jil to Airflow

##### Do not do a 1:1 mechanical translation blindly

AutoSys jobs often encode years of operational behavior implicitly. Before converting, extract:

- schedule semantics
- dependency semantics
- calendars/holiday logic
- retries
- timeout expectations
- notification rules
- late-arrival handling
- manual rerun procedures

##### What to preserve explicitly in Airflow

- start conditions
- task dependencies
- SLAs / alerts
- environment-specific parameters
- calendars
- concurrency limits
- timeouts
- catchup/backfill behavior

##### Good migration pattern

For each `.jil` job:

1. document current behavior
2. define the equivalent DAG/task graph
3. dry-run in lower environment
4. compare runtime/output behavior
5. cut over one family of jobs at a time

---

#### 12. EKS Execution Model Recommendation

##### Recommended shape

- Airflow scheduler/webserver/triggerer as platform components
- task execution in isolated pods or containers
- shared Python base image(s) per app family
- environment config via secrets/configmaps/IRSA
- logs centralized outside the pod lifecycle

##### Why this fits your environment

Your team already works with EKS and containerized Python services. That lowers adoption risk compared with introducing an entirely new compute model just for orchestration.

##### Where Lambda may still help

Only for narrow cases like:

- tiny utility triggers
- lightweight API/webhook adapters
- very short event-driven tasks
- auxiliary control-plane glue

It is not the natural home for heavier Python batch jobs that do file parsing, DB I/O, pandas work, or longer-running transformations.

---

#### 13. Email Sender Scripts in the Future State

##### Treat email as an output step, not embedded side-effect chaos

Standardize email sending:

- one library/module for email composition
- one strategy for transport
- one config source for recipients
- one template system if needed
- attachments or links generated deterministically

##### Better pattern

Instead of many ad hoc scripts:

- generate output artifact
- persist artifact metadata
- send email via standard utility
- log success/failure in Postgres
- keep recipient config in table/config, not hardcoded in scripts

##### For attachments

Prefer:

- attach small files only if necessary
- otherwise include S3-hosted link or internal distribution link
- store a copy of the sent artifact and message metadata

---

#### 14. Testing Strategy for the Migration

##### You need 4 testing layers

###### 1. Unit tests
For:

- parsing
- transformations
- validation logic
- email composition
- path/key generation
- schema mapping

###### 2. Integration tests
For:

- Postgres reads/writes
- S3 upload/download
- Airflow task entrypoints
- secret/config wiring

###### 3. Reconciliation tests
Most important for migration:

- old vs new row counts
- hash totals
- business aggregates
- sampled record diffs
- generated file comparisons

###### 4. Operational tests
For:

- reruns
- partial failure recovery
- duplicate-trigger protection
- backfills
- concurrent runs
- timeout/retry behavior

##### Golden rule

For migration work, **reconciliation tests are often more important than pure unit-test coverage**.

---

#### 15. Observability and Supportability

##### Add run metadata early

Have a central run log table with fields like:

- `run_id`
- `job_name`
- `business_date`
- `start_ts`
- `end_ts`
- `status`
- `row_count_in`
- `row_count_out`
- `file_count_in`
- `file_count_out`
- `source_ref`
- `error_message`
- `orchestrator` (autosys / airflow)
- `env`

##### Capture enough metadata to answer:

- what ran?
- what inputs were used?
- what outputs were produced?
- was this a rerun?
- did counts materially differ from baseline?
- can I replay it?
- who was notified?

##### Alerts

At minimum, alert on:

- task failure
- missing inputs
- validation failure
- row-count anomaly
- email send failure
- SLA breach

---

#### 16. Security / Access Model

##### Remove shared-drive assumptions completely

Legacy code often assumes:

- direct filesystem access
- broad inherited permissions
- static service-account credentials
- path-based security

In cloud, standardize around:

- IAM roles / IRSA
- least privilege
- secret rotation
- bucket/table/schema-specific access
- auditable service identities

##### Specific things to check during refactor

- hardcoded UNC paths
- hardcoded usernames/passwords
- implicit local temp-file dependencies
- assumptions about Excel COM / desktop execution
- scripts relying on mapped drives or Windows scheduler quirks

---

#### 17. Refactoring Pattern for the Python Apps

##### Split each app into layers

A good target structure:

###### domain layer
- business rules
- transformations
- validation

###### infrastructure layer
- S3 repository
- Postgres repository
- email client
- config loader

###### orchestration layer
- CLI / job entrypoint
- Airflow task wrapper

This makes the same logic reusable across:

- local runs
- AutoSys current state
- Airflow future state
- tests

##### Recommended short-term interface pattern

Introduce interfaces/adapters like:

- `InputRepository`
- `OutputRepository`
- `ConfigRepository`
- `NotificationService`

Then provide implementations such as:

- `SharedDriveInputRepository`
- `S3InputRepository`
- `PostgresConfigRepository`
- `SmtpNotificationService`

That lets you migrate incrementally without rewriting everything at once.

---

#### 18. A Practical “Both Sides Live at Once” Pattern

This is probably the highest-leverage implementation shape for you.

##### Current state
- AutoSys orchestrates
- app reads shared drive
- app writes shared drive
- email sent

##### Transitional state
- AutoSys still orchestrates
- app reads legacy source
- app writes legacy output
- app also writes Postgres and/or S3
- reconciliation step runs
- email sent
- downstream cloud readers validate in shadow mode

##### Future state
- Airflow orchestrates
- app reads Postgres/S3
- app writes Postgres/S3
- report artifacts written to S3
- email sent from standardized module
- shared drive retired

---

#### 19. How to Decide “S3-first” vs “Postgres-first” Per App

##### Pick Postgres-first when
- Excel is effectively a table
- downstream jobs read slices/subsets
- multiple jobs share current state
- correctness matters more than preserving exact file layout
- you expect APIs/UI/processes to consume the data later

##### Pick S3-first when
- the app is mostly file transfer / report generation
- files are the real artifact
- preserving exact original files matters
- the next step is still human/manual consumption
- the data is large but not operationally queried much

##### Pick hybrid when
- you need both file preservation and structured consumption

This hybrid case will be common.

---

#### 20. Rollback Planning

Every migration workstream should define rollback before cutover.

##### Minimum rollback questions

- if Airflow orchestration fails, can AutoSys resume?
- if Postgres load succeeds but downstream transform fails, what is rerun behavior?
- if S3 artifact writes succeed twice, do consumers break?
- if email sends before commit, can users receive false signals?
- can a failed cloud run be replayed from preserved raw input?

##### Good rollback pattern

- raw inputs preserved in S3
- target writes are idempotent/upsert-safe
- cutover is feature-flagged
- orchestration can temporarily point back to legacy path
- clear distinction between shadow runs and authoritative runs

---

#### 21. Suggested Work Plan

##### Workstream 1: Discovery / inventory
Deliverables:

- job inventory
- file inventory
- dependency map
- classification of each Excel/file usage

##### Workstream 2: Storage decision + standards
Deliverables:

- S3 conventions
- Postgres schema standards
- naming/versioning/idempotency standards
- run metadata model

##### Workstream 3: Refactor shared libraries
Deliverables:

- storage adapters
- email utility
- config/secrets loader
- validation framework
- reconciliation utilities

##### Workstream 4: Dual-write implementation in on-prem prod
Deliverables:

- safe dual-write
- row/file reconciliation
- monitoring

##### Workstream 5: Cloud-native execution
Deliverables:

- Docker images
- EKS runtime config
- Airflow DAGs
- lower-env validation

##### Workstream 6: Cutover and decommission
Deliverables:

- runbook
- rollback plan
- support handoff
- retirement of shared-drive dependencies

---

#### 22. Concrete Recommendation for Your Team

If I were guiding this effort, I would recommend the following default policy:

##### Default policy

- **Postgres is the system of record for structured operational data**
- **S3 is the system of record for raw files and generated artifacts**
- **Excel is not a system of record**
- **Airflow orchestrates; business logic lives in Python packages/CLIs**
- **EKS is the primary compute substrate**
- **Lambda is optional utility glue, not the backbone**
- **Dual-write + reconciliation is mandatory before cutover**
- **Every migrated job must be idempotent and replayable**

##### Why this is the right bias

It reduces:

- shared-drive coupling
- Excel fragility
- poor observability
- painful reruns
- hidden dependencies
- lock-in to legacy filesystem semantics

And it increases:

- testability
- replayability
- cloud portability
- auditability
- operational clarity
- future extensibility

---

#### 23. Risks to Watch Closely

##### Biggest technical risks

- migrating path/file assumptions without redesigning data contracts
- preserving Excel too deep into the architecture
- lack of idempotency in dual-write
- insufficient reconciliation
- monolithic Airflow tasks
- unclear ownership of config/reference data
- underestimating schedule/dependency semantics hidden in `.jil`
- not standardizing email behavior
- weak observability around cutover

##### Biggest organizational risks

- trying to migrate orchestration and storage and code structure all at once
- doing app-by-app rewrites without common migration standards
- allowing each team member to invent their own S3/DB conventions
- cutting over before shadow validation proves equivalence

---

#### 24. Final Bottom Line

For your situation, the most robust approach is:

1. **Inventory and classify every shared-drive/Excel dependency**
2. **Adopt a hybrid storage model: Postgres for structured state, S3 for files/artifacts**
3. **Add dual-write to the current on-prem AutoSys production flow**
4. **Refactor Python apps around storage/email abstractions**
5. **Build cloud-native Airflow + EKS execution against those new abstractions**
6. **Shadow, reconcile, cut over, and only then retire shared-drive dependencies**

If you do this well, you will not just “move jobs to the cloud”; you will remove the underlying architectural weakness that made the shared-drive model painful in the first place.

---

#### 25. Small Appendix: Quick Answers to the Specific Questions You Raised

##### “Should we use S3 and keep the file-based approach or go entirely to Postgres?”
Usually **neither extreme**. Use:

- **Postgres for structured operational truth**
- **S3 for file artifacts and raw/archive layers**

##### “Should we put S3 put/Postgres insert logic into the on-prem production pipeline first?”
Yes. That is one of the safest ways to migrate, provided:

- writes are idempotent
- reconciliation is built in
- legacy outputs remain unchanged during validation

##### “Does Airflow require Lambdas?”
No. For your team, **Airflow on EKS** or **MWAA** is the more natural framing.

##### “What about apps with an email sender script at the end?”
Standardize email as a reusable service/module and treat it as a final task in the workflow, with logging and deterministic artifacts.

---

### Claude:

#### Context & Assumptions

- **Current state**: Python apps on-prem, orchestrated via AutoSys (`.jil` files), reading/writing Excel files on a shared network drive.
- **Target state**: Apps containerized on EKS, orchestrated by a modern scheduler, file-based I/O replaced with cloud-native storage.
- **Constraints**: Migration must not disrupt on-prem production. Dual-write period required.
- **Team**: Small (3 people) — operational complexity matters.

---

#### 1. Storage Decision: S3 vs. Postgres (vs. Both)

This isn't binary. The right answer depends on *what the Excel files actually represent*.

##### Use Postgres When:
- The data is **tabular and queried relationally** (joins, filters, aggregations).
- Downstream consumers need **partial reads** (e.g., "give me just the rows for strategy X").
- You need **transactional guarantees** (ACID) — e.g., a portfolio snapshot that must be atomically consistent.
- Multiple apps read/write the **same logical dataset**.
- You want to eliminate parsing logic (openpyxl/xlrd) from every consumer.

##### Use S3 When:
- The file is a **report artifact** — something generated, stored, and later retrieved whole (e.g., a PDF, a client-facing Excel, a CSV dump).
- The data is **large and append-only** (e.g., tick data, logs).
- You need to **preserve the original file format** for compliance or audit trail.
- The consumer is a human or an external system that expects a file.

##### Recommended Hybrid Pattern
```
┌─────────────────────────────────────────────────────┐
│  Python App                                         │
│                                                     │
│  Structured data (positions, signals, weights)      │
│       → Postgres (via SQLAlchemy / asyncpg)         │
│                                                     │
│  Report artifacts (client Excel, PDF tearsheets)    │
│       → S3 (via boto3)                              │
│                                                     │
│  Raw inputs that must be preserved as-is            │
│       → S3 (with metadata tags for lineage)         │
└─────────────────────────────────────────────────────┘
```

##### Postgres Specifics
- Use **RDS Postgres** (not Aurora) unless you need multi-AZ read replicas — RDS is simpler and cheaper for your scale.
- Use **SQLAlchemy Core** (not ORM) for insert/query — you're doing data engineering, not web app modeling.
- Schema-per-domain is cleaner than one big schema. E.g., `signals.*`, `portfolio.*`, `reporting.*`.
- For time-series-heavy workloads, consider the `timescaledb` extension on RDS.

##### S3 Specifics
- Use a consistent key convention: `s3://{bucket}/{app_name}/{run_date}/{filename}`.
- Enable **versioning** on the bucket — it's free insurance.
- Use **Parquet** instead of CSV/Excel for any machine-consumed tabular data on S3. It's columnar, compressed, and pandas/polars read it natively.
- Tag objects with metadata: `run_id`, `git_sha`, `environment`.

---

#### 2. The Dual-Write Migration Strategy

This is the key architectural insight: **add cloud writes to the existing on-prem pipeline first, then migrate consumers.**

##### Phase 1: Dual-Write (On-Prem Stays Primary)
```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  AutoSys      │────▶│  Python App      │────▶│  Network     │
│  (unchanged)  │     │  (modified)      │     │  Drive       │
└──────────────┘     │                  │     └──────────────┘
                     │  + new code:     │
                     │  ├─ S3 put       │────▶  S3
                     │  └─ PG insert    │────▶  Postgres
                     └──────────────────┘
```

Implementation guidance:

- **Wrap the new writes in try/except.** Cloud write failures should log and alert but NOT fail the on-prem job during this phase. The network drive is still the source of truth.
- **Add a reconciliation check**: after each run, compare row counts / checksums between the network drive file and the cloud target. Log discrepancies.
- **Use a feature flag** (even a simple env var `CLOUD_WRITE_ENABLED=true`) so you can toggle this per-app without redeploying.
```python
import os
import logging

logger = logging.getLogger(__name__)

def write_results(df, legacy_path, s3_key=None, pg_table=None):
    """Write to legacy network drive, optionally dual-write to cloud."""
    ## Legacy write (always)
    df.to_excel(legacy_path, index=False)

    if os.getenv("CLOUD_WRITE_ENABLED", "false").lower() == "true":
        if s3_key:
            try:
                _write_to_s3(df, s3_key)
            except Exception:
                logger.exception(f"S3 write failed for {s3_key}")

        if pg_table:
            try:
                _write_to_postgres(df, pg_table)
            except Exception:
                logger.exception(f"Postgres write failed for {pg_table}")
```

##### Phase 2: Cloud Consumer Development (Feature Branch)

- Build the cloud version of each app on a feature branch.
- The cloud version reads from S3/Postgres instead of the network drive.
- Run both in parallel. Compare outputs. This is your integration test.

##### Phase 3: Cutover

- Flip the orchestrator from AutoSys to Airflow/Prefect/CronJob.
- The cloud app is now primary. The network drive write can be removed (or kept temporarily for rollback comfort).
- Decommission on-prem jobs one by one.

---

#### 3. Orchestration: Airflow vs. Prefect vs. EKS CronJobs

##### Option A: Airflow on EKS (Helm Chart + KubernetesExecutor)

**How it works**: Airflow scheduler and webserver run as persistent deployments on EKS. Each task in a DAG spins up an ephemeral pod (KubernetesExecutor). You do NOT need Lambdas.

**Pros**:

- Industry standard. Huge ecosystem of operators and providers.
- Excellent for complex DAGs with branching, retries, SLAs, and cross-DAG dependencies.
- Good visibility via the web UI (Gantt charts, task logs, run history).

**Cons**:

- Operationally heavy for a 3-person team. The Airflow metadata DB (Postgres), scheduler, webserver, and workers all need care and feeding.
- DAG authoring has a learning curve. The execution model (DAG parsing, XComs, task serialization) has real gotchas.
- Helm chart upgrades can be painful.

**Verdict**: Probably overkill for your current team size and workload, but correct if you expect significant growth in workflow complexity or team size within 12 months.

##### Option B: Self-Hosted Prefect on EKS ← Recommended

**How it works**: Prefect server (or Prefect Cloud — free tier is generous) provides the UI, scheduling, and API. A Prefect worker runs on EKS and picks up scheduled flow runs, executing them as Kubernetes Jobs.

**Pros**:

- Flows are just decorated Python functions. No DAG parsing quirks.
- The Kubernetes worker pattern is clean: each flow run = a K8s Job with its own pod.
- Much lighter operationally than Airflow. The server is a single container + Postgres.
- Native support for retries, caching, parameterized runs, notifications.
- If you use Prefect Cloud, you eliminate the self-hosted server entirely and just run the worker on EKS.

**Cons**:

- Smaller community than Airflow (though growing fast).
- If self-hosting, you still need to run Prefect server + its Postgres DB.
- Cross-flow dependencies are doable but less elegant than Airflow's DAG-level tooling.

**Self-hosted deployment sketch** (Helm on EKS):
```yaml
### prefect-server: Deployment
### - image: prefecthq/prefect:3-python3.11
### - command: prefect server start --host 0.0.0.0
### - requires: Postgres (RDS or in-cluster)
### - expose via internal ALB or ClusterIP

### prefect-worker: Deployment
### - image: prefecthq/prefect:3-python3.11
### - command: prefect worker start --pool default --type kubernetes
### - needs RBAC to create Jobs in the target namespace
```

**Prefect flow example**:
```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=2, retry_delay_seconds=30)
def extract_data(source: str) -> pd.DataFrame:
    ...

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def transform(df: pd.DataFrame) -> pd.DataFrame:
    ...

@task
def load_to_postgres(df: pd.DataFrame, table: str):
    ...

@task
def send_completion_email(recipients: list[str], report_s3_key: str):
    ...

@flow(name="daily-portfolio-pipeline", log_prints=True)
def daily_pipeline(run_date: str):
    raw = extract_data("s3://bucket/inputs/...")
    transformed = transform(raw)
    load_to_postgres(transformed, "portfolio.daily_snapshot")
    send_completion_email(["team@invesco.com"], "s3://bucket/reports/...")
```

##### Option C: EKS CronJobs

**How it works**: Kubernetes-native CronJob resources. Each job is a pod that runs on a schedule.

**Pros**:

- Zero additional infrastructure. It's built into Kubernetes.
- Dead simple for single-step scheduled tasks.
- You already know K8s.

**Cons**:

- No UI for monitoring (unless you add something like k9s or a dashboard).
- Multi-step workflows require manual chaining (e.g., Job A triggers Job B via a script or by hitting an API). This gets messy fast.
- No built-in retry with backoff, alerting, or run history.
- Cross-job dependencies are DIY.

**Verdict**: Good for simple "run this script at 6am" jobs. Not suitable as your primary orchestrator if you have multi-step workflows with dependencies — which you do, per your description of the AutoSys setup.

##### Recommendation

**Start with Prefect Cloud** (free tier: 3 users, unlimited flows). Deploy a single Kubernetes worker on EKS. This gives you:

- Near-zero ops overhead (no self-hosted server to manage).
- A proper UI for monitoring and debugging.
- Native K8s Job execution.
- A path to self-hosting later if you outgrow the free tier or need data residency.

If Prefect Cloud is a non-starter due to compliance (data leaving the VPC), self-host Prefect server on EKS backed by your RDS Postgres instance.

---

#### 4. Handling the Email Sender Scripts

Common pattern: the last step in many of your pipelines sends an email with results/reports.

##### Options (in order of preference)

1. **Amazon SES (Simple Email Service)**: Cheapest, most reliable for transactional email from within AWS. Use the `boto3` SES client. You'll need to verify sender domains/addresses.

2. **SMTP relay via your existing Exchange/O365**: If Invesco has an internal SMTP relay, you can keep using `smtplib` — just update the SMTP host and ensure EKS pods can reach it (VPC peering or transit gateway to corp network).

3. **Prefect notifications**: Prefect has built-in notification blocks (email, Slack, Teams). Good for "pipeline succeeded/failed" alerts. Less suitable for rich HTML reports with attachments.

##### Migration approach for email steps
```python
### Abstract the email sending behind an interface so you can swap implementations
from abc import ABC, abstractmethod

class EmailSender(ABC):
    @abstractmethod
    def send(self, to: list[str], subject: str, body: str,
             attachments: list[str] | None = None): ...

class SESEmailSender(EmailSender):
    def send(self, to, subject, body, attachments=None):
        ## boto3 SES implementation
        ...

class SMTPEmailSender(EmailSender):
    def send(self, to, subject, body, attachments=None):
        ## smtplib implementation (legacy)
        ...

### Factory based on environment
def get_email_sender() -> EmailSender:
    if os.getenv("EMAIL_BACKEND", "smtp") == "ses":
        return SESEmailSender()
    return SMTPEmailSender()
```

---

#### 5. Containerization Checklist

For each Python app being migrated:

- [ ] **Dockerfile**: Multi-stage build. Use `python:3.11-slim` as the runtime base. Pin all dependency versions.
- [ ] **Dependencies**: Freeze with `pip-compile` (pip-tools) or `uv`. Do not rely on `pip install -r requirements.txt` with unpinned versions.
- [ ] **Configuration**: All environment-specific config (DB connection strings, S3 bucket names, email recipients) via environment variables. Use Kubernetes Secrets for credentials, ConfigMaps for non-sensitive config.
- [ ] **Logging**: Structured JSON logging to stdout. EKS + CloudWatch Logs or Fluent Bit will handle collection.
- [ ] **Health checks**: Not needed for batch jobs (they run to completion). But if any app is a long-running service, add liveness/readiness probes.
- [ ] **Resource requests/limits**: Set CPU and memory requests based on profiling the on-prem runs. Start conservative and adjust.

##### Dockerfile template
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
ENTRYPOINT ["python", "main.py"]
```

---

#### 6. Migration Sequencing

Don't migrate everything at once. Prioritize by a combination of business impact and technical simplicity.

##### Suggested ordering heuristic

| Priority | Characteristics | Example |
|----------|----------------|---------|
| **Wave 1** | Simple (single-step, no downstream dependents), low business risk | Internal monitoring scripts, data quality checks |
| **Wave 2** | Multi-step but well-understood, moderate business importance | Daily portfolio snapshot pipelines |
| **Wave 3** | Complex DAGs, many dependencies, high business criticality | End-of-day processing, client reporting |

For each app in each wave:

1. Add dual-write logic (Phase 1).
2. Deploy to EKS on feature branch. Run in parallel with on-prem for 1–2 weeks.
3. Compare outputs (automated reconciliation).
4. Cut over orchestration.
5. Monitor for 1 week.
6. Decommission on-prem job.

---

#### 7. Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Network drive data differs from cloud copy during dual-write | Automated reconciliation checks after each run; alert on mismatch |
| EKS pod can't reach on-prem resources during transition | VPC peering / transit gateway to corp network; test connectivity early |
| Credential management across on-prem and cloud | AWS Secrets Manager + External Secrets Operator for K8s; rotate on cutover |
| Team bandwidth (3 people, ongoing BAU + migration) | Wave-based approach; don't parallelize waves; timebox each wave |
| Rollback needed after cutover | Keep on-prem AutoSys jobs dormant (not deleted) for 30 days post-cutover |

---

#### 8. Quick Reference: AutoSys → Prefect Mapping

| AutoSys Concept | Prefect Equivalent |
|----------------|-------------------|
| `.jil` job definition | `@flow` decorated Python function |
| Box job (container for sub-jobs) | Flow containing multiple `@task` calls |
| `condition: success(job_a)` | Task dependencies via return values (Prefect handles this natively) |
| `start_times` | Prefect schedule (cron, interval, or RRule) |
| `std_out_file` / `std_err_file` | Prefect UI logs (stdout captured automatically) |
| `alarm_if_fail` | Prefect automations (trigger notifications on failure) |
| `profile` / `owner` | Work pool + deployment labels |
| Machine/agent targeting | Kubernetes work pool with node selectors |