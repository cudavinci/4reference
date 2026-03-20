# Book5 - Refactoring: Improving the Design of Existing Code (2nd Edition)
**Martin Fowler, with Kent Beck**

---

### Chapter 1: Refactoring: A First Example

#### The Starting Point

The chapter opens with a small theater company billing program. The initial `statement` function calculates charges for a customer's performance invoice. It's a single long function with a switch statement handling different play types (`tragedy`, `comedy`), computing charges and volume credits inline.

**Key problem:** The code works, but it's hard to change. Adding an HTML statement output or new play types requires duplicating or deeply modifying the tangled logic.

> A program that works but is poorly structured is hard to change. The compiler doesn't care whether the code is ugly — but people do.

#### Decomposing the `statement` Function

Fowler's first move: **Extract Function** on logical chunks.

```python
def amount_for(a_performance: dict, play: dict) -> int:
    """Calculate the charge for a single performance."""
    result = 0
    if play["type"] == "tragedy":
        result = 40000
        if a_performance["audience"] > 30:
            result += 1000 * (a_performance["audience"] - 30)
    elif play["type"] == "comedy":
        result = 30000
        if a_performance["audience"] > 20:
            result += 10000 + 500 * (a_performance["audience"] - 20)
        result += 300 * a_performance["audience"]
    else:
        raise ValueError(f"unknown type: {play['type']}")
    return result
```

Each extraction follows the same rhythm:
1. Identify a coherent block of code
2. Extract it into its own function
3. **Run the tests** after every change
4. Commit frequently — small steps let you revert easily if something breaks

**Naming convention:** Use `result` as the return variable name inside extracted functions — it immediately signals the function's purpose.

#### Removing the `play` Variable (Replace Temp with Query)

Instead of passing `play` as a parameter, Fowler replaces the temp variable with a function call:

```python
def play_for(a_performance: dict) -> dict:
    return plays[a_performance["play_id"]]
```

This **removes a local variable**, making future extractions easier (fewer params to pass). The trade-off: a repeated lookup vs. simpler function signatures. Fowler argues the performance cost is negligible and clarity wins.

#### Extracting Volume Credits

```python
def volume_credits_for(perf: dict) -> int:
    result = max(perf["audience"] - 30, 0)
    if play_for(perf)["type"] == "comedy":
        result += perf["audience"] // 5
    return result
```

#### Replacing the Accumulator (Split Loop + Replace Temp with Query)

Fowler splits the loop so each concern (total amount, total credits) has its own loop, then extracts each into a function:

```python
def total_volume_credits(invoice: dict) -> int:
    return sum(volume_credits_for(perf) for perf in invoice["performances"])

def total_amount(invoice: dict) -> int:
    return sum(amount_for(perf) for perf in invoice["performances"])
```

**"But doesn't looping twice hurt performance?"** — Fowler's answer: rarely. The refactored code is easier to optimize later (e.g., caching), and most performance concerns about refactoring are unfounded. **Refactor first, then profile and optimize.**

#### Creating a Statement Data Structure (Split Phase)

To support both plain text and HTML output, Fowler introduces an intermediate data structure:

```python
def create_statement_data(invoice: dict, plays: dict) -> dict:
    """Build a data structure with all the info the rendering functions need."""
    result = {
        "customer": invoice["customer"],
        "performances": [enrich_performance(perf) for perf in invoice["performances"]],
    }
    result["total_amount"] = total_amount(result)
    result["total_volume_credits"] = total_volume_credits(result)
    return result

def enrich_performance(a_performance: dict) -> dict:
    result = dict(a_performance)  # shallow copy
    result["play"] = play_for(result)
    result["amount"] = amount_for(result)
    result["volume_credits"] = volume_credits_for(result)
    return result
```

Now rendering functions (`render_plain_text`, `render_html`) only depend on the data structure, not the raw invoice + plays.

#### Polymorphism for Play Type Calculation

The final refactoring replaces the conditional logic with polymorphism:

```python
class PerformanceCalculator:
    def __init__(self, a_performance: dict, a_play: dict):
        self.performance = a_performance
        self.play = a_play

    @property
    def amount(self) -> int:
        raise NotImplementedError

    @property
    def volume_credits(self) -> int:
        return max(self.performance["audience"] - 30, 0)


class TragedyCalculator(PerformanceCalculator):
    @property
    def amount(self) -> int:
        result = 40000
        if self.performance["audience"] > 30:
            result += 1000 * (self.performance["audience"] - 30)
        return result


class ComedyCalculator(PerformanceCalculator):
    @property
    def amount(self) -> int:
        result = 30000
        if self.performance["audience"] > 20:
            result += 10000 + 500 * (self.performance["audience"] - 20)
        result += 300 * self.performance["audience"]
        return result

    @property
    def volume_credits(self) -> int:
        return super().volume_credits + self.performance["audience"] // 5


def create_calculator(a_performance: dict, a_play: dict) -> PerformanceCalculator:
    """Factory function replacing conditionals with polymorphism."""
    match a_play["type"]:
        case "tragedy":
            return TragedyCalculator(a_performance, a_play)
        case "comedy":
            return ComedyCalculator(a_performance, a_play)
        case _:
            raise ValueError(f"unknown type: {a_play['type']}")
```

**Key takeaway:** Adding a new play type now means adding a new subclass — no existing code needs modification (Open-Closed Principle).

#### Chapter 1 Summary

The entire refactoring follows a pattern:
1. **Small steps** — each change is tiny, testable, and independently commitable
2. **Tests after every change** — if something breaks, you know exactly which change caused it
3. **Decompose → reorganize → replace conditionals with polymorphism**
4. The end result has the same behavior but is far easier to extend

---

### Chapter 2: Principles of Refactoring

#### Defining Refactoring

- **Refactoring (noun):** A change made to the internal structure of software to make it easier to understand and cheaper to modify without changing its observable behavior.
- **Refactoring (verb):** To restructure software by applying a series of refactorings without changing its observable behavior.

The key distinction from general "restructuring": refactoring is a **specific, disciplined technique** — a sequence of small behavior-preserving transformations that cumulatively produce a large restructuring. Each individual step is small enough that errors are easy to find.

#### The Two Hats

Fowler borrows Kent Beck's metaphor: at any moment, you're wearing either the **adding functionality** hat or the **refactoring** hat. Never both simultaneously.

- **Adding functionality:** Writing new tests, adding new capabilities, making tests pass
- **Refactoring:** Restructuring code without adding any new tests (existing tests should all still pass)

You swap hats frequently — sometimes every few minutes — but you should always be clear about which hat you're currently wearing.

#### Why Should We Refactor?

- **Improves the design of software** — without refactoring, architecture decays as people make short-term changes without understanding the full design
- **Makes software easier to understand** — code is read far more often than it's written; investing in clarity pays off
- **Helps you find bugs** — when you understand the code deeply enough to refactor it, bugs become visible
- **Helps you program faster** — counterintuitive but critical: good internal design lets you add features faster over time (the "Design Stamina Hypothesis")

#### When Should We Refactor?

**The Rule of Three:** The first time you do something, just do it. The second time, wince but do it anyway. The third time, refactor.

More practically:

- **Preparatory refactoring** — restructure before adding a feature so the feature is easier to add. *"It's like I want to go 100 miles east but instead of driving through the swamp, I'll drive 20 miles north to the highway."*
- **Comprehension refactoring** — refactor to understand code you're reading. As you understand it, embed that understanding back into the code.
- **Litter-pickup refactoring** — you see something slightly wrong while working nearby; fix it if easy, note it if hard.
- **Planned refactoring** — sometimes needed for neglected codebases, but ideally most refactoring is **opportunistic** (woven into feature work).
- **Long-term refactoring** — large-scale changes (replacing a library, untangling a dependency) done gradually over weeks by a team.

#### When Should We NOT Refactor?

- When the code works and you don't need to understand or modify it — treat it as an API
- When it's easier to rewrite from scratch than to refactor

#### Refactoring and Performance

Refactoring can make code slower (e.g., splitting a loop), but it almost never matters. The approach:
1. Write well-factored code without worrying about performance
2. Profile to find the actual bottlenecks (usually a small fraction of the code)
3. Optimize only those hotspots
4. Well-factored code is *easier* to optimize because you can isolate the hot path

#### Refactoring and Architecture

- Refactoring changes the role of upfront architecture: you don't need to predict every future need, because you can restructure later
- **YAGNI (You Ain't Gonna Need It):** Build only for current requirements, then refactor when requirements change
- This doesn't mean no architecture — it means you make architecture decisions that are easy to refactor

#### Refactoring and Software Development Process

- Self-testing code is a prerequisite for refactoring
- Refactoring enables Continuous Integration (CI): frequent integration reduces merge pain because each developer keeps their code well-factored
- The trio of **self-testing code + continuous integration + refactoring** (together called Extreme Programming) creates a virtuous cycle

---

### Chapter 3: Bad Smells in Code

**Definition:** A *code smell* is a surface-level indicator that something may be wrong in the code. Smells are heuristics, not rules — they suggest where to look, not necessarily what to do.

#### Mysterious Name

Code that doesn't clearly communicate what it does. Names should reveal intent. Key refactorings: **Change Function Declaration**, **Rename Variable**, **Rename Field**.

#### Duplicated Code

The same code structure in more than one place. Even slight variations count. Key refactorings: **Extract Function**, **Slide Statements**, **Pull Up Method**.

#### Long Function

Longer functions are harder to understand. The key heuristic: whenever you feel the need to write a comment, extract that block into a function named after the *intent* of the code (not what it does mechanically). Key refactorings: **Extract Function**, **Replace Temp with Query**, **Replace Conditional with Polymorphism**.

#### Long Parameter List

Too many parameters make functions hard to understand and call. Key refactorings: **Replace Parameter with Query**, **Preserve Whole Object**, **Introduce Parameter Object**, **Remove Flag Argument**, **Combine Functions into Class**.

#### Global Data

Global data can be modified from anywhere, making bugs extremely hard to track. Key refactoring: **Encapsulate Variable** (at minimum, wrap in a function so you can monitor access and modification).

#### Mutable Data

Mutations are a major source of bugs, especially when changes happen in unexpected places. Key refactorings: **Encapsulate Variable**, **Split Variable**, **Replace Derived Variable with Query**, **Combine Functions into Class**, **Change Reference to Value**, **Move Statements to Callers**.

#### Divergent Change

A single module changes for multiple different reasons (e.g., adding a new database AND adding a new financial instrument both require changes to the same module). Violates Single Responsibility. Key refactorings: **Split Phase**, **Extract Function**, **Extract Class**, **Move Function**.

#### Shotgun Surgery

The opposite of Divergent Change: a single logical change requires touching many different modules. Key refactorings: **Move Function**, **Move Field**, **Combine Functions into Class**, **Combine Functions into Transform**, **Inline Function**, **Inline Class**.

#### Feature Envy

A function that interacts more with data from another module than its own. It *wants* to be in the other module. Key refactoring: **Move Function**. Exception: Strategy and Visitor patterns deliberately separate function from data.

#### Data Clumps

Groups of data items that appear together repeatedly (e.g., `start_x, start_y, end_x, end_y`). If deleting one of the group would make the others meaningless, they belong in an object. Key refactorings: **Extract Class**, **Introduce Parameter Object**, **Preserve Whole Object**.

#### Primitive Obsession

Using primitive types (strings, ints) where a small object would be better (e.g., money, phone numbers, date ranges). Key refactorings: **Replace Primitive with Object**, **Replace Type Code with Subclasses**, **Replace Conditional with Polymorphism**.

#### Repeated Switches

The same `switch`/`match` statement (or `if-elif` chain) appearing in multiple places, switching on the same type code. Problem: adding a new case means finding and updating every switch. Key refactoring: **Replace Conditional with Polymorphism**.

#### Loops

Loops can often be replaced with pipeline operations (`map`, `filter`, `reduce`, list comprehensions) that more clearly communicate intent. Key refactoring: **Replace Loop with Pipeline**.

#### Lazy Element

A class or function that doesn't do enough to justify its existence (e.g., a class with one method that just delegates). Key refactorings: **Inline Function**, **Inline Class**, **Collapse Hierarchy**.

#### Speculative Generality

"We might need this someday" — abstract classes, hooks, special cases, parameters that are never used. Key refactorings: **Collapse Hierarchy**, **Inline Function**, **Inline Class**, **Change Function Declaration** (to remove unused params), **Remove Dead Code**.

#### Temporary Field

An object field that is only set in certain circumstances. Confusing because you expect all fields to be relevant. Key refactorings: **Extract Class**, **Move Function**, **Introduce Special Case**.

#### Message Chains

`a.get_b().get_c().get_d()` — a long chain of navigations couples the code to the object structure. Key refactorings: **Hide Delegate**, or better, **Extract Function** on the code *using* the chain + **Move Function** to push it closer to the chain.

#### Middle Man

A class where the majority of its methods just delegate to another class. Key refactorings: **Remove Middle Man**, **Inline Function**, **Replace Superclass with Delegate**, **Replace Subclass with Delegate**.

#### Insider Trading

Modules trading too much data back and forth. Key refactorings: **Move Function**, **Move Field**, **Hide Delegate**, **Replace Subclass with Delegate**, **Replace Superclass with Delegate**.

#### Large Class

A class doing too much — has too many fields, too much code, too many responsibilities. Key refactorings: **Extract Class**, **Extract Superclass**, **Replace Type Code with Subclasses**.

#### Alternative Classes with Different Interfaces

Two classes that do similar things but have different interfaces. Key refactorings: **Change Function Declaration**, **Move Function**, **Extract Superclass**.

#### Data Class

Classes that have fields, getters/setters, and nothing else. Not always a smell (data classes are fine for immutable data) but can indicate that behavior that should live with the data is elsewhere. Key refactorings: **Encapsulate Record**, **Remove Setting Method**, **Move Function**, **Extract Function**.

#### Refused Bequest

A subclass that doesn't want most of the behavior it inherits. Mild form: mostly harmless. Strong form (subclass rejects interface): use **Replace Subclass with Delegate** or **Replace Superclass with Delegate**.

#### Comments

Comments aren't inherently bad, but they often signal code that needs refactoring. If you feel the need to write a comment, try refactoring first so the code speaks for itself. Good comments explain *why*, not *what*. Key refactorings: **Extract Function**, **Change Function Declaration**, **Introduce Assertion**.

---

### Chapter 4: Building Tests

#### The Value of Self-Testing Code

> Make sure all tests are fully automatic and that they check their own results.

**Self-testing code:** A comprehensive test suite that you can run with a single command. The key benefit isn't catching bugs after writing code — it's the **safety net for refactoring**. Without tests, refactoring is too risky.

Fowler's workflow: write a test, make it fail, make it pass, then refactor. This is essentially Test-Driven Development (TDD), though Fowler doesn't insist on strict TDD — the critical point is having tests, not the order you write them.

#### Setting Up a Test Framework

The chapter uses a production planning example. In Python, this maps to `pytest`:

```python
# test_province.py
import pytest
from province import Province

@pytest.fixture
def asia():
    """Sample province data for testing."""
    return Province({
        "name": "Asia",
        "producers": [
            {"name": "Byzantium", "cost": 10, "production": 9},
            {"name": "Attalia", "cost": 12, "production": 10},
            {"name": "Sinope", "cost": 10, "production": 6},
        ],
        "demand": 30,
        "price": 20,
    })

def test_shortfall(asia):
    assert asia.shortfall == 5

def test_profit(asia):
    assert asia.profit == 230
```

**Key principles:**
- Each test should have its own fresh fixture — **never share mutable state between tests**. The `@pytest.fixture` mechanism provides a fresh copy for each test function.
- Tests should be **isolated** from each other; running order shouldn't matter.

#### What to Test

- **Probe the boundaries:** Test edge cases, zero, negative, empty collections.
- **Test the things most likely to break:** Focus on complex conditionals, data transformations, boundary conditions.
- **Think about what can go wrong,** not just what should go right.

```python
def test_zero_demand(asia):
    asia.demand = 0
    assert asia.shortfall == -25
    assert asia.profit == 0

def test_negative_demand(asia):
    asia.demand = -1
    assert asia.shortfall == -26
    assert asia.profit == -10

def test_empty_producers():
    no_producers = Province({"name": "Empty", "producers": [], "demand": 30, "price": 20})
    assert no_producers.shortfall == 30
    assert no_producers.profit == 0
```

#### Testing for Exceptions

```python
def test_string_for_producers():
    """Test with invalid data — string instead of list for producers."""
    data = {"name": "String producers", "producers": "", "demand": 30, "price": 20}
    prov = Province(data)
    assert prov.shortfall == 30  # or expect an error — test documents actual behavior
```

#### How Much Testing?

- **Coverage tools** are useful for finding *untested* code but don't guarantee *quality*. 100% coverage doesn't mean the tests are good.
- Fowler's heuristic: "I get a feeling of confidence from testing, and I adjust my strategy to maintain that level of confidence."
- Focus testing effort on complex, tricky, and error-prone areas.
- **When you find a bug, write a test for it first** before fixing it.
- Tests don't need to be perfect — imperfect tests that run frequently are far better than perfect tests you never write.

> "The best measure of a good test suite is subjective: how confident are you that if someone introduces a bug into the code, your tests will catch it?"

---

### Chapter 5: Introducing the Catalog

Chapters 6–12 form a catalog of refactorings. Each refactoring follows a consistent format:

- **Name** — builds a vocabulary for communicating about refactoring
- **Sketch** — a visual summary of the transformation
- **Motivation** — when to apply it and when not to
- **Mechanics** — step-by-step instructions for applying it safely
- **Examples** — demonstrations with code

The refactorings are organized by theme: basic operations (Ch. 6), encapsulation (Ch. 7), moving features (Ch. 8), organizing data (Ch. 9), conditionals (Ch. 10), APIs (Ch. 11), and inheritance (Ch. 12).

---

### Chapter 6: A First Set of Refactorings

#### Extract Function

**Motivation:** If you have to spend time figuring out *what* a chunk of code does, extract it into a function and name it after the *intent*. A function can be as short as a single line if the name adds clarity.

**Heuristic:** "If the code fragment requires a comment to explain what it does, extract it and name the function after that comment."

```python
# Before
def print_owing(invoice):
    print_banner()
    outstanding = calculate_outstanding(invoice)

    # print details
    print(f"name: {invoice.customer}")
    print(f"amount: {outstanding}")

# After
def print_owing(invoice):
    print_banner()
    outstanding = calculate_outstanding(invoice)
    print_details(invoice, outstanding)

def print_details(invoice, outstanding):
    print(f"name: {invoice.customer}")
    print(f"amount: {outstanding}")
```

**Mechanics:**
1. Create a new function named after the intent (what, not how)
2. Copy the extracted code into the new function
3. Check for local variables — pass them as parameters or return them
4. Replace the original code with a call to the new function
5. Test

#### Inline Function

**Motivation:** The inverse of Extract Function. When a function body is as clear as the name, or when you have a group of badly factored functions, inline them first, then re-extract better.

```python
# Before
def get_rating(driver):
    return 2 if more_than_five_late_deliveries(driver) else 1

def more_than_five_late_deliveries(driver):
    return driver.number_of_late_deliveries > 5

# After
def get_rating(driver):
    return 2 if driver.number_of_late_deliveries > 5 else 1
```

#### Extract Variable

**Motivation:** Break complex expressions into named local variables to add explanation.

```python
# Before
def price(order):
    return (
        order.quantity * order.item_price
        - max(0, order.quantity - 500) * order.item_price * 0.05
        + min(order.quantity * order.item_price * 0.1, 100)
    )

# After
def price(order):
    base_price = order.quantity * order.item_price
    quantity_discount = max(0, order.quantity - 500) * order.item_price * 0.05
    shipping = min(base_price * 0.1, 100)
    return base_price - quantity_discount + shipping
```

Within a class, prefer **Extract Function** (making properties/methods) over local variables, since methods are reusable across the class.

#### Inline Variable

**Motivation:** When a variable name says no more than the expression itself, or when the variable gets in the way of an adjacent refactoring.

```python
# Before
base_price = order.base_price
return base_price > 1000

# After
return order.base_price > 1000
```

#### Change Function Declaration

**Motivation:** Function names and parameter lists are the joints of the software system. Good names are critical. If you think of a better name, rename immediately.

**Simple Mechanics (rename):**

```python
# Before
def circum(radius):
    return 2 * math.pi * radius

# After
def circumference(radius):
    return 2 * math.pi * radius
```

**Migration Mechanics (for published APIs or complex changes):**
1. Extract the body into a new function with the desired signature
2. Have the old function delegate to the new one
3. Callers migrate one at a time
4. Remove the old function when all callers are updated

#### Encapsulate Variable

**Motivation:** For widely accessed data, wrap it in functions. This provides a clear point for monitoring, validation, or mutation control.

```python
# Before — module-level mutable data
_default_owner = {"first_name": "Martin", "last_name": "Fowler"}

# After — encapsulated with getter/setter
_default_owner = {"first_name": "Martin", "last_name": "Fowler"}

def get_default_owner():
    return dict(_default_owner)  # return a copy to prevent mutation

def set_default_owner(new_owner):
    global _default_owner
    _default_owner = new_owner
```

**Key insight:** For mutable data, returning a copy prevents callers from reaching past the encapsulation. For immutable data (frozen dataclasses, named tuples), this isn't necessary.

#### Rename Variable

**Motivation:** Good names are the heart of clear programming. For variables used beyond a single function, the name matters even more.

```python
# Before
a = height * width

# After
area = height * width
```

For persistent fields in dataclasses, encapsulate first (getter/setter), then rename the underlying field.

#### Introduce Parameter Object

**Motivation:** When the same group of parameters travel together across multiple functions, bundle them into an object.

```python
# Before
def amount_invoiced(start_date, end_date): ...
def amount_received(start_date, end_date): ...
def amount_overdue(start_date, end_date): ...

# After
@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

def amount_invoiced(date_range: DateRange): ...
def amount_received(date_range: DateRange): ...
def amount_overdue(date_range: DateRange): ...
```

**Key insight:** The new object often becomes a natural home for behavior (like `contains` above), creating a new abstraction that simplifies the domain model.

#### Combine Functions into Class

**Motivation:** When a group of functions operate on the same data, bundle them into a class. The class provides a common environment for the functions and simplifies argument passing.

```python
# Before — loose functions passing a reading dict around
def base_rate(month, year): ...
def base_charge(reading): return base_rate(reading["month"], reading["year"]) * reading["quantity"]
def taxable_charge(reading): return max(0, base_charge(reading) - tax_threshold(reading["year"]))

# After
class Reading:
    def __init__(self, data: dict):
        self.customer = data["customer"]
        self.quantity = data["quantity"]
        self.month = data["month"]
        self.year = data["year"]

    @property
    def base_charge(self) -> float:
        return base_rate(self.month, self.year) * self.quantity

    @property
    def taxable_charge(self) -> float:
        return max(0, self.base_charge - tax_threshold(self.year))
```

#### Combine Functions into Transform

**Motivation:** An alternative to the class approach: a transform function that takes the source data and returns an enriched copy with all derived values attached.

```python
def enrich_reading(original: dict) -> dict:
    result = dict(original)  # shallow copy — don't modify the input
    result["base_charge"] = calculate_base_charge(result)
    result["taxable_charge"] = max(0, result["base_charge"] - tax_threshold(result["year"]))
    return result
```

**Class vs. Transform:** Use a class when you want to enforce encapsulation or when the data is mutable. Use a transform when the data is essentially immutable and you're building a pipeline. **If the source data is mutated elsewhere, prefer the class** — a transform with stale derived values is a bug farm.

#### Split Phase

**Motivation:** When code does two different things in sequence (e.g., parse input, then compute on the parsed data), split it into two phases with an explicit intermediate data structure.

```python
# Before — parsing and computation interleaved
def price_order(product, quantity, shipping_method):
    base_price = product["base_price"] * quantity
    discount = max(quantity - product["discount_threshold"], 0) * product["base_price"] * product["discount_rate"]
    shipping_per_case = (
        shipping_method["discounted_fee"] if base_price > shipping_method["discount_threshold"]
        else shipping_method["fee_per_case"]
    )
    shipping_cost = quantity * shipping_per_case
    return base_price - discount + shipping_cost

# After — pricing and shipping in separate phases
@dataclass
class PriceData:
    base_price: float
    quantity: int
    discount: float

def price_order(product, quantity, shipping_method):
    price_data = calculate_pricing_data(product, quantity)
    return apply_shipping(price_data, shipping_method)

def calculate_pricing_data(product, quantity) -> PriceData:
    base_price = product["base_price"] * quantity
    discount = max(quantity - product["discount_threshold"], 0) * product["base_price"] * product["discount_rate"]
    return PriceData(base_price=base_price, quantity=quantity, discount=discount)

def apply_shipping(price_data: PriceData, shipping_method) -> float:
    shipping_per_case = (
        shipping_method["discounted_fee"] if price_data.base_price > shipping_method["discount_threshold"]
        else shipping_method["fee_per_case"]
    )
    shipping_cost = price_data.quantity * shipping_per_case
    return price_data.base_price - price_data.discount + shipping_cost
```

---

### Chapter 7: Encapsulation

#### Encapsulate Record

**Motivation:** Replace raw dicts/records with objects that control access. This lets you hide what is stored vs. what is derived.

```python
# Before
organization = {"name": "Acme Gooseberries", "country": "GB"}

# After
class Organization:
    def __init__(self, data: dict):
        self._name = data["name"]
        self._country = data["country"]

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def country(self) -> str:
        return self._country

    @country.setter
    def country(self, value: str):
        self._country = value
```

For nested records (e.g., `customers[id]["usages"][year][month]`), encapsulation is even more valuable — it hides the internal navigation structure.

#### Encapsulate Collection

**Motivation:** When a class exposes a mutable collection directly, callers can modify the collection without the owning class knowing. Return a copy or a read-only view instead.

```python
class Person:
    def __init__(self, name: str):
        self._name = name
        self._courses: list[Course] = []

    @property
    def courses(self) -> tuple[Course, ...]:
        return tuple(self._courses)  # return immutable view

    def add_course(self, course: Course):
        self._courses.append(course)

    def remove_course(self, course: Course):
        self._courses.remove(course)
```

**Key point:** Never provide a setter for a collection that replaces the entire list. Provide `add` and `remove` methods. If you must allow bulk replacement, copy the incoming collection.

#### Replace Primitive with Object

**Motivation:** Simple data items often grow into something richer. A phone number that started as a string eventually needs formatting, validation, area-code extraction. Wrap it early.

```python
# Before
orders = [o for o in all_orders if o.priority == "high" or o.priority == "rush"]

# After
class Priority:
    LEGAL_VALUES = ("low", "normal", "high", "rush")

    def __init__(self, value: str):
        if value not in self.LEGAL_VALUES:
            raise ValueError(f"Invalid priority: {value}")
        self._value = value

    def higher_than(self, other: "Priority") -> bool:
        return self.LEGAL_VALUES.index(self._value) > self.LEGAL_VALUES.index(other._value)

    def __eq__(self, other):
        return isinstance(other, Priority) and self._value == other._value

    def __str__(self):
        return self._value

orders = [o for o in all_orders if o.priority.higher_than(Priority("normal"))]
```

#### Replace Temp with Query

**Motivation:** Temps used once to store intermediate results can be replaced by method/function calls. This makes the logic reusable and reduces parameter passing in Extract Function.

```python
# Before
def calculate_total(order):
    base_price = order.quantity * order.item_price
    if base_price > 1000:
        return base_price * 0.95
    return base_price * 0.98

# After
class Order:
    @property
    def base_price(self):
        return self.quantity * self.item_price

    @property
    def total(self):
        if self.base_price > 1000:
            return self.base_price * 0.95
        return self.base_price * 0.98
```

**Caveat:** Only do this when the extracted query has no side effects (is referentially transparent). If the computation is expensive, profile before worrying.

#### Extract Class

**Motivation:** A class doing two things should be split into two classes. Signs: a subset of the fields/methods form a natural cluster, or data that changes together is separate from data that doesn't.

```python
# Before — Person has phone number logic mixed in
class Person:
    def __init__(self, name, office_area_code, office_number):
        self._name = name
        self._office_area_code = office_area_code
        self._office_number = office_number

    @property
    def telephone_number(self):
        return f"({self._office_area_code}) {self._office_number}"

# After — phone number extracted
class TelephoneNumber:
    def __init__(self, area_code, number):
        self._area_code = area_code
        self._number = number

    def __str__(self):
        return f"({self._area_code}) {self._number}"

class Person:
    def __init__(self, name, office_area_code, office_number):
        self._name = name
        self._telephone_number = TelephoneNumber(office_area_code, office_number)

    @property
    def telephone_number(self):
        return str(self._telephone_number)
```

#### Inline Class

**Motivation:** The inverse of Extract Class. When a class is too thin — not pulling its weight — fold it back into its host.

Also useful as an intermediate step: inline two classes into one, then re-extract into better-factored classes.

#### Hide Delegate

**Motivation:** When a client calls `person.department.manager`, it depends on both `Person` and `Department`. Hide the delegation:

```python
class Person:
    @property
    def manager(self):
        return self._department.manager
```

Now clients call `person.manager` and don't need to know about `Department`.

**Danger:** If you do this too much, the host class becomes a swollen middle man. Balance is key.

#### Remove Middle Man

**Motivation:** The inverse of Hide Delegate. When a class has too many delegating methods, let clients call the delegate directly.

```python
# Instead of person.manager (delegating):
manager = person.department.manager
```

There's no "right" amount of hiding — it evolves over time. Add delegates when coupling hurts; remove them when the middle man bloats.

#### Substitute Algorithm

**Motivation:** When you find a clearer or simpler way to accomplish what a function does, replace the entire body.

```python
# Before
def found_person(people):
    for p in people:
        if p == "Don":
            return "Don"
        if p == "John":
            return "John"
        if p == "Kent":
            return "Kent"
    return ""

# After
def found_person(people):
    candidates = {"Don", "John", "Kent"}
    return next((p for p in people if p in candidates), "")
```

---

### Chapter 8: Moving Features

#### Move Function

**Motivation:** Move a function to the module/class where it's most used or where its context lives. Good modularity means related things are together.

**Heuristics for where a function should live:**
- What data does it reference most?
- What other functions call it?
- What functions does it call?

```python
# Before — account_type is passed in but owns the logic
class Account:
    @property
    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.overdraft_charge
        return result

    @property
    def overdraft_charge(self):
        if self.type.is_premium:
            base = 10
            if self._days_overdrawn <= 7:
                return base
            return base + (self._days_overdrawn - 7) * 0.85
        return self._days_overdrawn * 1.75

# After — move overdraft_charge to AccountType
class AccountType:
    def overdraft_charge(self, days_overdrawn):
        if self.is_premium:
            base = 10
            if days_overdrawn <= 7:
                return base
            return base + (days_overdrawn - 7) * 0.85
        return days_overdrawn * 1.75

class Account:
    @property
    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.type.overdraft_charge(self._days_overdrawn)
        return result
```

#### Move Field

**Motivation:** Move a field to the class/record that uses it most. A sign you need this: you always pass the field to functions in another class, or every time a record changes, you need to update a field in another record.

```python
# Before — discount_rate on Customer
class Customer:
    def __init__(self, name, discount_rate):
        self.name = name
        self.discount_rate = discount_rate

class CustomerContract:
    def __init__(self, start_date):
        self.start_date = start_date

# After — discount_rate moves to CustomerContract
class CustomerContract:
    def __init__(self, start_date, discount_rate):
        self.start_date = start_date
        self.discount_rate = discount_rate

class Customer:
    def __init__(self, name, discount_rate):
        self.name = name
        self._contract = CustomerContract(datetime.today(), discount_rate)

    @property
    def discount_rate(self):
        return self._contract.discount_rate

    @discount_rate.setter
    def discount_rate(self, value):
        self._contract.discount_rate = value
```

#### Move Statements into Function

**Motivation:** When the same code always executes alongside a function call, move it inside the function.

```python
# Before
def emit_photo_data(photo, output):
    output.append(f"<p>title: {photo.title}</p>")
    output.append(f"<p>location: {photo.location}</p>")

# caller always adds the date too:
emit_photo_data(photo, result)
result.append(f"<p>date: {photo.date.strftime('%Y-%m-%d')}</p>")

# After
def emit_photo_data(photo, output):
    output.append(f"<p>title: {photo.title}</p>")
    output.append(f"<p>location: {photo.location}</p>")
    output.append(f"<p>date: {photo.date.strftime('%Y-%m-%d')}</p>")
```

#### Move Statements to Callers

**Motivation:** The inverse — when a function does something that only *some* callers want, move that part back to those callers.

This commonly happens as code evolves: a function that was perfectly cohesive now has a line that should behave differently in different contexts.

#### Slide Statements

**Motivation:** Move related code to be adjacent, making it easier to understand and a precursor to Extract Function.

```python
# Before
pricing_plan = retrieve_pricing_plan()
order = retrieve_order()
charge_per_unit = pricing_plan.unit
# ... unrelated code ...
units = order.units
total = charge_per_unit * units

# After — slide declarations next to their usage
pricing_plan = retrieve_pricing_plan()
charge_per_unit = pricing_plan.unit
order = retrieve_order()
units = order.units
total = charge_per_unit * units
```

**Safety check:** Ensure no data dependency or side effect prevents the reordering. A statement can't move past code that modifies data it reads (or vice versa).

#### Replace Inline Code with Function Call

**Motivation:** When you have code that does the same thing as an existing library function, use the library function. It communicates intent better and reduces duplication.

```python
# Before
has_new_england = False
for s in states:
    if s == "MA" or s == "CT" or s == "ME" or s == "VT" or s == "NH" or s == "RI":
        has_new_england = True
        break

# After
has_new_england = any(s in NEW_ENGLAND_STATES for s in states)
```

#### Split Loop

**Motivation:** A loop that does two different things should be split into two loops, each doing one thing. This makes it possible to extract each loop body into its own function.

```python
# Before — single loop calculates both totals
youngest_age = float("inf")
total_salary = 0
for p in people:
    if p.age < youngest_age:
        youngest_age = p.age
    total_salary += p.salary

# After — separate loops, then extract
youngest_age = min(p.age for p in people)
total_salary = sum(p.salary for p in people)
```

**"But doesn't this mean looping twice?"** — Yes, and it almost never matters. If profiling shows it does, recombine the loops later.

#### Replace Loop with Pipeline

**Motivation:** Collection pipelines (map, filter, reduce, list comprehensions) communicate intent more clearly than loops.

```python
# Before
names = []
for c in companies:
    if c.country == "India":
        names.append(c.name)

# After
names = [c.name for c in companies if c.country == "India"]
```

More complex pipelines:

```python
# Before — nested loop logic
result = []
for line in input_lines:
    fields = line.strip().split(",")
    if fields[1].strip() == "office":
        city = fields[0].strip()
        result.append(f"office in {city}")

# After
result = [
    f"office in {fields[0].strip()}"
    for line in input_lines
    for fields in [line.strip().split(",")]
    if fields[1].strip() == "office"
]
```

#### Remove Dead Code

**Motivation:** Unused code creates confusion. Delete it — version control remembers everything.

```python
# Before
def calculate_price(order):
    # old_price = order.quantity * 5  # commented out since 2019
    return order.quantity * order.item_price
```

Just delete the commented-out line. Don't keep code "just in case" — that's what `git log` is for.

---

### Chapter 9: Organizing Data

#### Split Variable

**Motivation:** A variable that is assigned more than once (and isn't a loop counter or collecting variable) is doing two jobs. Give each job its own variable.

```python
# Before — 'temp' is reused for two different purposes
def distance_travelled(scenario, time):
    result = 0
    acc = scenario.primary_force / scenario.mass  # acceleration phase 1
    primary_time = min(time, scenario.delay)
    result = 0.5 * acc * primary_time ** 2
    secondary_time = time - scenario.delay
    if secondary_time > 0:
        primary_velocity = acc * scenario.delay
        acc = (scenario.primary_force + scenario.secondary_force) / scenario.mass  # reused!
        result += primary_velocity * secondary_time + 0.5 * acc * secondary_time ** 2
    return result

# After — each acceleration gets its own variable
def distance_travelled(scenario, time):
    result = 0
    primary_acceleration = scenario.primary_force / scenario.mass
    primary_time = min(time, scenario.delay)
    result = 0.5 * primary_acceleration * primary_time ** 2
    secondary_time = time - scenario.delay
    if secondary_time > 0:
        primary_velocity = primary_acceleration * scenario.delay
        secondary_acceleration = (scenario.primary_force + scenario.secondary_force) / scenario.mass
        result += primary_velocity * secondary_time + 0.5 * secondary_acceleration * secondary_time ** 2
    return result
```

#### Rename Field

**Motivation:** Names matter — especially in records and classes used widely. Renaming a field is straightforward with encapsulation already in place (just rename the internal field; the property name is what callers see).

#### Replace Derived Variable with Query

**Motivation:** Mutable derived data easily becomes stale. Replace it with a calculation.

```python
# Before — _discounted_total is updated whenever a discount changes
class ProductionPlan:
    def __init__(self):
        self._adjustments = []
        self._production = 0  # derived, maintained manually

    def apply_adjustment(self, adjustment):
        self._adjustments.append(adjustment)
        self._production += adjustment.amount

# After — calculate on demand
class ProductionPlan:
    def __init__(self):
        self._adjustments = []

    @property
    def production(self):
        return sum(a.amount for a in self._adjustments)
```

**Exception:** When the calculation is expensive and you've profiled to confirm it's a bottleneck, caching is appropriate — but encapsulate it.

#### Change Reference to Value

**Motivation:** Value objects are simpler to reason about because they're immutable. If a field doesn't need to be shared and updated in place, make it a value.

```python
# Before — Person's telephone number is a shared reference
class TelephoneNumber:
    def __init__(self, area_code, number):
        self.area_code = area_code  # mutable
        self.number = number        # mutable

# After — immutable value object
@dataclass(frozen=True)
class TelephoneNumber:
    area_code: str
    number: str
```

With a frozen dataclass, `==` compares by value automatically. To change the number, you create a new `TelephoneNumber` instead of mutating.

#### Change Value to Reference

**Motivation:** Sometimes you *need* shared identity — e.g., multiple orders reference the same customer, and updating the customer should be reflected everywhere.

```python
# Solution: use a repository / registry
_customer_repository: dict[str, Customer] = {}

def register_customer(id: str) -> Customer:
    if id not in _customer_repository:
        _customer_repository[id] = Customer(id)
    return _customer_repository[id]

class Order:
    def __init__(self, data: dict):
        self._customer = register_customer(data["customer_id"])
```

---

### Chapter 10: Simplifying Conditional Logic

#### Decompose Conditional

**Motivation:** Complex conditional logic is one of the hardest things to read. Extract the condition and each branch into functions named for their intent.

```python
# Before
if plan.start_date <= a_date <= plan.end_date:
    charge = plan.base_rate * quantity + plan.tax
else:
    charge = plan.base_rate * quantity * plan.off_peak_factor + plan.tax

# After
if is_peak_season(a_date, plan):
    charge = peak_charge(quantity, plan)
else:
    charge = off_peak_charge(quantity, plan)
```

Or using a conditional expression for simple cases:

```python
charge = peak_charge(quantity, plan) if is_peak_season(a_date, plan) else off_peak_charge(quantity, plan)
```

#### Consolidate Conditional Expression

**Motivation:** When multiple conditions yield the same result, combine them into a single check with a descriptive name.

```python
# Before
def disability_amount(employee):
    if employee.seniority < 2:
        return 0
    if employee.months_disabled > 12:
        return 0
    if employee.is_part_time:
        return 0
    return compute_disability(employee)

# After
def disability_amount(employee):
    if is_not_eligible_for_disability(employee):
        return 0
    return compute_disability(employee)

def is_not_eligible_for_disability(employee):
    return (
        employee.seniority < 2
        or employee.months_disabled > 12
        or employee.is_part_time
    )
```

#### Replace Nested Conditional with Guard Clauses

**Motivation:** Use guard clauses (early returns) for special cases at the top of a function, leaving the "happy path" as the main logic.

```python
# Before — deeply nested
def pay_amount(employee):
    if employee.is_separated:
        result = separated_amount()
    else:
        if employee.is_retired:
            result = retired_amount()
        else:
            result = normal_pay_amount(employee)
    return result

# After — guard clauses
def pay_amount(employee):
    if employee.is_separated:
        return separated_amount()
    if employee.is_retired:
        return retired_amount()
    return normal_pay_amount(employee)
```

**Key insight:** Guard clauses say "this is an unusual condition — handle it and get out." The indented `if-else` form implies both branches are equally likely/normal. Use the form that matches the semantics.

#### Replace Conditional with Polymorphism

**Motivation:** When you have a switch/match on a type code that appears in multiple places, replace it with a class hierarchy. Each case becomes a subclass with its own implementation.

```python
# Before — switch on bird type
def plumage(bird):
    match bird["type"]:
        case "EuropeanSwallow":
            return "average"
        case "AfricanSwallow":
            return "average" if bird["number_of_coconuts"] <= 2 else "tired"
        case "NorwegianBlueParrot":
            return "beautiful" if bird["voltage"] <= 100 else "scorched"

# After — polymorphism
class Bird:
    def __init__(self, data):
        self._name = data["name"]

class EuropeanSwallow(Bird):
    @property
    def plumage(self):
        return "average"

class AfricanSwallow(Bird):
    def __init__(self, data):
        super().__init__(data)
        self._number_of_coconuts = data["number_of_coconuts"]

    @property
    def plumage(self):
        return "average" if self._number_of_coconuts <= 2 else "tired"

class NorwegianBlueParrot(Bird):
    def __init__(self, data):
        super().__init__(data)
        self._voltage = data["voltage"]

    @property
    def plumage(self):
        return "beautiful" if self._voltage <= 100 else "scorched"

def create_bird(data):
    match data["type"]:
        case "EuropeanSwallow": return EuropeanSwallow(data)
        case "AfricanSwallow": return AfricanSwallow(data)
        case "NorwegianBlueParrot": return NorwegianBlueParrot(data)
        case _: return Bird(data)
```

**Variant — using polymorphism for a variation within a type:** When you don't want a full hierarchy for the main type, create a helper hierarchy for just the varying behavior (delegation instead of inheritance).

#### Introduce Special Case

**Motivation:** When many callers check for a special value (often `None`) and do the same thing, create a Special Case object (also known as the **Null Object pattern**).

```python
# Before — scattered null checks
customer_name = site.customer.name if site.customer != "unknown" else "occupant"
plan = site.customer.plan if site.customer != "unknown" else BASIC_PLAN

# After — special case class
class UnknownCustomer:
    @property
    def name(self):
        return "occupant"

    @property
    def plan(self):
        return BASIC_PLAN

    @property
    def is_unknown(self):
        return True

class Site:
    @property
    def customer(self):
        return self._customer if self._customer != "unknown" else UnknownCustomer()

# Now callers just use site.customer.name — no special-casing needed
```

#### Introduce Assertion

**Motivation:** Assertions document assumptions that should always be true. They make implicit assumptions explicit and serve as both documentation and a safety net.

```python
class Customer:
    def apply_discount(self, amount):
        assert self.discount_rate is not None, "discount_rate must be set before applying discount"
        return amount - (self.discount_rate * amount)
```

**Key point:** Assertions should never affect the logic — the program should behave identically whether they're present or stripped out. Don't use assertions for validation of external inputs; use them to document internal invariants.

---

### Chapter 11: Refactoring APIs

#### Separate Query from Modifier

**Motivation (Command-Query Separation):** A function should either return a value (query) or have a side effect (command), never both. This makes code easier to reason about and test.

```python
# Before — find miscreant AND send alert (side effect + return value)
def alert_for_miscreant(people):
    for p in people:
        if p.name == "Don" or p.name == "John":
            send_alert(p)
            return p.name
    return ""

# After — separate the query from the command
def find_miscreant(people):
    for p in people:
        if p.name == "Don" or p.name == "John":
            return p.name
    return ""

def alert_for_miscreant(people):
    if miscreant := find_miscreant(people):
        send_alert(miscreant)
```

#### Parameterize Function

**Motivation:** When multiple functions do very similar things with different literal values, unify them into a single function with a parameter.

```python
# Before
def ten_percent_raise(person):
    person.salary = person.salary * 1.10

def five_percent_raise(person):
    person.salary = person.salary * 1.05

# After
def raise_salary(person, factor):
    person.salary = person.salary * (1 + factor)
```

#### Remove Flag Argument

**Motivation:** Boolean (or string) flags that change function behavior are confusing for callers. Replace with explicit functions.

```python
# Before
def set_dimension(name, value):
    if name == "height":
        self._height = value
    elif name == "width":
        self._width = value

# After
def set_height(value):
    self._height = value

def set_width(value):
    self._width = value
```

**Key insight:** The caller's code should read clearly. `book_concert(customer, True)` is opaque; `book_concert_premium(customer)` communicates intent.

#### Preserve Whole Object

**Motivation:** When you extract several values from an object just to pass them to a function, pass the whole object instead. This reduces parameter lists and makes the function more resilient to changes in the object's structure.

```python
# Before
low = room.days_temp_range.low
high = room.days_temp_range.high
if heating_plan.within_range(low, high): ...

# After
if heating_plan.within_range(room.days_temp_range): ...
```

**Caveat:** If passing the whole object introduces a dependency you don't want (e.g., a utility function shouldn't depend on a domain object), keep the individual parameters.

#### Replace Parameter with Query

**Motivation:** When a parameter can be derived from another parameter or from the receiver, remove it and have the function compute the value itself.

```python
# Before
class Order:
    @property
    def final_price(self):
        base = self.quantity * self.item_price
        level = 1 if self.quantity > 100 else 2
        return self.discounted_price(base, level)

    def discounted_price(self, base, level):
        return base * 0.95 if level == 1 else base * 0.98

# After
class Order:
    @property
    def final_price(self):
        base = self.quantity * self.item_price
        return self.discounted_price(base)

    @property
    def discount_level(self):
        return 1 if self.quantity > 100 else 2

    def discounted_price(self, base):
        return base * 0.95 if self.discount_level == 1 else base * 0.98
```

**Caveat:** Don't do this if computing the value introduces an unwanted dependency or side effect into the called function.

#### Replace Query with Parameter

**Motivation:** The inverse — when a function reaches into a global or has an unwanted dependency to get a value, pass it as a parameter instead. This is common when removing a dependency on a mutable global.

```python
# Before — function depends on a global thermostat
def target_temperature(plan):
    current_temp = thermostat.current_temperature  # global dependency
    if plan.target > current_temp:
        return plan.target
    return plan.target - (plan.target - current_temp) * plan.adjustment

# After — caller provides the value
def target_temperature(plan, current_temp):
    if plan.target > current_temp:
        return plan.target
    return plan.target - (plan.target - current_temp) * plan.adjustment
```

This makes the function **referentially transparent** (same inputs → same output), which is easier to test and reason about. The trade-off: it pushes the responsibility to the caller.

#### Remove Setting Method

**Motivation:** If a field should not change after construction, remove its setter. This communicates immutability.

```python
# Before
class Person:
    def __init__(self, id_):
        self.id = id_  # settable — but should it be?

# After
class Person:
    def __init__(self, id_):
        self._id = id_

    @property
    def id(self):
        return self._id
    # No setter — id is immutable after construction
```

#### Replace Constructor with Factory Function

**Motivation:** Constructors have limitations: they must return an instance of that exact class (no subclasses), they can't have descriptive names. Factory functions are more flexible.

```python
# Before
class Employee:
    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code

# After
class Employee:
    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code

def create_employee(name, type_code):
    return Employee(name, type_code)

# Or for subclass selection:
def create_employee(name, type_code):
    match type_code:
        case "engineer": return Engineer(name)
        case "manager": return Manager(name)
        case "salesman": return Salesman(name)
        case _: raise ValueError(f"unknown type: {type_code}")
```

#### Replace Function with Command

**Motivation:** When a function is complex enough that you need to break it apart, but the pieces share significant local state, wrap it in a command object. The command object turns local variables into fields that all methods can access.

**Definition:** A *command object* (or just "command") is an object that encapsulates a function invocation. It provides facilities like undo, lifecycle management, and customization that plain functions don't.

```python
# Before — complex scoring function with many local variables
def score(candidate, medical_exam, scoring_guide):
    result = 0
    health_level = 0
    high_medical_risk = False

    if medical_exam.is_smoker:
        health_level += 10
        high_medical_risk = True

    certification_grade = "regular"
    if scoring_guide.state_with_low_certification(candidate.origin_state):
        certification_grade = "low"
        result -= 5

    # ... more complex logic using all these temps ...
    result -= max(health_level - 5, 0)
    return result

# After — command object
class Scorer:
    def __init__(self, candidate, medical_exam, scoring_guide):
        self._candidate = candidate
        self._medical_exam = medical_exam
        self._scoring_guide = scoring_guide

    def execute(self):
        self._result = 0
        self._health_level = 0
        self._high_medical_risk = False
        self._score_smoking()
        self._certify()
        self._result -= max(self._health_level - 5, 0)
        return self._result

    def _score_smoking(self):
        if self._medical_exam.is_smoker:
            self._health_level += 10
            self._high_medical_risk = True

    def _certify(self):
        self._certification_grade = "regular"
        if self._scoring_guide.state_with_low_certification(self._candidate.origin_state):
            self._certification_grade = "low"
            self._result -= 5

# Usage
score = Scorer(candidate, medical_exam, scoring_guide).execute()
```

#### Replace Command with Function

**Motivation:** The inverse — when a command object is simple enough that a plain function would do, simplify. Commands add complexity; don't keep that complexity if you don't need it.

---

### Chapter 12: Dealing with Inheritance

#### Pull Up Method

**Motivation:** When subclasses have identical methods, move the method to the superclass to eliminate duplication.

```python
# Before
class Employee:
    pass

class Engineer(Employee):
    @property
    def annual_cost(self):
        return self.monthly_cost * 12

class Salesman(Employee):
    @property
    def annual_cost(self):
        return self.monthly_cost * 12

# After
class Employee:
    @property
    def annual_cost(self):
        return self.monthly_cost * 12
```

**Variation — Template Method:** If the methods are *similar* but not identical, parameterize the differences or extract the differing parts into abstract methods, then pull up the common structure.

#### Pull Up Field

**Motivation:** When subclasses have the same field, move it to the superclass.

#### Pull Up Constructor Body

**Motivation:** When subclass constructors have common initialization logic, pull the common parts to the superclass `__init__`.

```python
# Before
class Employee:
    def __init__(self):
        self._name = None

class Manager(Employee):
    def __init__(self, name, grade):
        super().__init__()
        self._name = name
        self._grade = grade

class Engineer(Employee):
    def __init__(self, name):
        super().__init__()
        self._name = name

# After
class Employee:
    def __init__(self, name):
        self._name = name

class Manager(Employee):
    def __init__(self, name, grade):
        super().__init__(name)
        self._grade = grade

class Engineer(Employee):
    def __init__(self, name):
        super().__init__(name)
```

#### Push Down Method

**Motivation:** When a method is only relevant to one subclass, move it out of the superclass into that subclass.

#### Push Down Field

**Motivation:** When a field is only used by one subclass, push it down.

#### Replace Type Code with Subclasses

**Motivation:** When an object has a type code that affects behavior (e.g., `type_code == "engineer"` triggers different logic), replace the type code with subclasses.

**Direct subclassing:**

```python
# Before
class Employee:
    def __init__(self, name, type_code):
        self._name = name
        self._type_code = type_code

# After
class Employee:
    def __init__(self, name):
        self._name = name

class Engineer(Employee):
    @property
    def type(self):
        return "engineer"

class Manager(Employee):
    @property
    def type(self):
        return "manager"

def create_employee(name, type_code):
    match type_code:
        case "engineer": return Engineer(name)
        case "manager": return Manager(name)
        case _: raise ValueError(f"Unknown type: {type_code}")
```

**Indirect subclassing (when you can't subclass the main class):** Subclass the *type* instead:

```python
class EmployeeType:
    pass

class Engineer(EmployeeType):
    def __str__(self):
        return "engineer"

class Manager(EmployeeType):
    def __str__(self):
        return "manager"

class Employee:
    def __init__(self, name, type_code):
        self._name = name
        self._type = self._create_type(type_code)

    @staticmethod
    def _create_type(type_code):
        match type_code:
            case "engineer": return Engineer()
            case "manager": return Manager()
            case _: raise ValueError(f"Unknown type: {type_code}")
```

#### Remove Subclass

**Motivation:** When subclasses no longer justify their complexity (e.g., they've been refactored down to just a type code), fold them back into the superclass. The inverse of Replace Type Code with Subclasses.

#### Extract Superclass

**Motivation:** When two classes do similar things, create a superclass and pull up the common features.

```python
# Before — two unrelated classes with similar fields/methods
class Department:
    def __init__(self, name, staff):
        self._name = name
        self._staff = staff

    @property
    def total_annual_cost(self):
        return sum(e.annual_cost for e in self._staff)

    @property
    def head_count(self):
        return len(self._staff)

class Employee:
    def __init__(self, name, id_, annual_cost):
        self._name = name
        self._id = id_
        self._annual_cost = annual_cost

# After — common name and annual cost pulled into Party superclass
class Party:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def annual_cost(self):
        raise NotImplementedError
```

**Alternative:** If you don't want or can't use inheritance, **Extract Class** and use delegation instead.

#### Collapse Hierarchy

**Motivation:** When a superclass and subclass are no longer sufficiently different, merge them into one class.

#### Replace Subclass with Delegate

**Motivation:** Inheritance has limitations: a class can only vary on one axis, and it creates tight coupling between parent and child. Delegation provides the same behavior variation with more flexibility.

**When to prefer delegation over inheritance:**
- The object needs to vary on multiple independent axes
- The "type" can change at runtime (you can swap a delegate, but you can't change an object's class)
- You want to avoid coupling to the superclass's implementation

**Example — booking with premium variant:**

```python
# Before — inheritance
class Booking:
    def __init__(self, show, date):
        self._show = show
        self._date = date

class PremiumBooking(Booking):
    def __init__(self, show, date, extras):
        super().__init__(show, date)
        self._extras = extras

    @property
    def has_talkback(self):
        return self._show.has_talkback

    @property
    def base_price(self):
        return round(super().base_price + self._extras.premium_fee)

# After — delegation
class Booking:
    def __init__(self, show, date):
        self._show = show
        self._date = date
        self._premium_delegate = None

    def be_premium(self, extras):
        self._premium_delegate = PremiumBookingDelegate(self, extras)

    @property
    def has_talkback(self):
        if self._premium_delegate:
            return self._premium_delegate.has_talkback
        return self._show.has_talkback and not self._is_peak_day

    @property
    def base_price(self):
        result = self._show.price[self._date]  # base calculation
        if self._premium_delegate:
            result = self._premium_delegate.extend_base_price(result)
        return result


class PremiumBookingDelegate:
    def __init__(self, host_booking, extras):
        self._host = host_booking
        self._extras = extras

    @property
    def has_talkback(self):
        return self._host._show.has_talkback

    def extend_base_price(self, base):
        return round(base + self._extras.premium_fee)
```

**Bird hierarchy example** demonstrates the same pattern: replacing a class hierarchy (EuropeanSwallow, AfricanSwallow, NorwegianBlueParrot) with a single Bird class that delegates species-specific behavior to SpeciesDelegate subclasses. The factory function creates the appropriate delegate.

#### Replace Superclass with Delegate

**Motivation:** When inheritance creates problems — the subclass doesn't really want *all* the superclass behavior (Refused Bequest), or the semantic "is-a" relationship is misleading. Classic example: a `Stack` shouldn't inherit from `List` because stacks don't support arbitrary list operations.

```python
# Before — Scroll inherits from CatalogItem, but it's a stretch
class CatalogItem:
    def __init__(self, id_, title, tags):
        self._id = id_
        self._title = title
        self._tags = tags

class Scroll(CatalogItem):
    def __init__(self, id_, title, tags, date_last_cleaned):
        super().__init__(id_, title, tags)
        self._last_cleaned = date_last_cleaned

# After — Scroll delegates to CatalogItem
class Scroll:
    def __init__(self, id_, catalog_item, date_last_cleaned):
        self._id = id_
        self._catalog_item = catalog_item
        self._last_cleaned = date_last_cleaned

    @property
    def title(self):
        return self._catalog_item.title

    @property
    def tags(self):
        return self._catalog_item.tags

    def has_tag(self, tag):
        return tag in self._catalog_item.tags
```

**Fowler's advice on inheritance vs. delegation:**

> "Favor a judicious mixture of composition and inheritance over either alone, and always be ready to change your mind."

Use inheritance when the relationship genuinely is-a and the subclass wants all the superclass behavior. Use delegation when the relationship is more "uses-a" or "has-a", or when inheritance creates coupling problems. The refactorings in this chapter make it straightforward to switch between the two as your understanding evolves.

---
