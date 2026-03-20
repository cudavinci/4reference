# API Design Patterns — JJ Geewax (Manning, 2021)

> Comprehensive summary for refactoring reference. Code examples translated to **Python** (backend) / **vanilla JS** (frontend). Sections like *Review*, *Exercises*, and *What's Next* are omitted.

---

## Part 1: Introduction

### 1 Introduction to APIs

#### 1.1 What are web APIs?

- **API (Application Programming Interface):** A contract defining how two computer systems interact.
- **Library API:** Code distributed as a package; consumers hold local copies. Producers can't force changes on consumers.
- **Web API:** Exposed over a network; no local copy. The producer has full control — they can change algorithms, shut down, etc., and the consumer has no recourse.
- Key asymmetry: web API producers hold all the power, which makes *good design* critical since mistakes are hard to undo.

> **Figure 1.1** — Sequence diagram showing a consumer calling `encrypt()` on a server. The server can change its algorithm or shut down at any time.

#### 1.2 Why do APIs matter?

- Software designed only for humans (GUIs) is hard for computers to automate — visual changes break programmatic interactions.
- APIs are interfaces *for computers*: no visual layer, stable contracts, evolve in "compatible" ways.
- APIs enable **composition** — treating functionality like Lego bricks to assemble larger systems from reusable building blocks.

#### 1.3 What are resource-oriented APIs?

- **RPC-style API:** Action-centric. You *call* a remote procedure: `predictWeather(postalCode=10011)`, `sendEmail(to=...)`.
  - Great for stateless actions, but naming is ad-hoc — is it `ShowAllFlights()` or `ListFlights()`?
- **Stateful vs. Stateless:** A stateless call is independent of all other calls. A stateful call depends on prior stored context.
- **Resource-oriented API:** Standardizes around *resources* (nouns/things) and a small set of *standard methods* (verbs): `Create`, `Get`, `List`, `Update`, `Delete`.
  - Pattern: `<StandardMethod><Resource>()` — e.g., `CreateFlightReservation()`, `ListFlightReservations()`.
  - Learning one new resource + 5 standard methods = 5 new RPCs learned for free.

```python
## RPC-style (ad-hoc naming)
schedule_flight(date="2024-06-01")
cancel_reservation(id="res_123")
show_all_bookings(user="me")

## Resource-oriented (standardized)
create_flight_reservation(body={...})
delete_flight_reservation(id="res_123")
list_flight_reservations(parent="users/me")
```

> **Table 1.2** — Standard methods: Create, Get, List, Delete, Update.
> **Table 1.3** — Standard methods × FlightReservation resource = 5 predictable RPCs.

#### 1.4 What makes an API "good"?

An API exists because: (1) you have functionality users want, and (2) those users want to use it *programmatically*.

##### 1.4.1 Operational

- The system must actually **do what it claims** — functional correctness.
- Must also meet **nonoperational requirements**: latency, accuracy, throughput, reliability.

##### 1.4.2 Expressive

- Users must be able to **clearly dictate** what they want and how — not resort to workarounds.
- Anti-pattern: forcing users to abuse `TranslateText()` to detect language. Better: provide a dedicated `DetectLanguage()` method.

```python
## Bad: abusing translate to detect language
def detect_language(input_text: str) -> str | None:
    supported = ["en", "es", "fr", "de"]
    for lang in supported:
        translated = translate_api.translate_text(
            text=input_text, target_language=lang
        )
        if translated == input_text:
            return lang
    return None

## Good: dedicated method
language = translate_api.detect_language(text=input_text)
```

##### 1.4.3 Simple

- Simplicity ≠ fewer RPCs. Collapsing everything into `ExecuteAction()` just shifts complexity into a single call.
- Goal: expose functionality in the most straightforward way, **as simple as possible, but no simpler**.
- Principle: "Make the common case awesome and the advanced case possible." Hide advanced options from typical users.

```python
## Simple common case — just target language
translate_text(input_text="Hello world", target_language="es")

## Advanced case — explicit model selection still works
translate_text(input_text="Hello world", model_id="model_42")
```

##### 1.4.4 Predictable

- **Consistency** across naming, fields, and behavior. If one method calls it `text`, all methods should call it `text` (not `inputText` or `content`).
- Users learn by pattern-matching, not by reading every doc page. Inconsistency breaks their educated guesses and kills productivity.
- This is the entire purpose of API design patterns: build with well-known, well-defined, predictable blueprints.

---

### 2 Introduction to API design patterns

#### 2.1 What are API design patterns?

- **Software design pattern:** A reusable blueprint for solving a category of problems — not a library, but a template applied with minor adjustments.
- Analogy: building a shed. Options range from "buy pre-built" (off-the-shelf library) to "build from scratch" (custom code). Design patterns are the "build from blueprints" middle ground — moderate difficulty, good flexibility.
- Design patterns focus on **specific components**, not entire systems — like a roof shape or window design, not the whole shed.
- **API design pattern:** A software design pattern applied to an API's *interface*. Focuses on the surface area (resources, methods, fields) rather than implementation. May also dictate certain *behavioral* aspects (e.g., eventual consistency).

> **Table 2.1** — Difficulty/flexibility spectrum: pre-built → kit → blueprints → scratch.

#### 2.2 Why are API design patterns important?

- APIs are **rigid** (changes break consumers) and **public** (changes affect everyone). This is the worst-case combination for iterative design.
- Unlike GUIs (flexible — a moved button is annoying but not catastrophic), APIs are *brittle*: renaming a field breaks all existing client code.
- **Flexibility × Audience matrix** (Table 2.2):
  - Flexible + Private → very easy to change (internal monitoring console)
  - Flexible + Public → moderate (Facebook.com UI)
  - Rigid + Private → difficult (internal storage API)
  - Rigid + Public → very difficult (public Facebook API)
- Since APIs live in the "rigid + public" quadrant, getting it right the first time matters enormously → proven patterns are invaluable.

#### 2.3 Anatomy of an API design pattern

Each pattern in the book follows a standard structure:

##### 2.3.1 Name and synopsis

- A short, descriptive name (e.g., "IO pattern" for import/export) plus a one-sentence summary.
- Goal: quickly identify whether a pattern is worth investigating for your problem.

##### 2.3.2 Motivation

- Defines the **problem space**: user objectives, constraints, edge cases, failure scenarios.
- Articulates *why* the pattern is needed before jumping to *how*.

##### 2.3.3 Overview

- High-level description of the **solution strategy**: components, responsibilities, general approach.
- When multiple solutions exist (e.g., different ways to model many-to-many relationships), discusses trade-offs among them.

##### 2.3.4 Implementation

- The detailed "how": interface definitions in code, field formats, resource relationships, behavioral rules.
- Includes a **Final API definition** — an annotated code listing showing what a correct implementation looks like.

##### 2.3.5 Trade-offs

- What you **give up** by adopting the pattern: functional limitations, added complexity, data consistency concerns.
- Also covers near-misses — when the pattern *almost* fits but doesn't perfectly.

#### 2.4 Case study: Twapi, a Twitter-like API

A running example demonstrating patterns in action on a Twitter clone.

##### 2.4.1 Overview

- Twapi's core: post short messages, view others' messages.
- Explores three operations: creating messages, listing messages, and exporting data.

##### 2.4.2 Listing messages

- **Without patterns:** Simple `ListMessages(parent) → Message[]`. Works until the list grows to thousands/millions of messages (500K messages × 140 chars = ~70 MB response).
- **With Pagination pattern:** Add `pageToken` and `maxPageSize` to the request, `nextPageToken` to the response. Retrieve data in manageable chunks.

```python
## Without pagination — dangerous at scale
@dataclass
class ListMessagesRequest:
    parent: str

@dataclass
class ListMessagesResponse:
    results: list[Message]

## With pagination — safe and scalable
@dataclass
class ListMessagesRequest:
    parent: str
    max_page_size: int = 100
    page_token: str = ""

@dataclass
class ListMessagesResponse:
    results: list[Message]
    next_page_token: str = ""
```

> **Figure 2.2** — Sequence diagram: consumer pages through results until `next_page_token` is empty.

##### 2.4.3 Exporting data

- **Without patterns:** Add an `ExportMessages()` RPC that takes a destination (e.g., S3 bucket). But this is a long-running operation — you can't just return the result in one HTTP response.
- **With Long-Running Operations (LRO) pattern:** Return an `Operation` resource immediately. Client polls for completion.
- **With Importing and Exporting pattern:** Standardize `ExportMessages()` to return an LRO and accept polymorphic `OutputConfig` destinations (S3, GCS, etc.).

```python
## Export returning an LRO
@dataclass
class ExportMessagesRequest:
    parent: str
    output_config: OutputConfig

@dataclass
class ExportMessagesResponse:
    output_config: OutputConfig  # echo back where data went

@dataclass
class OutputConfig:
    gcs_destination: GcsDestination | None = None
    s3_destination: S3Destination | None = None
```

---

## Part 2: Design Principles

### 3 Naming

#### 3.1 Why do names matter?

- Names are the **first thing users see** and the foundation of the API's usability.
- Bad names cause confusion, increase support burden, and are nearly impossible to change in rigid, public APIs.

#### 3.2 What makes a name "good"?

##### Expressive

- Names should **clearly communicate** what the thing is or does. `translateText` beats `doAction`.
- If users need to read documentation to understand a name, the name has failed.

##### Simple

- Prefer short, common words over jargon: `send` over `transmit`, `list` over `enumerate`.
- Avoid abbreviations unless universally understood (`id` is fine; `cre_dt` is not).

##### Predictable

- Follow **consistent patterns** across the entire API so users can guess names for things they haven't seen.
- If one resource uses `createTime`, all resources should use `createTime` (not `createdAt`, `creation_date`, etc.).

#### 3.3 Language, grammar, and syntax

##### Language

- Use **American English** as the lingua franca for API identifiers.
- Avoid region-specific terms or idioms.

##### Grammar

- Resources = **nouns** (`Message`, `User`), Methods = **verbs** (`Create`, `Delete`).
- Use **plural** for collection names (`messages`, `users`), **singular** for individual resource types.
- Boolean fields: use affirmative adjective/past-participle form — `enabled`, `archived`, `visible` (not `isEnabled`, `disabled`).

##### Syntax

- Use **camelCase** for field names and method parameters in JSON APIs (e.g., `pageToken`, `maxPageSize`).
- Use consistent casing throughout — never mix `snake_case` and `camelCase`.

#### 3.4 Context

- Names should be **contextually appropriate** — a `title` field on a `Book` resource doesn't need to be called `bookTitle`.
- Avoid redundant prefixes that repeat the parent resource name.

#### 3.5 Data types and units

- If a field represents a measurement, include the **unit** in the name: `sizeBytes`, `delaySeconds`, `distanceKm`.
- Exception: fields with universally understood units (e.g., `currency` in a financial API where everything is in the same denomination).

#### 3.6 Case study: What happens when you choose bad names?

- Demonstrates how inconsistent or misleading names create cascading confusion, workarounds, and support costs.
- Moral: naming deserves as much design effort as architecture. It's deceptively simple and critically important.

---

### 4 Resource scope and hierarchy

#### 4.1 What is resource layout?

- **Resource layout** is the map of all resources in an API and how they relate to each other.
- APIs typically have multiple resource types connected through various relationships.

##### Types of relationships

- **Reference:** Resource A stores the ID of Resource B in a field. Loosely coupled. Either can exist independently.
- **Hierarchy (parent-child):** Resource B exists *inside* Resource A. B's identifier is scoped to A. Deleting A implies deleting all children B.
- **In-line data:** Resource A *contains* data from B directly as a nested field, rather than referencing it. Tight coupling.

> **Entity relationship diagrams** (Figure 4.x) — shows how to diagram resource relationships.

#### 4.2 Choosing the right relationship

##### Do you need a relationship at all?

- First question: does a relationship genuinely exist, or are you forcing one?
- Sometimes resources are truly independent.

##### References or in-line data?

- **Reference** (store an ID): use when the related resource has its own lifecycle, is large, or changes frequently. Avoids data staleness but requires an extra API call.
- **In-line data** (embed the data): use when the data is small, read-mostly, and tightly coupled. Convenient but can go stale.

##### Hierarchy

- Use when a child resource has **no meaning without its parent** — e.g., `Message` under `ChatRoom`.
- The child's ID is scoped to the parent: `/chatRooms/room1/messages/msg1`.
- Implies **cascade delete**: deleting the parent deletes all children.

#### 4.3 Anti-patterns

##### Resources for everything

- Not every concept deserves to be a top-level resource. Avoid creating resources for things that are really just fields (e.g., a `Color` resource when `color: string` suffices).

##### Deep hierarchies

- Limit nesting to **2-3 levels max**. Deep hierarchies like `/a/1/b/2/c/3/d/4` make URLs unwieldy, IDs fragile, and cross-parent operations painful.
- If you need more than 3 levels, flatten by promoting intermediate resources to the top level with references.

##### In-line everything

- Don't embed entire related resources inline. This bloats payloads, creates staleness issues, and makes it impossible to address the embedded data independently.

---

### 5 Data types and defaults

#### 5.1 Introduction to data types

- Every API field needs a data type. The choice of type affects serialization, validation, and default behavior.

##### Missing vs. null

- **Missing field:** The field is absent from the JSON payload entirely. Usually means "use the server default" or "don't change this field."
- **Null value:** The field is explicitly present with value `null`. Means "intentionally empty / no value."
- This distinction is critical for partial updates — missing means "leave as-is," null means "clear it."
- Recommendation: treat missing and null as **semantically identical** where possible, to simplify client implementations.

#### 5.2 Booleans

- Default value: **`false`** (so the default behavior is the *absence* of the feature).
- Use **positive, affirmative naming**: `enabled`, `archived`, `verified` (not `disabled`, `notArchived`).
  - Avoids double negatives: `if not disabled` → confusing. `if enabled` → clear.
- Anti-pattern: `optional bool enableEncryption` where the default (false) means no encryption. If the common case needs encryption, reconsider the default or the naming.

#### 5.3 Numbers

##### Bounds

- Define and document **min/max bounds** for all numeric fields.
- Avoid exposing implementation limits directly (e.g., don't say "max is 2147483647" — say "max is 10000 results").

##### Default values

- Numeric default: **0**, unless a different value makes domain sense (e.g., `maxPageSize` defaults to a sensible non-zero value like 100).

##### Serialization

- Integers up to 32-bit: serialize as JSON numbers.
- **64-bit integers: serialize as strings** to avoid precision loss in JavaScript (`Number.MAX_SAFE_INTEGER` = 2^53 - 1).

```python
## Serializing large IDs safely
import json

data = {"id": "9223372036854775807"}  # string, not int
json.dumps(data)  # '{"id": "9223372036854775807"}'
```

```js
// JS consumer safely handles string IDs
const data = JSON.parse(response);
const id = BigInt(data.id);  // use BigInt, not Number
```

#### 5.4 Strings

##### Bounds

- Always define a **max length** for string fields. Unbounded strings invite abuse and storage issues.

##### Default values

- Default: **empty string `""`**

##### Serialization

- Use **UTF-8** encoding with **NFC normalization** (Canonical Decomposition followed by Canonical Composition).
- NFC ensures that equivalent Unicode sequences (e.g., `é` as a single code point vs. `e` + combining accent) are stored identically.

#### 5.5 Enumerations

- **Avoid enum types in the API**. Use **string fields** with documented allowed values instead.
- Reason: adding a new enum value is a breaking change in many client libraries (e.g., proto3, TypeScript strict enums). Strings are forward-compatible — unknown values can be handled gracefully.
- Convention: use `UPPER_SNAKE_CASE` string constants for enum-like values.

#### 5.6 Lists

##### Atomicity

- **Atomic replacement only**: to update a list field, the client sends the complete new list. No partial list operations (no "append item 7" or "remove index 3").
- This avoids concurrency nightmares — two clients appending simultaneously could produce corrupted state.

##### Bounds

- Set a documented **maximum length** for list fields.

##### Default values

- Default: **empty list `[]`**

#### 5.7 Maps

- **Keys must be strings** (JSON object keys are always strings).
- Use maps when the set of keys is **dynamic and user-defined** (e.g., labels/tags). Use regular fields when keys are known at design time.

##### Bounds

- Set a maximum number of entries.

##### Default values

- Default: **empty map `{}`**

---

## Part 3: Fundamentals

### 6 Resource identification

#### 6.1 What is a resource identifier?

- Every resource needs a **unique identifier** — an opaque string that distinguishes it from all other resources.
- Identifiers serve as the **permanent address** for a resource. Everything else about a resource may change, but its ID must not.

#### 6.2 What makes a good identifier?

Desirable attributes of identifiers:

- **Easy to use:** simple to copy, paste, share verbally, embed in URLs.
- **Unique:** no two resources share the same identifier, ever.
- **Permanent:** once assigned, an ID never changes or gets reassigned, even after deletion (**tomb-stoning**).
- **Fast to generate:** ID creation should not be a bottleneck.
- **Unpredictable:** sequential IDs leak information (total count, creation rate). Random IDs prevent enumeration attacks.
- **Readable, shareable, verifiable:** humans should be able to work with IDs without special tooling.
- **Informationally dense:** more entropy per character = shorter IDs.

#### 6.3 What format should identifiers use?

##### UUIDs

- **UUID (Universally Unique Identifier):** 128-bit value, typically displayed as 32 hex chars with hyphens (`550e8400-e29b-41d4-a716-446655440000`).
- Only 4 bits of entropy per character (hex = 16 symbols), so UUIDs are long relative to their information content.
- Widely supported, but case-sensitive hex can cause issues.

##### Crockford's Base32

- Uses **32 ASCII characters** (`0-9, A-Z` minus `I`, `L`, `O`, `U`) — case-insensitive, URL-safe, avoids ambiguous characters.
- **5 bits per character** vs UUID's 4 bits → ~20% more informationally dense.
- Optional **hyphens** for readability (ignored during parsing).
- Optional **checksum character** using modulo 37 → Base37 digit (adds `*`, `~`, `$`, `=`, `U`). Catches typos and transpositions.

```python
## Crockford Base32 encoding example
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def encode_base32(n: int) -> str:
    if n == 0:
        return CROCKFORD_ALPHABET[0]
    result = []
    while n > 0:
        result.append(CROCKFORD_ALPHABET[n % 32])
        n //= 32
    return "".join(reversed(result))

def checksum(n: int) -> str:
    CHECK_SYMBOLS = CROCKFORD_ALPHABET + "*~$=U"
    return CHECK_SYMBOLS[n % 37]

## encode_base32(946536423) → "Y3FZ57"
## With checksum: "Y3FZ57" + checksum(946536423) → "Y3FZ57*"
```

#### 6.4 Resource type prefixes

- Prefix identifiers with the **resource type**: `books/abcde-12345`, `users/vwxyz-67890`.
- Makes IDs self-describing — you can determine the resource type from the ID alone.
- Hierarchy expressed through path segments: `chatRooms/abc/messages/xyz`.

#### 6.5 Tomb-stoning

- **Tomb-stoning (soft deletion):** When a resource is deleted, mark it as deleted rather than physically removing it. The ID is permanently reserved.
- Prevents ID reuse, which would cause confusion if old references suddenly point to a different resource.
- A `Get` on a tomb-stoned resource should return a clear "deleted" error, not "not found."

#### 6.6 Database storage

- **Strings:** Most flexible, easy to query and debug. Slight storage overhead.
- **Raw bytes:** Compact, but hard to read in logs/debuggers.
- **Integers:** Very compact, fast indexing, but limited to sequential or pre-mapped values.
- Recommendation: store as **strings** unless storage/performance constraints demand otherwise.

---

### 7 Standard methods

#### 7.1 Motivation

- Standard methods provide a **predictable, uniform interface** for CRUD operations across all resources.
- Users learn 5-6 verbs once, then apply them to every new resource type.

#### 7.2 Overview of standard methods

| Method | HTTP | Idempotent | Description |
|--------|------|------------|-------------|
| **Get** | `GET` | Yes | Retrieve a single resource by ID |
| **List** | `GET` | Yes | Retrieve a collection of resources |
| **Create** | `POST` | No | Create a new resource |
| **Update** | `PATCH` | Yes | Partial modification of a resource |
| **Delete** | `DELETE` | Special | Remove a resource |
| **Replace** | `PUT` | Yes | Full replacement of a resource |

#### 7.3 Implementation

##### Get

- Accepts a single `id` field. Returns the full resource.
- Must be **side-effect free** — no state mutation on read.

##### List

- Accepts `parent` (scope), `maxPageSize`, `pageToken`, optional `filter`.
- Returns `results[]` + `nextPageToken`.
- Must be side-effect free.

##### Create

- Accepts the resource data in the request body. Returns the created resource with server-generated fields (ID, timestamps).
- **Not idempotent** — calling twice creates two resources.
- Optionally allow client-specified IDs (with collision checks).

##### Update (PATCH)

- **Partial update**: only fields present in the request body are modified; absent fields are left unchanged.
- Uses a **field mask** to specify which fields to update (see Chapter 8).
- Idempotent: applying the same patch twice yields the same result.
- Must be side-effect free.

##### Delete

- Accepts an `id`. Returns void/empty.
- Should use an **imperative approach** (not idempotent): deleting an already-deleted resource returns an error, not a silent success. This prevents masking bugs where the wrong resource is targeted.
- Hard deletes remove data; soft deletes (tomb-stoning) mark as deleted.

##### Replace (PUT)

- **Full replacement**: the entire resource is overwritten with the provided data. Missing fields revert to defaults.
- Idempotent: sending the same full resource twice yields the same state.
- Useful when the client has a complete local copy and wants to sync it.

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GetBookRequest:
    id: str

@dataclass
class ListBooksRequest:
    parent: str = ""
    max_page_size: int = 100
    page_token: str = ""
    filter: str = ""

@dataclass
class ListBooksResponse:
    results: list = field(default_factory=list)
    next_page_token: str = ""

@dataclass
class CreateBookRequest:
    resource: dict = field(default_factory=dict)
    id: Optional[str] = None  # optional client-specified ID

@dataclass
class UpdateBookRequest:
    resource: dict = field(default_factory=dict)
    field_mask: list[str] = field(default_factory=list)

@dataclass
class DeleteBookRequest:
    id: str = ""
```

#### 7.4 Which methods to support

- Not every resource needs all methods. Immutable resources skip Update/Replace. Append-only logs skip Delete.
- Minimum viable set for most resources: **Get, List, Create, Delete**.

#### 7.5 Side effects and security

- Standard methods (Get, List, Update, Replace, Delete) must be **side-effect free** — they do exactly what their name implies and nothing more.
- **Security note:** When a user requests a resource they don't have access to, return **404 Not Found** (not 403 Forbidden). A 403 leaks information about the resource's existence.

---

### 8 Partial updates and retrievals

#### 8.1 Motivation

- Sending and receiving entire resources on every request is wasteful — especially for large resources where only a few fields are relevant.
- **Field masks** solve this by letting clients specify exactly which fields to read or write.

#### 8.2 Field masks

- A **field mask** is an array of **field path strings** specifying which fields to include.
- Transport: passed as a query parameter (for GET) or request body field (for PATCH).

##### Syntax

- **Dot notation** for nested fields: `"author.name"`, `"address.city"`.
- **Asterisk `*`** as a wildcard: `"*"` means "all fields at this level."
- **Backtick escaping** for fields containing dots or special characters: `` `field.with.dots` ``.
- **Repeated fields** use `*` for for-each semantics but **no index-based access** (no `items[3]`).

#### 8.3 Default behavior

- **Retrieval (Get/List):** Default field mask = `"*"` (all fields). Clients can narrow to reduce payload.
- **Update (PATCH):** Default field mask = inferred from provided data. Only fields present in the request body are updated.

#### 8.4 Handling missing, null, and undefined

- **Missing field + field mask omits it** → leave as-is (no change).
- **Field present + in field mask** → update to provided value.
- **Null + in field mask** → clear the field.
- Recommendation: treat missing and null as semantically identical where possible.
- Invalid/unknown fields in a field mask should be **ignored** (treated as undefined), not cause errors. This enables forward-compatible clients.

```python
## Partial update with field mask
update_request = {
    "resource": {
        "id": "books/abc123",
        "title": "New Title",
    },
    "field_mask": ["title"]  # only update title
}

## Partial retrieval
## GET /books/abc123?fieldMask=title,author.name
```

#### 8.5 Alternatives

- **JSON Patch (RFC 6902):** Array of operations (`add`, `remove`, `replace`, `move`, `copy`, `test`). More powerful but more complex.
- **JSON Merge Patch (RFC 7396):** Simpler — send a partial JSON document, fields present are updated, `null` means delete. Can't distinguish "set to null" from "remove."
- Field masks are the recommended default for resource-oriented APIs due to simplicity and explicitness.

---

### 9 Custom methods

#### 9.1 Motivation

- Standard methods cover CRUD, but some operations don't fit: `LaunchRocket()`, `TranslateText()`, `SendNotification()`.
- Custom methods fill the gap for **actions that go beyond basic resource manipulation**.

#### 9.2 HTTP mapping and naming

- Use **HTTP POST** with a **colon separator** in the URL: `POST /rockets/1234:launch`.
- The colon distinguishes custom methods from sub-resources (`/rockets/1234/launch` would imply a `launch` child resource).
- Naming convention: **`<Verb><Noun>`** — e.g., `ArchiveMessage`, `TranslateText`, `RunJob`.

#### 9.3 Side effects

- Unlike standard methods, custom methods **are allowed to have side effects** — sending emails, triggering workflows, modifying related resources.

#### 9.4 Types of custom methods

##### Resource-targeted

- Operate on a specific resource: `POST /rockets/1234:launch`.
- The resource ID is in the URL path.

##### Collection-targeted

- Operate on a collection: `POST /messages:batchDelete`.
- Applied to multiple resources at once.

##### Stateless

- Pure computation, no stored state: `POST /translations:translate`.
- Useful for GDPR/compliance — stateless means no data retention.
- Attach to a **parent resource** for billing/authorization purposes even though no resource is being modified.

```python
## Resource-targeted custom method
## POST /rockets/1234:launch
@dataclass
class LaunchRocketRequest:
    id: str
    target_orbit: str = ""

## Stateless custom method
## POST /translations:translateText
@dataclass
class TranslateTextRequest:
    text: str
    source_language: str = ""
    target_language: str = "en"

@dataclass
class TranslateTextResponse:
    translated_text: str = ""
    detected_source_language: str = ""
```

#### 9.5 Trade-offs

- Custom methods can **hide bad resource design** — if you find yourself with many custom methods, reconsider whether you're missing a resource.
- Use sparingly: standard methods should cover the vast majority of interactions.

---

### 10 Long-running operations

#### 10.1 Motivation

- Some API calls take too long to complete in a single request-response cycle (data exports, ML model training, bulk processing).
- **Long-Running Operations (LROs)** let the server acknowledge the request immediately and provide a way to track progress asynchronously.

#### 10.2 Overview

- An LRO is a **generic `Operation` resource** with type parameters for the result and metadata:
  `Operation<ResultT, MetadataT>`
- The API method returns an `Operation` immediately. The client checks back later for completion.

#### 10.3 Implementation

##### The Operation resource

```python
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional, Union
from datetime import datetime

ResultT = TypeVar("ResultT")
MetadataT = TypeVar("MetadataT")

@dataclass
class OperationError:
    code: str = ""
    message: str = ""
    details: Optional[dict] = None

@dataclass
class Operation(Generic[ResultT, MetadataT]):
    id: str = ""
    done: bool = False
    expire_time: Optional[datetime] = None
    result: Optional[Union[ResultT, OperationError]] = None
    metadata: Optional[MetadataT] = None
```

##### Key fields

- `id`: Unique identifier for the operation.
- `done`: Boolean — `True` when complete (success or failure).
- `result`: Either the `ResultT` value (on success) or an `OperationError` (on failure). Errors go in `result`, **not** as HTTP status codes.
- `metadata`: `MetadataT` for progress tracking (e.g., `messagesProcessed`, `percentComplete`).
- `expireTime`: When the operation resource will be garbage-collected.

##### Top-level collection

- Operations live in a **top-level collection** `/operations` — not nested under the resource they operate on. This enables cross-resource operation listing and avoids hierarchy complications.

##### Resolution: polling vs. waiting

- **Polling:** Client repeatedly calls `GetOperation(id)` with **exponential backoff**.
- **Waiting:** Client calls `WaitOperation(id)` (custom method using HTTP GET). Server holds the connection until done or timeout. More efficient but requires long-lived connections.

##### Canceling, pausing, resuming

- **CancelOperation:** Custom method `POST /operations/{id}:cancel`. Best-effort — may not take effect immediately.
- **Pause/Resume:** Via metadata `paused` boolean field. `POST /operations/{id}:pause` and `POST /operations/{id}:resume`.

##### Listing and filtering

- `ListOperations` supports filtering (e.g., by `done` status, by parent resource).

##### Persistence and expiration

- Default: keep `Operation` resources **forever**, like any other resource.
- If storage is a concern, use a **rolling window** with `expireTime` — e.g., delete after 30 days based on completion timestamp (not creation timestamp).
- Expiration times should be **uniform** across operation types — don't vary by result type, as that creates confusing, unpredictable behavior.

#### 10.4 Trade-offs

- LROs are complex, generic, parameterized resources that come into existence as side effects of other operations — breaking the standard resource creation model.
- Alternative: just make the request hang until completion. Simpler, but doesn't work in distributed architectures where different microservices initiate and monitor work.
- Confusion can arise between LROs and **rerunnable jobs** (Chapter 11).

---

### 11 Rerunnable jobs

#### 11.1 Motivation

- LROs handle one-off async operations, but sometimes you need **configurable, repeatable units of work** that can be run on demand or on a schedule.
- Three problems LROs alone don't solve:
  1. **Configuration sprawl:** Each invocation requires all parameters. Storing the configuration server-side avoids this.
  2. **Permission conflation:** With on-demand methods, "can configure" and "can execute" are the same permission. Jobs separate them.
  3. **Scheduling:** Jobs can be triggered on a server-managed schedule without client-side crontab scripts.

#### 11.2 Overview

- A **Job** is a resource that stores the *configuration* for a unit of work. A separate **`Run`** custom method on the Job triggers *execution*.
- Two-phase pattern: (1) `CreateJob()` with configuration, (2) `RunJob()` with no parameters → returns an LRO.

> **Figure 11.1** — Sequence diagram: User creates a `BackupChatRoomJob`, then later calls `RunBackupChatRoomJob()`, which returns an `Operation` that follows the standard LRO flow.

#### 11.3 Implementation

##### Job resources

- Jobs are normal resources with standard methods (Create, Get, List, Update, Delete).
- The Job resource stores what would have been the request parameters of the on-demand custom method.
- Jobs may be **immutable** — create and delete only, no update. This avoids concurrency issues when a job is running while being modified.
- Standard methods on Jobs are **synchronous** (unlike the on-demand custom method which returns an LRO).

```python
## On-demand custom method (before Jobs pattern)
@dataclass
class BackupChatRoomRequest:
    id: str                    # ChatRoom to back up
    destination: str = ""
    compression_format: str = ""
    encryption_key: str = ""

## Job resource (after applying the pattern)
@dataclass
class BackupChatRoomJob:
    id: str = ""
    chat_room: str = ""        # reference to ChatRoom
    destination: str = ""
    compression_format: str = ""
```

##### The custom run method

- Each Job has a `Run` custom method: `POST /backupChatRoomJobs/{id}:run`.
- The run method accepts **only the Job ID** — no other parameters. All configuration is stored on the Job resource.
- Returns an **LRO** that resolves to the job's output.

```python
@dataclass
class RunBackupChatRoomJobRequest:
    id: str  # only the job ID — no configuration params

@dataclass
class RunBackupChatRoomJobResponse:
    destination: str = ""  # where the backup landed

@dataclass
class RunBackupChatRoomJobMetadata:
    messages_counted: int = 0
    messages_processed: int = 0
    bytes_written: int = 0
```

##### Job execution resources

- When a job's output is **ephemeral** (no resource created or modified), the LRO's result would disappear when the operation expires.
- Solution: **Execution resources** — a child resource of the Job that permanently stores each run's output.
- Executions are **read-only** — they support Get, List, and optionally Delete, but never Create or Update (they're created internally by the `Run` method).
- Executions live as **children of the Job**: `/analyzeChatRoomJobs/{id}/executions/{execId}`.

```python
@dataclass
class AnalyzeChatRoomJobExecution:
    id: str = ""
    job: str = ""    # snapshot of the job config at execution time
    sentence_complexity: float = 0.0
    sentiment: float = 0.0
    abuse_score: float = 0.0
```

> **Figure 11.2** — Sequence diagram: RunAnalyzeJob → creates Operation → backend creates Execution resource when done → Operation resolves with Execution as result.

#### 11.4 Trade-offs

- Alternative to permission separation: a more granular permission system that inspects method parameters. More flexible but far more complex.
- Alternative to Execution resources: keep `Operation` resources forever. Works, but requires filtering through all operations to find those related to a specific job.

---

## Part 4: Resource Relationships

### 12 Singleton sub-resources

#### 12.1 Motivation

- Sometimes a resource has data that is **conceptually part of it** but awkward to store directly as a field — due to size, security, or volatility.
- **Singleton sub-resource:** A resource that exists exactly once per parent resource, automatically created/destroyed with its parent.
- It's a hybrid: behaves like a **property** (tied to parent lifecycle) but is accessed like a **resource** (via its own API methods).

#### 12.2 Implementation

- **Singleton sub-resource** has no `id` of its own — its identity derives entirely from the parent.
  - URL pattern: `/resources/{id}/singletonChild` (no `{childId}` segment).

```python
@dataclass
class Car:
    id: str = ""
    make: str = ""
    model: str = ""

@dataclass
class CarSettings:
    """Singleton sub-resource of Car. No id field — identified by parent."""
    seat_heating: bool = False
    seat_position: int = 5
    wheel_position: int = 5
    mirror_position: int = 5
```

##### Standard method behavior

| Method | Behavior |
|--------|----------|
| **Get** | Works normally — returns the singleton |
| **Update** | Works normally — partial update via field mask |
| **Create** | Not exposed — singleton is auto-created with parent |
| **Delete** | Not exposed — singleton is auto-destroyed with parent |
| **List** | Not applicable — there's only one |

- **Reset pattern:** Since you can't Delete + Create to restore defaults, expose a custom `Reset` method:

```python
def reset_car_settings(car_id: str) -> CarSettings:
    """Custom method: POST /cars/{car_id}/settings:reset"""
    default = CarSettings()
    # overwrite stored settings with defaults
    return save_settings(car_id, default)
```

#### 12.3 When to use singletons

Three signals that a field should become a singleton sub-resource:

- **Size / Complexity:** The data is large or deeply structured (e.g., a document's access-control list). Fetching the parent shouldn't require loading this heavy payload every time.
- **Security:** The data requires different access permissions than the parent (e.g., anyone can read a `Car`, but only the owner should read `CarSettings`).
- **Volatility:** The data changes at a very different rate than the parent (e.g., car metadata is static, but settings change constantly).

#### 12.4 Trade-offs

- **No nesting singletons under singletons.** If `/cars/{id}/settings` needs its own sub-structure, use fields within the singleton, not another singleton child.
- A singleton is always exactly one-per-parent. If you might need zero or many, use a regular sub-resource collection instead.
- Singletons add API surface area — only extract when the size/security/volatility justification is clear.

---

### 13 Cross references

#### 13.1 Motivation

- Resources often refer to other resources. A `Book` has an `Author`. How do you represent that relationship?
- **Cross reference (foreign key):** A field on one resource that holds the **unique identifier** of another resource.

#### 13.2 Implementation

- The reference field is a **string** holding the target resource's ID.
- Naming convention: `<targetType>Id` (e.g., `authorId`).

```python
@dataclass
class Book:
    id: str = ""
    title: str = ""
    author_id: str = ""  # cross reference → Author resource
```

##### Dynamic references (polymorphic targets)

- When the reference can point to **different resource types**, add a `target_type` field:

```python
@dataclass
class Comment:
    id: str = ""
    content: str = ""
    target_id: str = ""
    target_type: str = ""  # "Post", "Photo", "Video", etc.
```

#### 13.3 Data integrity

- **Core question:** What happens when the referenced resource is deleted?
- Three strategies:

| Strategy | Behavior | Trade-off |
|----------|----------|-----------|
| **Prevent deletion** | Reject delete if any resource references target | Safe but rigid; hard to untangle |
| **Cascade delete** | Delete all referencing resources when target is deleted | Dangerous implicit data loss |
| **Allow dangling** | Let the reference become a dangling pointer | Flexible; consumers must handle missing targets |

- **Recommended (Geewax):** Allow dangling pointers (option 3). It's the simplest, most scalable approach. API consumers should always validate that a referenced resource still exists before relying on it.

#### 13.4 Value vs. reference

- **Reference:** Store only the ID; always look up the latest data. Data is always fresh but requires extra API calls.
- **Value (snapshot):** Copy the data inline at write time. Fast reads, but data can become stale.
- **Guideline:** Default to references. Use value/snapshot only when staleness is acceptable and read performance is critical.
- In practice, tools like **GraphQL** can stitch references together in a single round-trip, reducing the cost of the reference approach.

---

### 14 Association resources

#### 14.1 Motivation

- Many-to-many relationships (e.g., Users ↔ Groups) can't be modeled with a simple cross-reference field on either side.
- **Association resource:** A standalone resource representing the **relationship itself** (like a join table in SQL).

#### 14.2 Implementation

- The association resource (e.g., `Membership`) has its own collection and holds references to both sides:

```python
@dataclass
class Membership:
    id: str = ""
    user_id: str = ""   # reference → User
    group_id: str = ""  # reference → Group
    role: str = ""       # relationship metadata
    joined_at: str = ""
```

- Standard methods apply to the association resource itself:
  - `CreateMembership` — establish a relationship
  - `DeleteMembership` — dissolve it
  - `ListMemberships` — query relationships (filter by `user_id` or `group_id`)
  - `GetMembership` — retrieve a specific relationship

##### Uniqueness constraint

- A duplicate `CreateMembership` (same user + group) should return **409 Conflict**.
- The `(user_id, group_id)` pair acts as a composite unique key.

##### Read-only reference fields

- The `user_id` and `group_id` fields must be **immutable after creation** — you cannot reassign a membership to a different user or group. Instead, delete and recreate.

#### 14.3 Alias methods

- Direct question: "What groups is User X in?" requires filtering `ListMemberships` by `user_id`, then fetching each `Group`. Cumbersome.
- **Alias methods** provide shortcuts:

```python
def list_group_users(group_id: str) -> list[User]:
    """GET /groups/{group_id}/users — returns User resources directly."""
    memberships = list_memberships(group_id=group_id)
    return [get_user(m.user_id) for m in memberships]

def list_user_groups(user_id: str) -> list[Group]:
    """GET /users/{user_id}/groups — returns Group resources directly."""
    memberships = list_memberships(user_id=user_id)
    return [get_group(m.group_id) for m in memberships]
```

- Alias methods are **read-only** convenience endpoints. All writes still go through the association resource.

#### 14.4 Referential integrity

- What happens when a User or Group is deleted?

| Strategy | Behavior |
|----------|----------|
| **Restrict** | Block deletion if any Memberships reference the resource (409 Conflict) |
| **Cascade** | Delete all related Memberships when the parent is deleted |
| **Do nothing** | Leave dangling Membership records |

- **Preferred:** Restrict deletion (force explicit cleanup) or do nothing (let consumers handle it). Cascade deletion of association resources is less dangerous than cascading the primary resources themselves but still warrants caution.

---

### 15 Add and remove custom methods

#### 15.1 Motivation

- Association resources are powerful but heavy — sometimes you just need to track that "User X is in Group Y" with **no metadata** on the relationship itself.
- **Add/Remove custom methods** are a lighter alternative: custom methods on the *managing* resource that manipulate membership without a separate association resource.

#### 15.2 Implementation

```python
def add_group_user(group_id: str, user_id: str) -> None:
    """POST /groups/{group_id}:addUser"""
    # internally appends user_id to the group's member list
    pass

def remove_group_user(group_id: str, user_id: str) -> None:
    """POST /groups/{group_id}:removeUser"""
    # internally removes user_id from the group's member list
    pass
```

- The relationship lives **inside** the managing resource (e.g., `Group.member_ids: list[str]`), not as a separate resource.

##### Error handling

| Scenario | Error |
|----------|-------|
| Add a user already in the group | **409 Conflict** |
| Remove a user not in the group | **412 Precondition Failed** |

#### 15.3 Trade-offs vs. association resources

| Aspect | Association resource | Add/Remove methods |
|--------|---------------------|--------------------|
| Relationship metadata | ✅ Supported (role, joined_at, etc.) | ❌ None |
| Reciprocal access | ✅ Both sides can query | ❌ Only the managing side |
| Separate permissions | ✅ Own ACLs | ❌ Tied to managing resource |
| Complexity | Higher | Lower |

- Use **Add/Remove** when: the relationship is simple (no metadata), one side clearly "owns" it, and you want minimal API surface.
- Use **Association resources** when: you need metadata, bidirectional queries, or independent access control on the relationship.

---

### 16 Polymorphism

#### 16.1 Motivation

- Sometimes a single collection contains resources of **different subtypes** (e.g., a `Messages` collection with `TextMessage`, `ImageMessage`, `VideoMessage`).
- **Polymorphic resource:** A resource with a `type` field that determines which subset of fields is relevant.

#### 16.2 Implementation

- Add a **`type` string field** to the resource:

```python
@dataclass
class Message:
    id: str = ""
    type: str = ""  # "text", "image", "video"
    # --- fields below vary by type ---
    text_content: str = ""        # only for type="text"
    image_uri: str = ""           # only for type="image"
    video_uri: str = ""           # only for type="video"
    video_duration_sec: float = 0 # only for type="video"
```

##### Data structure strategies

Three approaches for organizing type-specific fields:

| Strategy | Description | Pros | Cons |
|----------|-------------|------|------|
| **Superset** | All fields on a single flat resource; irrelevant fields left empty | Simple, flat | Grows unwieldy with many types |
| **Shared with interpretation** | A shared field whose *meaning* changes by type (e.g., `content` is text body or image URI) | Compact | Confusing semantics |
| **Typed dimension objects** | Nest type-specific data in sub-objects (e.g., `text_data`, `image_data`) | Clean separation | Deeper nesting; only one sub-object populated |

- **Recommended for most cases:** Superset for small type variations; typed dimension objects for larger ones.

#### 16.3 Validation

- The `type` field must be **immutable** — set at creation, never changed.
- On Create: validate that all **required** fields for the given type are present.
- On Create/Update: **ignore** fields that don't apply to the given type (don't reject them — be tolerant).

#### 16.4 Polymorphic methods — avoid them

- **Polymorphic resource:** One collection, multiple types → ✅ Fine.
- **Polymorphic method:** One method that behaves differently based on input type → ❌ Bad.
- Why: a polymorphic method assumes all current (and future) types can be handled uniformly. Adding a new type that needs different behavior breaks the contract.
- **Prefer:** Separate methods per type when behavior diverges.

> **Key principle:** It's fine for data to be polymorphic, but behavior should be monomorphic.

---

## Part 5: Collective Operations

### 17 Copy and move

#### 17.1 Motivation

- Users inevitably need to **duplicate** or **relocate** resources. Using standard methods (Create + Delete for move, Get + Create for copy) is fragile and non-atomic.
- Dedicated **custom methods** (`Copy`, `Move`) encapsulate the complexity and provide atomicity guarantees.

#### 17.2 Implementation

- **Copy:** `POST /resources/{id}:copy` — creates a duplicate, usually under a new or specified parent.
- **Move:** `POST /resources/{id}:move` — relocates the resource to a different parent.

```python
@dataclass
class CopyChatRoomRequest:
    id: str = ""
    destination_parent: str = ""

@dataclass
class MoveMessageRequest:
    id: str = ""
    destination_id: str = ""
```

##### Child resources

- When copying a parent, should child resources be copied too? Generally **yes** for copy (deep copy), but this should be evaluated case-by-case.
- When moving, child resources move automatically since their identity is relative to the parent.

##### External data (copy-on-write)

- If a resource references external data (e.g., a file in cloud storage), copying can either:
  - **Copy by reference:** Both resources point to the same external data. Cheaper but creates shared-state coupling.
  - **Copy by value (copy-on-write):** Defer the actual duplication until one copy is modified. Best of both worlds but more complex to implement.

##### Atomicity and consistency

- **Copy:** Use database snapshots or transactions for consistent reads during copy. If unavailable, lock writes (dangerous — enables DoS via spam copy requests). Last resort: ignore and accept a "smear" of data.
- **Move:** Consistency is harder — requires updating all cross-references to the moved resource. Use transactions or locks. Ignoring consistency during a move risks **overwriting concurrent updates**, which is far worse than during copy.

#### 17.3 Trade-offs

- Both operations are **exceptionally difficult** to implement correctly, especially move.
- **Copy** is often genuinely useful. **Move** is frequently a symptom of poor resource layout — consider fixing the hierarchy instead.
- Cutting corners on atomicity and consistency leads to data corruption. Implement carefully or don't implement at all.

---

### 18 Batch operations

#### 18.1 Motivation

- **Batch operation:** A method that operates on **multiple resources atomically** in a single API call.
- Web APIs lack built-in transaction support. Batch methods provide a limited form of atomicity across resources without requiring a full transaction system.
- Use case: enable or set a default config atomically — two operations that must both succeed or both fail.

#### 18.2 Overview

- Four batch custom methods, analogous to the standard methods (no batch List — that's just List with pagination):
  - `BatchGet<Resources>()`
  - `BatchCreate<Resources>()`
  - `BatchUpdate<Resources>()`
  - `BatchDelete<Resources>()`

#### 18.3 Implementation

##### Atomicity

- **All batch methods must be completely atomic** — all operations succeed or all fail. No partial success.
- Even for `BatchGet`: if 1 of 100 IDs is invalid, the entire request fails.
- This simplifies the response interface (no need to track per-item success/failure).

##### Operation on the collection

- Batch methods target the **collection**, not the parent resource:
  - ✅ `POST /chatRooms/*/messages:batchUpdate`
  - ❌ `POST /chatRooms/*:batchUpdateMessages`

##### Ordering of results

- Results **must** be returned in the same order as the requests/IDs were provided. This is critical for matching server-assigned IDs back to the original inputs.

##### Common fields

- Two strategies for structuring batch requests:

| Strategy | When to use |
|----------|-------------|
| **Hoist fields** into batch request (e.g., `ids: list[str]`) | Simple operations: BatchGet, BatchDelete |
| **List of individual requests** (e.g., `requests: list[CreateRequest]`) | Complex operations: BatchCreate, BatchUpdate |

- These strategies can be combined (e.g., hoist `parent` and `field_mask` while using a list of `UpdateRequest`).
- If a hoisted field **conflicts** with an individual request's field, reject the entire request (don't guess intent).

##### Operating across parents

- Use a **wildcard hyphen** (`-`) for the parent in the URL to indicate cross-parent operations:
  - `POST /chatRooms/-/messages:batchCreate` with individual `parent` fields per request.
- If a non-wildcard parent conflicts with request-level parents, reject the request.

##### Batch Get

```python
@dataclass
class BatchGetMessagesRequest:
    parent: str = ""   # specific parent or "-" for cross-parent
    ids: list[str] = field(default_factory=list)

@dataclass
class BatchGetMessagesResponse:
    resources: list[Message] = field(default_factory=list)
```

- Uses HTTP **GET**. IDs passed as query parameters.
- Supports a single hoisted `field_mask` for partial retrieval.
- No pagination — define and document an upper limit on batch size.

##### Batch Delete

```python
@dataclass
class BatchDeleteMessagesRequest:
    parent: str = ""
    ids: list[str] = field(default_factory=list)
```

- Uses HTTP **POST** (custom method convention). Returns `void`.
- Must be strictly **imperative**: deleting an already-deleted resource is an error (the batch didn't cause the deletion).

##### Batch Create

```python
@dataclass
class BatchCreateMessagesRequest:
    parent: str = ""   # or "-" for multi-parent
    requests: list[CreateMessageRequest] = field(default_factory=list)

@dataclass
class BatchCreateMessagesResponse:
    resources: list[Message] = field(default_factory=list)
```

- Uses a list of standard `CreateRequest` objects (not just resources) because the parent isn't stored on the resource itself.
- Results must be in the same order as requests — especially important since IDs don't exist yet.

##### Batch Update

```python
@dataclass
class BatchUpdateMessagesRequest:
    parent: str = ""
    requests: list[UpdateMessageRequest] = field(default_factory=list)
    field_mask: FieldMask = None  # hoisted, applies to all if set

@dataclass
class BatchUpdateMessagesResponse:
    resources: list[Message] = field(default_factory=list)
```

- Uses HTTP **POST** (not PATCH) — follows custom method convention.
- Field mask can be hoisted or per-request; if both are set, they must match.

#### 18.4 Trade-offs

- Atomicity is prioritized over convenience — even batch get fails entirely if one ID is bad.
- Input format is intentionally inconsistent across methods (IDs for get/delete, full requests for create/update) to favor simplicity per method over global uniformity.

---

### 19 Criteria-based deletion

#### 19.1 Motivation

- Batch delete requires knowing IDs in advance. Sometimes you want to delete all resources matching a **filter** without pre-fetching IDs.
- Stitching `List` + `BatchDelete` is non-atomic: resources matching the filter could change between the two calls.

#### 19.2 Overview

- **Purge method:** A custom method combining List's filter with BatchDelete's deletion.
- `POST /chatRooms/*/messages:purge`
- Extremely dangerous — this is the most powerful deletion tool in the API.

#### 19.3 Implementation

##### Safety: force flag (validation by default)

- **`force` boolean field** (default: `false`). When false, the purge acts as a **dry run** (validation only).
- This is the inverse of a `validateOnly` flag — the safe default is to *not* delete.
- Response includes `purge_count` (number of matches) and `purge_sample` (sample of matching resource IDs).

```python
@dataclass
class PurgeMessagesRequest:
    parent: str = ""
    filter: str = ""
    force: bool = False  # default = dry run only

@dataclass
class PurgeMessagesResponse:
    purge_count: int = 0
    purge_sample: list[str] = field(default_factory=list)
```

> **Figure 19.1** — Sequence: Consumer sends purge with `force=false` → gets count + sample → verifies → re-sends with `force=true` → deletion happens.

##### Filtering results

- The `filter` field works identically to the standard List method's filter.
- **Danger:** An empty or undefined filter matches **all resources**. This is consistent with List behavior but catastrophic for purge.

##### Result count

- For `force=true`: exact count of deleted resources.
- For `force=false` (validation): can be an **estimate** to save computation. Estimates should err on the side of overestimating.

##### Result sample set

- `purge_sample`: a list of IDs of resources that would be deleted. At least ~100 items for large data sets.
- Lets users spot-check that the filter matches the intended resources.

##### Consistency

- No guarantee that the same resources matched during validation will be deleted during execution. Data can change between calls.
- This is acceptable — if exact point-in-time behavior is needed, use List + BatchDelete instead.

#### 19.4 Trade-offs

- This method is inherently dangerous. Only expose it when absolutely necessary.
- Prefer batch delete when IDs are known. Purge is a last resort for large-scale criteria-based cleanup.

---

### 20 Anonymous writes

#### 20.1 Motivation

- Not all data fits the resource model. **Time-series data, analytics events, log entries** — data that is written once, never individually addressed, and only read as aggregates.
- Creating a full resource (with ID, Get, Update, Delete) for each data point is overkill.

#### 20.2 Overview

- **Write method:** A custom method for ingesting **anonymous data entries** — data without unique identifiers.
- Entries are write-only: no Get, Update, or Delete. Data is consumed only through aggregate queries.
- Terminology: **entry** (not resource) — emphasizes the non-addressable nature.

> **Figure 20.1** — Sequence: Client calls `WriteEntry(...)` → Server responds `200 OK` → later, `GetEntryCount(...)` returns aggregate.

#### 20.3 Implementation

```python
@dataclass
class ChatRoomStatEntry:
    name: str = ""
    value: str | int | float | bool = None

@dataclass
class WriteChatRoomStatEntryRequest:
    parent: str = ""
    entry: ChatRoomStatEntry = None
```

- **Return type:** `void` — there's nothing meaningful to return (no resource was created).
- **URL pattern:** Target the collection: `POST /chatRooms/*/statEntries:write` (not `/chatRooms/*:writeStatEntry`).
- **Batch variant:** `POST /chatRooms/*/statEntries:batchWrite` — also returns `void`.

##### Consistency

- Write methods can be **eventually consistent** — it's fine to return `200 OK` before the data is visible in aggregates.
- Return HTTP **202 Accepted** (instead of 200) if there's a significant delay before data visibility.
- **Do not use LROs** for write methods — entries have no unique ID to track, and creating Operation resources defeats the purpose of lightweight writes.

#### 20.4 Trade-offs

- Almost exclusively for **analytical/statistical data**. Not suitable for transactional data.
- Data loaded via write methods is a one-way street — it cannot be individually retrieved or removed.
- If worried about duplicate entries, use the request deduplication pattern (Ch 26).

---

### 21 Pagination

#### 21.1 Motivation

- Collections can grow too large for a single API response. Even single resources can become too large (e.g., a 100 MB attachment).
- **Pagination:** Splitting large result sets into manageable chunks delivered over multiple requests.

#### 21.2 Overview

- Uses **opaque page tokens** as cursors — not page numbers.
- Three key fields: `page_token` (request), `max_page_size` (request), `next_page_token` (response).

> **Figure 21.1** — Flow: Consumer requests page 1 → gets data + "Page 2 is next" → requests page 2 → gets data + "Page 3 is next" → requests page 3 → "It's the last page."

#### 21.3 Implementation

```python
@dataclass
class ListChatRoomsRequest:
    page_token: str = ""
    max_page_size: int = 0

@dataclass
class ListChatRoomsResponse:
    results: list[ChatRoom] = field(default_factory=list)
    next_page_token: str = ""
```

##### Page size

- **Maximum, not exact:** The API returns *up to* `max_page_size` results. It may return fewer (e.g., due to time limits on scanning).
- **Default:** ~10 results. Be consistent across all resources in the API.
- **Upper bound:** Silently clamp excessively large page sizes rather than rejecting them.

##### Page tokens

- **Termination:** Pagination is complete when `next_page_token` is empty/null — not when results are empty (a page can be empty but still have a next token).
- **Opacity:** Tokens must be **encrypted**, not just Base64-encoded. If consumers can decode the token, it becomes part of the API surface and can't be changed.
- **Format:** Base64-encoded encrypted string (UTF-8). Works in URLs and JSON.
- **Consistency:** Offset-based tokens suffer from duplicate/missing results when data changes. Use last-seen-result cursors instead.
- **Lifetime:** Set expiration (e.g., 60 minutes). Expired tokens simply fail — consumer retries from the beginning.

##### Total count

- Generally **don't include** a total result count — it's expensive to compute at scale.
- If absolutely needed, add a `total_results: int` field to the response. Accept that it may be slow or inaccurate.

##### Paging inside resources

- For very large single resources (e.g., file attachments), use the same pagination pattern with a **custom read method**:

```python
@dataclass
class ReadAttachmentRequest:
    id: str = ""
    page_token: str = ""
    max_bytes: int = 0

@dataclass
class ReadAttachmentResponse:
    chunk: Attachment = None
    field_mask: FieldMask = None  # which fields have data so far
    next_page_token: str = ""
```

#### 21.4 Trade-offs

- **No bidirectional paging.** Can only go forward. For browsing UIs, build a client-side cache.
- **No arbitrary windows.** Can't jump to "page 5." Use filters and ordering instead.

#### 21.5 Anti-pattern: Offsets and limits

- Using `offset` + `limit` parameters (like SQL's `OFFSET`/`LIMIT`) is tempting but problematic:
  - **Leaks implementation:** Ties the API to relational DB semantics forever.
  - **Expensive at scale:** Finding offset starting points in distributed systems gets progressively slower.
  - **Inconsistent:** Inserts during paging cause duplicate results.
- **Always prefer opaque page tokens** over offset/limit.

---

### 22 Filtering

#### 22.1 Motivation

- The standard List method returns all resources. Clients often need a subset matching specific criteria.
- Client-side filtering (fetch all → filter locally) wastes bandwidth and compute.

#### 22.2 Overview

- Add a **`filter` string field** to the standard List request. The API server evaluates the filter and returns only matching resources.

```python
@dataclass
class ListChatRoomsRequest:
    filter: str = ""
    max_page_size: int = 0
    page_token: str = ""
```

#### 22.3 Implementation

##### Structure: string vs. structured

- **String filters** (SQL-like): `title = "New Chat!" AND userLimit >= 5`
- **Structured filters** (MongoDB-like): `{ "title": "New Chat!", "userLimit": { "$gt": 5 } }`
- Both are functionally equivalent (interconvertible via serialize/parse).
- **Prefer string filters** because:
  - Syntax is enforced server-side (can evolve without client changes)
  - Familiar to anyone who knows SQL
  - More readable for complex Boolean conditions

##### Filter syntax and behavior

- Use an existing language spec (e.g., Google's AIP Filtering spec, CEL, or a SQL `WHERE` subset) rather than inventing your own.
- **Key constraints:**
  - **Execution time:** Filters should only require a single resource's context to evaluate — no joins, no cross-resource lookups, no external data fetches. Keep evaluation **hermetic**.
  - **Array fields:** Don't support index-based filtering (`tags[0] = "new"`). Instead support **presence checks** (`"new" in tags`). Arrays should be treated as unordered sets.
  - **Strictness:** Be strict — reject typos in field names with errors rather than silently returning empty results. Reject type mismatches (e.g., `userCount = "string"`) with errors.
  - **Custom functions:** For advanced filtering needs (prefix matching, image classification), expose **named functions** (e.g., `endsWith(title, "(new)")`, `imageContains(profilePhoto, "dog")`) rather than wildcards or regex.

#### 22.4 Trade-offs

- Filtering adds server-side resource cost but saves client-side waste. Worth supporting for most resources, especially if collections can grow large.
- String filters are easier to evolve over time than structured filters (no schema changes needed — just update docs).

---

### 23 Importing and exporting

#### 23.1 Motivation

- Standard methods and batch methods transfer data between the API server and the client. But sometimes data needs to flow directly between the API and an **external storage system** (S3, Samba, etc.).
- Using a middleman application (fetch from storage → create via API) wastes bandwidth and adds failure points.

#### 23.2 Overview

- Two custom methods: **Import** and **Export**.
- Both return **LROs** (they can take a long time).
- The API communicates directly with the external storage system, cutting out the client as middleman.

> **Figure 23.2** — Architecture: Data loader app calls `Import()` on the API server → API server fetches bytes directly from external storage → parses and creates resources internally.

- Configuration is split into:
  - **DataSource / DataDestination:** How to connect to the storage system (polymorphic — `S3Source`, `SambaSource`, etc.)
  - **InputConfig / OutputConfig:** How to transform data (content type, compression, file templates)

#### 23.3 Implementation

##### Import and export methods

```python
## POST /chatRooms/*/messages:export → returns LRO
## POST /chatRooms/*/messages:import → returns LRO
```

- Anchored to a specific resource type (e.g., `ExportMessages`, `ImportMessages`).
- Can also import non-addressable data into a single resource (e.g., `ImportTrainingData` into a `VirtualAssistant`).

##### Storage system configuration

```python
@dataclass
class DataSource:
    type: str = ""  # "s3", "samba", etc.

@dataclass
class S3Source(DataSource):
    type: str = "s3"
    bucket_id: str = ""
    mask: str = ""  # glob pattern, e.g., "folder/messages.*.csv"
```

- Separate `DataSource` (for import) and `DataDestination` (for export) interfaces — they're similar but not identical (glob mask vs. prefix).

##### Input/Output config

```python
@dataclass
class MessageInputConfig:
    content_type: str = ""        # "json", "csv", or auto-detect
    compression_format: str = ""  # "zip", "bz2", or none

@dataclass
class MessageOutputConfig:
    content_type: str = ""
    filename_template: str = ""   # e.g., "messages-part-${number}"
    max_file_size_mb: int = 0
    compression_format: str = ""
```

##### Consistency

- **Export:** Use database snapshots if available. Otherwise accept a "smear" of data (best-effort, not point-in-time). Exporting is **not** backing up.
- **Import:** Not equivalent to restore — imported IDs are ignored (new IDs assigned). Duplicate imports create duplicate resources.

##### Identifiers and collisions

- On import: **ignore resource IDs** from the source data. Assign new IDs. Keep source IDs in exported data for provenance tracking.
- Import ≠ backup/restore. No consistency guarantees. Duplicates are expected.

##### Failures and retries

- **Export failures:** Safe to retry (each export is independent). Leave partial data in storage — let the owner decide what to do with it.
- **Import failures:** Dangerous to retry naively — may create duplicates. Use an `import_request_id` per record for **deduplication** (same concept as Ch 26).

##### Filtering and field masks

- **Export:** Supports a `filter` string field (same syntax as List filter). Filter is placed on the export request, not inside `OutputConfig`.
- **Import:** Generally should **not** support filtering. The user should transform data before importing.

#### 23.4 Trade-offs

- Narrow scope: one resource type per import/export call. Not for multi-resource backup/restore.
- Import ≠ backup restore. No atomic guarantees. Designed as a simple data mover, not a consistency engine.

---

## Part 6: Safety and Security

### 24 Versioning and compatibility

#### 24.1 Overview

- **Backward compatibility:** A change is backward compatible if existing consumers continue to work without modification after the change is deployed.
- Backward compatibility is **context-dependent** — what counts as "compatible" varies by API and user base.

#### 24.2 Types of changes

- **Adding functionality:** New fields, methods, or resources. Generally backward compatible, but can still break consumers that do strict schema validation or iterate over unknown fields.
- **Fixing bugs:** Correcting wrong behavior. May break consumers who depend on the buggy behavior — a gray area.
- **Mandatory changes:** Forced by external requirements (e.g., GDPR compliance). Not optional; must be made regardless of compatibility.
- **Under-the-hood changes:** Performance improvements, swapping ML models, etc. Don't change the API contract, but may alter observable behavior (e.g., different prediction outputs from a new model).
- **Changing semantics:** Altering the *meaning* of existing fields/methods. Almost always breaking.

#### 24.3 Versioning strategies

##### 24.3.1 Perpetual stability

- **Concept:** Versions are frozen forever once released. Backward-compatible changes are injected into the *current* version. Incompatible changes are reserved for the next major version.
- Existing consumers are never forced to upgrade.
- Downside: over time, the API accumulates cruft since nothing is ever removed.

##### 24.3.2 Agile instability

- **Concept:** A sliding-window lifecycle for each version: **Preview → Current → Deprecated → Deleted**.
- Only **one version is "Current"** at a time. When a new version becomes current, the old one enters deprecation.
- Forces frequent upgrades; consumers must keep up.
- Downside: high maintenance burden on consumers.

##### 24.3.3 Semantic versioning (SemVer)

- Format: `major.minor.patch`
  - **Major** = breaking change
  - **Minor** = backward-compatible new features
  - **Patch** = backward-compatible bug fixes
- Widely understood, but granularity introduces complexity (many versions to manage).

#### 24.4 Trade-offs and spectrums

- **Granularity vs. Simplicity:** More versions = more precise compatibility signals, but harder to manage.
- **Stability vs. New functionality:** Stable APIs resist change; agile APIs evolve fast but break consumers.
- **Happiness vs. Ubiquity:** Aim to minimize the "cannot use this API" bucket while maximizing the "okay with this" bucket. Perfect happiness for all is impossible — optimize the distribution.

---

### 25 Soft deletion

#### 25.1 Overview

- **Soft deletion:** Marking a resource as deleted without physically removing it from storage. Enables undo.
- Implemented by adding a `deleted: bool` field (output-only) to the resource, or incorporating a deleted state into an existing state field.

#### 25.2 Implementation

##### Standard method behavior changes

- **Get:** Returns the resource normally even if `deleted == True`. No special handling needed.
- **List:** Excludes deleted resources by default. Add `include_deleted: bool` field to the request to optionally include them.
- **Delete:** Sets `deleted = True` and returns the resource (not void — allows the client to see the final state). Returns `412 Precondition Failed` if the resource is already deleted.

##### Custom methods

- **Undelete:** `POST /resources/{id}:undelete` — sets `deleted = False`. Returns `412 Precondition Failed` if the resource is not currently deleted.
- **Expunge:** `POST /resources/{id}:expunge` — permanently removes the resource from storage. Returns void. Can be called on any resource (deleted or not).

```python
## Flask-style soft deletion endpoints
from flask import Flask, jsonify, abort
app = Flask(__name__)

@app.route("/resources/<resource_id>", methods=["DELETE"])
def soft_delete(resource_id):
    resource = db.get(resource_id)
    if resource["deleted"]:
        abort(412, "Resource is already deleted")
    resource["deleted"] = True
    resource["expire_time"] = now() + timedelta(days=30)
    db.save(resource)
    return jsonify(resource)

@app.route("/resources/<resource_id>:undelete", methods=["POST"])
def undelete(resource_id):
    resource = db.get(resource_id)
    if not resource["deleted"]:
        abort(412, "Resource is not deleted")
    resource["deleted"] = False
    resource["expire_time"] = None
    db.save(resource)
    return jsonify(resource)

@app.route("/resources/<resource_id>:expunge", methods=["POST"])
def expunge(resource_id):
    db.permanently_delete(resource_id)
    return "", 204
```

##### Expiration

- **`expire_time`:** Timestamp field set when a resource is soft-deleted (e.g., 30 days in the future per policy). After expiration, the resource is automatically expunged.

##### Other considerations

- **Referential integrity:** Same rules apply as hard delete — dependent resources need to be handled.
- **Batch delete:** Inherits soft-delete behavior (marks each as deleted).
- **Adding soft deletion to an existing API** that previously hard-deleted is likely a **breaking change** — increment the major version.

#### 25.3 Trade-offs

- Soft deletion is powerful for undo and audit, but increases storage requirements and query complexity (must filter out deleted resources).
- The `expunge` method provides a safety valve for true permanent removal (e.g., PII compliance).

---

### 26 Request deduplication

#### 26.1 Overview

- **Problem:** Network unreliability means a request might be sent but the response never arrives. For idempotent methods (GET), just retry. For non-idempotent methods (POST, PATCH), retrying blindly may duplicate work.
- **Solution:** Attach a unique **request identifier** (`request_id`) to each non-idempotent request. The server uses this to detect and deduplicate retries.

> **Figure 26.1–26.2** — Two failure modes: (1) request never reaches server, (2) response never reaches client. The client can't distinguish them.

> **Figure 26.3** — Sequence diagram showing the deduplication flow: server checks cache for request ID, processes if new, caches the response, and returns the cached response on retry.

#### 26.2 Implementation

##### 26.2.1 Request identifier

- An optional string field on request interfaces, chosen by the **client** (not server-generated).
- Should follow the same format standards as resource identifiers (random, Crockford's Base32, with checksum character).
- If the request ID is invalid, return `400 Bad Request`. If it's blank/missing, skip deduplication entirely and process normally.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CreateChatRoomRequest:
    resource: dict
    request_id: Optional[str] = None
```

##### 26.2.2 Avoiding derived identifiers

- Don't hash the request body to derive the ID — this implicitly deduplicates without the client opting in.
- Deduplication should be an explicit client intent, not an implicit default.

##### 26.2.3 Response caching

- When processing a request with a `request_id`, cache the full response keyed by that ID.
- On a duplicate request, return the cached response as-is — even if the underlying data has since changed (stale data is acceptable and expected here; the goal is to return what the client *would have seen*).

##### 26.2.4 Request ID collisions

- Since clients choose their own IDs, collisions are possible (two different clients accidentally use the same ID).
- **Defense:** When caching, also store a **fingerprint** (e.g., SHA-256 hash) of the request body. On a cache hit, verify the fingerprint matches. If it doesn't, return `409 Conflict`.

```python
import hashlib, json

def handle_with_dedup(request_id: str, request_body: dict, cache, process_fn):
    if request_id is None:
        return process_fn(request_body)

    body_hash = hashlib.sha256(
        json.dumps(request_body, sort_keys=True).encode()
    ).hexdigest()

    cached = cache.get(request_id)
    if cached:
        if cached["hash"] == body_hash:
            return cached["response"]
        else:
            raise ConflictError("409 Conflict: request ID collision")

    response = process_fn(request_body)
    cache.set(request_id, {"response": response, "hash": body_hash})
    return response
```

##### 26.2.5 Cache expiration

- Retries typically happen within seconds of failure. A good default: **5 minutes** TTL, restarting the timer on each cache hit.
- This is technically a rate-limiter on duplicate execution, not a true guarantee of single-execution forever.

#### 26.3 Trade-offs

- Simple mechanism (one optional field) that prevents dangerous duplication on non-idempotent methods.
- Some APIs may make `request_id` **required** rather than optional for particularly sensitive methods.
- Add on an as-needed basis, starting with the most sensitive methods.

---

### 27 Request validation

#### 27.1 Overview

- **Problem:** Unsafe API methods (create, update, delete) can't be safely poked to see what happens. But users need a way to preview behavior without side effects.
- **Solution:** Add a `validate_only: bool` field to request interfaces. When `True`, the server validates the request (permissions, referential integrity, field format, etc.) but does **not** execute it.

```python
@dataclass
class CreateChatRoomRequest:
    resource: dict
    validate_only: bool = False  # Default must be False
```

#### 27.2 Implementation

##### Behavior

- **Default is `False`** — critical. Inverting the default would cripple the API since every request would need to explicitly opt out.
- When `validate_only=True`, the server should validate as much as possible: permissions, field format, referential integrity, uniqueness constraints.
- If validation passes, return a **plausible response** (populate what fields you can; server-generated fields like IDs may be left blank or filled with realistic placeholders).
- If validation fails, return the exact same error that a real request would produce.
- Validation requests must be **safe, idempotent, and free of side effects**.

> **Figure 27.2** — Validation requests may still connect to internal components (storage, access control) to check references and permissions, but never write data.

##### 27.2.1 External dependencies

- If an external service supports validation calls, use them. If not, **skip that validation** entirely.
- Safety and idempotency are more important than validating every single aspect.
- Fallback: perform local validation where possible (e.g., email format check instead of actually sending an email).

> **Figure 27.3** — External dependencies like SMTP servers make full validation difficult/impossible. Avoid side effects; skip what you can't safely validate.

##### 27.2.2 Special side effects

- For methods with random or nondeterministic outcomes (e.g., a lottery), a validation response should return a **plausible** result — not necessarily the *real* one.
- The goal is representative, not accurate. Both a winning and losing result are valid validation responses.

#### 27.3 Trade-offs

- Simple flag that gives users confidence before executing dangerous operations.
- Benefits the API too: expensive methods (monetarily, computationally) avoid waste when users just want to validate.
- Not all methods need it — add where it provides value.

---

### 28 Resource revisions

#### 28.1 Overview

- **Resource revision:** A snapshot of a resource at a specific point in time, identified by a unique `revision_id` and timestamped with `revision_create_time`.
- Enables viewing history, rolling back to a prior state, and deleting specific historical snapshots.
- Not a separate interface — just two additional fields on the existing resource:

```python
@dataclass
class Message:
    id: str
    content: str
    # ... other fields ...
    revision_id: str          # Unique per-revision
    revision_create_time: str  # ISO timestamp
```

#### 28.2 Implementation

##### 28.2.1 Revision identifiers

- **Random identifiers preferred** over incrementing numbers or timestamps:
  - Incrementing numbers reveal gaps when revisions are deleted.
  - Timestamps risk collisions under high concurrency.
  - Random IDs (Crockford's Base32, ~13 chars / 60 bits) are opaque and sufficient — resources have far fewer revisions than total resources.
- Include a checksum character for the same reasons as resource IDs.

##### 28.2.2 Creating revisions

- **Implicit:** The API automatically creates a revision on every update (or on a schedule, or at milestones). Most common approach — like Google Docs revision history.

> **Figure 28.1** — Flow: User calls UpdateResource → API updates resource in DB → API automatically calls createRevision to store the snapshot.

- **Explicit:** User calls a custom `CreateRevision` method when they want a snapshot. Puts the user in control.

> **Figure 28.2** — Flow: User calls CreateRevision → API reads current resource → stores a new revision.

```python
## Explicit revision creation
@app.route("/chatRooms/<room_id>/messages/<msg_id>:createRevision", methods=["POST"])
def create_revision(room_id, msg_id):
    message = db.get_message(msg_id)
    revision = store_revision(message)  # Snapshot with new revision_id
    return jsonify(revision)
```

- Whichever strategy is chosen, be consistent across all revisable resource types.
- The `revision_id` must be populated when a resource is first created.

##### 28.2.3 Retrieving specific revisions

- Use the `@` separator: `GET /chatRooms/1/messages/2@abcd` retrieves revision `abcd` of message `2`.
- The standard Get method handles this — no new endpoint needed.
- The returned resource's `id` field should mirror exactly what was requested (including the `@revision` suffix if provided).

##### 28.2.4 Listing revisions

- Custom method: `GET /resources/{id}:listRevisions` (not the standard List method, since revisions aren't child resources).
- Supports pagination (same pattern as Ch 21). Uses an `id` field rather than `parent` since the target is a single resource.

##### 28.2.5 Restoring a previous revision

- Custom method: `POST /resources/{id}:restoreRevision` with `revision_id` in the request body.
- Creates a **new** revision whose data is copied from the specified old revision. Does not move or delete the old revision.
- This preserves history — the old revision stays in place; a new revision (with a new ID and current timestamp) appears at the top.

```python
@app.route("/messages/<msg_id>:restoreRevision", methods=["POST"])
def restore_revision(msg_id):
    target_rev_id = request.json["revision_id"]
    # Fetch old revision data
    old = db.get_message(f"{msg_id}@{target_rev_id}")
    # Update current resource to match old data
    db.update_message(msg_id, old.content)
    # Create a new revision representing the restoration
    new_rev = db.create_revision(msg_id)
    return jsonify(new_rev)
```

##### 28.2.6 Deleting revisions

- Custom method: `DELETE /resources/{id}:deleteRevision` — requires the full resource+revision identifier.
- **Separate from the standard Delete method** — mixing up "delete the resource" and "delete a single revision" could be catastrophic.
- **Cannot delete the current (most recent) revision** — returns `412 Precondition Failed`. Deleting the current revision would implicitly restore a previous one, expanding the method's scope.
- **Revisions should always be hard-deleted** (not soft-deleted), since restoring a soft-deleted resource may need to jump across revision states.

##### 28.2.7 Handling child resources

- By default, revisions should focus on a **single resource's data**, not its entire child hierarchy.
- Hierarchy-aware revisions (snapshotting the resource and all children) are much more complex and storage-intensive. Avoid unless it's a firm business requirement.

#### 28.3 Trade-offs

- Powerful for audit trails, undo, and legal document tracking, but adds significant complexity and storage overhead.
- Hierarchy-aware revisions are even more extreme. If resource revisioning can be avoided, it should be.

---

### 29 Request retrial

#### 29.1 Overview

- **Problem:** Server-side errors are often transient (overload, temporary downtime). Clients need guidance on *whether* and *when* to retry.
- Two categories of errors:
  - **Client errors (4xx):** Usually the request itself is wrong — retrying won't help (except for specific codes).
  - **Server errors (5xx):** Often transient — retrying may succeed.

#### 29.2 Implementation

##### 29.2.1 Retry eligibility

Three categories of HTTP error codes:

**Generally retriable:**

| Code | Name | Reason |
|------|------|--------|
| 408 | Request Timeout | Client was too slow |
| 421 | Misdirected Request | Sent to wrong server |
| 425 | Too Early | Server doesn't want to handle a potentially replayed request |
| 429 | Too Many Requests | Rate limited |
| 503 | Service Unavailable | Server overloaded |

**Definitely not retriable:**

| Code | Name | Reason |
|------|------|--------|
| 403 | Forbidden | Server refuses to handle it |
| 405 | Method Not Allowed | Invalid method |
| 412 | Precondition Failed | Precondition not met |
| 501 | Not Implemented | Server doesn't support it |

**Maybe retriable** (depends on idempotency):

| Code | Name | Reason |
|------|------|--------|
| 500 | Internal Server Error | Unknown failure |
| 502 | Bad Gateway | Downstream sent invalid response |
| 504 | Gateway Timeout | Downstream didn't respond |

For "maybe" cases, use request deduplication (Ch 26) to make retries safe.

##### 29.2.2 Exponential back-off

- Start with a 1-second delay. On each failure, double it: 1s → 2s → 4s → 8s → 16s → ...
- Add **maximum delay** (e.g., 32s) and **maximum retries** (e.g., 10) to prevent infinite loops.

##### 29.2.3 Stampeding herds

- **Stampeding herd:** Many clients fail simultaneously and all retry on the same exponential schedule, re-overloading the server in synchronized waves.
- **Fix:** Add **random jitter** to each delay. The jitter is not additive to the doubling — it's an independent random offset per attempt.

```python
import asyncio
import random

async def get_with_retries(
    fetch_fn,
    resource_id: str,
    max_delay_s: float = 32.0,
    max_retries: int = 10,
):
    delay_s = 1.0
    for attempt in range(max_retries):
        try:
            return await fetch_fn(resource_id)
        except RetriableError:
            if attempt == max_retries - 1:
                raise
            actual_delay = delay_s + random.random()  # jitter up to 1s
            await asyncio.sleep(actual_delay)
            delay_s = min(delay_s * 2, max_delay_s)
```

##### 29.2.4 Retry-After header

- When the server knows exactly when a request will be eligible for retry (e.g., rate-limit reset), use the `Retry-After` HTTP header (RFC 7231, section 7.1.3).
- **Prefer durations** (e.g., `Retry-After: 120`) **over timestamps** — clock synchronization between client and server is unreliable.
- When `Retry-After` is present, the client should use that value instead of the exponential back-off delay.

#### 29.3 Trade-offs

- Relies on clients following the rules — the server ultimately has no control over retry behavior.
- Essentially zero downside: exponential back-off is a well-proven standard, and `Retry-After` only helps when the server has extra information.

---

### 30 Request authentication

#### 30.1 Overview

Three requirements for authenticating API requests:

- **Origin:** Proof that the request came from the claimed sender (user identity).
- **Integrity:** Proof that the request content was not tampered with in transit.
- **Nonrepudiation:** The sender cannot later deny having sent the request. This requires **asymmetric** credentials — if both parties share a secret, the server could forge a request and the sender could deny it.

#### 30.2 Digital signatures

- A digital signature is a chunk of bytes that can only be generated with a **private key** and verified with the corresponding **public key**.
- Meets all three requirements: origin (only the private key holder can sign), integrity (signature is tied to exact content), nonrepudiation (only one party holds the private key).

#### 30.3 Implementation

##### 30.3.1 Credential generation

- The **user** generates a public-private keypair (e.g., RSA 2048-bit). The private key must **never leave the user's hands**.
- Why user-generated? If the server generated the private key, nonrepudiation breaks — the server could have kept a copy.

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_credentials():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key
```

##### 30.3.2 Registration and credential exchange

- User registers with the API by providing their **public key**. The server stores it and returns a unique user ID.
- Identity = possession of the private key. No passwords, no biometrics — just asymmetric key ownership.

> **Figure 30.1** — Registration flow: Client sends `CreateUser({publicKey: key_pub})` → Server stores key, returns `User {id: 1234, publicKey: key_pub}`.

##### 30.3.3 Generating and verifying signatures

```python
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def sign(payload: bytes, private_key) -> bytes:
    return private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

def verify(payload: bytes, signature: bytes, public_key) -> bool:
    try:
        public_key.verify(signature, payload, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False
```

##### 30.3.4 Request fingerprinting

- Don't just sign the body — sign a **fingerprint** of the entire request, including:

| Field | Location | Description |
|-------|----------|-------------|
| Method | First line | HTTP verb (GET, POST, etc.) |
| Path | First line | Target resource path |
| Host | Header | Destination host |
| Content | Body | Request payload (as a Digest header hash) |
| Date | Header | When the request was created |

- The `(request-target)` pseudo-header combines method + path: `post /chatRooms/1`.
- The `Digest` header stores a Base64-encoded SHA-256 hash of the body, avoiding signing arbitrarily large payloads directly.
- Fingerprint = newline-joined `header: value` pairs in a defined order.

##### 30.3.5 Including the signature

- Send a `Signature` HTTP header containing: `headers` (ordered list of signed headers), `keyId` (user ID for public key lookup), `algorithm` (e.g., `rsa-sha256`), and the `signature` itself.

Example header value:
```
keyId="1234",algorithm="rsa-sha256",headers="(request-target) host date digest",signature="mgBAQEsEsoBCgIOBiNfum37y..."
```

##### 30.3.6 Authenticating requests (server side)

1. Verify the `Digest` header matches the actual request body hash.
2. Parse the `Signature` header to extract metadata.
3. Recompute the fingerprint using the headers listed in the signature.
4. Look up the public key by `keyId`.
5. Verify the signature against the fingerprint using the public key.

#### 30.4 Trade-offs

- Digital signatures with asymmetric keys are the most secure option (nonrepudiation), but computationally expensive.
- For many APIs, **HMAC** (shared secret) or **OAuth 2.0** (token-based) are simpler and sufficient when nonrepudiation isn't required.
- Use digital signatures when: third parties are involved, requests are sensitive (health/financial records), or audit trails must prove who made each request.

---

## Glossary of Major Concepts

| Concept | Definition |
|---------|-----------|
| **API (Application Programming Interface)** | A contract defining how two computer systems interact, either via a local library or over a network. |
| **Resource** | The fundamental noun in a resource-oriented API; a structured data entity with a unique identifier. |
| **Resource-oriented API** | An API design style centered on resources (nouns) with standard methods (verbs) rather than ad-hoc RPC actions. |
| **Standard methods** | The five canonical operations on resources: Get, List, Create, Update, Delete — mapped to HTTP verbs. |
| **Custom method** | A non-standard action on a resource, expressed as a verb on the resource URL (e.g., `:archive`, `:sendEmail`). |
| **Identifier** | A unique, opaque, server-generated string (typically Crockford's Base32 + checksum) that permanently identifies a resource. |
| **Field mask** | A list of field paths specifying which fields to update in a partial-update (PATCH) request. |
| **Singleton sub-resource** | A 1:1 child resource with no ID of its own; accessed by type under its parent (e.g., `/users/1/settings`). |
| **Cross reference** | A string field on a resource that holds the identifier of another resource, creating a pointer relationship. |
| **Association resource** | A dedicated resource representing a many-to-many relationship between two other resources. |
| **Polymorphic resource** | A resource with a `type` discriminator field and type-specific data stored in a one-of/union structure. |
| **Long-running operation (LRO)** | A resource representing an in-progress asynchronous task, polled until completion. |
| **Rerunnable job** | A stored configuration resource that can be executed repeatedly, each run producing an LRO. |
| **Copy / Move** | Custom methods that duplicate or relocate a resource, using an `destinationParent` identifier for the target location. |
| **Batch operations** | Methods that operate on multiple resources in a single call: BatchGet, BatchCreate, BatchUpdate, BatchDelete. |
| **Atomicity** | A guarantee that a batch operation either fully succeeds or fully fails — no partial results. |
| **Criteria-based deletion (Purge)** | A custom method that deletes all resources matching a filter string; uses a `force` flag for safety and returns a count. |
| **Anonymous write (Entry)** | A write-only data record (e.g., log entry) that is not a full resource — no ID, no Get method, eventually consistent. |
| **Pagination** | Splitting large List results across pages using opaque `page_token` cursors and `max_page_size` limits. |
| **Filtering** | A string-based query language on List requests that supports comparison, logic, and function operators with hermetic evaluation. |
| **Importing / Exporting** | Custom methods for bulk data transfer between an API and external storage (DataSource / DataDestination). |
| **Backward compatibility** | A property of a change where existing consumers continue to work without modification. |
| **Semantic versioning (SemVer)** | A versioning scheme (`major.minor.patch`) communicating the nature of changes. |
| **Perpetual stability** | A versioning strategy where released API versions are frozen forever; only compatible changes are injected. |
| **Agile instability** | A versioning strategy with a sliding lifecycle (Preview → Current → Deprecated → Deleted). |
| **Soft deletion** | Marking a resource as deleted (`deleted: True`) without physically removing it; supports Undelete and Expunge. |
| **Expunge** | A custom method that permanently, irreversibly removes a (soft-)deleted resource. |
| **Request deduplication** | Using a client-chosen `request_id` to prevent non-idempotent methods from executing twice on retry. |
| **Request validation** | A `validate_only: bool` flag that makes the server check the request without executing it — safe and idempotent. |
| **Resource revision** | A timestamped snapshot of a resource identified by a `revision_id`, enabling history browsing and rollback. |
| **Exponential back-off** | A retry timing strategy that doubles the delay after each failed attempt (1s → 2s → 4s → ...). |
| **Jitter** | Random noise added to retry delays to prevent stampeding herds (many clients retrying in sync). |
| **Retry-After header** | An HTTP response header (RFC 7231) specifying how long a client should wait before retrying. |
| **Digital signature** | A cryptographic value generated with a private key and verified with a public key, proving origin, integrity, and nonrepudiation. |
| **Request fingerprint** | A canonical representation of an HTTP request (method, path, host, date, body digest) used as the payload for digital signing. |
| **Nonrepudiation** | The inability of the request sender to later deny having sent the request; requires asymmetric credentials. |
| **Idempotent** | A property of an operation where executing it multiple times produces the same result as executing it once. |
| **Etag / Concurrency control** | A version token used to detect concurrent modifications and prevent lost updates (optimistic locking). |
| **Data integrity (references)** | Ensuring that cross-references always point to valid, existing resources; handling dangling pointers. |
| **Consistency smear** | A time window during import/export where the exported data may reflect a mix of states due to concurrent modifications. |