# Book4 - Crafting Test-Driven Software with Python — Summary

**Author:** Alessandro Molina | **Publisher:** Packt (2021)

---

### Part 1: Past and Present of Test-Driven Development

---

## Chapter 1: Getting Started with Software Testing

### Why software testing?

- Software testing verifies that code behaves as expected before shipping
- Catches bugs early, reduces cost of fixes, enables safe refactoring
- Tests act as living documentation of expected behavior

### Types of software tests

- **Unit tests** — test a single function/class in isolation; fast, numerous
- **Integration/Functional tests** — test multiple components working together
- **Acceptance/End-to-End tests** — test the whole system from user's perspective
- **Black-box tests** — test without knowledge of internals (input → expected output)
- **White-box tests** — test with knowledge of internals (verify paths/branches)

### The testing pyramid

- Bottom (most tests): **Unit tests** — fast, cheap, isolated
- Middle: **Integration tests** — moderate speed, test component interaction
- Top (fewest tests): **E2E/Acceptance tests** — slow, expensive, test full workflows
- Inverted pyramid = anti-pattern (too many slow tests, too few fast ones)

### Testing in Python

- Python stdlib includes `unittest` module (xUnit-style)
- **`pytest`** is the de facto standard third-party framework (used throughout book)
- **`pip install pytest`**

```python
# unittest style
import unittest

class TestExample(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)

# pytest style (simpler — just use assert)
def test_addition():
    assert 1 + 1 == 2
```

### Arrange, Act, Assert pattern

```python
def test_something():
    # Arrange — set up preconditions
    data = [3, 1, 2]

    # Act — perform the action under test
    data.sort()

    # Assert — verify expected outcome
    assert data == [1, 2, 3]
```

### Test discovery in pytest

- Files must be named `test_*.py` or `*_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test` (no `__init__`)
- Run with: `$ pytest` (auto-discovers tests)
- Verbose: `$ pytest -v`

---

## Chapter 2: Test Doubles with a Chat Application

### What are test doubles?

- **Test double** = generic term for any object that replaces a real dependency in tests
- Needed when real dependencies are slow, unreliable, or have side effects (I/O, network, DB)

### Types of test doubles

#### Fakes

- Simplified working implementations (e.g., in-memory DB instead of real DB)

```python
# Real dependency
class DatabaseStorage:
    def save(self, data):
        # writes to actual database
        ...

# Fake — functional but simplified
class FakeStorage:
    def __init__(self):
        self._data = []
    def save(self, data):
        self._data.append(data)
```

#### Stubs

- Return pre-configured responses; don't have real logic
- Replace a component to control what the system-under-test sees

```python
class StubConnection:
    def recv(self):
        return "Hello"  # always returns this, no real network
```

#### Spies

- Record how they were called (args, call count) for later verification

```python
class SpyConnection:
    def __init__(self):
        self.sent_messages = []
    def send(self, msg):
        self.sent_messages.append(msg)

# In test:
spy = SpyConnection()
chat.broadcast("hi", spy)
assert "hi" in spy.sent_messages
```

#### Mocks

- Pre-programmed with expectations; verify interactions happened correctly
- **`unittest.mock`** — Python stdlib mocking library

```python
from unittest.mock import Mock

mock_conn = Mock()
mock_conn.recv.return_value = "Hello"

result = mock_conn.recv()
assert result == "Hello"
mock_conn.recv.assert_called_once()
```

### `unittest.mock` key features

```python
from unittest.mock import Mock, patch, MagicMock

# Mock — generic mock object
m = Mock()
m.some_method.return_value = 42
m.some_method()  # returns 42
m.some_method.assert_called_once()

# side_effect — raise exception or call function
m.method.side_effect = ValueError("boom")

# patch — temporarily replace an object
with patch("module.ClassName") as MockClass:
    instance = MockClass.return_value
    instance.method.return_value = "fake"

# patch as decorator
@patch("module.function_name")
def test_something(mock_func):
    mock_func.return_value = "mocked"
```

### Dependency injection for testability

- Pass dependencies as constructor args instead of hardcoding them
- Makes it trivial to swap real implementations for test doubles

```python
class ChatClient:
    def __init__(self, connection):  # inject dependency
        self._connection = connection

# In production:
client = ChatClient(RealConnection("server.com"))

# In tests:
client = ChatClient(FakeConnection())
```

---

## Chapter 3: Test-Driven Development while Creating a TODO List

### The TDD cycle: Red → Green → Refactor

1. **Red** — Write a failing test for the next piece of functionality
2. **Green** — Write the minimum code to make the test pass
3. **Refactor** — Clean up the code while keeping tests green
4. Repeat

### Starting with a failing test

```python
# Write the test FIRST — it should fail (Red)
def test_add_todo():
    app = TodoApp()
    app.add("Buy groceries")
    assert app.todos == [("Buy groceries", False)]
```

### Making it pass with minimum code

```python
# Write just enough to pass (Green)
class TodoApp:
    def __init__(self):
        self.todos = []

    def add(self, item):
        self.todos.append((item, False))
```

### Refactoring

- After green, improve code structure without changing behavior
- Tests give confidence that refactoring didn't break anything

### Key TDD principles

- Never write production code without a failing test
- Write only enough test to fail (one assertion at a time)
- Write only enough code to pass the current failing test
- Tests guide the design — they are a first-class citizen

---

## Chapter 4: Scaling the Test Suite

### Organizing tests into directories

```
project/
├── src/
│   └── mypackage/
│       └── __init__.py
├── tests/
│   ├── unit/
│   ├── functional/
│   └── acceptance/
└── setup.py
```

### Continuous Integration (CI)

- **CI** = automatically run tests on every commit/push
- Book uses **Travis CI** as example (`.travis.yml`)

```yaml
language: python
python:
  - "3.7"
  - "3.8"
install:
  - "pip install -e src"
script:
  - "python -m unittest discover tests -v"
```

### Running tests in the cloud

- Push to GitHub → Travis CI picks up → runs test suite → reports pass/fail
- Badge in README shows build status

### Performance tests & benchmarks

```python
import unittest
import time

class TestPerformance(unittest.TestCase):
    def test_operation_speed(self):
        start = time.time()
        # ... operation ...
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Too slow: {elapsed}s"
```

### `pytest.ini` / `setup.cfg` configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = -v
```

---

### Part 2: Crafting Quality Code with PyTest

---

## Chapter 5: Introduction to PyTest

### Why PyTest over unittest

- Simpler syntax — plain `assert` instead of `self.assertEqual()`
- Better output on failures (shows values, diffs)
- Powerful fixture system (vs setUp/tearDown)
- Rich plugin ecosystem
- **`pip install pytest`**

### Writing tests with PyTest

```python
# No class needed, no imports needed for basic tests
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"

# Can still use classes (no inheritance required)
class TestMath:
    def test_multiply(self):
        assert 3 * 4 == 12
```

### PyTest assertions

```python
# pytest rewrites assert statements for rich failure messages
def test_list():
    result = [1, 2, 3]
    assert result == [1, 2, 4]
    # E  assert [1, 2, 3] == [1, 2, 4]
    # E    At index 2 diff: 3 != 4

# Testing exceptions
import pytest

def test_raises():
    with pytest.raises(ValueError):
        int("not_a_number")

def test_raises_match():
    with pytest.raises(ValueError, match="invalid literal"):
        int("abc")
```

### PyTest fixtures

- **Fixture** = a function that provides test data or setup/teardown logic
- Declared with `@pytest.fixture` decorator
- Injected by name into test function arguments

```python
import pytest

@pytest.fixture
def sample_list():
    return [1, 2, 3]

def test_length(sample_list):
    assert len(sample_list) == 3

# Fixture with teardown (using yield)
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn          # test runs here
    conn.close()        # teardown after test
```

### Fixture scopes

```python
@pytest.fixture(scope="function")   # default — per test function
@pytest.fixture(scope="class")      # once per test class
@pytest.fixture(scope="module")     # once per test module
@pytest.fixture(scope="session")    # once per entire test session
```

### conftest.py

- Special file for sharing fixtures across multiple test files
- Pytest auto-discovers `conftest.py` files
- Can exist at any level of the test directory hierarchy

```python
# tests/conftest.py — available to ALL tests
@pytest.fixture
def app():
    return Application()
```

### Parametrize — running a test with multiple inputs

```python
@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

### Markers

```python
@pytest.mark.slow
def test_big_computation():
    ...

# Run only slow tests:    $ pytest -m slow
# Skip slow tests:        $ pytest -m "not slow"

@pytest.mark.skip(reason="not implemented yet")
def test_future_feature():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    ...
```

### Useful CLI options

```bash
pytest -v                   # verbose output
pytest -s                   # show print statements (no capture)
pytest -x                   # stop on first failure
pytest --lf                 # re-run only last failed tests
pytest -k "test_add"        # run tests matching keyword expression
pytest --tb=short           # shorter tracebacks
```

---

## Chapter 6: Dynamic and Parametric Fixtures and Test Configuration

### Dynamic fixtures with `request`

```python
@pytest.fixture
def dynamic_fixture(request):
    # request.param gives the parametrized value
    return request.param * 2

@pytest.mark.parametrize("dynamic_fixture", [1, 2, 3], indirect=True)
def test_doubled(dynamic_fixture):
    assert dynamic_fixture in [2, 4, 6]
```

### `pytest_addoption` — custom CLI options

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default="test",
        help="Environment to run tests against"
    )

@pytest.fixture
def env(request):
    return request.config.getoption("--env")
```

```bash
$ pytest --env=staging
```

### Temporary directories & files

```python
# tmp_path — built-in fixture (pathlib.Path)
def test_write_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    assert f.read_text() == "hello"

# tmp_path_factory — session-scoped
@pytest.fixture(scope="session")
def shared_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("data")
```

### capsys — capturing stdout/stderr

```python
def test_print(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
```

### monkeypatch — temporarily modifying objects

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test123")
    assert os.environ["API_KEY"] == "test123"

def test_patch_function(monkeypatch):
    monkeypatch.setattr("module.expensive_call", lambda: "mocked")
```

---

## Chapter 7: Acceptance Testing with BDD

### What is BDD?

- **Behavior-Driven Development (BDD)** = extension of TDD that uses natural language to describe behavior
- Tests are written in **Gherkin** syntax (Given/When/Then)
- Bridges gap between developers and non-technical stakeholders

### `pytest-bdd` — BDD plugin for pytest

- **`pip install pytest-bdd`**

#### Feature files (`.feature`)

```gherkin
# features/contacts.feature
Feature: Contact management
  As a user I want to manage my contacts

  Scenario: Add a contact
    Given I have an empty contact book
    When I add a contact "Alice" with number "1234567890"
    Then I should have 1 contact
    And the contact "Alice" should exist
```

#### Step definitions

```python
from pytest_bdd import scenario, given, when, then, parsers

@scenario("contacts.feature", "Add a contact")
def test_add_contact():
    pass

@given("I have an empty contact book")
def empty_app():
    return Application()

@when(parsers.parse('I add a contact "{name}" with number "{number}"'))
def add_contact(empty_app, name, number):
    empty_app.run(f"contacts add {name} {number}")

@then(parsers.parse("I should have {count:d} contact"))
def check_count(empty_app, count):
    assert len(empty_app._contacts) == count
```

#### Key Gherkin keywords

- **Given** — preconditions / initial context
- **When** — action performed
- **Then** — expected outcome / assertion
- **And** — additional step (inherits type of preceding keyword)
- **Scenario Outline** + **Examples** — parametrized scenarios

```gherkin
Scenario Outline: Add multiple contacts
  Given I have an empty contact book
  When I add a contact "<name>" with number "<number>"
  Then I should have 1 contact

  Examples:
    | name  | number     |
    | Alice | 1234567890 |
    | Bob   | 0987654321 |
```

---

## Chapter 8: PyTest Essential Plugins

### `pytest-cov` — code coverage

- **`pip install pytest-cov`**
- Uses `coverage.py` under the hood

```bash
# Basic coverage report
$ pytest --cov=mypackage

# Show which lines are not covered
$ pytest --cov=mypackage --cov-report=term-missing

# Output:
# Name                    Stmts  Miss  Cover  Missing
# mypackage/__init__.py      48     1    98%    68
```

```python
# Exclude lines from coverage
from . import main  # pragma: no cover
main()  # pragma: no cover
```

```ini
# pytest.ini — auto-run coverage every time
[pytest]
addopts = --cov=contacts --cov-report=term-missing
```

#### Coveralls — coverage as a service

- Integrates with CI (Travis CI) to track coverage trends over time
- **`pip install coveralls`**

```yaml
# .travis.yml
after_success:
  - coveralls
```

### `pytest-benchmark` — performance benchmarking

- **`pip install pytest-benchmark`**
- Provides a `benchmark` fixture

```python
from contacts import Application

def test_loading(benchmark):
    app = Application()
    app._contacts = [(f"Name {n}", "number") for n in range(1000)]
    app.save()

    benchmark(app.load)  # benchmarks the app.load call
```

```bash
$ pytest -v benchmarks
# Reports: Min, Max, Mean, OPS (Kops/s), Rounds
```

#### Comparing benchmark runs

```bash
# Save benchmarks and compare against previous
$ pytest --benchmark-autosave --benchmark-compare

# Profile bottlenecks
$ pytest --benchmark-cprofile=tottime
```

### `flaky` — retry unstable tests

- **`pip install flaky`**
- For tests that sometimes fail due to timing, concurrency, external services

```python
from flaky import flaky

@flaky
def test_appender():
    l = []
    flaky_appender(l, range(7000))
    assert l == list(range(7000))
```

```bash
# Detect flakiness
$ pytest test_flaky.py --force-flaky --min-passes=10 --max-runs=10

# Control retries
$ pytest --max-runs=3
```

### `pytest-testmon` — smart test selection

- **`pip install pytest-testmon`**
- Builds a dependency graph between code and tests
- On subsequent runs, only re-runs tests affected by code changes

```bash
# First run — builds relationship graph
$ pytest --testmon

# After changing code — only runs affected tests
$ pytest --testmon
# collected 16 items / 14 deselected / 2 selected
```

- Caveat: can't detect changes to config files, data files, or databases

### `pytest-xdist` — parallel test execution

- **`pip install pytest-xdist`**
- Distributes tests across multiple CPU workers

```bash
# Run with 2 workers
$ pytest -n 2

# Auto-detect CPU count
$ pytest -n auto
```

- Tests must be **isolated** (no shared state) for parallel execution
- Benchmarks are unreliable in parallel mode — use `--ignore benchmarks`

---

## Chapter 9: Managing Test Environments with Tox

### Introducing Tox

- **Tox** = virtual environment manager for testing
- Automates: create venvs, install deps, run test commands
- **`pip install tox`**

#### `tox.ini` configuration

```ini
[tox]
setupdir = ./src

[testenv]
deps =
    pytest == 6.0.2
    pytest-bdd == 3.4.0
    flaky == 3.7.0
    pytest-benchmark == 3.2.3
    pytest-cov == 2.10.1
commands =
    pytest --cov=contacts {posargs}
```

```bash
# Run all environments
$ tox

# Pass extra args to pytest
$ tox -- ./tests -k load

# Run specific environment
$ tox -e benchmarks
```

### Testing multiple Python versions with Tox

```ini
[tox]
setupdir = ./src
envlist = py37, py38, py39

[testenv]
deps = ...
commands = pytest --cov=contacts --benchmark-skip {posargs}

# Per-version overrides
[testenv:py27]
deps =
    pytest == 4.6.11
    ...
```

### Using environments for more than Python versions

```ini
# Separate benchmarks environment (not in envlist)
[testenv:benchmarks]
commands =
    pytest --no-cov ./benchmarks {posargs}
```

```bash
$ tox -e benchmarks  # explicitly run benchmarks
```

### Using Tox with Travis CI

- **`pip install tox-travis`** — bridges Tox and Travis
- `tox-travis` reuses Travis's Python instead of installing it twice

```yaml
# .travis.yml
language: python
python:
  - 3.7
  - 3.8
  - 3.9
  - nightly
install:
  - "pip install tox-travis"
  - "pip install coveralls"
script:
  - "tox"
after_success:
  - coveralls
  - "tox -e benchmarks"
```

---

### Part 3: Testing for the Web

---

## Chapter 10: Testing Documentation and Property-Based Testing

### Testing documentation

- Documentation rots when code changes but docs don't
- **`doctest`** + **Sphinx** can verify code examples in docs actually run

#### Sphinx setup

- **`pip install sphinx`**

```bash
$ sphinx-quickstart docs --ext-doctest --ext-autodoc
```

#### `autoclass` directive — code-based reference

```rst
.. autoclass:: contacts.Application
   :members:
```

- Generates docs from docstrings → docs stay in sync with code

#### `testcode` / `testoutput` — verified user guides

```rst
.. testsetup::

    from contacts import Application
    app = Application()

.. testcode::

    app.run("contacts add Name 0123456789")

.. testcode::

    app.run("contacts ls")

.. testoutput::

    Name 0123456789
```

```bash
$ make doctest  # runs all testcode blocks and verifies testoutput
```

- `code-block` = display only (not verified)
- `testcode` = displayed AND executed (verified)

### Property-based testing with Hypothesis

- **`pip install hypothesis`**
- Instead of testing specific examples, test **properties** that should hold for all inputs
- Hypothesis generates random inputs automatically

#### Key concept: strategies

```python
from hypothesis import given
from hypothesis import strategies as st

# st.integers() — generates random ints
# st.text() — generates random strings
# st.lists() — generates random lists
# st.floats(), st.booleans(), st.none(), etc.

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)
```

#### Composite strategies

```python
@st.composite
def phone_number(draw):
    prefix = draw(st.sampled_from(["+1", "+44", ""]))
    digits = draw(st.text(
        alphabet="0123456789",
        min_size=7, max_size=10
    ))
    return prefix + digits
```

#### Hypothesis finds edge cases automatically

- Empty strings, boundary values, unicode, very large numbers
- When a test fails, Hypothesis **shrinks** the input to the minimal failing case
- Failed examples are saved in a database and replayed on future runs

```python
@given(st.text())
def test_add_contact_name(name):
    app = Application()
    # Hypothesis will try "", " ", unicode, very long strings, etc.
    if name.strip():
        app.run(f"contacts add {name} 1234567890")
        assert len(app._contacts) == 1
```

---

## Chapter 11: Testing for the Web: WSGI versus HTTP

### Testing HTTP clients

#### Using real HTTP (slow, fragile)

```python
import requests

class HTTPClient:
    def __init__(self, url, requests=requests):
        self._url = url
        self._requests = requests

    def GET(self):
        return self._requests.get(self._url).text

    def POST(self, **kwargs):
        return self._requests.post(self._url, **kwargs).text

    def DELETE(self):
        return self._requests.delete(self._url).text
```

#### `requests-mock` — mock HTTP responses without network

- **`pip install requests-mock`**

```python
import requests_mock as rm

class TestHTTPClient:
    def test_GET(self):
        with rm.Mocker() as m:
            m.get("http://httpbin.org/get", json={
                "headers": {"Host": "httpbin.org"},
                "args": {}
            })
            client = HTTPClient(url="http://httpbin.org/get")
            response = client.GET()
            assert '"Host": "httpbin.org"' in response
```

- Fast (no network), but doesn't verify client-server compatibility

### Testing WSGI with WebTest

- **WSGI** (Web Server Gateway Interface) = Python standard for web app ↔ server communication (PEP 333)
- **`pip install webtest`**

#### WSGI basics

```python
# Minimal WSGI application
class Application:
    def __call__(self, environ, start_response):
        start_response(
            '200 OK',
            [('Content-type', 'text/plain; charset=utf-8')]
        )
        return ["Hello World".encode("utf-8")]
```

#### WebTest — test WSGI apps without a server

```python
import webtest

class TestWSGIApp:
    def test_GET(self):
        client = webtest.TestApp(Application())
        response = client.get("http://httpbin.org/get").text
        assert '"Host": "httpbin.org"' in response

    def test_POST(self):
        client = webtest.TestApp(Application())
        response = client.post(
            url="http://httpbin.org/get?alpha=1",
            params={"beta": "2"}
        ).json
        assert response["form"] == {"beta": "2"}
```

- `TestApp` routes all requests to the WSGI app in-memory (no network!)
- Tests run in milliseconds vs seconds for real HTTP

#### Dependency injection for dual testing

```python
class HTTPClient:
    def __init__(self, url, requests=requests):  # inject requests
        self._requests = requests
        ...

# Integration test — inject WebTest instead of requests
client = HTTPClient(
    url="http://httpbin.org/get",
    requests=webtest.TestApp(Application())
)
```

### Using WebTest with web frameworks

- Works with any WSGI framework: **Flask, Django, Pyramid, TurboGears2**

```python
# conftest.py — fixture to select framework via CLI
def pytest_addoption(parser):
    parser.addoption("--framework", action="store",
                     help="Choose: [tg2, django, flask, pyramid]")

@pytest.fixture
def wsgiapp(request):
    framework = request.config.getoption("--framework")
    if framework == "flask":
        from myapp.flask import make_application
    elif framework == "django":
        from myapp.django import make_application
    # ...
    return make_application()
```

```bash
$ pytest --framework=flask
$ pytest --framework=django
```

### Writing Django tests with Django's test client

```python
from django.test import TestCase

class HttpbinTests(TestCase):
    def test_home(self):
        response = self.client.get("/")
        self.assertContains(response, "Hello World")

    def test_GET(self):
        response = self.client.get("/get").content.decode("utf-8")
        assert '"Host": "httpbin.org"' in response
```

```bash
$ python manage.py test
```

- **`pytest-django`** — package that lets you run Django tests with pytest

---

## Chapter 12: End-to-End Testing with the Robot Framework

### Introducing the Robot Framework

- **Robot Framework** = automation framework for ATDD/BDD-style end-to-end testing
- Tests written in natural English-like keyword syntax in `.robot` files
- Originally developed by Nokia; widely used for web and mobile E2E tests
- **`pip install robotframework robotframework-seleniumlibrary webdrivermanager robotframework-screencaplibrary`**

#### `.robot` file structure

```robot
*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BROWSER}    chrome

*** Test Cases ***
Hello World
    Run    echo "Hello World" > hello.txt
    ${filecontent} =    Get File    hello.txt
    Should Contain    ${filecontent}    Hello

*** Keywords ***
Echo Hello
    Log    Hello!
```

- `*** Settings ***` — configure libraries
- `*** Variables ***` — reusable variables
- `*** Test Cases ***` — the tests themselves
- `*** Keywords ***` — custom reusable commands
- Multiple spaces separate commands from arguments

### Testing with web browsers

- **`SeleniumLibrary`** — Robot library for browser automation (wraps Selenium)
- **`webdrivermanager`** — download browser drivers

```bash
$ webdrivermanager firefox chrome
```

```robot
*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Search On Google
    Open Browser    http://www.google.com    Chrome
    Input Text    name=q    Stephen\ Hawking
    Press Keys    name=q    ENTER
    Page Should Contain    Wikipedia
    Close Window
```

### Recording the execution of tests

- **`ScreenCapLibrary`** — screenshots and video recording

```robot
*** Settings ***
Library    SeleniumLibrary
Library    ScreenCapLibrary

Test Setup      Start Video Recording
Test Teardown   Stop Video Recording
```

- Recordings and screenshots embedded in `log.html`

### Testing with headless browsers

```robot
*** Variables ***
${BROWSER}        headlesschrome
${NOTHEADLESS}=   "headlesschrome" not in "${BROWSER}"

*** Test Cases ***
Search On Google
    Open Browser    http://www.google.com    ${BROWSER}
    Run Keyword If    ${NOTHEADLESS}    Wait Until Page Contains Element    cnsw
    ...
```

### Testing multiple browsers

```bash
# Override variable from CLI
$ robot --variable browser:firefox searchgoogle.robot
$ robot --variable browser:headlessfirefox searchgoogle.robot
```

### Extending the Robot Framework

#### Adding custom keywords (in `.robot` files)

```robot
*** Keywords ***
Echo Hello
    Log    Hello!

*** Test Cases ***
Use Custom Keywords
    Echo Hello
```

#### Extending Robot from Python

```python
# HelloLibrary/__init__.py
class HelloLibrary:
    def say_hello(self):
        print("Hello from Python!")
```

```python
# setup.py
from setuptools import setup
setup(name='robotframework-hellolibrary', packages=['HelloLibrary'])
```

```robot
*** Settings ***
Library    HelloLibrary

*** Test Cases ***
Use Custom Keywords
    Say Hello
```

#### Library scoping

```python
class HelloLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"   # share instance across suite
    # or "GLOBAL" for entire test run (default is per-test)
```

---

### Quick Reference: Libraries Introduced

| Library / Tool | Purpose | Install |
|---|---|---|
| `pytest` | Test framework | `pip install pytest` |
| `unittest.mock` | Mocking (stdlib) | built-in |
| `pytest-bdd` | BDD / Gherkin tests | `pip install pytest-bdd` |
| `pytest-cov` | Code coverage | `pip install pytest-cov` |
| `pytest-benchmark` | Performance benchmarking | `pip install pytest-benchmark` |
| `flaky` | Retry unstable tests | `pip install flaky` |
| `pytest-testmon` | Smart test selection | `pip install pytest-testmon` |
| `pytest-xdist` | Parallel test execution | `pip install pytest-xdist` |
| `tox` | Test environment manager | `pip install tox` |
| `tox-travis` | Tox + Travis CI bridge | `pip install tox-travis` |
| `coveralls` | Coverage-as-a-service | `pip install coveralls` |
| `hypothesis` | Property-based testing | `pip install hypothesis` |
| `sphinx` | Documentation generator | `pip install sphinx` |
| `requests-mock` | Mock HTTP requests | `pip install requests-mock` |
| `webtest` | WSGI integration testing | `pip install webtest` |
| `pytest-django` | Django + pytest bridge | `pip install pytest-django` |
| `robotframework` | E2E test framework | `pip install robotframework` |
| `robotframework-seleniumlibrary` | Browser automation | `pip install robotframework-seleniumlibrary` |
| `robotframework-screencaplibrary` | Video/screenshot recording | `pip install robotframework-screencaplibrary` |
| `webdrivermanager` | Browser driver management | `pip install webdrivermanager` |
