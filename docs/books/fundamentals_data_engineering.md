# Book6 - Fundamentals of Data Engineering — Summary
#### Joe Reis & Matt Housley (O'Reilly, 2022)

> **Context**: This summary is tailored for a team migrating on-prem pipelines (Excel files on shared network drives, Autosys/.jil orchestration) to a cloud-native architecture (AWS S3 / Postgres, Airflow orchestration, EKS deployment). Sections less relevant to this context are trimmed or omitted.

---

## Part I: Foundation and Building Blocks

---

### Chapter 1: Data Engineering Described

#### What Is Data Engineering?

##### Data Engineering Defined

- **Data engineering**: The development, implementation, and maintenance of systems and processes that take in raw data and produce high-quality, consistent information for downstream use cases (analytics, ML).
- **Data engineer**: Manages the data engineering lifecycle — from getting data from source systems to serving data for end use cases.
- DE sits at the intersection of: **security, data management, DataOps, data architecture, orchestration, and software engineering**.

##### The Data Engineering Lifecycle

Five stages, plus undercurrents that cut across all stages:

```
Stages:          Generation → Ingestion → Transformation → Serving
                                   ↕
                               Storage (underlies all)

Outputs:         Analytics | Machine Learning | Reverse ETL

Undercurrents:   Security | Data Management | DataOps |
                 Data Architecture | Orchestration | Software Engineering
```

**See Figure 1-1 for the canonical data engineering lifecycle diagram.**

##### Evolution of the Data Engineer

| Era | Key Developments |
|---|---|
| **1980–2000** | Data warehousing, SQL, Kimball/Inmon modeling, MPP databases, BI |
| **2000s** | Big data era begins — Hadoop, MapReduce, commodity hardware, AWS launches |
| **2010s** | Big data engineering — Spark, Kafka, streaming, code-first culture, open source explosion |
| **2020s** | Data lifecycle engineering — managed services, abstraction, modern data stack, DataOps, governance |

- The modern data engineer is a **data lifecycle engineer** — focused higher in the value chain on management, architecture, orchestration, and governance rather than low-level infrastructure.
- The term "big data" is passé; the tooling has been democratized and absorbed into standard DE practice.

##### Data Engineering and Data Science

- DE is **upstream** from data science/analytics. DE provides the inputs that data scientists convert into value.
- **See Figure 1-5 (Data Science Hierarchy of Needs)**: DS teams spend 70–80% of time on data collection, cleaning, and prep. Good DE frees them to focus on modeling and analysis.

#### Data Engineering Skills and Activities

##### Data Maturity and the Data Engineer

**Data maturity** = the progression toward higher data utilization, capabilities, and integration across the org. Three stages:

| Stage | Characteristics | DE Focus |
|---|---|---|
| **1. Starting with data** | Fuzzy goals, small team, ad hoc requests | Get buy-in, define architecture, build foundations, avoid undifferentiated heavy lifting |
| **2. Scaling with data** | Formal practices, growing pipelines, specialist roles | Establish formal data practices, adopt DevOps/DataOps, build scalable architecture |
| **3. Leading with data** | Self-service analytics, seamless new data intro, automation | Automation, custom tooling for competitive advantage, data governance, DataOps |

> **Relevant to your migration**: You're moving from Stage 1→2 territory. Focus on formalizing practices, choosing scalable architecture, and avoiding custom builds where off-the-shelf solutions exist.

##### Type A vs Type B Data Engineers

- **Type A (Abstraction)**: Uses managed services and off-the-shelf tools. Avoids reinventing the wheel. Works at all maturity levels.
- **Type B (Build)**: Builds custom data tools and systems for competitive advantage. More common at stages 2–3.

> **For your team**: Default to Type A. Use managed services (Airflow on MWAA/Cloud Composer or self-hosted on EKS, S3 for object storage, RDS Postgres). Only build custom when it provides clear competitive advantage for portfolio optimization workflows.

#### Data Engineers Inside an Organization

- **Internal-facing DE**: Maintains pipelines and warehouses for BI, reports, DS, ML (this is your team).
- **External-facing DE**: Builds systems for customer-facing applications.
- Key upstream stakeholders: software engineers, data architects, DevOps/SREs.
- Key downstream stakeholders: data analysts, data scientists, ML engineers.

---

### Chapter 2: The Data Engineering Lifecycle

#### What Is the Data Engineering Lifecycle?

The lifecycle stages turn raw data into useful end products:

1. **Generation** — Source systems produce data
2. **Storage** — Data is persisted for use
3. **Ingestion** — Data is moved from source to storage
4. **Transformation** — Data is changed into useful form
5. **Serving** — Data is made available for analytics, ML, reverse ETL

Storage underpins all stages. The stages are not strictly linear — they overlap, repeat, and interweave.

#### Generation: Source Systems

- **Source system**: The origin of data (application database, IoT device, message queue, spreadsheet, API, etc.).
- You typically don't own or control source systems — maintain open communication with source system owners.
- Key evaluation questions for source systems:
  - Data persistence model? Rate of generation? Schema type (fixed vs schemaless)?
  - Data quality/consistency? Duplicate handling? Late-arriving data?
  - Will reading from it impact its performance? How are schema changes communicated?

> **Your context**: Current source systems are Excel files on a shared network drive. This is a classic file-based source system with slow access and no schema enforcement.

#### Storage

- Cloud architectures often leverage **multiple** storage solutions simultaneously.
- Key evaluation questions:
  - Read/write speed compatibility? Will it bottleneck downstream?
  - Can it scale? Does it support complex queries or just raw storage?
  - Are you capturing metadata, lineage, schema evolution?

##### Understanding Data Access Frequency

- **Hot data**: Frequently accessed (e.g., serving user requests) — fast storage.
- **Lukewarm data**: Accessed periodically (weekly/monthly reports).
- **Cold data**: Rarely queried, archived for compliance — cheap storage, expensive retrieval (e.g., S3 Glacier).

#### Ingestion

- Source systems and ingestion are the most common bottlenecks in the lifecycle.
- Key questions: Use case? Frequency? Volume? Format? Quality?

##### Batch vs Streaming

- **Batch**: Process data in chunks at scheduled intervals. Default for most analytics/ML use cases. Simpler and cheaper.
- **Streaming**: Continuous, near-real-time. Adopt only when business use case justifies the added complexity.
- Many frameworks (Spark, Flink) handle both batch and micro-batch.

##### Push vs Pull

- **Push**: Source writes to a target (database, object store, filesystem).
- **Pull**: Ingestion system queries source on schedule (traditional ETL).
- **CDC (Change Data Capture)**: Can be push (trigger-based, log-based) or pull (timestamp-based queries). Log-based CDC adds minimal load to source DB.

#### Transformation

- Converts raw data to useful forms for downstream consumption.
- Early transformations: type casting, format standardization, deduplication.
- Later transformations: schema normalization, aggregation, featurization for ML.
- **Business logic** is a major driver — data modeling translates business rules into reusable patterns.

#### Serving Data

- **Analytics**: BI (historical), operational analytics (real-time), embedded analytics (customer-facing).
- **Machine Learning**: Feature engineering, model training data.
- **Reverse ETL**: Feeding processed data back into source systems (e.g., scored models → CRM).
- Data has **value** only when it's consumed. Avoid "data vanity projects."

#### Major Undercurrents Across the Data Engineering Lifecycle

##### Security

- **Principle of least privilege**: Give users/systems only the access they need, nothing more.
- Antipattern: Giving admin access to all users. Catastrophe waiting to happen.
- Security is about people, process, and technology. Culture of security first.
- Protect data in flight and at rest (encryption, tokenization, masking).
- Know IAM, network security, password policies, and encryption.

##### Data Management

Key facets:

- **Data governance**: Discoverability, security, accountability. Core categories: data quality, metadata, privacy.
- **Metadata**: Four types:
  - *Business metadata*: Business definitions, rules, data owners.
  - *Technical metadata*: Schema, data lineage, pipeline workflows.
  - *Operational metadata*: Job IDs, runtime logs, process results.
  - *Reference metadata*: Lookup data (codes, standards, calendars).
- **Data quality**: Accuracy, completeness, timeliness. Test and monitor proactively.
- **Master data management (MDM)**: Golden records — consistent entity definitions across the org.
- **Data modeling**: Converting data into usable form. Kimball, Inmon, Data Vault are key patterns (covered in Ch 8).
- **Data lineage**: Audit trail of data through its lifecycle — critical for debugging and compliance.
- **Data lifecycle management**: Archival, retention, destruction policies. Cloud makes this easier with tiered storage classes but pay-as-you-go means CFOs watch storage costs closely.

##### DataOps

Combines Agile, DevOps, and statistical process control (SPC) for data products. Three pillars:

1. **Automation**: CI/CD for data pipelines, environment management, configuration as code.
2. **Observability and monitoring**: Detect data quality issues, stale data, pipeline failures before stakeholders do. Apply SPC. Related concept: **DODD (Data Observability Driven Development)** — like TDD for data.
3. **Incident response**: Rapid root cause identification, blameless communication, proactive issue detection.

> **Automation maturity progression** (highly relevant to your migration):
> 1. Cron jobs → fragile, no dependency awareness
> 2. Orchestration framework (Airflow) → dependency-aware DAGs, alerting, backfill
> 3. Automated DAG deployment with testing → CI/CD for DAGs, validated before deploy
> 4. Full DataOps → metadata-driven DAGs, automated quality checks, lineage tracking

##### Orchestration

- **Orchestration** ≠ scheduling. An orchestrator manages **job dependencies** via DAGs. A scheduler (cron) just triggers at fixed times.
- DAGs can be run once or on schedule (daily, hourly, etc.).
- Orchestration systems provide: dependency management, job history, visualization, alerting, backfill capability.
- **Airflow**: Open-sourced by Airbnb in 2014, written in Python. Highly extensible. Mindshare leader. Alternatives: Prefect, Dagster (better metadata/portability/testability), Argo (K8s-native).

```python
# Conceptual Airflow DAG structure
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG("etl_pipeline", start_date=datetime(2024, 1, 1), schedule="@daily") as dag:

    def extract():
        # Pull data from source (e.g., read from S3 or query source DB)
        ...

    def transform():
        # Apply business logic, clean data, reshape
        ...

    def load():
        # Write to destination (S3, Postgres, data warehouse)
        ...

    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load", python_callable=load)

    t1 >> t2 >> t3  # Dependency chain
```

##### Software Engineering

- Core data processing code (SQL, Spark, Python) remains essential.
- **Testing**: Unit, regression, integration, end-to-end, smoke tests — all apply to data pipelines.
- **Infrastructure as code (IaC)**: Terraform, Helm, CloudFormation. Manage cloud infra declaratively.
- **Pipelines as code**: DAGs defined in Python/code. Core concept in modern orchestration.
- **Streaming**: Windowing methods, joins in real-time, function platforms (Lambda, Flink).

---

### Chapter 3: Designing Good Data Architecture

#### What Is Data Architecture?

- **Data architecture**: The design of systems to support the evolving data needs of an enterprise, achieved through **flexible and reversible decisions** reached through careful **evaluation of trade-offs**.
- Distinct from but related to **enterprise architecture** (TOGAF, Gartner, EABOK frameworks).
- Has two components:
  - **Operational architecture**: *What* needs to be done (functional requirements).
  - **Technical architecture**: *How* it will happen (systems, technologies, implementation).

##### "Good" Data Architecture

- Serves business requirements with reusable building blocks while maintaining flexibility.
- Key distinguishing trait: **agility** — ability to respond to changes in business and technology.
- Bad data architecture: tightly coupled, rigid, overly centralized, or "accidentally" architected.

#### Principles of Good Data Architecture

##### Principle 1: Choose Common Components Wisely

- Common components = shared building blocks across the org (object storage, event-streaming platforms, version control, observability).
- Should be accessible and understandable. Keep them simple and avoid customization that creates technical debt.

##### Principle 2: Plan for Failure

- Availability = percentage of time a system is operational (e.g., 99.99% = ~52 min downtime/year).
- **Reliability**: System performs function correctly. **Durability**: Data survives intact.
- Design for failure: redundancy, graceful degradation, self-healing, automated recovery.

##### Principle 3: Architect for Scalability

- **Scaling up** (vertical): Bigger machine. **Scaling out** (horizontal): More machines.
- **Elasticity**: Dynamically scale with demand. Cloud-native advantage.

##### Principle 4: Architecture Is Leadership

- Architects mentor, collaborate, and guide. Not ivory tower — hands-on influence.

##### Principle 5: Always Be Architecting

- Architecture is never "done." Iterate continuously.

##### Principle 6: Build Loosely Coupled Systems

- Systems should be independent, able to change without cascading effects.
- Modular, well-defined interfaces between components.
- Opposite of tightly coupled monolith where changing one component breaks everything.

##### Principle 7: Make Reversible Decisions

- **Two-way doors** (easily reversible): Preferred. Try things, revert if needed.
- **One-way doors** (irreversible): Proceed with great caution.
- Cloud environments favor two-way doors — spin up, test, tear down.

> **Relevant to your S3 vs Postgres decision**: This is a two-way door. You can start with S3 (file-based, familiar to your team) and add Postgres later. Or use both — S3 for raw/landing zone, Postgres for curated/queried data. The hybrid approach is low-risk and reversible.

##### Principle 8: Prioritize Security

- Bake security into every layer. Hardened defaults, principle of least privilege, encryption at rest and in transit.

##### Principle 9: Embrace FinOps

- **FinOps**: Cloud financial operations. Monitor spend, optimize costs, allocate by team/project.
- Cloud costs are operational (OpEx), not capital (CapEx). Track and attribute them.

#### Major Architecture Concepts

##### Domains and Services

- **Domain**: A real-world subject area with its own data, rules, and logic (e.g., "portfolio management," "trading").
- **Service**: A set of functionality in a domain, accessed via a well-defined interface.

##### Distributed Systems, Scalability, and Designing for Failure

- Horizontal scaling distributes load but introduces complexity (CAP theorem, network partitions).
- Design for failure at every level.

##### Tight vs Loose Coupling: Tiers, Monoliths, and Microservices

- **Monolith**: Single deployment unit. Simple but hard to scale independently.
- **Microservices**: Independent, loosely coupled services. Flexible but complex.
- **Practical middle ground**: Start monolithic, extract services when clear boundaries emerge.

##### Event-Driven Architecture

- Systems communicate via events rather than direct calls.
- Great for decoupling, real-time processing, and audit trails.

##### Brownfield vs Greenfield Projects

- **Brownfield**: Working within existing systems (your migration — existing Autosys, Excel-based pipelines).
- **Greenfield**: Starting from scratch.
- Brownfield requires understanding legacy constraints, incremental migration, running old and new in parallel.

> **Your migration strategy** (brownfield approach): Keep on-prem running, add S3/Postgres writes to production pipeline, build cloud pipeline on feature branch, validate, cutover.

#### Examples and Types of Data Architecture

##### Data Warehouse

- Centralized, highly structured repository for analytical data.
- Uses schema-on-write — data conforms to schema upon loading.
- Optimized for complex queries and aggregations (OLAP).
- Cloud warehouses (Snowflake, BigQuery, Redshift) separate compute from storage.

##### Data Lake

- Stores raw data in its native format (schema-on-read).
- Object storage (S3) is the standard substrate.
- Risk: becomes a "data swamp" without governance, metadata, and quality enforcement.

##### Convergence: Data Lakehouse and Data Platform

- **Data Lakehouse**: Combines lake (raw storage, schema-on-read) with warehouse features (ACID transactions, schema enforcement, query optimization). Examples: Delta Lake, Apache Iceberg, Apache Hudi.
- **Data Platform**: Umbrella term for the full stack — lake + warehouse + processing + governance + serving.

##### Modern Data Stack

- Collection of cloud-native, modular, plug-and-play tools.
- Typical components: Fivetran (ingestion) → Snowflake (warehouse) → dbt (transformation) → Looker (BI) → Airflow (orchestration).

##### Lambda Architecture

- Parallel **batch layer** (full reprocessing) and **speed layer** (real-time) with a **serving layer** merging results.
- Complexity: Maintaining two separate codepaths. Falling out of favor.

##### Kappa Architecture

- Streaming-only. All data treated as streams. Simpler than Lambda but requires mature streaming infra.

##### Data Mesh

- Decentralized, domain-oriented architecture.
- Four principles:
  1. **Domain-oriented ownership**: Each domain team owns its data end-to-end.
  2. **Data as a product**: Each domain exposes curated "data products" with SLAs.
  3. **Self-serve data platform**: Central platform team provides infrastructure as a service.
  4. **Federated computational governance**: Standards enforced computationally across domains.

---

### Chapter 4: Choosing Technologies Across the Data Engineering Lifecycle

#### Key Evaluation Criteria

| Factor | Question to Ask |
|---|---|
| **Team size & capabilities** | Can your team realistically learn and maintain this technology? |
| **Speed to market** | How quickly can you deliver value? |
| **Interoperability** | Does it play well with your other tools? |
| **Cost optimization** | TCO (total cost of ownership) + opportunity cost? |
| **FinOps** | Can you monitor and control cloud spend? |

#### Today vs Future: Immutable vs Transitory Technologies

- **Immutable technologies**: SQL, object storage, Linux, networking fundamentals — learn these deeply.
- **Transitory technologies**: Specific vendors, frameworks, SaaS tools — change rapidly.
- Focus on understanding the immutables. Choose transitory tech based on current needs.

#### Location

##### On Premises

- You own hardware, network, physical security. High upfront CapEx.
- Limitations: slow provisioning, finite capacity, hard to scale dynamically.
- **Your current state**: Autosys on-prem, shared network drives, Excel files.

##### Cloud

- Pay-as-you-go, elastic scaling, managed services.
- **IaaS**: VMs, raw compute (EC2). **PaaS**: Managed services (RDS, S3). **SaaS**: Fully managed applications (Snowflake).
- Cloud-native advantages: separation of compute and storage, auto-scaling, global availability.

##### Hybrid Cloud

- Mix of on-prem and cloud. **Your migration approach** — run on-prem and cloud in parallel during transition.

#### Build vs Buy

- **Default to buy (managed services)** unless custom build provides clear competitive advantage.
- **Open source**: Free licensing but not free to operate. Consider operational burden (patching, scaling, debugging).
- **Managed open source**: Best of both worlds (e.g., Amazon MWAA for Airflow, Amazon RDS for Postgres).

> **For your team**: Use managed Airflow (MWAA) or self-host on EKS via Helm chart. Use RDS Postgres (managed) instead of running Postgres yourself on EC2. Use S3 natively (zero ops burden).

#### Monolith vs Modular

- **Monolith**: Single system does everything. Simple at first, hard to evolve.
- **Modular**: Compose best-of-breed tools. More flexible, but integration complexity.
- **Distributed monolith**: Worst of both worlds — "microservices" that are actually tightly coupled.

> **Recommended**: Modular approach. S3 (storage) + Postgres (queryable store) + Airflow (orchestration) + Python (processing). Loosely coupled, replaceable components.

#### Serverless vs Servers

- **Serverless** (Lambda, Fargate): No server management, scale-to-zero, pay per invocation. Good for event-driven and sporadic workloads.
- **Containers** (EKS/K8s): You manage the cluster. Good for long-running, complex workloads.
- Serverless for simple tasks (triggers, small transforms). Containers for heavy processing (your existing K8s expertise on EKS).

#### Orchestration Example: Airflow

- Airflow as the de facto standard for batch orchestration.
- DAG-based dependency management replaces Autosys .jil files.
- Key benefits over Autosys: Python-native DAG definitions, built-in dependency resolution, web UI for monitoring, backfill capability, rich ecosystem of operators/hooks.

---

## Part II: The Data Engineering Lifecycle in Depth

---

### Chapter 5: Data Generation in Source Systems

#### Sources of Data: How Is Data Created?

- Data originates as analog or digital signals, then flows into systems.
- Know your source systems deeply — patterns, quirks, volumes, frequencies.

#### Source Systems: Main Ideas

##### Files and Unstructured Data

- Files (CSV, Excel, JSON, XML, etc.) are the universal exchange medium between organizations.
- **Your current state**: Excel files on shared network drive = file-based source system.

##### APIs

- Standard method for inter-system data exchange. REST, GraphQL, gRPC.
- Despite frameworks, maintaining API connections often requires ongoing engineering effort.

##### Application Databases (OLTP Systems)

- Store application state (e.g., account balances). Optimized for high-throughput reads/writes.
- **ACID properties**: Atomicity, Consistency, Isolation, Durability — guarantee transaction reliability.

##### Online Analytical Processing (OLAP) Systems

- Optimized for complex queries, aggregations, historical analysis. Column-oriented storage.
- May serve as source system if you're reading from another team's warehouse.

##### Change Data Capture (CDC)

- Tracks changes (inserts, updates, deletes) in a source database.
- Methods: timestamp-based (pull), trigger-based (push), log-based (push, minimal source load).
- **Log-based CDC** (e.g., Debezium reading Postgres WAL) is preferred — minimal impact on source DB.

##### Logs

- Application and system logs are a critical data source. Often semi-structured (JSON, key-value).
- **Database logs**: Transaction logs (WAL in Postgres) are the basis for log-based CDC.

##### CRUD and Insert-Only Patterns

- **CRUD**: Create, Read, Update, Delete. Standard mutable pattern.
- **Insert-only (append-only)**: Never update/delete — only insert new records. Creates natural audit trail. Used in event sourcing and streaming.

##### Messages and Streams

- **Message queue**: Asynchronous communication between systems. Messages consumed and deleted.
- **Event stream**: Append-only log of events. Can be replayed. Retained for a configurable period.
- Key platforms: Apache Kafka, AWS Kinesis, Google Pub/Sub, Apache Pulsar.

##### Types of Time

- **Event time**: When the event actually occurred.
- **Ingestion time**: When the data was ingested into the pipeline.
- **Processing time**: When the data was processed/transformed.
- Understanding the difference is critical for correct analytics and handling late-arriving data.

#### Source System Practical Details

##### Databases

- **Relational (RDBMS)**: Tables with rows and columns. Schema-enforced. Strong for structured data. (Postgres, MySQL, Oracle).
- **NoSQL**: Key-value (DynamoDB), document (MongoDB), wide-column (Cassandra), graph (Neo4j).
- **Considerations**: Connection management, query load on source DB, change tracking strategy.

##### APIs

- REST (most common), GraphQL (flexible queries), Webhooks (push-based), gRPC (high-performance).

##### Message Queues and Event-Streaming Platforms

- **Kafka**: Distributed event-streaming platform. Topics, partitions, consumer groups. High throughput, durable, replayable.
- **Cloud equivalents**: Kinesis (AWS), Pub/Sub (GCP).

#### Undercurrents and Their Impact on Source Systems

- **DataOps**: Track data quality at the source. Metadata collection.
- **Orchestration**: Coordinate ingestion jobs and dependency chains.
- **Software engineering**: Version control source definitions, test data contracts.

---

### Chapter 6: Storage

#### Raw Ingredients of Data Storage

##### Magnetic Disk Drive (HDD)

- Sequential reads fast, random access slow. Cheap per GB.

##### Solid-State Drive (SSD)

- Much faster random access. More expensive. Wear leveling limits write cycles.

##### Random Access Memory (RAM)

- Orders of magnitude faster than disk. Volatile. Used for caching and in-memory processing.

##### Serialization

- **Definition**: Encoding data structures into byte sequences for storage or transmission.
- **Row-oriented**: CSV, JSON, Avro — good for transactional workloads (write-heavy).
- **Column-oriented**: Parquet, ORC — good for analytical workloads (read/scan-heavy, compressible).

> **For your team**: Migrate Excel files to **Parquet on S3** for analytical workloads (columnar, compressed, fast reads) or **insert into Postgres** for queryable structured data.

##### Compression

- Reduces storage cost and I/O. Common algorithms: gzip, Snappy (fast), Zstandard (good ratio), LZ4 (fastest).
- Parquet and ORC have built-in compression support.

##### Caching

- Frequently accessed data kept in faster storage layer (RAM, SSD). Critical for hot data serving.

#### Data Storage Systems

##### Single Machine vs Distributed Storage

- Single machine: simpler but limited. Distributed: scales but introduces consistency challenges.
- **CAP Theorem**: Distributed systems can guarantee at most 2 of 3: Consistency, Availability, Partition tolerance.

##### Eventual vs Strong Consistency

- **Strong consistency**: Reads always return latest write. Higher latency.
- **Eventual consistency**: Reads may return stale data temporarily. Lower latency, higher availability. (S3 now offers strong read-after-write consistency.)

##### File Storage

- Traditional hierarchical filesystem (directories and files). Network file storage (NFS, SMB/CIFS).
- **Your current state**: Shared network drive = network file storage. Slow access, no metadata, no versioning.
- Cloud file storage exists (EFS, FSx) but object storage (S3) is usually the better choice for data engineering.

##### Block Storage

- Raw storage blocks (EBS, local SSD). Used as underlying storage for databases and VMs.
- Not directly used in data pipelines — but your Postgres database sits on block storage.

##### Object Storage

- **Key-value store**: Objects addressed by key (path). Flat namespace (though `/` simulates hierarchy).
- **S3**: The de facto standard for cloud data storage. Highly durable (99.999999999% — "11 nines"), massively scalable, cheap.
- **Ideal for**: Data lakes, landing zones, raw/archive data, Parquet/CSV/JSON files.
- **Not ideal for**: Low-latency random access, transactional workloads (use a database instead).
- **Antipattern**: Using S3 for high-rate random-access updates (it's optimized for large sequential reads/writes).

```python
# Example: Writing a Pandas DataFrame to S3 as Parquet
import boto3
import pandas as pd
import io

df = pd.DataFrame({"portfolio_id": [1, 2], "nav": [1000000.5, 2500000.3]})

# Write to Parquet in-memory, then upload to S3
buffer = io.BytesIO()
df.to_parquet(buffer, engine="pyarrow", index=False)
buffer.seek(0)

s3 = boto3.client("s3")
s3.put_object(Bucket="my-data-lake", Key="curated/portfolios/2024-01-15.parquet", Body=buffer)
```

```python
# Example: Writing to Postgres
import psycopg2
from io import StringIO

conn = psycopg2.connect("host=mydb.rds.amazonaws.com dbname=analytics user=etl_user")
cur = conn.cursor()

# Use COPY for bulk loading (much faster than INSERT for large batches)
buffer = StringIO()
df.to_csv(buffer, index=False, header=False)
buffer.seek(0)

cur.copy_expert("COPY portfolios FROM STDIN WITH CSV", buffer)
conn.commit()
```

##### Cache and Memory-Based Storage Systems

- Redis, Memcached — for sub-millisecond access to frequently queried data.

##### Indexes, Partitioning, and Clustering

- **Index**: Data structure that speeds up lookups on specific columns (B-tree, hash, bitmap).
- **Partitioning**: Splitting data into segments by a key (date, region). Reduces scan scope.
- **Clustering**: Physically ordering data on disk to match a common access pattern.

> **S3 "partitioning"**: Achieved via key prefix naming convention:
> ```
> s3://my-bucket/raw/portfolios/year=2024/month=01/day=15/data.parquet
> ```
> This enables efficient prefix-based listing and integrates with tools like Athena, Spark, Hive.

#### Data Engineering Storage Abstractions

##### The Data Warehouse

- Central, highly curated, schema-enforced analytical store.
- Cloud warehouses (Snowflake, BigQuery, Redshift) separate compute from storage.

##### The Data Lake

- Raw storage in native format on object storage (S3). Schema-on-read.
- Risk of "data swamp" without governance. Need metadata management.

##### The Data Lakehouse

- Adds ACID transactions, schema enforcement, and time travel to data lake.
- Technologies: **Delta Lake**, **Apache Iceberg**, **Apache Hudi**.
- Enables warehouse-like queries directly on S3 data.

##### Stream-to-Batch Storage Architecture

- Streaming data lands in an event platform (Kafka), then is periodically materialized to object storage (S3) or a warehouse in batch windows.

#### Big Ideas and Trends in Storage

##### Separation of Compute from Storage

- **Core cloud-native pattern**: Storage (S3) is decoupled from compute (Spark on EMR, Athena, etc.).
- Scale storage and compute independently. Pay for each separately.
- Enables multiple compute engines to query the same data (Spark, Presto, Athena, Redshift Spectrum).

> **Highly relevant to your architecture**: S3 as storage layer + multiple compute engines. EKS pods can read from S3 directly. Postgres handles structured queries. No need to pick one — use both.

##### Data Storage Lifecycle and Data Retention

- Define retention policies. Cloud storage tiers reduce cost for aging data:
  - S3 Standard → S3 Infrequent Access → S3 Glacier → Glacier Deep Archive.
- Automate lifecycle transitions with S3 Lifecycle Rules.

---

### Chapter 7: Ingestion

#### What Is Data Ingestion?

- Moving data from source systems into the data engineering lifecycle.
- **Data pipeline**: The combination of architecture, systems, and processes that move data through lifecycle stages. Intentionally flexible definition.

#### Key Engineering Considerations for the Ingestion Phase

##### Bounded vs Unbounded Data

- **Bounded**: Finite dataset (e.g., a daily CSV export, a database table snapshot).
- **Unbounded**: Continuous stream of data with no defined end (e.g., Kafka topic, IoT sensor feed).
- Batch processing inherently treats data as bounded. Streaming handles unbounded data.

##### Frequency

- How often should data be updated? Real-time? Hourly? Daily?
- **Your context**: Currently batch (Autosys schedules). Airflow will maintain batch cadence but with better dependency management. Consider whether any pipelines benefit from more frequent updates.

##### Synchronous vs Asynchronous Ingestion

- **Synchronous**: Source sends data and waits for acknowledgment. Tightly coupled.
- **Asynchronous**: Source fires and forgets (or relies on a queue/buffer). Decoupled, more resilient.
- Prefer async ingestion for pipeline decoupling and fault tolerance.

##### Serialization and Deserialization

- Data must be serialized for transmission and deserialized upon receipt.
- Format compatibility between source and destination matters (CSV → Parquet conversion, JSON parsing, etc.).

##### Throughput and Scalability

- Design ingestion to handle peak loads, not just average.
- Use buffering (queues, object storage) to absorb spikes.

##### Reliability and Durability

- Can you replay failed ingestion? Is data buffered safely?
- **At-least-once** delivery is common (handle deduplication downstream).
- **Exactly-once** delivery is the gold standard but harder to achieve.

##### Push vs Pull Patterns

- **Push**: Source writes data to target. Examples: Webhooks, database-triggered CDC, sensor → message queue.
- **Pull**: Ingestion system queries source on schedule. Examples: Scheduled API polls, `SELECT *` from source DB.

#### Batch Ingestion Considerations

##### Snapshot vs Differential Extraction

- **Snapshot (full extract)**: Grab entire dataset each time. Simple but expensive for large datasets.
- **Differential (incremental)**: Only grab what changed since last extraction. More efficient, more complex.

> **Your migration**: Currently likely doing full Excel file reads. As you move to Postgres/S3, implement incremental extraction using timestamps or CDC.

##### File-Based Export and Ingestion

- Export data to files (CSV, Parquet), transfer to target storage.
- Simple, reliable, battle-tested. Works well with S3 as landing zone.

> **Your pattern**: Excel → Python → Parquet → S3 (or directly to Postgres via COPY).

##### ETL vs ELT

- **ETL (Extract, Transform, Load)**: Transform before loading. Traditional on-prem approach.
- **ELT (Extract, Load, Transform)**: Load raw, transform in place. Cloud-native approach — leverage cheap storage and powerful cloud compute.
- **ELT is the modern default** — land raw data in S3/warehouse, then transform using SQL/Spark/dbt.

```
# ETL (traditional — your current on-prem approach)
Source → [Python transform on local server] → Destination

# ELT (cloud-native — your target state)
Source → [Land raw in S3] → [Transform with Spark/SQL/dbt] → Curated in S3/Postgres
```

##### Data Migration

- Moving data from one system to another (your exact project).
- Key principles: run old and new in parallel, validate data parity, cutover when confident.

#### Message and Stream Ingestion Considerations

- **Schema evolution**: Handle backward/forward compatible schema changes (Avro schema registry).
- **Late-arriving data**: Define SLAs for acceptable lateness. Decide how to handle late records.
- **Ordering and deduplication**: Distributed systems don't guarantee order. Handle at consumer side.
- **Dead-letter queues (DLQ)**: Failed messages routed to a separate queue for manual inspection.
- **Replay**: Ability to re-consume historical messages (Kafka supports this with retention).

#### Ways to Ingest Data

##### Direct Database Connection

- Query source DB directly (JDBC/ODBC). Simple but puts load on source.
- Use read replicas or off-peak windows to minimize impact.

##### Change Data Capture (CDC)

- Log-based CDC (Debezium) reads database transaction logs. Minimal source impact, near-real-time.
- Recommended for database-to-database or database-to-stream ingestion.

##### APIs

- REST polling, webhook push, GraphQL subscriptions.
- Watch for rate limits, pagination, auth token management.

##### Message Queues and Event-Streaming Platforms

- Kafka, Kinesis, Pub/Sub for real-time data ingestion.

##### Managed Data Connectors

- Fivetran, Airbyte, Stitch — managed ELT tools that handle source→destination pipelines.
- Good for reducing engineering effort on commoditized integrations.

##### Moving Data with Object Storage

- Upload files to S3, then process. Simple, reliable, decoupled.
- Works well as the **landing zone** pattern.

```
# Landing zone pattern for your migration:
# 1. On-prem pipeline writes to S3 (new step added to existing pipeline)
# 2. Cloud pipeline reads from S3, transforms, loads to Postgres or curated S3
# 3. Both pipelines run in parallel during migration period

# On-prem addition:
import boto3
s3 = boto3.client("s3")
s3.upload_file("output.parquet", "my-landing-zone", "raw/portfolios/2024-01-15.parquet")
```

---

### Chapter 8: Queries, Modeling, and Transformation

#### Queries

##### What Is a Query?

- A query retrieves or acts on data. SQL is the primary language.
- SQL categories: **DDL** (CREATE, DROP), **DML** (SELECT, INSERT, UPDATE, DELETE), **DCL** (GRANT, REVOKE), **TCL** (COMMIT, ROLLBACK).

##### The Life of a Query

```
SQL query → Parsing → Bytecode → Query Optimizer → Execution → Results
```

##### The Query Optimizer

- Analyzes query plan and determines most efficient execution strategy.
- Considers: join order, index usage, data scan size, join algorithms.
- Different databases optimize differently — understand your engine's optimizer.

##### Improving Query Performance

- **Optimize joins**: Prejoin frequently combined datasets. Avoid many-to-many explosions.
- **Use CTEs and subqueries wisely**: CTEs improve readability but some engines don't optimize them.
- **Manage data scan size**: Partition data, use columnar formats (Parquet), predicate pushdown.
- **Avoid full table scans**: Use indexes, partition pruning, column projection.
- **Caching**: Materialized views, query result caching.

```sql
-- Example: Partitioned query on S3 data via Athena
-- Only scans the relevant date partition
SELECT portfolio_id, SUM(market_value) as total_mv
FROM portfolio_holdings
WHERE year = '2024' AND month = '01'
GROUP BY portfolio_id;
```

##### Queries on Streaming Data

- Streaming SQL (e.g., Flink SQL, KSQL) operates on unbounded data.
- **Windowing**: Tumbling windows (fixed, non-overlapping), sliding/hopping windows (overlapping), session windows (activity-based).

#### Data Modeling

##### What Is a Data Model?

- An abstract representation of data, its relationships, and constraints.
- Serves as a contract between data producers and consumers.

##### Conceptual, Logical, and Physical Data Models

- **Conceptual**: High-level business entities and relationships (no technical detail).
- **Logical**: Detailed structure with attributes and data types (database-agnostic).
- **Physical**: Actual implementation — tables, columns, indexes, partitions (database-specific).

##### Normalization

- **Normalization**: Organizing data to reduce redundancy. Normal forms (1NF through 3NF typically).
  - **1NF**: Atomic values, unique rows.
  - **2NF**: 1NF + no partial dependencies on composite keys.
  - **3NF**: 2NF + no transitive dependencies.
- Fully normalized = minimal redundancy, maximum integrity, but complex joins for analytics.
- **Denormalization**: Intentionally introducing redundancy for query performance. Common in analytics.

##### Techniques for Modeling Batch Analytical Data

**Kimball (Dimensional Modeling)**
- **Star schema**: Central fact table surrounded by dimension tables.
  - **Fact tables**: Quantitative measurements (transactions, events). Grain = level of detail per row.
  - **Dimension tables**: Descriptive attributes (who, what, when, where).
- Simple, intuitive, fast queries. Widely adopted.

```sql
-- Star schema example
-- Fact table: portfolio_holdings (grain: one row per holding per day)
-- Dimensions: dim_portfolio, dim_security, dim_date

SELECT d.date, p.portfolio_name, s.security_name, f.market_value
FROM fact_portfolio_holdings f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_portfolio p ON f.portfolio_key = p.portfolio_key
JOIN dim_security s ON f.security_key = s.security_key
WHERE d.date = '2024-01-15';
```

**Inmon (Corporate Information Factory)**
- Top-down approach. Build a normalized enterprise data warehouse (3NF) first, then create dimensional data marts.
- More rigorous, better for complex enterprises, but slower to build.

**Data Vault**
- Hybrid approach designed for agility and auditability.
- Three entity types:
  - **Hubs**: Unique business keys.
  - **Links**: Relationships between hubs.
  - **Satellites**: Descriptive attributes with timestamps (full history).
- Insert-only (append-only), full auditability, parallelizable loading.

**Wide Denormalized Tables**
- Single flat table with many columns. Simple queries (no joins), but can be very wide.
- Popular in data lake environments and for ML feature tables.

> **Recommendation for your team**: Start with **wide denormalized tables** in S3/Parquet for simplicity. If you adopt Postgres for serving, consider a lightweight **star schema** for commonly queried datasets. Full Kimball/Inmon/Data Vault is overkill for your current scale.

#### Transformations

##### Batch Transformations

- SQL-based transforms in a warehouse or on files (Spark, dbt, Pandas).
- **dbt (Data Build Tool)**: SQL-first transformation framework. Version-controlled, tested, documented. Widely adopted.

```sql
-- dbt-style transformation example
-- models/curated/portfolio_daily_nav.sql
WITH raw_holdings AS (
    SELECT * FROM {{ ref('stg_portfolio_holdings') }}
),
aggregated AS (
    SELECT
        portfolio_id,
        as_of_date,
        SUM(market_value) AS total_nav,
        COUNT(DISTINCT security_id) AS num_holdings
    FROM raw_holdings
    GROUP BY portfolio_id, as_of_date
)
SELECT * FROM aggregated
```

##### Materialized Views, Federation, and Query Virtualization

- **Materialized view**: Precomputed query result stored physically. Fast reads, must be refreshed.
- **Federation**: Query across multiple data sources as if they were one.
- **Query virtualization**: Virtual tables that execute queries on the fly against underlying sources.

##### Streaming Transformations and Processing

- Apply transforms to data in motion (Kafka Streams, Flink, Spark Structured Streaming).
- Useful for real-time enrichment, filtering, aggregation.

---

### Chapter 9: Serving Data for Analytics, Machine Learning, and Reverse ETL

#### General Considerations for Serving Data

##### Trust

- Downstream consumers must trust the data. Trust is built through quality, consistency, and transparency.
- Data quality issues erode trust quickly and are hard to rebuild.

##### What's the Use Case, and Who's the User?

- Understand the consumer: analyst, data scientist, ML pipeline, external customer?
- Tailor serving layer to use case: ad hoc queries, dashboards, model training, API access.

##### Data Products

- A **data product** is a dataset (or data-derived artifact) treated as a product — with SLAs, documentation, ownership, and quality guarantees.

##### Self-Service or Not?

- Self-service analytics: Users access and analyze data without IT help.
- Requires good data quality, documentation, and accessible tools.

##### Data Definitions and Logic

- **Metrics layer / semantic layer**: Centralized definitions of business metrics. Prevents conflicting definitions across teams.

#### Analytics

##### Business Analytics (BI)

- Dashboards, reports, ad hoc queries on historical data.
- Tools: Tableau, Power BI, Looker, Metabase.
- Logic-on-read approach: Store data clean but fairly raw, apply business logic at query time via BI tool.

##### Operational Analytics

- Real-time or near-real-time monitoring. Live dashboards, alerting.
- Data consumed directly from streaming sources or near-real-time refreshed tables.

##### Embedded Analytics

- Analytics delivered to external customers within a product.
- Access control is critical — each customer must see only their data (multi-tenancy).

#### Machine Learning

- Data engineers provide the infrastructure for ML: feature pipelines, training data management, serving infrastructure.
- **Feature stores**: Centralized repositories for ML features with versioning, sharing, and serving (online + offline).
- Key considerations: Data quality sufficient for features? Data discoverable? Technical/org boundaries between DE and ML clear?

#### Ways to Serve Data for Analytics and ML

| Method | Use Case |
|---|---|
| **File exchange (S3)** | Share Parquet/CSV files. Simple. Good for batch ML training. |
| **Database (Postgres, warehouse)** | Structured queries, BI tools, dashboards. |
| **Streaming (Kafka)** | Real-time consumers, event-driven serving. |
| **Query federation** | Query across multiple sources without moving data. |
| **Semantic/metrics layer** | Consistent business definitions across tools. |
| **Notebooks** | Interactive analysis, ad hoc exploration (Jupyter). |

#### Reverse ETL

- Pushing processed/enriched data from the analytical layer back to operational systems (CRM, SaaS platforms, production applications).
- Growing practice as companies want to operationalize their analytics.

---

## Part III: Security, Privacy, and the Future of Data Engineering

---

### Chapter 10: Security and Privacy

#### People

##### The Power of Negative Thinking

- The weakest link in security is human. Always think through attack and leak scenarios.
- Best way to protect sensitive data: **don't ingest it in the first place** unless there's a real downstream need.

##### Always Be Paranoid

- Verify credential requests. When in doubt, hold off and get second opinions.

#### Processes

##### The Principle of Least Privilege

- Every user, service, and system gets the minimum access necessary.
- Applied to: IAM roles, database users, S3 bucket policies, Kubernetes RBAC.

```yaml
# Example: K8s RBAC for a pipeline service account (least privilege)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: etl-pipeline-role
  namespace: data-pipelines
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "watch", "create"]
```

##### Shared Responsibility in the Cloud

- Cloud provider secures the infrastructure **of** the cloud. You secure everything **in** the cloud.
- You are responsible for: IAM policies, network config, encryption keys, application security, data classification.

##### Always Back Up Your Data

- S3 versioning, cross-region replication, database snapshots (RDS automated backups).
- Test restore procedures regularly.

#### Technology

##### Encryption

- **At rest**: S3 SSE (server-side encryption), RDS encryption, EBS encryption.
- **In transit**: TLS/SSL for all network communication. Enforce HTTPS.
- Manage encryption keys via KMS (Key Management Service).

##### Logging, Monitoring, and Alerting

- CloudTrail for API audit logs. CloudWatch for metrics and alarms.
- Monitor: access patterns, unusual queries, failed auth attempts, data egress spikes.

##### Network Access

- VPCs, security groups, NACLs. Minimize public-facing endpoints.
- Use VPC endpoints for S3 and other AWS services (traffic stays within AWS network).

##### Security for Low-Level Data Engineering

- Principle of least privilege for IAM roles attached to EKS pods (IRSA — IAM Roles for Service Accounts).
- Use secrets management (AWS Secrets Manager, HashiCorp Vault) instead of hardcoded credentials.

```python
# Example: Retrieving a database password from AWS Secrets Manager
import boto3
import json

def get_db_credentials(secret_name: str) -> dict:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

creds = get_db_credentials("prod/postgres/etl-user")
# creds = {"username": "etl_user", "password": "...", "host": "...", "dbname": "analytics"}
```

---

### Chapter 11: The Future of Data Engineering

#### The Data Engineering Lifecycle Isn't Going Away

- The lifecycle stages (generation, storage, ingestion, transformation, serving) are durable concepts.
- Specific tools will change but the lifecycle framework persists.

#### The Decline of Complexity and Rise of Easy-to-Use Data Tools

- Abstraction continues. Tools become simpler, more accessible, less ops burden.
- Managed services replace self-hosted infrastructure.

#### The Cloud-Scale Data OS and Improved Interoperability

- Cloud is converging toward a "data OS" — interoperable services that compose seamlessly.
- Open table formats (Iceberg, Delta Lake, Hudi) enable interoperability across engines.

#### "Enterprisey" Data Engineering

- Governance, quality, lineage, cataloging — once "enterprise-only" practices — are now mainstream.
- Data mesh, data contracts, data products are formalizing these patterns.

#### Moving Beyond the Modern Data Stack, Toward the Live Data Stack

- Real-time analytical databases (ClickHouse, Apache Druid, Materialize) enable low-latency analytics.
- Streaming pipelines become first-class alongside batch.
- Tight feedback loops between applications and ML models.

---

## Appendix A: Serialization and Compression Technical Details

#### Serialization Formats

| Format | Type | Schema | Use Case |
|---|---|---|---|
| **CSV** | Row | None | Simple interchange, human-readable. Fragile (quoting, encoding issues). |
| **JSON** | Row (semi-structured) | Self-describing | API interchange, logs. Human-readable but verbose. |
| **Avro** | Row (binary) | Schema embedded | Streaming (Kafka), schema evolution, compact. |
| **Parquet** | Columnar (binary) | Schema embedded | Analytics, data lakes, ML training. Highly compressed, fast scans. |
| **ORC** | Columnar (binary) | Schema embedded | Hive/Spark ecosystems. Similar to Parquet. |
| **Arrow** | Columnar (in-memory) | Schema defined | Inter-process data exchange, zero-copy reads. Not for storage. |

> **Recommended for your migration**:
> - **Landing zone / raw**: Parquet (columnar, compressed, schema-embedded, Athena-queryable)
> - **Streaming**: Avro (compact, schema evolution via registry)
> - **Interchange with legacy systems**: CSV (if needed), but migrate to Parquet ASAP

#### Compression Algorithms

| Algorithm | Speed | Ratio | Notes |
|---|---|---|---|
| **gzip** | Moderate | Good | Most compatible. Default for many tools. |
| **Snappy** | Very fast | Lower | Optimized for speed. Common in Spark/Hadoop. |
| **Zstandard (zstd)** | Fast | Excellent | Best balance of speed and ratio. Growing adoption. |
| **LZ4** | Fastest | Lower | Ultra-low latency. Good for streaming. |
| **bzip2** | Slow | Excellent | Maximum compression. Rarely used in pipelines. |

> **Recommendation**: Use **Snappy** or **Zstandard** with Parquet on S3. Both offer good speed/ratio tradeoffs for analytical workloads.

---

## Appendix B: Cloud Networking

#### Key Concepts

- **VPC (Virtual Private Cloud)**: Isolated network within AWS. You define subnets, routing, and access.
- **Subnets**: Public (internet-accessible) and private (internal only). Data infrastructure belongs in private subnets.
- **Security Groups**: Stateful firewall rules at the instance level. Whitelist ingress/egress.
- **VPC Endpoints**: Private connectivity to AWS services (S3, Secrets Manager) without traversing the public internet.
- **VPC Peering / Transit Gateway**: Connect multiple VPCs. Useful for multi-account architectures.

> **For your EKS deployment**:
> - EKS worker nodes in private subnets.
> - S3 access via VPC Gateway Endpoint (free, private).
> - RDS Postgres in private subnet, accessible only from EKS security group.
> - Airflow web UI exposed via ALB in public subnet (with authentication).

```
┌──────────────────── VPC ────────────────────┐
│                                              │
│  ┌─ Private Subnet ─┐   ┌─ Private Subnet ─┐│
│  │  EKS Worker Nodes │   │  RDS Postgres    ││
│  │  Airflow Workers  │──▶│  (analytics DB)  ││
│  └───────┬───────────┘   └──────────────────┘│
│          │                                    │
│          │  VPC Endpoint                      │
│          ▼                                    │
│       ┌──────┐                                │
│       │  S3  │ (data lake)                    │
│       └──────┘                                │
│                                              │
│  ┌─ Public Subnet ──┐                        │
│  │  ALB → Airflow UI │                        │
│  └───────────────────┘                        │
└──────────────────────────────────────────────┘
```

---

## Quick Reference: Mapping Your Migration

| Current State (On-Prem) | Target State (Cloud) |
|---|---|
| Excel files on shared network drive | S3 (Parquet) + Postgres (RDS) |
| Autosys .jil orchestration | Apache Airflow (MWAA or on EKS) |
| Manual file-based data movement | Automated S3 put + Postgres insert |
| On-prem server execution | EKS (Kubernetes) on AWS |
| No formal data quality checks | DataOps: automated testing, monitoring, alerting |
| Ad hoc schema (Excel columns) | Enforced schema (Parquet schema, Postgres DDL) |
| No data lineage | Airflow DAG lineage + metadata tracking |

#### Recommended Migration Sequence

1. **Add S3 writes to on-prem pipeline** — dual-write: existing output + S3 upload (Parquet).
2. **Optionally add Postgres inserts** — for data that needs structured querying.
3. **Build cloud pipeline on feature branch** — Airflow DAGs reading from S3/Postgres, running on EKS.
4. **Validate data parity** — compare on-prem outputs vs cloud outputs.
5. **Cutover** — switch downstream consumers to cloud pipeline.
6. **Decommission** — retire on-prem Autosys jobs.

---
