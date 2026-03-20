# Book3 - Architecture Patterns with Python
**By Harry Percival & Bob Gregory (O'Reilly, 2020)**
**Subtitle:** Enabling Test-Driven Development, Domain-Driven Design, and Event-Driven Microservices

> Core thesis: As software grows in complexity, the way we structure our code matters more than the way we write individual functions. This book applies DDD, TDD, and event-driven patterns in Python to build systems that are testable, maintainable, and scalable.

---

## Introduction

### Why Do Our Designs Go Wrong?

- **Big ball of mud**: the natural state of software when we don't actively manage complexity
- Symptoms: hard to change, hard to test, side-effect-laden code
- The cure: **encapsulation** (simplifying behavior & hiding data) and **abstractions** (simplified interfaces hiding complex details)
- Layering: each layer depends only on the layer below it

### Encapsulation and Abstractions

- **Encapsulation**: simplifying behavior and hiding data behind a well-defined interface
- **Abstraction**: a simplified description of a system that emphasizes some details while ignoring others
- In traditional layered architecture, the problem is tight coupling to the database ("everything depends on the DB")

### The Dependency Inversion Principle

- **DIP**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- Instead of `BusinessLogic -> Database`, use `BusinessLogic -> AbstractRepository <- ConcreteRepository`
- The domain model should be the most important layer and should have *no* dependencies on infrastructure

---

## Part I: Building an Architecture to Support Domain Modeling

---

## Chapter 1: Domain Modeling

### What Is a Domain Model?

- **Domain model**: the mental map that business owners carry of the business processes they manage
- The software should mirror this mental map as closely as possible
- The book's example domain: a furniture allocation service (assigning incoming orders to batches of stock)

### Exploring the Domain Language

- Key terms from the example domain:
  - **SKU** (Stock Keeping Unit): a unique product type (e.g., `RED-CHAIR`)
  - **Batch**: a quantity of a SKU arriving on a specific date
  - **Order Line**: a single line on a customer's order (SKU + quantity)
  - **Allocate**: link an order line to a batch, reducing available stock

### Unit Testing Domain Models

```python
# Domain model tests are pure Python - no DB, no frameworks
def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=date.today())
    line = OrderLine("order-ref", "SMALL-TABLE", 2)

    batch.allocate(line)

    assert batch.available_quantity == 18
```

- Tests use plain Python objects — no ORM, no framework
- Business rules are expressed as simple unit tests

### Dataclasses Are Great for Value Objects

- **Value Object**: defined by its attributes, has no persistent identity, is interchangeable with other instances with same values
- Use `@dataclass(frozen=True)` for immutability

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int
```

### Entities vs Value Objects

| | Entity | Value Object |
|---|---|---|
| Identity | Has a persistent identity | Defined entirely by values |
| Equality | By reference/ID | By value (structural equality) |
| Mutability | Typically mutable | Preferably immutable |
| Example | `Batch` (has a reference) | `OrderLine` (no unique identity) |

### Domain Services

- When a piece of logic doesn't naturally belong to any existing entity/value object, it becomes a **domain service function**
- Example: `allocate()` is a standalone function in `model.py`, not a method on either `Order` or `Batch`

```python
# Domain service function (src/allocation/domain/model.py)
def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
    batch.allocate(line)
    return batch.reference
```

### Exceptions as Domain Concepts

```python
class OutOfStock(Exception):
    pass
```

- Domain exceptions are part of the ubiquitous language

---

## Chapter 2: Repository Pattern

### The Normal ORM Way: Model Depends on ORM

- Typical approach: define your model classes inheriting from the ORM base class (e.g., `django.db.models.Model`)
- Problem: your domain model is now coupled to the ORM — the most important layer depends on infrastructure

### Inverting the Dependency: ORM Depends on Model

- **Key library**: `SQLAlchemy` (specifically its Classical Mapping / Imperative Mapping)
- Define your domain model as plain Python classes *first*, then tell SQLAlchemy how to map them

```python
# orm.py — SQLAlchemy imperative/classical mapping
from sqlalchemy.orm import mapper, relationship
from domain import model

def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)  # table object
    mapper(model.Batch, batches, properties={
        '_allocations': relationship(lines_mapper, secondary=allocations)
    })
```

- This keeps the domain model **ignorant of persistence** — it's just plain Python classes
- The ORM imports the model, not the other way around

### Introducing the Repository Pattern

- **Repository**: an abstraction over persistent storage; it pretends all data is in memory
- Simplest possible interface: `.add()` and `.get()`

```python
import abc
from domain import model

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(
            reference=reference
        ).one()

    def list(self):
        return self.session.query(model.Batch).all()
```

### Building a Fake Repository for Tests

```python
class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
```

- Fake repos enable fast, isolated unit tests with no DB needed

### Trade-Offs

| Pros | Cons |
|---|---|
| Simple interface for storage | Extra layer of abstraction (an "ORM is already an abstraction") |
| Easy to swap infra via fakes for testing | ORM mapping requires extra setup |
| Writes are decoupled from reads | Another thing for devs to learn |

---

## Chapter 3: A Brief Interlude: On Coupling and Abstractions

### Abstracting State Aids Testability

- Problem: how do you test code that has side effects (file I/O, HTTP calls, DB writes)?
- Three approaches:
  1. **Mock everything** (fragile, couples tests to implementation)
  2. **Edge-to-edge testing** (integration/E2E — slow, complex)
  3. **Abstract away side effects** behind simple interfaces (the book's preferred approach)

### The "Ports and Adapters" / Hexagonal Architecture

- Business logic at the core, infrastructure at the edges
- **Port**: an abstract interface (e.g., `AbstractRepository`)
- **Adapter**: a concrete implementation (e.g., `SqlAlchemyRepository`, `FakeRepository`)

### Functional Core, Imperative Shell

- Alternative framing: keep the *core* logic pure (no side effects), push I/O to the *shell*
- Not always achievable in Python, but a useful ideal

### Choosing the Right Abstraction

- Good abstractions simplify testing, aid in reasoning about code
- Bad abstractions add complexity without reducing coupling
- Rule of thumb: introduce an abstraction when you have a *concrete reason* (e.g., testability, swappability)

---

## Chapter 4: Our First Use Case: Flask API and Service Layer

### Connecting Our Application to the Real World

- **Flask** is the web framework used throughout the book
- Entrypoint (Flask route) should be thin — it just translates HTTP requests into domain operations

### A Typical Service Function

```python
# service_layer/services.py
def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batchref = model.allocate(OrderLine(orderid, sku, qty), batches)
    session.commit()
    return batchref
```

- **Service layer** (aka use-case layer): orchestrates a workflow
  - Fetches data from repositories
  - Calls domain model methods
  - Commits changes
- It doesn't *contain* business logic — it *coordinates* it

### The Service Layer and the Flask Endpoint

```python
# entrypoints/flask_app.py
@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            repo, session,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400
    return jsonify({"batchref": batchref}), 201
```

### Why Is Everything Called a Service?

- **Domain service**: pure logic that doesn't belong on an entity (e.g., `model.allocate()`)
- **Service layer / application service**: orchestration — fetches objects, invokes domain, persists results
- **Infrastructure service**: talks to external systems (email, file systems)

### Testing the Service Layer with Fakes

```python
# Unit tests use FakeRepository — no database needed
def test_returns_allocation():
    repo = FakeRepository([
        Batch("b1", "COMPLICATED-LAMP", 100, eta=None),
    ])
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, FakeSession())
    assert result == "b1"
```

---

## Chapter 5: TDD in High Gear and Low Gear

### Test Pyramid / Test Spectrum

- **Unit tests** (domain model): fast, isolated, business-rule focused
- **Service-layer tests**: test use cases, use fakes for infra
- **E2E tests** (against Flask + real DB): slow but validate integration

### Rules of Thumb for Test Types

- Write a few E2E tests to prove the plumbing works
- Write the bulk of your tests against the service layer (using fakes)
- Write unit tests for complex domain logic
- Aim to test *behavior*, not implementation

### High Gear vs. Low Gear

- **Low gear**: testing the domain model directly when building/debugging complex logic
- **High gear**: testing via the service layer once the API is stable
- Moving tests up to the service layer makes them less coupled to implementation — easier to refactor

### Fully Decoupling the Service-Layer Tests from the Domain

- Ideal: service-layer tests only use domain primitives (strings, ints) — never import domain classes
- This makes it easier to change the domain model without rewriting all tests

---

## Chapter 6: Unit of Work Pattern

### The Unit of Work Collaborates with the Repository

- **Unit of Work (UoW)**: abstracts the concept of an atomic operation / database transaction
- Provides a single entrypoint to repositories and handles `commit()` / `rollback()`

```python
class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError
```

### Real and Fake UoW

```python
# Real UoW
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


# Fake UoW for tests
class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
```

### Using UoW in Service Layer

```python
def allocate(orderid: str, sku: str, qty: int,
             uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:  # context manager handles transaction
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        batchref = product.allocate(line)
        uow.commit()  # explicit commit
    return batchref
```

- The `with` block ensures rollback on failure (via `__exit__`)
- Explicit `commit()` makes it clear when a transaction succeeds

---

## Chapter 7: Aggregates and Consistency Boundaries

### Why Do We Need Aggregates?

- An **aggregate** is a cluster of domain objects treated as a single unit for data changes
- It acts as a **consistency boundary**: all invariants within the aggregate are guaranteed to be consistent after each operation
- Operations across aggregates accept **eventual consistency**

### Choosing an Aggregate

- In the allocation example, `Product` becomes the aggregate root
- A `Product` contains its `Batch`es — you always go through the `Product` to allocate

```python
class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")
        batch.allocate(line)
        self.version_number += 1
        return batch.reference
```

### Optimistic Concurrency with Version Numbers

- `version_number` is incremented on each change to detect concurrent modifications
- Implemented with SQLAlchemy's `version_id_col` feature

```sql
-- Optimistic lock at DB level
UPDATE products SET version_number=:new
WHERE sku=:sku AND version_number=:old
```

- If two transactions try to modify the same `Product` concurrently, one will fail (0 rows updated) and retry

### One Aggregate = One Repository

- Each aggregate type gets its own repository
- The repository fetches the *entire* aggregate (root + children) and saves it as a unit
- Aggregates reference each other only by identity (e.g., `sku` string), not by direct object reference

---

## Chapter 8: Events and the Message Bus

### Events

- **Domain Event**: a data structure representing something that happened in the domain
- Events are simple dataclasses

```python
from dataclasses import dataclass

class Event:
    pass

@dataclass
class OutOfStock(Event):
    sku: str

@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str
```

### The Model Raises Events

- Domain objects collect events on an internal list; they don't dispatch them directly
- Events are harvested and dispatched *after* the transaction commits

```python
class Product:
    def __init__(self, sku, batches, version_number=0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = []  # list of domain events

    def allocate(self, line):
        try:
            batch = next(...)
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None
        ...
```

### The Message Bus Maps Events to Handlers

```python
# service_layer/messagebus.py
HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]

def handle(event: events.Event, uow: AbstractUnitOfWork):
    for handler in HANDLERS[type(event)]:
        handler(event, uow=uow)
```

### The UoW Publishes Events to the Message Bus

```python
class AbstractUnitOfWork(abc.ABC):
    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)
```

- `products.seen` tracks all aggregates loaded during this UoW
- After commit, the service layer calls `messagebus.handle()` for each collected event

---

## Chapter 9: Going to Town on the Message Bus

### A New Architecture: Everything Is an Event Handler

- Refactors the entire application so that *all use cases* are event handlers
- The Flask endpoint just creates an event and passes it to the message bus
- The message bus becomes the single entrypoint for the service layer

```python
# Flask entrypoint
@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(
            request.json["orderid"], request.json["sku"], request.json["qty"]
        )
        results = messagebus.handle(event, uow)
        batchref = results.pop(0)
    except InvalidSku as e:
        return jsonify({"message": str(e)}), 400
    return jsonify({"batchref": batchref}), 201
```

### Test-Driving a New Handler

- New use case: `BatchQuantityChanged` event triggers reallocation if needed
- Test is end-to-end through the message bus: send events, assert outcomes

### Optionally: Unit Testing Event Handlers in Isolation with a Fake Message Bus

```python
class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))
```

- Allows testing individual handlers without triggering the full chain
- Use edge-to-edge tests first; resort to isolated handler tests only for complex chains

---

## Chapter 10: Commands and Command Handler

### Commands and Events

| | Event | Command |
|---|---|---|
| Named | Past tense (`BatchCreated`) | Imperative mood (`CreateBatch`) |
| Error handling | Fail independently | Fail noisily |
| Sent to | All listeners (broadcast) | One recipient (directed) |

- **Commands** capture *intent*; **Events** capture *facts*
- Commands are sent by one actor to another with expectation of result
- Events are broadcast — sender doesn't know/care who handles them

```python
class Command:
    pass

@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int

@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None
```

### Differences in Exception Handling

```python
# messagebus.py
Message = Union[commands.Command, events.Event]

def handle(message: Message, uow):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
    return results

def handle_event(event, queue, uow):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling event %s", event)
            continue  # events: log and continue

def handle_command(command, queue, uow):
    handler = COMMAND_HANDLERS[type(command)]  # exactly one handler
    try:
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise  # commands: raise to caller
```

- **Events**: catch exceptions, log, continue (event failures are isolated)
- **Commands**: let exceptions bubble up (the caller needs to know it failed)

### Recovering from Errors Synchronously

- **Library: `tenacity`** — Python library for retry logic with exponential backoff

```python
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

def handle_event(event, queue, uow):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential()
            ):
                with attempt:
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logger.error("Failed to handle event %s times, giving up!",
                         retry_failure.last_attempt.attempt_number)
            continue
```

---

## Chapter 11: Event-Driven Architecture: Using Events to Integrate Microservices

### Distributed Ball of Mud, and Thinking in Nouns

- Anti-pattern: splitting a system into microservices by *nouns* (Orders, Batches, Warehouse) and using synchronous HTTP calls between them
- This creates **temporal coupling**: every part must be online at the same time
- **Connascence**: a taxonomy for types of coupling. Events reduce Connascence of Execution/Timing to Connascence of Name (only need to agree on event names/fields)

### The Alternative: Temporal Decoupling Using Asynchronous Messaging

- Think in terms of *verbs* (ordering, allocating), not *nouns* (orders, batches)
- Microservices should be **consistency boundaries** (like aggregates)
- Use **asynchronous messaging** (events) to integrate services — accept eventual consistency

### Using a Redis Pub/Sub Channel for Integration

- **Message broker**: infrastructure that routes messages between services (e.g., Redis pub/sub, RabbitMQ, Kafka, Amazon EventBridge)
- The book uses Redis pub/sub as a lightweight example

```python
# Redis event consumer (entrypoint) — src/allocation/entrypoints/redis_eventconsumer.py
r = redis.Redis(**config.get_redis_host_and_port())

def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")  # listen on channel

    for m in pubsub.listen():
        handle_change_batch_quantity(m)

def handle_change_batch_quantity(m):
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())
```

```python
# Redis event publisher — src/allocation/adapters/redis_eventpublisher.py
def publish(channel, event: events.Event):
    r.publish(channel, json.dumps(asdict(event)))
```

### Internal Versus External Events

- Keep a clear distinction: not all internal events should be published externally
- Outbound events are a place where **validation** is especially important

---

## Chapter 12: Command-Query Responsibility Segregation (CQRS)

### Domain Models Are for Writing

- All the patterns in the book (aggregates, UoW, domain events) exist to enforce rules during *writes*
- Reads have very different requirements: simpler logic, higher throughput, staleness is OK

### Most Users Aren't Going to Buy Your Furniture

- Reads vastly outnumber writes in most systems
- Reads can be **eventually consistent** — trade consistency for performance

### Post/Redirect/Get and CQS

- **CQS (Command-Query Separation)**: functions should either modify state OR answer questions, never both
- Separate your POST (write) and GET (read) endpoints

### Hold On to Your Lunch, Folks

- Simplest CQRS: use raw SQL for reads, bypassing the domain model entirely

```python
# views.py — raw SQL read model
def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(uow.session.execute(
            'SELECT ol.sku, b.reference'
            ' FROM allocations AS a'
            ' JOIN batches AS b ON a.batch_id = b.id'
            ' JOIN order_lines AS ol ON a.orderline_id = ol.id'
            ' WHERE ol.orderid = :orderid',
            dict(orderid=orderid)
        ))
    return [{"sku": sku, "batchref": batchref} for sku, batchref in results]
```

### Alternatives for Read Models

| Option | Pros | Cons |
|---|---|---|
| Use repositories | Simple, consistent approach | Performance issues with complex queries |
| Custom ORM queries | Reuse DB config and model definitions | Adds query language complexity |
| Hand-rolled SQL | Fine control over performance | Schema changes affect both ORM and SQL |
| Separate read store (events) | Read-only copies scale out; queries are simple | Complex technique; eventual consistency |

### Updating a Read Model Table Using an Event Handler

```python
# Build a denormalized read-model table, updated by event handlers
EVENT_HANDLERS = {
    events.Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,  # updates the read table
    ],
}

def add_allocation_to_read_model(event: events.Allocated, uow):
    with uow:
        uow.session.execute(
            'INSERT INTO allocations_view (orderid, sku, batchref)'
            ' VALUES (:orderid, :sku, :batchref)',
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref)
        )
        uow.commit()
```

### Changing Our Read Model Implementation Is Easy

- Can swap from SQL table to Redis with minimal changes
- Integration tests still pass because they test through the message bus, not the storage backend

```python
# Redis-backed read model
def add_allocation_to_read_model(event: events.Allocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)

# In redis_eventpublisher.py
def update_readmodel(orderid, sku, batchref):
    r.hset(orderid, sku, batchref)

def get_readmodel(orderid):
    return r.hgetall(orderid)
```

---

## Chapter 13: Dependency Injection (and Bootstrapping)

### Implicit Versus Explicit Dependencies

- **Explicit**: handler declares `uow: AbstractUnitOfWork` as a parameter — easy to swap in tests
- **Implicit**: handler does `from allocation.adapters import email` — tied to implementation; requires `mock.patch` in tests

```python
# Explicit (preferred) — dependency is a parameter
def send_out_of_stock_notification(event: events.OutOfStock, send_mail: Callable):
    send_mail('stock@made.com', f'Out of stock for {event.sku}')

# Implicit (less preferred) — dependency is a hardcoded import
from allocation.adapters import email
def send_out_of_stock_notification(event: events.OutOfStock, uow):
    email.send('stock@made.com', f'Out of stock for {event.sku}')
```

- Mocks tightly couple tests to *implementation*; explicit DI couples them to *abstractions*

### Preparing Handlers: Manual DI with Closures and Partials

```python
# Using closures / functools.partial to inject dependencies
import functools

def bootstrap(...)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    # closure approach
    allocate_composed = lambda cmd: allocate(cmd, uow)
    # or equivalently with a partial
    allocate_composed = functools.partial(allocate, uow=uow)
```

- Closures use late binding (can cause surprises with mutable deps)
- `functools.partial` uses early binding — generally safer

### An Alternative Using Classes

```python
class AllocateHandler:
    def __init__(self, uow: unit_of_work.AbstractUnitOfWork):
        self.uow = uow

    def __call__(self, cmd: commands.Allocate):
        line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
        with self.uow:
            # ... handler body
```

### A Bootstrap Script

```python
# src/allocation/bootstrap.py
def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    send_mail: Callable = email.send,
    publish: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:

    if start_orm:
        orm.start_mappers()

    dependencies = {"uow": uow, "send_mail": send_mail, "publish": publish}

    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    # ... same for command handlers

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )

def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)
```

- `inspect.signature` matches handler params to the dependencies dict
- Keeps all initialization in one place — the **composition root**

### Initializing DI in Our Tests

```python
# Integration test bootstrap
@pytest.fixture
def sqlite_bus(sqlite_session_factory):
    bus = bootstrap.bootstrap(
        start_orm=True,
        uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
        send_mail=lambda *args: None,  # no-op
        publish=lambda *args: None,
    )
    yield bus
    clear_mappers()

# Unit test bootstrap
def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        send_mail=lambda *args: None,
        publish=lambda *args: None,
    )
```

### Building an Adapter "Properly": A Worked Example

1. **Define the abstract interface** (ABC)
2. **Implement the real thing** (e.g., `EmailNotifications` using `smtplib`)
3. **Build a fake** for unit/service-layer tests (e.g., `FakeNotifications`)
4. **Find a "less fake" for integration** (e.g., MailHog in Docker)
5. **Integration test** against the less-fake version

```python
# Abstract
class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError

# Real
class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(smtp_host, port=port)
        self.server.noop()

    def send(self, destination, message):
        msg = f"Subject: allocation service notification\n{message}"
        self.server.sendmail(
            from_addr="allocations@example.com",
            to_addrs=[destination],
            msg=msg
        )

# Fake (for unit tests)
class FakeNotifications(AbstractNotifications):
    def __init__(self):
        self.sent = defaultdict(list)  # type: Dict[str, List[str]]

    def send(self, destination, message):
        self.sent[destination].append(message)
```

### DI Framework Mentions

- **`Inject`** — used at MADE.com, works fine but annoys Pylint
- **`Punq`** — written by Bob Gregory
- **`dependencies`** — by the DRY-Python crew
- For most cases, manual DI (lambdas/partials + bootstrap script) is sufficient

### Message Bus Is Given Handlers at Runtime

```python
class MessageBus:
    def __init__(self, uow, event_handlers, command_handlers):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")
```

---

## Epilogue

### How Do I Get There from Here?

- You don't need a greenfield project — these patterns can be incrementally adopted in existing codebases
- Link refactoring to feature work to justify the investment (**"architecture tax"**)

### Separating Entangled Responsibilities

1. Identify **use cases** — give each an imperative name (Apply Billing Charges, Create Workspace)
2. Create a single function/class per use case that orchestrates the work
3. Pull data access and I/O out of the domain model and into use-case functions

### Identifying Aggregates and Bounded Contexts

- Break apart your object graph by replacing direct object references with IDs
- **Bidirectional links** are a code smell — they suggest aggregate boundaries are wrong
- For *reads*, replace ORM loops with raw SQL (first step toward CQRS)
- For *writes*, use message bus + events to coordinate between aggregates

### An Event-Driven Approach to Go to Microservices via Strangler Pattern

- **Strangler Fig pattern**: wrap a new system around the edges of the old one, gradually replacing functionality
- **Event interception**:
  1. Raise events in the old system
  2. Build a new system that consumes those events
  3. Replace the old system

### Convincing Your Stakeholders to Try Something New

- Use **domain modeling** (event storming, CRC cards, event modeling) to align engineers and business
- Treat domain problems as TDD katas — start small, demonstrate value

### Footguns

- **Reliable messaging is hard**: Redis pub/sub is not a production message broker; consider RabbitMQ, Kafka, Amazon EventBridge
- **Small, focused transactions**: design operations to fail independently
- **Idempotency**: handlers should be safe to call repeatedly with the same message
- **Event schema evolution**: document and version your events (JSON schema + markdown)

---

## Appendix A: Summary Diagram and Table

### Component Reference

| Layer | Component | Description |
|---|---|---|
| **Domain** | Entity | Object with identity that may change over time |
| | Value Object | Immutable, defined entirely by its attributes |
| | Aggregate | Cluster of objects treated as a unit; consistency boundary |
| | Event | Dataclass representing something that happened |
| | Command | Dataclass representing a job the system should do |
| **Service Layer** | Handler | Receives a command/event and orchestrates response |
| | Unit of Work | Abstraction around atomic DB operations |
| | Message Bus | Routes commands/events to their handlers |
| **Adapters** | Repository | Abstraction around persistent storage |
| | Event Publisher | Pushes events to external message bus |
| **Entrypoints** | Web (Flask) | Translates HTTP requests → commands |
| | Event Consumer | Translates external messages → commands |
| **Infrastructure** | External Message Bus | Message broker (Redis, Kafka, etc.) for inter-service communication |

---

## Appendix B: A Template Project Structure

### Project Layout

```
.
├── Dockerfile
├── Makefile
├── docker-compose.yml
├── mypy.ini
├── requirements.txt
├── src
│   ├── allocation
│   │   ├── __init__.py
│   │   ├── adapters/        (orm.py, repository.py)
│   │   ├── config.py
│   │   ├── domain/          (model.py, events.py, commands.py)
│   │   ├── entrypoints/     (flask_app.py, redis_eventconsumer.py)
│   │   └── service_layer/   (handlers.py, messagebus.py, unit_of_work.py)
│   └── setup.py
└── tests
    ├── conftest.py
    ├── e2e/          (test_api.py)
    ├── integration/  (test_orm.py, test_repository.py)
    ├── pytest.ini
    └── unit/         (test_batches.py, test_handlers.py)
```

### Key Config Patterns

- **`config.py`**: functions (not constants) that read from `os.environ` with sensible dev defaults
- **`docker-compose.yml`**: define services, set env vars, mount volumes for dev hot-reload
- **`setup.py`**: minimal `pip install -e` for src package
- **`PYTHONDONTWRITEBYTECODE=1`**: prevents .pyc clutter when mounting volumes in Docker
- **Library: `environ-config`** — elegant environment-based config in Python

---

## Appendix C: Swapping Out the Infrastructure: Do Everything with CSVs

### Key Lesson

- Because the domain model and service layer are decoupled from infrastructure, you can swap Postgres for CSV files by implementing new `CsvRepository` and `CsvUnitOfWork` classes
- All domain logic and service-layer orchestration is reused unchanged

```python
class CsvRepository(repository.AbstractRepository):
    def __init__(self, folder):
        self._batches_path = Path(folder) / "batches.csv"
        self._allocations_path = Path(folder) / "allocations.csv"
        self._batches = {}
        self._load()

    def get(self, reference):
        return self._batches.get(reference)

    def add(self, batch):
        self._batches[batch.reference] = batch

class CsvUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self, folder):
        self.batches = CsvRepository(folder)

    def commit(self):
        # write allocations back to CSV
        ...

    def rollback(self):
        pass
```

---

## Appendix D: Repository and Unit of Work Patterns with Django

*(Brief overview — see the book for full Django-specific code)*

- Django's ORM uses the Active Record pattern (model = table row), unlike SQLAlchemy's Data Mapper
- You can still apply Repository and UoW patterns on top of Django, though it requires more effort
- The key trick: use Django's `model_to_dict` and manual mapping to keep your domain model separate from Django models
- Django's `transaction.atomic()` can serve as the UoW's `commit()` boundary

---

## Appendix E: Validation

### Three Types of Validation

1. **Syntax validation**: is the input well-formed? (correct types, required fields present)
2. **Semantics validation**: does the input make sense? (is this a real SKU? is quantity positive?)
3. **Pragmatic validation**: can we do what's being asked? (is there enough stock?)

### Where to Validate

- **Syntax**: at the edge — in the entrypoint or on the message/command itself
- **Semantics**: in the domain model or handlers (e.g., checking a SKU exists)
- **Pragmatic**: deep in the domain model (business rules like "can't allocate more than available")

### The Ensure Pattern

```python
# Validation at command creation
@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int

    def __post_init__(self):
        if not self.orderid:
            raise ValueError("orderid is required")
        if self.qty <= 0:
            raise ValueError("qty must be positive")
```

- Validate as early as possible
- Commands/events should be valid by construction
- Don't let invalid data propagate through the system

---
