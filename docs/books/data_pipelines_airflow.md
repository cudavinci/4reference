# Book7 - Data Pipelines with Apache Airflow — 2nd Edition (Manning, 2026)

> **Context:** On-prem JIL/Autosys orchestration migrating to cloud. Current state uses Excel files on slow shared network drives. Future state: S3 or Postgres for data, Airflow (MWAA or EKS) for orchestration. 1.5-month refactoring window.

---

## Part 1 — Getting Started

---

### Chapter 1: Meet Apache Airflow

#### 1.1 Introducing Data Pipelines

- **Data pipeline**: a sequence of tasks that must execute in a defined order to achieve a result (e.g., fetch → clean → load)
- **DAG (Directed Acyclic Graph)**: the core abstraction — tasks are nodes, dependencies are directed edges, and cycles are forbidden
  - Directed = edges have direction (A must finish before B)
  - Acyclic = no circular dependencies (prevents deadlocks)
- **Execution algorithm** (3-step loop):
  1. For each incomplete task, check if all upstream tasks are done
  2. If so, add to execution queue
  3. Execute queued tasks; repeat until all complete
- DAGs enable **parallel execution** naturally — independent branches run simultaneously without explicit threading logic
- **Workflow managers** (alternatives): Dagster, Prefect, Luigi, Argo, Temporal, ControlM. Airflow is the most widely adopted open-source option.

**See Figure 1.3 for DAG vs. cyclic graph visualization**

#### 1.2 Introducing Airflow

- Pipelines defined in **Python code** (not XML/YAML like Oozie or JIL)
- Five core components:

| Component | Role |
|-----------|------|
| **DAG Processor** | Reads `.py` DAG files, serializes to metastore |
| **Scheduler** | Checks schedules, queues tasks when dependencies met |
| **Workers** | Execute queued tasks |
| **Triggerer** | Handles deferred/async tasks |
| **API Server** | Web UI + REST API; gateway to metastore |

- **Web UI** provides: DAG list, graph view (dependency visualization), grid view (historical run matrix), task logs, manual trigger/clear controls
- Supports **incremental loading** and **backfilling** natively

**See Figure 1.8 for architecture diagram, Figure 1.9 for full execution flow**

#### 1.3 When to Use Airflow

- **Good fit**: batch-oriented ETL/ELT, scheduled data processing, ML pipelines, orchestrating external services
- **Not ideal for**: real-time streaming (use Kafka/Flink), simple single-step cron jobs, non-technical users who can't write Python

#### Autosys → Airflow Mental Model

| Autosys/JIL | Airflow |
|-------------|---------|
| JIL job definition | Python DAG file |
| `condition: s(prev_job)` | `prev_task >> next_task` |
| Autosys scheduler | Airflow scheduler + executor |
| `autorep -j` / `sendevent` | Web UI + REST API |
| `.jil` files | `.py` files in `dags/` folder |

---

### Chapter 2: Anatomy of an Airflow DAG

#### 2.1 Collecting Data from Numerous Sources

- Real-world example: fetching rocket launch images from an API, downloading them, and notifying users

#### 2.2 Writing Your First Airflow DAG

**Two main DAG definition styles:**

```python
# Style 1: Context manager (recommended)
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import pendulum

with DAG(
    dag_id="my_pipeline",
    start_date=pendulum.datetime(2025, 1, 1),
    schedule="@daily",
):
    fetch = BashOperator(
        task_id="fetch_data",
        bash_command="curl -o /tmp/data.json https://api.example.com/data",
    )

    process = PythonOperator(
        task_id="process_data",
        python_callable=my_processing_function,
    )

    fetch >> process  # dependency: fetch before process
```

```python
# Style 2: Taskflow API (modern, decorator-based — see Ch 6)
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2025, 1, 1))
def my_pipeline():
    @task
    def fetch():
        ...
    @task
    def process(data):
        ...
    process(fetch())

my_pipeline()
```

##### 2.2.1 Tasks vs. Operators

- **Operator** = abstract class defining *what* work is done (e.g., `BashOperator`, `PythonOperator`, `S3CopyObjectOperator`)
- **Task** = wrapper around an operator managing *how* it's scheduled, retried, and tracked
- Common operators: `BashOperator`, `PythonOperator`, `EmailOperator`, `SQLExecuteQueryOperator`, plus hundreds of provider-specific operators

##### 2.2.2 Running Arbitrary Python Code

```python
def _get_pictures():
    # Any Python logic here — read files, call APIs, transform data
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
    for launch in launches["results"]:
        response = requests.get(launch["image"])
        with open(f"/tmp/images/{launch['id']}.jpg", "wb") as img:
            img.write(response.content)

get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable=_get_pictures,
)
```

#### 2.3 Running a DAG in Airflow

```bash
# Quick local setup
pip install apache-airflow
airflow standalone  # starts all services, creates admin user
# UI at http://localhost:8080 (airflow/airflow)

# Docker setup (recommended for team consistency)
docker compose up
```

#### 2.4 Running at Regular Intervals

- Set `schedule` parameter: `"@daily"`, `"@hourly"`, cron string, `timedelta`, or `None` (manual only)
- Set `start_date` and optionally `end_date` to bound the schedule window

#### 2.5 Handling Failing Tasks

- Failed tasks appear red in the UI graph/grid views
- Click failed task → view logs (full stdout/stderr captured) → fix issue → **Clear Task Instance** to rerun
- Options when clearing: upstream, downstream, past, future, only-failed
- No need to restart the entire pipeline — Airflow reruns from the failure point

#### 2.6 DAG Versioning

- Airflow 3 automatically tracks DAG code changes
- Historical DAG structures viewable via UI dropdown
- Foundation for safe backfills (run historical data against the code version that existed at that time)

---

### Chapter 3: Time-Based Scheduling

#### 3.1 Processing User Events

- Use case: website event tracking API that stores only 30 days of data → need daily download + stats calculation
- Demonstrates why scheduling with date-awareness matters

#### 3.2 The Basic Components of an Airflow Schedule

| Parameter | Required | Description |
|-----------|----------|-------------|
| `start_date` | Yes | Earliest possible execution |
| `end_date` | No | Stop scheduling after this date |
| `schedule` | Yes | When to run (cron, preset, timedelta, `None`) |
| `catchup` | No | Execute missed past runs (default `False` in Airflow 3) |

- **`catchup=True`**: If `start_date` is in the past, Airflow creates runs for every missed interval
- **`catchup=False`** (Airflow 3 default): Only future runs execute

#### 3.3 Running Regularly Using Trigger-Based Schedules

##### 3.3.2 Cron Expressions

```
# ┌─── minute (0-59)
# │ ┌─── hour (0-23)
# │ │ ┌─── day of month (1-31)
# │ │ │ ┌─── month (1-12)
# │ │ │ │ ┌─── day of week (0-6, Sun=0)
# * * * * *

"0 0 * * *"       # Daily at midnight
"0 0 * * MON-FRI" # Weekdays at midnight
"0 9,17 * * *"    # 9am and 5pm daily
"*/15 * * * *"    # Every 15 minutes
```

##### 3.3.3 Shorthand Presets

| Preset | Equivalent Cron |
|--------|----------------|
| `@hourly` | `0 * * * *` |
| `@daily` | `0 0 * * *` |
| `@weekly` | `0 0 * * 0` |
| `@monthly` | `0 0 1 * *` |
| `@yearly` | `0 0 1 1 *` |

##### 3.3.4 Frequency-Based Timetables

```python
# For patterns cron can't express (e.g., every 2 days):
from datetime import timedelta
schedule = timedelta(days=2)
```

#### 3.4 Incremental Processing with Data Intervals

- Each scheduled run has an implicit **data interval** (`data_interval_start` → `data_interval_end`)
- Tasks should process only data from their interval, not the entire dataset
- Use Jinja templating to parameterize by date:

```python
fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "curl -o /data/events/{{ logical_date | ds }}.json "
        "'http://events-api:8001/events?date={{ logical_date | ds }}'"
    ),
)
```

#### 3.5 Handling Irregular Intervals

- Custom timetable classes for non-standard schedules (e.g., business days only, market hours)

#### 3.6 Managing Backfilling of Historical Data

- `catchup=True` + historical `start_date` = automatic backfill
- CLI: `airflow dags backfill -s 2025-01-01 -e 2025-03-01 my_dag`
- ⚠️ Be cautious with large date ranges — can spawn hundreds of concurrent runs

#### 3.7 Designing Well-Behaved Tasks

- **Atomicity**: Task either fully succeeds or fully fails (no partial writes). Use temp files + atomic rename, or database transactions.
- **Idempotency**: Running the same task twice with the same inputs produces the same result. Critical for reruns/backfills. Strategies:
  - Overwrite output files (not append)
  - Use `INSERT ... ON CONFLICT DO UPDATE` for database writes
  - Include execution date in output paths for partitioning

---

### Chapter 4: Asset-Aware Scheduling

#### 4.1 Challenges of Scaling Time-Based Schedules

- Problem: multiple teams fetch the same data independently → duplicated work, inconsistent results, API overload
- Time-based coupling: downstream DAGs scheduled N minutes after upstream "should" finish → fragile

#### 4.2 Introducing Asset-Aware Scheduling

- **Asset**: a virtual reference to a data dependency, identified by URI (e.g., `s3://bucket/data.csv`, `postgres://db/table`)
- **Producer DAG**: updates the asset (has `outlets=[asset]` on the writing task)
- **Consumer DAG**: triggered when the asset is updated (has `schedule=[asset]`)
- Decouples producers from consumers — no hardcoded timing or job names

**See Figure 4.2 for producer/consumer pattern diagram**

#### 4.3 Producing Asset Events

```python
from airflow.sdk import Asset

events_dataset = Asset("s3://my-bucket/events/daily.json")

fetch_events = PythonOperator(
    task_id="fetch_events",
    python_callable=_fetch_events,
    outlets=[events_dataset],  # declares this task updates the asset
)
```

#### 4.4 Consuming Asset Events

```python
with DAG(
    dag_id="stats_consumer",
    schedule=[events_dataset],  # triggers when asset is updated
    start_date=pendulum.datetime(2025, 1, 1),
):
    calculate_stats = PythonOperator(...)
```

#### 4.5 Adding Extra Information to Events

```python
from airflow.sdk import Metadata

def _fetch_events(**context):
    # ... fetch data ...
    yield Metadata(events_dataset, extra={"row_count": len(data), "date": "2025-01-15"})
```

#### 4.6 Skipping Updates

```python
from airflow.exceptions import AirflowSkipException

def _fetch_events(output_path, **context):
    if Path(output_path).exists():
        raise AirflowSkipException()  # no asset event emitted → consumer not triggered
    # ... fetch data ...
```

#### 4.7 Consuming Multiple Assets

```python
# Wait for ALL assets to update (AND logic):
schedule = [asset_1, asset_2]

# Boolean logic:
schedule = (asset_1 | (asset_2 & asset_3))  # asset_1 OR (asset_2 AND asset_3)
```

#### 4.8 Combining Time- and Asset-Based Schedules

- Assets can work alongside time-based triggers for hybrid scheduling

#### Migration Relevance

> **Autosys parallel**: Autosys "conditions" (e.g., `condition: s(upstream_job)`) are conceptually similar but tightly coupled by job name. Assets decouple by data URI — the consumer doesn't know or care which DAG produced the data.
>
> **For your S3 migration**: Define assets as S3 URIs. On-prem producer DAGs write to S3 + emit asset events. Cloud consumer DAGs trigger automatically when S3 data lands.

---

### Chapter 5: Templating Tasks Using the Airflow Context

#### 5.1 Inspecting Data for Processing with Airflow

- Use case: downloading Wikipedia pageview data where the URL contains the execution date/hour

#### 5.2 Task Context and Jinja Templating

- **Jinja templating**: `{{ variable }}` syntax replaced at runtime with actual values
- Works in any operator argument that is a **templated field** (check operator docs)

##### 5.2.1 Templating Operator Arguments

```python
# BashOperator — bash_command is a templated field
download = BashOperator(
    task_id="download",
    bash_command=(
        "curl -o /tmp/pageviews-{{ logical_date.strftime('%Y%m%d-%H') }}.gz "
        "'https://dumps.wikimedia.org/other/pageviews/"
        "{{ logical_date.year }}/{{ logical_date.year }}-"
        "{{ '{:02d}'.format(logical_date.month) }}/...'"
    ),
)
```

##### 5.2.2 Templating the PythonOperator

```python
# PythonOperator receives context as **kwargs automatically
def _process_data(**context):
    logical_date = context["logical_date"]
    start = context["data_interval_start"]
    end = context["data_interval_end"]
    print(f"Processing data for {start} to {end}")

process = PythonOperator(
    task_id="process",
    python_callable=_process_data,
)
```

##### 5.2.3 Passing Additional Variables to the PythonOperator

```python
# op_kwargs supports Jinja templating too
process = PythonOperator(
    task_id="process",
    python_callable=_process_data,
    op_kwargs={
        "input_path": "/data/{{ logical_date | ds }}.json",
        "output_path": "/data/stats/{{ logical_date | ds }}.csv",
    },
)
```

##### 5.2.4 Inspecting Templated Arguments

```bash
# CLI tool to see rendered template values without running the task
airflow tasks render my_dag my_task 2025-04-24T00:00:00
```

Also viewable in the Web UI under the task's "Rendered Template" tab.

#### 5.3 What Is Available for Templating

| Variable | Type | Description |
|----------|------|-------------|
| `logical_date` | `pendulum.DateTime` | The logical execution date |
| `data_interval_start` | `pendulum.DateTime` | Start of the data interval |
| `data_interval_end` | `pendulum.DateTime` | End of the data interval |
| `ds` | `str` | `logical_date` as `YYYY-MM-DD` |
| `ts` | `str` | `logical_date` as ISO 8601 |
| `dag` | `DAG` | Reference to the current DAG |
| `dag_run` | `DagRun` | Current DAG run metadata |
| `task_instance` | `TaskInstance` | Current task instance (for XCom) |
| `params` | `dict` | User-supplied parameters |
| `macros` | module | Utility functions (`macros.ds_add(ds, 7)`, etc.) |

#### 5.4 Bringing It All Together

```python
# Full example: download Wikipedia data, extract top pages, write to Postgres
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

write_to_postgres = SQLExecuteQueryOperator(
    task_id="write_to_postgres",
    conn_id="my_postgres",                    # connection stored in Airflow
    sql="postgres_query.sql",                 # external SQL file (also templated)
    template_searchpath="/tmp",
)
```

```bash
# Store database credentials in Airflow (not in code)
airflow connections add \
    --conn-type postgres \
    --conn-host localhost \
    --conn-login postgres \
    --conn-password mysecretpassword \
    my_postgres
```

#### Migration Relevance

> **Replaces JIL variable expansion**: Autosys uses `${AUTODATE}`, `${AUTORUNS}`. Airflow's `{{ logical_date }}`, `{{ ds }}`, `{{ data_interval_start }}` are far more powerful and Pythonic.

---

### Chapter 6: Defining Dependencies Between Tasks

#### 6.1 Basic Dependencies

```python
# Linear: A → B → C
fetch >> clean >> load

# Fan-out: one task triggers multiple parallel tasks
fetch_weather >> clean_weather
fetch_sales >> clean_sales

# Fan-in: multiple tasks feed into one
[clean_weather, clean_sales] >> join_datasets >> train_model
```

#### 6.2 Branching

##### 6.2.2 Branching Within the DAG

```python
from airflow.operators.python import BranchPythonOperator

def _pick_source(**context):
    if context["data_interval_start"] < ERP_MIGRATION_DATE:
        return "fetch_from_old_system"
    return "fetch_from_new_system"

pick_source = BranchPythonOperator(
    task_id="pick_source",
    python_callable=_pick_source,
)
pick_source >> [fetch_from_old_system, fetch_from_new_system]
```

- Non-selected branches are **skipped** (not failed)
- Downstream tasks need `trigger_rule="none_failed"` to run after branching

#### 6.3 Conditional Tasks

```python
from airflow.operators.latest_only import LatestOnlyOperator

# Only deploy model on the most recent run (skip during backfills)
latest_only = LatestOnlyOperator(task_id="latest_only")
latest_only >> deploy_model
```

#### 6.4 Exploring Trigger Rules

| Rule | Fires When | Use Case |
|------|-----------|----------|
| `all_success` (default) | All parents succeeded | Normal flow |
| `all_failed` | All parents failed | Error-only handlers |
| `all_done` | All parents finished (any state) | Cleanup/teardown |
| `one_failed` | ≥1 parent failed | Early alert |
| `one_success` | ≥1 parent succeeded | Race condition / first-wins |
| `none_failed` | No parent failed (skipped OK) | After branching |
| `none_skipped` | No parent skipped | All-branches-required |
| `always` | Regardless | Monitoring/logging |

#### 6.5 Sharing Data Between Tasks

##### 6.5.1 XComs (Cross-Communication)

```python
# Push (explicit)
def _train(**context):
    model_id = str(uuid.uuid4())
    context["task_instance"].xcom_push(key="model_id", value=model_id)

# Pull
def _deploy(**context):
    model_id = context["task_instance"].xcom_pull(
        task_ids="train_model", key="model_id"
    )
```

##### 6.5.2 When (Not) to Use XComs

- ✅ Small values: IDs, file paths, row counts, status flags
- ❌ Large data: DataFrames, files, images → use S3/Postgres instead
- XComs are stored in the metastore database — keep them small

#### 6.6 Chaining Python Tasks with the Taskflow API

```python
from airflow.sdk import task, dag

@dag(schedule="@daily", start_date=pendulum.datetime(2025, 1, 1))
def my_ml_pipeline():

    @task
    def train_model():
        model_id = str(uuid.uuid4())
        # ... training logic ...
        return model_id  # automatically pushed as XCom

    @task
    def deploy_model(model_id: str):
        print(f"Deploying {model_id}")

    # Dependencies + XCom passing inferred automatically
    deploy_model(train_model())

my_ml_pipeline()
```

- `@task` decorator replaces `PythonOperator` + manual XCom push/pull
- Return values are automatically XCom-pushed; function arguments are auto-pulled
- Use when DAG is mostly Python; mix with traditional operators as needed

---

## Part 2 — Beyond the Basics

---

### Chapter 7: Triggering Workflows with External Input

#### 7.1 Polling Conditions with Sensors

- **Sensor**: a special operator that repeatedly checks ("pokes") a condition until it's true or times out
- **Poke interval**: seconds between checks (default 60)
- **Timeout**: max wait time (default 7 days)

```python
from airflow.providers.standard.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id="wait_for_file",
    filepath="/data/incoming/daily_extract.csv",
    poke_interval=300,       # check every 5 minutes
    timeout=3600,            # give up after 1 hour
    mode="reschedule",       # release worker slot between pokes
)
```

##### 7.1.1 Custom Sensors

```python
from airflow.providers.standard.sensors.python import PythonSensor

def _check_data_ready(source_id):
    path = Path(f"/data/{source_id}")
    return (path / "_SUCCESS").exists() and list(path.glob("data-*.csv"))

wait = PythonSensor(
    task_id="wait_for_data",
    python_callable=_check_data_ready,
    op_kwargs={"source_id": "source_a"},
    timeout=timedelta(minutes=30),
)
```

##### 7.1.2 Sensor Modes and Deadlock Prevention

- **`mode="poke"` (default)**: sensor holds a worker slot the entire time → can cause **deadlock** if all slots occupied by waiting sensors
- **`mode="reschedule"`**: releases worker slot between pokes → prevents deadlock
- **Deferrable operators**: even better — yield control to the triggerer process, consuming zero worker slots while waiting
- Always set `max_active_tasks` on sensor-heavy DAGs as a safety net

**See Figure 7.8 for sensor deadlock visualization**

#### 7.2 Starting Workflows with the REST API and CLI

```bash
# CLI trigger
airflow dags trigger my_dag

# REST API trigger with configuration payload
curl -u airflow:airflow -X POST \
    "http://localhost:8080/api/v1/dags/my_dag/dagRuns" \
    -H "Content-Type: application/json" \
    -d '{"conf": {"source": "manual", "run_type": "full"}}'
```

```python
# Access trigger config inside a task
def _process(**context):
    config = context["dag_run"].conf
    source = config.get("source", "default")
```

#### 7.3 Triggering Workflows with Messages

```python
from airflow.providers.common.messaging.triggers.msg_queue import MessageQueueTrigger
from airflow.sdk import Asset, AssetWatcher

trigger = MessageQueueTrigger(
    queue="kafka://kafka:9092/events",
    apply_function="my_package.kafka_filter.should_trigger",
)

kafka_asset = Asset(
    "kafka_queue_asset",
    watchers=[AssetWatcher(name="kafka_watcher", trigger=trigger)],
)

with DAG(dag_id="event_driven_dag", schedule=[kafka_asset]):
    process = PythonOperator(...)
```

> **Migration relevance**: Replaces Autosys file-watcher jobs with sensors. REST API triggering replaces `sendevent -E FORCE_STARTJOB`. Kafka triggering enables true event-driven orchestration without polling.

---

### Chapter 8: Communicating with External Systems

#### 8.1 Installing Additional Operators

```bash
# Provider packages for cloud services
pip install apache-airflow-providers-amazon      # S3, SageMaker, Redshift, etc.
pip install apache-airflow-providers-google       # GCS, BigQuery, Dataflow, etc.
pip install apache-airflow-providers-postgres     # PostgresOperator, PostgresHook
pip install apache-airflow-providers-cncf-kubernetes  # KubernetesPodOperator
```

#### 8.2 Developing a Machine Learning Model

- Example: MNIST digit classifier using SageMaker
- Pattern: upload training data to S3 → train with `SageMakerTrainingOperator` → deploy with `SageMakerEndpointOperator`

```python
from airflow.providers.amazon.aws.operators.sagemaker import (
    SageMakerTrainingOperator,
    SageMakerEndpointOperator,
)

train = SageMakerTrainingOperator(
    task_id="train_model",
    config={
        "TrainingJobName": "my-model-{{ logical_date | ts_nodash }}",
        "AlgorithmSpecification": {...},
        "InputDataConfig": [{"ChannelName": "train", "DataSource": {"S3DataSource": {...}}}],
        "OutputDataConfig": {"S3OutputPath": f"s3://{BUCKET}/output"},
        "ResourceConfig": {"InstanceType": "ml.c4.xlarge", "InstanceCount": 1, ...},
        "wait_for_completion": True,
    },
)
```

> ⚠️ **EKS note**: SageMaker operators are Lambda/API-based — they submit jobs to SageMaker, which runs on its own infrastructure. These work fine from both MWAA and EKS-hosted Airflow. No Lambda dependency.

#### 8.3 Moving Data Between Systems

##### 8.3.2 PostgresToS3Operator

```python
from airflow.providers.amazon.aws.transfers.postgres_to_s3 import PostgresToS3Operator

extract = PostgresToS3Operator(
    task_id="postgres_to_s3",
    postgres_conn_id="source_db",
    query="SELECT * FROM trades WHERE trade_date = '{{ ds }}'",
    s3_conn_id="aws_default",
    s3_bucket="my-data-lake",
    s3_key="raw/trades/{{ ds }}.csv",
)
```

##### 8.3.3 Outsourcing the Heavy Work

```python
from airflow.providers.docker.operators.docker import DockerOperator

crunch = DockerOperator(
    task_id="heavy_computation",
    image="my-registry/number-cruncher:latest",
    environment={"S3_BUCKET": "my-bucket", "DATE": "{{ ds }}"},
    network_mode="host",
    auto_remove="success",
)
```

- **Key principle**: Airflow orchestrates, it doesn't execute heavy computation. Offload to SageMaker, Spark, Docker containers, or Kubernetes pods.

---

### Chapter 9: Extending Airflow with Custom Operators and Sensors

#### 9.1 Starting with a PythonOperator

- Always start with `PythonOperator` for prototyping; refactor to custom operator when the pattern stabilizes

#### 9.2 Building a Custom Hook

- **Hook** = reusable class for connecting to an external service. Handles auth, sessions, connection caching.

```python
from airflow.hooks.base import BaseHook

class MyServiceHook(BaseHook):
    def __init__(self, conn_id: str):
        self._conn_id = conn_id
        self._session = None

    def get_conn(self):
        if self._session is None:
            config = self.get_connection(self._conn_id)  # reads from Airflow metastore
            self._session = requests.Session()
            self._session.auth = (config.login, config.password)
            self._base_url = f"{config.schema}://{config.host}:{config.port}"
        return self._session

    def get_data(self, start_date, end_date):
        session = self.get_conn()
        response = session.get(f"{self._base_url}/data?start={start_date}&end={end_date}")
        response.raise_for_status()
        return response.json()
```

#### 9.3 Building a Custom Operator

```python
from airflow.models import BaseOperator

class FetchAndStoreOperator(BaseOperator):
    template_fields = ("_start_date", "_end_date", "_output_path")  # Jinja-enabled fields

    def __init__(self, conn_id, start_date, end_date, output_path, **kwargs):
        super().__init__(**kwargs)
        self._conn_id = conn_id
        self._start_date = start_date
        self._end_date = end_date
        self._output_path = output_path

    def execute(self, context):
        hook = MyServiceHook(self._conn_id)
        data = hook.get_data(self._start_date, self._end_date)
        Path(self._output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._output_path, "w") as f:
            json.dump(data, f)
        self.log.info(f"Wrote {len(data)} records to {self._output_path}")
```

#### 9.4 Building Custom Sensors

```python
from airflow.sensors.base import BaseSensorOperator

class DataAvailableSensor(BaseSensorOperator):
    template_fields = ("_start_date", "_end_date")

    def __init__(self, conn_id, start_date, end_date, **kwargs):
        super().__init__(**kwargs)
        self._conn_id = conn_id
        self._start_date = start_date
        self._end_date = end_date

    def poke(self, context):
        hook = MyServiceHook(self._conn_id)
        try:
            data = hook.get_data(self._start_date, self._end_date)
            return len(data) > 0  # True = condition met, sensor completes
        except Exception:
            return False  # False = keep waiting
```

#### 9.5 Building a Custom Deferrable Operator

- For long-running tasks, yield to the **triggerer** to avoid holding worker slots
- Requires implementing a `Trigger` class and using `TaskDeferred` in the operator's `execute` method

#### 9.6 Packaging the Components

```
my_airflow_package/
├── hooks.py          # MyServiceHook
├── operators.py      # FetchAndStoreOperator
├── sensors.py        # DataAvailableSensor
├── __init__.py
└── setup.py          # for pip install
```

```bash
pip install -e ./my_airflow_package
# or add to MWAA requirements.txt
```

---

### Chapter 10: Testing

#### 10.1 Getting Started with Testing

##### 10.1.1 Integrity Testing All DAGs

```python
# tests/test_dag_integrity.py
import glob, os, pytest
from airflow.models import DagBag

DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "dags/**/*.py")
DAG_FILES = glob.glob(DAG_PATH, recursive=True)

@pytest.mark.parametrize("dag_file", DAG_FILES)
def test_dag_integrity(dag_file):
    """Verify DAGs parse without errors (no cycles, valid task IDs, etc.)."""
    dag_bag = DagBag(dag_folder=dag_file, include_examples=False)
    assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"
```

- Run this in CI on every PR — catches syntax errors, circular dependencies, and import failures before deployment

##### 10.1.2 Setting Up a CI/CD Pipeline

- Use GitHub Actions (or equivalent) with steps:
  1. Lint: `flake8`, `ruff check`
  2. Format: `black --check`
  3. Type check: `mypy`
  4. DAG integrity test: `pytest tests/test_dag_integrity.py`
  5. Unit tests: `pytest tests/`

#### 10.2 Working with External Systems

**Unit testing with mocks:**

```python
def test_my_operator(mocker):
    # Mock the hook so we don't need a real database
    mocker.patch.object(
        MyServiceHook, "get_connection",
        return_value=Connection(conn_id="test", login="user", password="pass"),
    )
    mocker.patch.object(
        MyServiceHook, "get_data",
        return_value=[{"id": 1, "value": 42}],
    )

    task = FetchAndStoreOperator(
        task_id="test", conn_id="test",
        start_date="2025-01-01", end_date="2025-01-02",
        output_path="/tmp/test_output.json",
    )
    task.execute(context={})
    assert Path("/tmp/test_output.json").exists()
```

**⚠️ Critical mocking rule**: Mock where the function is *called*, not where it's *defined*.

**Integration testing with real containers:**

```python
from pytest_docker_tools import fetch, container

postgres_image = fetch(repository="postgres:16-alpine")
postgres = container(
    image="{postgres_image.id}",
    environment={"POSTGRES_USER": "test", "POSTGRES_PASSWORD": "test"},
    ports={"5432/tcp": None},
)

def test_postgres_operator(postgres):
    port = postgres.ports["5432/tcp"][0]["HostPort"]
    # Run operator against real Postgres container
    # Assert results in the actual database
```

#### 10.3 Using Tests for Development

- Use `pytest` with breakpoints (`breakpoint()`) and IDE debuggers for interactive development
- Test individual operators with `task.execute(context={})` — no need for a running Airflow instance

#### 10.4 Testing Complete DAGs

```python
# dag.test() runs the entire DAG locally in a single process
from my_dags.pipeline import my_dag

my_dag.test(logical_date=datetime(2025, 1, 15, tzinfo=timezone.utc))
```

- **Whirl**: open-source tool for emulating production Airflow environments locally with Docker
- **DTAP pattern**: separate Development, Test, Acceptance, Production environments with corresponding Git branches

#### Testing Strategy Summary

| Layer | What | How | When |
|-------|------|-----|------|
| DAG integrity | Parse errors, cycles | `DagBag` import test | Every PR (CI) |
| Unit tests | Individual operators | `task.execute()` + mocks | Every PR (CI) |
| Integration tests | Operators + real systems | `pytest-docker-tools` | Nightly / pre-deploy |
| DAG-level tests | End-to-end pipeline | `dag.test()` or Whirl | Pre-deploy |

---

### Chapter 11: Running Tasks in Containers

#### 11.1 Challenges of Different Operators

- **Dependency conflicts**: DAG A needs `pandas==1.5`, DAG B needs `pandas==2.0` — can't have both in one Python environment
- **Solution**: run each task in its own container with isolated dependencies

#### 11.2 Introducing Containers

- **Container** = lightweight isolated process with its own filesystem, libraries, and binaries. Shares host kernel (much lighter than VMs).
- **Docker image** = immutable blueprint for containers
- **Dockerfile** = recipe for building an image

```dockerfile
FROM python:3.12-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY scripts/my_task.py /usr/local/bin/my-task
RUN chmod +x /usr/local/bin/my-task
ENTRYPOINT ["/usr/local/bin/my-task"]
CMD ["--help"]
```

#### 11.3 Containers and Airflow

- **Why containers?**
  - Dependency isolation per task
  - Uniform interface (all tasks are DockerOperator or KubernetesPodOperator)
  - Independent development and testing of task images
  - Reproducible builds via CI/CD

#### 11.4 Running Tasks in Docker

```python
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

fetch = DockerOperator(
    task_id="fetch_data",
    image="my-registry/data-fetcher:1.0",
    command=[
        "fetch-data",
        "--start-date", "{{ data_interval_start | ds }}",
        "--end-date", "{{ data_interval_end | ds }}",
        "--output-path", "/data/raw/{{ ds }}.json",
    ],
    mounts=[Mount(source="shared_data_volume", target="/data", type="volume")],
    network_mode="bridge",
    auto_remove="success",
)
```

**Docker workflow:**

1. Developer writes Dockerfile + task script
2. CI/CD builds image, pushes to registry (ECR)
3. DAG references image by tag
4. Worker pulls image, runs container, captures logs

**See Figure 11.9 for Docker CI/CD workflow diagram**

#### 11.5 Running Tasks in Kubernetes

##### 11.5.1-11.5.2 Kubernetes Basics

- **Pod**: smallest K8s unit (one or more containers)
- **Service**: stable network endpoint for pods
- **PersistentVolume (PV)** / **PersistentVolumeClaim (PVC)**: shared storage that survives pod restarts

```yaml
# PersistentVolumeClaim for shared task data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-data
  namespace: airflow
spec:
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 10Gi
  storageClassName: gp2  # or your EKS storage class
```

##### 11.5.3 Using the KubernetesPodOperator

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

volume = k8s.V1Volume(
    name="pipeline-data",
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="pipeline-data"),
)
volume_mount = k8s.V1VolumeMount(
    name="pipeline-data", mount_path="/data", read_only=False,
)

fetch = KubernetesPodOperator(
    task_id="fetch_data",
    image="123456789.dkr.ecr.us-east-1.amazonaws.com/data-fetcher:1.0",
    cmds=["fetch-data"],
    arguments=[
        "--start-date", "{{ data_interval_start | ds }}",
        "--end-date", "{{ data_interval_end | ds }}",
        "--output-path", "/data/raw/{{ ds }}.json",
    ],
    namespace="airflow",
    name="fetch-data-pod",
    volumes=[volume],
    volume_mounts=[volume_mount],
    image_pull_policy="Always",
    is_delete_operator_pod=True,  # cleanup after execution
    in_cluster=True,  # True when Airflow itself runs in K8s (EKS)
)
```

##### 11.5.4 Diagnosing Kubernetes-Related Issues

```bash
kubectl -n airflow get pods                    # list pods
kubectl -n airflow describe pod <pod-name>     # events, status, errors
kubectl -n airflow logs <pod-name>             # task stdout/stderr
```

##### DockerOperator vs KubernetesPodOperator

| Aspect | DockerOperator | KubernetesPodOperator |
|--------|---------------|----------------------|
| Runs on | Single Docker host | K8s cluster (multi-node) |
| Scaling | Limited to one machine | Automatic across cluster |
| Resource control | Basic | CPU/memory requests + limits |
| Data sharing | Docker volumes | PersistentVolumeClaims |
| Cleanup | Manual | `is_delete_operator_pod=True` |
| **Your use case** | Local dev | **Production on EKS** |

> ⚠️ **EKS note**: When Airflow itself runs on EKS (via MWAA or self-hosted), set `in_cluster=True`. KubernetesPodOperator creates pods in the same cluster. This is the native EKS pattern — no Lambdas involved.

---

## Part 3 — Airflow in Practice

---

### Chapter 12: Best Practices

#### 12.1 Writing Clean DAGs

##### 12.1.1 Using Style Conventions

```bash
# Enforce consistent style across your team
pip install ruff     # fast linter + formatter (replaces flake8 + black)
ruff check dags/     # lint
ruff format dags/    # auto-format
```

##### 12.1.2 Managing Credentials Centrally

```python
# NEVER hardcode credentials in DAG files
# Use Airflow connections (stored encrypted in metastore)
from airflow.hooks.base import BaseHook

def _fetch_data(conn_id, **context):
    creds = BaseHook.get_connection(conn_id)
    # creds.host, creds.login, creds.password, creds.port, etc.
```

##### 12.1.3 Specifying Configuration Details Consistently

```python
# Option A: Airflow Variables (stored in metastore, editable via UI)
from airflow.sdk import Variable
input_path = Variable.get("pipeline_input_path")

# Option B: YAML config file
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

##### 12.1.4 Avoiding Computation in Your DAG Definition

```python
# ❌ BAD: this runs every time the DAG file is parsed (every few seconds!)
result = expensive_api_call()
task = PythonOperator(op_kwargs={"data": result}, ...)

# ✅ GOOD: computation deferred to task execution time
def _my_task():
    result = expensive_api_call()
    # ... process result ...

task = PythonOperator(python_callable=_my_task, ...)
```

##### Using Factories to Generate Common Patterns

```python
def create_etl_tasks(source_name, dag):
    """Factory function generating fetch → transform → load for any source."""
    fetch = PythonOperator(
        task_id=f"fetch_{source_name}",
        python_callable=_fetch,
        op_kwargs={"source": source_name},
        dag=dag,
    )
    transform = PythonOperator(
        task_id=f"transform_{source_name}",
        python_callable=_transform,
        dag=dag,
    )
    load = PythonOperator(
        task_id=f"load_{source_name}",
        python_callable=_load,
        dag=dag,
    )
    fetch >> transform >> load
    return fetch, load

# Generate identical pipelines for multiple sources
for source in ["positions", "trades", "benchmarks"]:
    first, last = create_etl_tasks(source, dag)
    last >> final_report
```

##### Task Groups for Visual Organization

```python
from airflow.utils.task_group import TaskGroup

for source in ["positions", "trades", "benchmarks"]:
    with TaskGroup(source, tooltip=f"ETL for {source}"):
        create_etl_tasks(source, dag)
```

**See Figure 12.3 for task groups in the Airflow UI**

##### Dynamic Task Mapping

```python
# Generate tasks dynamically based on runtime data
@task
def get_source_list():
    return ["positions", "trades", "benchmarks"]

@task
def process_source(source_name):
    # ... process one source ...

with DAG(...):
    sources = get_source_list()
    process_source.expand(source_name=sources)  # creates N parallel task instances
```

**See Figure 12.5 for Dynamic Task Mapping schematic**

#### 12.2 Designing Reproducible Tasks

- **Idempotent**: rerunning produces the same result (use UPSERT, overwrite files, include execution date in paths)
- **Deterministic**: same input → same output (avoid implicit dict ordering, unseeded randomness, race conditions)
- **Functional paradigm**: pure functions, no side effects, explicit inputs/outputs

#### 12.3 Handling Data Efficiently

- **Filter early**: push WHERE clauses to the source database, not Python
- **Process incrementally**: use `data_interval_start`/`end` to bound queries
- **Cache intermediate data**: write to S3/Postgres between tasks (not local filesystem)
- **Avoid local filesystems**: Workers may be on different machines (especially on EKS) — use shared storage (S3, PVC)
- **Offload heavy work**: Use the database for aggregations (SQL), Spark for big data, SageMaker for ML

#### 12.4 Managing Concurrency Using Pools

```python
# Create pool in UI: Admin → Pools → Add → name="postgres_pool", slots=4

# Assign task to pool
load_task = PythonOperator(
    task_id="load_to_postgres",
    python_callable=_load,
    pool="postgres_pool",  # max 4 concurrent tasks hitting Postgres
)
```

> **Migration relevance**: Pools replace Autosys "resources" and "max_run_alarm" — they prevent overwhelming shared databases or APIs during parallel execution.

---

### Chapter 13: Project — Finding the Fastest Way to Get Around NYC

*(Summarized for reusable architectural patterns)*

#### Key Architecture Pattern: Raw → Processed → Export

```
S3 (or MinIO)
├── raw/              # Immutable copies of source data
│   ├── citibike/     #   timestamped: {ts_nodash}.json
│   └── taxi/         #   timestamped: {ts_nodash}.csv
├── processed/        # Transformed, normalized data
│   ├── citibike/     #   common schema: {ts_nodash}.parquet
│   └── taxi/         #   common schema: {ts_nodash}.parquet
└── export/           # Ready for consumption
    └── combined/     #   joined data: {ts_nodash}.parquet
```

#### Idempotent File Operations

```python
# Include execution timestamp in S3 keys for safe reruns
s3_key = f"raw/trades/{data_interval_start.strftime('%Y%m%d%H%M%S')}.json"
```

#### Idempotent Database Writes

```python
def _write_to_postgres(df, table, execution_date):
    with engine.begin() as conn:
        # Delete any existing records from this execution (idempotent)
        conn.execute(f"DELETE FROM {table} WHERE airflow_execution_date = '{execution_date}'")
        df["airflow_execution_date"] = execution_date
        df.to_sql(table, conn, if_exists="append", index=False)
```

---

### Chapter 14: Project — Keeping Family Traditions Alive with Airflow and Generative AI

*(Summarized for reusable patterns)*

#### 14.2–14.3 RAG (Retrieval-Augmented Generation) Architecture

- **RAG** = retrieve relevant documents from a vector database, then pass them as context to an LLM
- Advantages over fine-tuning: no retraining needed, always current, source-transparent, cheaper

#### Airflow + Vector DB Pipeline Pattern

```
Producer DAG (scheduled):
  1. Fetch new/updated documents from source
  2. Preprocess text (DockerOperator for isolation)
  3. Generate embeddings (embedding model in container)
  4. Upsert to vector database (Weaviate/Milvus/Pinecone)
  5. Delete outdated records

Consumer (on-demand or API-triggered):
  1. Embed user query
  2. Vector similarity search → top-K documents
  3. Pass query + documents to LLM
  4. Return generated response
```

> **Relevance**: If your team builds ML features (factor models, etc.) that need document context (research reports, filings), this RAG + Airflow pattern is directly applicable on EKS.

---

## Part 4 — Airflow in Production

---

### Chapter 15: Operating Airflow in Production

#### 15.1 Revisiting the Airflow Architecture

**See Figure 15.1 for production architecture diagram**

All components (API server, scheduler, DAG processor, triggerer, workers) communicate through the **metastore** (Postgres/MySQL). In production, each can be scaled independently.

#### 15.2 Choosing the Executor

| Executor | Distributed | Complexity | Best For |
|----------|------------|------------|----------|
| **LocalExecutor** | No | Low | Dev, small-scale, single-machine |
| **CeleryExecutor** | Yes | Medium | Multi-machine, MWAA uses this |
| **KubernetesExecutor** | Yes | High | EKS-native, each task = pod |
| **HybridExecutor** | Yes | High | Mix (e.g., Celery + K8s) |

**LocalExecutor**: Tasks run as subprocesses on the scheduler machine. Max parallelism configurable (default 32). Good for getting started.

**CeleryExecutor**: Tasks distributed via message broker (Redis/RabbitMQ/SQS) to worker machines.

```
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
```

**KubernetesExecutor**: Each task launches as a K8s pod. No persistent workers — pods created on demand.

```
AIRFLOW__CORE__EXECUTOR=KubernetesExecutor
```

> ⚠️ **For your setup:**
> - **MWAA** uses CeleryExecutor under the hood with dynamic worker scaling — you don't configure it directly
> - **Self-hosted on EKS**: KubernetesExecutor is the natural fit — each task runs in its own pod, leveraging EKS autoscaling
> - **KubernetesPodOperator** works with ANY executor (including Celery) — it always creates K8s pods regardless of the executor choice

#### 15.3 Configuring the Metastore

```bash
# Connection string for production Postgres
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:password@rds-endpoint:5432/airflow

# Useful CLI commands
airflow db migrate    # create/upgrade schema
airflow db check      # verify connectivity
airflow db clean      # delete old records (pass --clean-before-timestamp)
```

- **Production**: Always use external managed database (RDS for MWAA/EKS). Never SQLite.
- MWAA manages this automatically.

#### 15.4 Configuring the Scheduler

**Key tuning parameters:**

| Setting | Default | Purpose |
|---------|---------|---------|
| `AIRFLOW__CORE__PARALLELISM` | 32 | Global max concurrent tasks |
| `AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG` | 16 | Max tasks running per DAG |
| `AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG` | 16 | Max concurrent DAG runs |
| `AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC` | 5 | Seconds between scheduler loops |

- Multiple schedulers can run simultaneously (row-level DB locking ensures safety). Requires Postgres 9.6+ or MySQL 8+.
- MWAA handles scheduler scaling automatically.

#### 15.5 Configuring the DAG Processor Manager

| Setting | Default | Purpose |
|---------|---------|---------|
| `AIRFLOW__DAG_PROCESSOR__MIN_FILE_PROCESS_INTERVAL` | 0 | Min seconds between re-parsing a DAG file |
| `AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES` | 2 | Max parallel parsing processes |

#### 15.6 Capturing Logs

**Three log types:**

1. **API server logs** (web access/error)
2. **Scheduler logs** (task scheduling decisions)
3. **Task logs** (per task instance, per attempt)

**Remote log storage** (critical for distributed/EKS deployments):

```
AIRFLOW__LOGGING__REMOTE_LOGGING=True
AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID=aws_default
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://my-airflow-logs/logs
```

> **MWAA**: Logs automatically go to CloudWatch. For self-hosted EKS, configure S3 remote logging.

#### 15.7 Visualizing and Monitoring Airflow Metrics

**Pipeline: Airflow → StatsD → Prometheus → Grafana**

```bash
# Enable StatsD metrics
AIRFLOW__METRICS__STATSD_ON=True
AIRFLOW__METRICS__STATSD_HOST=statsd-exporter
AIRFLOW__METRICS__STATSD_PORT=9125
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'airflow'
    static_configs:
      - targets: ['statsd-exporter:9102']
```

**See Figure 15.10 for the metrics pipeline diagram**

**Key metrics to monitor:**

| Signal | Metric | Meaning |
|--------|--------|---------|
| Latency | `dagrun.*.first_task_scheduling_delay` | Time from schedule to execution |
| Load | `executor.running_tasks` | Current task load |
| Errors | `ti_failures`, `dag_processing.import_errors` | Task/DAG failures |
| Saturation | `executor.open_slots` | Remaining capacity |

#### 15.8 Setting Up Alerts

```python
def _alert_on_failure(context):
    # Send Slack/PagerDuty/email notification
    task_instance = context["task_instance"]
    dag_id = context["dag"].dag_id
    # ... send alert ...

dag = DAG(
    dag_id="critical_pipeline",
    default_args={"on_failure_callback": _alert_on_failure},
    on_failure_callback=_alert_on_failure,  # DAG-level too
)
```

#### 15.9 Scaling Airflow Beyond a Single Instance

**Option A: Single instance, multiple teams** — shared infrastructure, simpler ops, but resource contention
**Option B: Instance per team** — full isolation, more operational overhead

> **For your team**: Start with shared MWAA instance. If your DAGs need specific EKS resources (GPU, high memory), use KubernetesPodOperator to run those tasks on dedicated node groups while keeping Airflow on MWAA.

---

### Chapter 16: Securing Airflow

#### 16.1 Role-Based Access Control (RBAC)

| Role | Access Level |
|------|-------------|
| `Admin` | Full access (security management) |
| `Op` | View + edit connections, pools, variables |
| `User` | Trigger/pause/clear DAGs, no secrets access |
| `Viewer` | Read-only |
| `Public` | No access (default for unauthenticated) |

```bash
airflow users create --role User --username bobsmith \
    --email firstname@company.com --firstname Bob --lastname Smith \
    --password <secure_password>
```

#### 16.2 Encrypting Data at Rest

```python
# Generate Fernet key for encrypting connections/variables in the metastore
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

```
AIRFLOW__CORE__FERNET_KEY=<your-generated-key>
# Or read from file: AIRFLOW__CORE__FERNET_KEY_CMD=cat /secrets/fernet.key
```

- Fernet = symmetric encryption for passwords stored in the metastore
- **Never** store the key in plain text alongside the database

#### 16.3 Connecting with a Directory Service (LDAP)

- Integrate with corporate LDAP/Active Directory for SSO
- Configuration in `webserver_config.py`:

```python
from flask_appbuilder.const import AUTH_LDAP
AUTH_TYPE = AUTH_LDAP
AUTH_LDAP_SERVER = "ldap://your-ldap-server:389"
AUTH_LDAP_SEARCH = "dc=companyname,dc=com"
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"
```

#### 16.4 Encrypting Traffic to the Web Server (HTTPS)

```bash
# Generate self-signed cert (dev/internal only)
openssl req -x509 -newkey rsa:4096 -sha256 -nodes -days 365 \
    -keyout privatekey.pem -out certificate.pem \
    -subj "/CN=airflow.internal"
```

```
AIRFLOW__API__SSL_CERT=/path/to/certificate.pem
AIRFLOW__API__SSL_KEY=/path/to/privatekey.pem
```

> **MWAA**: HTTPS is handled automatically. For self-hosted EKS, use an ALB with ACM certificate.

#### 16.5 Fetching Credentials from Secrets-Management Systems

```
# Use AWS Secrets Manager as the secrets backend
AIRFLOW__SECRETS__BACKEND=airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}
```

- **Lookup order**: Secrets backend → Environment variables → Airflow metastore
- Supported: AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager

> **For your setup**: Use AWS Secrets Manager. Store database credentials, API keys, and service account tokens there. MWAA has native Secrets Manager integration.

---

### Chapter 17: Airflow Deployment Options

#### 17.1 Managed Airflow

##### 17.1.1 Astronomer

- Fully managed Airflow by the company that employs many core Airflow committers
- Available on AWS, Azure, GCP
- Features: in-browser IDE, observability tooling, dbt integration (Cosmos)

##### 17.1.2 Google Cloud Composer

- Managed Airflow on GKE (Google Kubernetes Engine)
- Tight GCP service integration (BigQuery, GCS, Dataflow)

##### 17.1.3 Amazon Managed Workflows for Apache Airflow (MWAA)

- **Executor**: CeleryExecutor with dynamic worker scaling
- **DAG deployment**: Upload to designated S3 bucket
- **Dependencies**: `requirements.txt` in S3 bucket
- **Plugins**: Zip file in S3 bucket
- **Monitoring**: CloudWatch integration
- **Scaling**: Small/medium/large environment sizes; workers auto-scale with load
- **Cost**: Base environment fee + per-worker-hour + metastore storage

> ⚠️ **MWAA does NOT use Lambda for task execution** — it uses CeleryExecutor with Fargate-based workers. There is no Lambda dependency to worry about.
>
> **EKS integration**: From MWAA, use `KubernetesPodOperator` to run tasks on your EKS cluster. MWAA's Airflow scheduler connects to EKS via IAM role. This gives you MWAA's managed scheduler + EKS's compute flexibility.

#### 17.2 Airflow on Kubernetes (Self-Hosted on EKS)

##### 17.2.3 Deploying with the Apache Airflow Helm Chart

```bash
# Add Helm repo and install
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow \
    --create-namespace --namespace airflow \
    --set apiServer.service.type=LoadBalancer
```

**Pods created:**

- `airflow-api-server` — Web UI
- `airflow-scheduler` — Scheduling loop
- `airflow-dag-processor` — DAG parsing
- `airflow-triggerer` — Deferred task handling
- `airflow-worker` — Task execution (with CeleryExecutor)
- `airflow-redis` — Message broker (Celery)
- `airflow-postgresql` — Metastore (replace with RDS)
- `airflow-statsd` — Metrics

##### 17.2.5 Changing the apiserver Secret Key

```bash
# Create stable secret (prevents pod restarts on helm upgrade)
kubectl create secret generic my-apiserver-secret \
    --namespace airflow \
    --from-literal="api-secret-key=$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
```

##### 17.2.6 Using an External Database

```yaml
# values.yaml — disable built-in Postgres, use RDS
postgresql:
  enabled: false
data:
  metadataSecretName: rds-connection-secret
```

##### 17.2.7 Deploying DAGs — Three Options

**Option 1: Bake into Docker image** (most reproducible)
```dockerfile
FROM apache/airflow:3.1.3
COPY dags/ ${AIRFLOW_HOME}/dags/
```

**Option 2: Persistent Volume** (shared NFS/EFS mount)
```yaml
dags:
  persistence:
    enabled: true
    existingClaim: efs-dags-claim
```

**Option 3: Git-sync sidecar** (auto-pulls from repo)
```yaml
dags:
  gitSync:
    enabled: true
    repo: https://github.com/your-org/airflow-dags.git
    branch: main
    subPath: "dags"
```

> **Recommendation for your team**: Start with **MWAA** for managed simplicity. Use **Git-sync** for DAG deployment (matches your Git workflow). Use **KubernetesPodOperator** to run heavy tasks on EKS. This avoids managing the Airflow infrastructure while still leveraging your existing EKS cluster for compute.

#### 17.2.8 Deploying a Python Library

- Package custom hooks/operators as a pip-installable package
- For MWAA: add to `requirements.txt` in S3
- For self-hosted: bake into the Airflow Docker image

#### 17.2.9 Configuring the Executor(s)

- Default Helm chart uses CeleryExecutor
- Switch to KubernetesExecutor:
```yaml
executor: "KubernetesExecutor"
```
- With KubernetesExecutor, workers are created as pods on demand — no persistent worker pods needed

#### 17.3 Choosing a Deployment Strategy

| Criteria | MWAA | Self-hosted EKS |
|----------|------|-----------------|
| Operational overhead | Low | High |
| Customization | Limited | Full |
| Cost predictability | Environment-based pricing | Pay for what you run |
| Executor choice | CeleryExecutor (fixed) | Any executor |
| K8s integration | Via KubernetesPodOperator | Native |
| Scaling | Auto (workers) | Manual (configure autoscaler) |
| Security | AWS-managed | You manage |

---

## Quick Reference: Autosys → Airflow Migration Cheat Sheet

| Autosys Concept | Airflow Equivalent | Key Chapter |
|----------------|-------------------|-------------|
| `.jil` file | Python DAG file (`.py`) | 2 |
| `insert_job` / `job_type: CMD` | `BashOperator` or `PythonOperator` | 2 |
| `condition: s(prev_job)` | `prev_task >> next_task` | 6 |
| `date_conditions` / `start_times` | `schedule=` (cron, preset, timetable) | 3 |
| `box_name` (grouping) | `TaskGroup` | 12 |
| `std_out_file` / `std_err_file` | Automatic log capture (UI or S3) | 15 |
| `alarm_if_fail` / `notification` | `on_failure_callback` | 15 |
| `watch_file` | `FileSensor` | 7 |
| `sendevent -E FORCE_STARTJOB` | REST API trigger or `airflow dags trigger` | 7 |
| `autorep -j -d` | Web UI grid view | 2 |
| `max_run_alarm` / `resources` | Pools (`pool="my_pool"`) | 12 |
| Environment variables for dates | `{{ logical_date }}`, `{{ ds }}`, `{{ data_interval_start }}` | 5 |
| `profile` (run-as user) | K8s service account / IAM role | 16 |
| Autosys server | MWAA environment or EKS Helm deployment | 17 |
