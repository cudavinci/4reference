# Cloud Migration Framework for Python Apps: Shared Drive / Excel → S3 or PostgreSQL, AutoSys/.jil → Airflow, On-Prem → EKS

## Executive Summary

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

# 1. The Core Decision: S3 vs PostgreSQL

## Recommended decision rule

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

## Practical enterprise recommendation

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

## Anti-pattern to avoid

Do **not** simply replace “shared drive Excel files” with “S3 Excel files” and call the migration complete unless there is a strong business reason those files must remain files. That usually preserves the same fragility with better infrastructure.

A better pattern is:

- treat Excel as an **ingest format**, not a system of record
- parse and validate into **Postgres tables**
- generate Excel only as an **output artifact** when humans actually need it

---

# 2. Decision Matrix

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

# 3. Suggested Target Architecture

## Control plane

- **Airflow** for orchestration
- **Git-based DAG deployment**
- **EKS** for containerized task execution
- **Secrets Manager / Kubernetes secrets / IRSA-based access**
- **CloudWatch / Splunk / central logging** for logs and alerts

## Data plane

- **Postgres** for operational state and structured business data
- **S3** for file/object storage
- Optional:
  - **SES** or existing SMTP relay for outbound email
  - **Lambda only where it is clearly useful**, not because Airflow requires it
  - **SQS/EventBridge** later if event-driven triggers become useful

## Workload execution pattern

Each legacy job becomes:

1. extract / receive input
2. validate
3. persist to target storage
4. transform
5. publish outputs
6. send email / notifications
7. write run metadata and status

---

# 4. Airflow Thoughts for Your Situation

## Does Airflow require Lambda?

No. Airflow does **not** require Lambda.

For your setup, the more natural fit is usually:

- **Airflow running on Kubernetes / EKS**
- tasks executed as Python tasks or containerized jobs
- optionally launching dedicated pods per task for isolation

Lambda can still be useful for very small auxiliary tasks, but it is not the default answer for Python batch pipelines with dependencies, file movement, validation, database I/O, and email sending.

## What likely fits best

You likely want one of these:

### Option A: Self-managed Airflow on EKS
Best if:

- your team is already comfortable with EKS/Kubernetes
- you want full control
- you already operate platform components in-cluster
- custom dependencies/images are common

### Option B: Amazon MWAA
Best if:

- you want less operational burden for Airflow itself
- you can live within the managed service shape
- your org prefers managed services over operating Airflow directly

### My default lean for you

Because you already operate EKS and seem comfortable with containerized Python services, **Airflow on EKS is a very reasonable default**, especially if your jobs already package cleanly into Docker images.

That said, if your team does **not** want another stateful platform to own, **MWAA is worth serious consideration**.

---

# 5. Migration Strategy: The Safest Way

## Phase 0: Inventory and classify everything

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

## Phase 1: Define target contracts, not just target infrastructure

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

## Phase 2: Add dual-write to current on-prem production

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

## Phase 3: Build cloud-native readers first

Before cutting over the whole pipeline:

- build cloud-native consumers that read from Postgres/S3
- validate they reproduce the same business result
- run them in parallel on a feature branch or shadow mode

This reduces cutover risk dramatically.

## Phase 4: Replace orchestration

Only after storage and job contracts are stable:

- translate `.jil` schedules/dependencies into Airflow DAGs
- preserve dependency semantics explicitly
- keep tasks small and observable
- avoid giant PythonOperators that hide all logic in one step

## Phase 5: Controlled cutover

Cut over in this order:

1. cloud writes in parallel
2. cloud reads in shadow mode
3. primary consumers switch to cloud storage
4. orchestration switches from AutoSys to Airflow
5. shared-drive writes downgraded to fallback only
6. shared-drive dependency removed

## Phase 6: Decommission legacy paths

Only after:

- reconciliation passes over multiple cycles
- support playbooks are updated
- rollback plan exists
- downstream consumers are confirmed

---

# 6. Strong Recommendation: Use a “Bronze / Silver / Gold” Data Mindset Even If You Do Not Call It That

A simple pattern:

## Bronze
- raw source files exactly as received
- stored in S3
- immutable
- timestamped / versioned

## Silver
- parsed, cleaned, validated structured data
- stored in Postgres
- standardized schema
- business rules applied

## Gold
- curated outputs for applications, reports, emails, APIs
- could live in Postgres, S3, or both depending on consumer needs

This helps avoid conflating “input artifact preservation” with “operational truth.”

---

# 7. What to Do About Excel Specifically

## Split Excel use cases into 3 buckets

### A. Excel as human-maintained configuration
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

### B. Excel as system-generated intermediate data
Recommendation:

- eliminate this
- replace with Postgres tables or Parquet/CSV in S3 as appropriate

### C. Excel as final user deliverable
Recommendation:

- keep generating it if users genuinely need it
- write generated files to S3
- optionally email link/attachment
- do not use the output workbook as the next job’s source of truth

---

# 8. Postgres Design Guidance

## Use Postgres for operational truth, but design it intentionally

Good practices:

- separate schemas by domain / app if helpful
- use proper primary keys
- add unique constraints that support idempotent upserts
- track `created_at`, `updated_at`, `run_id`, `source_file`, `source_version`
- distinguish current-state tables vs historical tables
- make soft-delete / active flags explicit where needed
- store original raw payload references for traceability

## Common table patterns

### Reference/config tables
- relatively small
- business-managed
- may come from spreadsheets initially

### Staging tables
- one load/run at a time
- used for validation and reconciliation
- truncated/partitioned as appropriate

### Current-state tables
- latest active state used by applications

### History/audit tables
- append-only or slowly changing
- critical for migration validation and rollback confidence

## Avoid

- giant JSONB dumping-ground designs unless the data is truly semi-structured
- over-normalization that makes simple batch processes painful
- under-modeling business keys

---

# 9. S3 Design Guidance

## Treat S3 as an object store with conventions

Use consistent key structure, for example:

`app_name/dataset/env/YYYY/MM/DD/run_id/file_name.ext`

or

`domain/dataset/version=1/business_date=YYYY-MM-DD/run_id=.../artifact.parquet`

## Recommended S3 usage

- raw inbound files
- source Excel preservation
- generated reports
- backfill drops
- manifests/checksums
- large extracts
- archival snapshots

## Add these from day 1

- bucket versioning where appropriate
- lifecycle rules
- SSE encryption
- clear naming conventions
- metadata or manifest files for lineage
- checksum/hash logging for important files

---

# 10. Airflow DAG Design Principles for This Migration

## Make tasks represent business boundaries

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

## Favor idempotent tasks

A rerun should not create corrupt duplication or inconsistent state.

Use:

- deterministic partitions
- upserts
- run IDs
- “already processed?” checks
- write temp then promote patterns for files

## Separate orchestration from business logic

Airflow should orchestrate, not contain all the logic.

Preferred pattern:

- reusable Python package / CLI / container
- Airflow task invokes a clear entrypoint
- the same code can be run locally, in tests, or by Airflow

## Support backfills explicitly

Every job should define:

- business date
- run date
- partition/date-range arguments
- replay behavior
- overwrite vs merge semantics

---

# 11. Translating AutoSys/.jil to Airflow

## Do not do a 1:1 mechanical translation blindly

AutoSys jobs often encode years of operational behavior implicitly. Before converting, extract:

- schedule semantics
- dependency semantics
- calendars/holiday logic
- retries
- timeout expectations
- notification rules
- late-arrival handling
- manual rerun procedures

## What to preserve explicitly in Airflow

- start conditions
- task dependencies
- SLAs / alerts
- environment-specific parameters
- calendars
- concurrency limits
- timeouts
- catchup/backfill behavior

## Good migration pattern

For each `.jil` job:

1. document current behavior
2. define the equivalent DAG/task graph
3. dry-run in lower environment
4. compare runtime/output behavior
5. cut over one family of jobs at a time

---

# 12. EKS Execution Model Recommendation

## Recommended shape

- Airflow scheduler/webserver/triggerer as platform components
- task execution in isolated pods or containers
- shared Python base image(s) per app family
- environment config via secrets/configmaps/IRSA
- logs centralized outside the pod lifecycle

## Why this fits your environment

Your team already works with EKS and containerized Python services. That lowers adoption risk compared with introducing an entirely new compute model just for orchestration.

## Where Lambda may still help

Only for narrow cases like:

- tiny utility triggers
- lightweight API/webhook adapters
- very short event-driven tasks
- auxiliary control-plane glue

It is not the natural home for heavier Python batch jobs that do file parsing, DB I/O, pandas work, or longer-running transformations.

---

# 13. Email Sender Scripts in the Future State

## Treat email as an output step, not embedded side-effect chaos

Standardize email sending:

- one library/module for email composition
- one strategy for transport
- one config source for recipients
- one template system if needed
- attachments or links generated deterministically

## Better pattern

Instead of many ad hoc scripts:

- generate output artifact
- persist artifact metadata
- send email via standard utility
- log success/failure in Postgres
- keep recipient config in table/config, not hardcoded in scripts

## For attachments

Prefer:

- attach small files only if necessary
- otherwise include S3-hosted link or internal distribution link
- store a copy of the sent artifact and message metadata

---

# 14. Testing Strategy for the Migration

## You need 4 testing layers

### 1. Unit tests
For:

- parsing
- transformations
- validation logic
- email composition
- path/key generation
- schema mapping

### 2. Integration tests
For:

- Postgres reads/writes
- S3 upload/download
- Airflow task entrypoints
- secret/config wiring

### 3. Reconciliation tests
Most important for migration:

- old vs new row counts
- hash totals
- business aggregates
- sampled record diffs
- generated file comparisons

### 4. Operational tests
For:

- reruns
- partial failure recovery
- duplicate-trigger protection
- backfills
- concurrent runs
- timeout/retry behavior

## Golden rule

For migration work, **reconciliation tests are often more important than pure unit-test coverage**.

---

# 15. Observability and Supportability

## Add run metadata early

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

## Capture enough metadata to answer:

- what ran?
- what inputs were used?
- what outputs were produced?
- was this a rerun?
- did counts materially differ from baseline?
- can I replay it?
- who was notified?

## Alerts

At minimum, alert on:

- task failure
- missing inputs
- validation failure
- row-count anomaly
- email send failure
- SLA breach

---

# 16. Security / Access Model

## Remove shared-drive assumptions completely

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

## Specific things to check during refactor

- hardcoded UNC paths
- hardcoded usernames/passwords
- implicit local temp-file dependencies
- assumptions about Excel COM / desktop execution
- scripts relying on mapped drives or Windows scheduler quirks

---

# 17. Refactoring Pattern for the Python Apps

## Split each app into layers

A good target structure:

### domain layer
- business rules
- transformations
- validation

### infrastructure layer
- S3 repository
- Postgres repository
- email client
- config loader

### orchestration layer
- CLI / job entrypoint
- Airflow task wrapper

This makes the same logic reusable across:

- local runs
- AutoSys current state
- Airflow future state
- tests

## Recommended short-term interface pattern

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

# 18. A Practical “Both Sides Live at Once” Pattern

This is probably the highest-leverage implementation shape for you.

## Current state
- AutoSys orchestrates
- app reads shared drive
- app writes shared drive
- email sent

## Transitional state
- AutoSys still orchestrates
- app reads legacy source
- app writes legacy output
- app also writes Postgres and/or S3
- reconciliation step runs
- email sent
- downstream cloud readers validate in shadow mode

## Future state
- Airflow orchestrates
- app reads Postgres/S3
- app writes Postgres/S3
- report artifacts written to S3
- email sent from standardized module
- shared drive retired

---

# 19. How to Decide “S3-first” vs “Postgres-first” Per App

## Pick Postgres-first when
- Excel is effectively a table
- downstream jobs read slices/subsets
- multiple jobs share current state
- correctness matters more than preserving exact file layout
- you expect APIs/UI/processes to consume the data later

## Pick S3-first when
- the app is mostly file transfer / report generation
- files are the real artifact
- preserving exact original files matters
- the next step is still human/manual consumption
- the data is large but not operationally queried much

## Pick hybrid when
- you need both file preservation and structured consumption

This hybrid case will be common.

---

# 20. Rollback Planning

Every migration workstream should define rollback before cutover.

## Minimum rollback questions

- if Airflow orchestration fails, can AutoSys resume?
- if Postgres load succeeds but downstream transform fails, what is rerun behavior?
- if S3 artifact writes succeed twice, do consumers break?
- if email sends before commit, can users receive false signals?
- can a failed cloud run be replayed from preserved raw input?

## Good rollback pattern

- raw inputs preserved in S3
- target writes are idempotent/upsert-safe
- cutover is feature-flagged
- orchestration can temporarily point back to legacy path
- clear distinction between shadow runs and authoritative runs

---

# 21. Suggested Work Plan

## Workstream 1: Discovery / inventory
Deliverables:

- job inventory
- file inventory
- dependency map
- classification of each Excel/file usage

## Workstream 2: Storage decision + standards
Deliverables:

- S3 conventions
- Postgres schema standards
- naming/versioning/idempotency standards
- run metadata model

## Workstream 3: Refactor shared libraries
Deliverables:

- storage adapters
- email utility
- config/secrets loader
- validation framework
- reconciliation utilities

## Workstream 4: Dual-write implementation in on-prem prod
Deliverables:

- safe dual-write
- row/file reconciliation
- monitoring

## Workstream 5: Cloud-native execution
Deliverables:

- Docker images
- EKS runtime config
- Airflow DAGs
- lower-env validation

## Workstream 6: Cutover and decommission
Deliverables:

- runbook
- rollback plan
- support handoff
- retirement of shared-drive dependencies

---

# 22. Concrete Recommendation for Your Team

If I were guiding this effort, I would recommend the following default policy:

## Default policy

- **Postgres is the system of record for structured operational data**
- **S3 is the system of record for raw files and generated artifacts**
- **Excel is not a system of record**
- **Airflow orchestrates; business logic lives in Python packages/CLIs**
- **EKS is the primary compute substrate**
- **Lambda is optional utility glue, not the backbone**
- **Dual-write + reconciliation is mandatory before cutover**
- **Every migrated job must be idempotent and replayable**

## Why this is the right bias

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

# 23. Risks to Watch Closely

## Biggest technical risks

- migrating path/file assumptions without redesigning data contracts
- preserving Excel too deep into the architecture
- lack of idempotency in dual-write
- insufficient reconciliation
- monolithic Airflow tasks
- unclear ownership of config/reference data
- underestimating schedule/dependency semantics hidden in `.jil`
- not standardizing email behavior
- weak observability around cutover

## Biggest organizational risks

- trying to migrate orchestration and storage and code structure all at once
- doing app-by-app rewrites without common migration standards
- allowing each team member to invent their own S3/DB conventions
- cutting over before shadow validation proves equivalence

---

# 24. Final Bottom Line

For your situation, the most robust approach is:

1. **Inventory and classify every shared-drive/Excel dependency**
2. **Adopt a hybrid storage model: Postgres for structured state, S3 for files/artifacts**
3. **Add dual-write to the current on-prem AutoSys production flow**
4. **Refactor Python apps around storage/email abstractions**
5. **Build cloud-native Airflow + EKS execution against those new abstractions**
6. **Shadow, reconcile, cut over, and only then retire shared-drive dependencies**

If you do this well, you will not just “move jobs to the cloud”; you will remove the underlying architectural weakness that made the shared-drive model painful in the first place.

---

# 25. Small Appendix: Quick Answers to the Specific Questions You Raised

## “Should we use S3 and keep the file-based approach or go entirely to Postgres?”
Usually **neither extreme**. Use:

- **Postgres for structured operational truth**
- **S3 for file artifacts and raw/archive layers**

## “Should we put S3 put/Postgres insert logic into the on-prem production pipeline first?”
Yes. That is one of the safest ways to migrate, provided:

- writes are idempotent
- reconciliation is built in
- legacy outputs remain unchanged during validation

## “Does Airflow require Lambdas?”
No. For your team, **Airflow on EKS** or **MWAA** is the more natural framing.

## “What about apps with an email sender script at the end?”
Standardize email as a reusable service/module and treat it as a final task in the workflow, with logging and deterministic artifacts.

---