# Book2 - Python Testing with pytest, Second Edition — Summary

> **Author:** Brian Okken | **Publisher:** Pragmatic Bookshelf (Feb 2022)
> **Sample App:** "Cards" — a CLI task tracker built with **Typer** (CLI), **Rich** (formatting), and **TinyDB** (database)

---

### Part I — Primary Power

#### 1. Getting Started with pytest

##### Installing pytest
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat
pip install pytest
```

##### Running pytest
- `pytest` — searches current dir + subdirs for tests
- `pytest test_file.py` — run one file
- `pytest test_file.py::test_func` — run one test
- `pytest dir/` — run a directory
- `-v` / `--verbose` — show individual test names and PASSED/FAILED
- `--tb=no` — suppress tracebacks

##### Test Discovery
- Files named `test_*.py` or `*_test.py`
- Functions/methods named `test_*`
- Classes named `Test*`

##### Test Outcomes
| Symbol | Meaning |
|--------|---------|
| `.` / PASSED | Test succeeded |
| `F` / FAILED | Assertion or uncaught exception in test |
| `s` / SKIPPED | Test skipped via `@pytest.mark.skip` or `skipif` |
| `x` / XFAIL | Expected failure, and it did fail |
| `X` / XPASS | Expected failure, but it passed |
| `E` / ERROR | Exception in a fixture or hook, not the test itself |

---

#### 2. Writing Test Functions

##### Installing the Sample Application
- Cards is an installable Python package: `pip install ./cards_proj/`
- **Application code** = code under test (CUT/SUT/DUT)
- **Test code** = code that validates the application

##### Writing Knowledge-Building Tests
- Quick tests to verify understanding of data structures / APIs
- Cards uses a Python **dataclass** (`Card`) with `summary`, `owner`, `state`, `id`
  - `compare=False` on `id` means equality ignores `id`
  - Convenience methods: `Card.from_dict(d)`, `card.to_dict()`

##### Using assert Statements
- pytest uses plain `assert` — no `assertEqual`, `assertTrue`, etc.
- **Assert rewriting**: pytest intercepts `assert` to provide rich failure diffs
- `-vv` shows full diff details (matching vs differing attributes, caret markers)

##### Failing with pytest.fail() and Exceptions
- Any uncaught exception fails a test
- `pytest.fail("message")` explicitly fails with a message
- Use `assert` by default; reserve `pytest.fail()` for assertion helpers

##### Writing Assertion Helper Functions
```python
def assert_identical(c1: Card, c2: Card):
    __tracebackhide__ = True        # hide this frame from traceback
    assert c1 == c2
    if c1.id != c2.id:
        pytest.fail(f"id's don't match. {c1.id} != {c2.id}")
```

##### Testing for Expected Exceptions
```python
# Check exception type
with pytest.raises(TypeError):
    cards.CardsDB()

# Check exception message with regex
with pytest.raises(TypeError, match="missing 1 .* positional argument"):
    cards.CardsDB()

# Inspect the exception object
with pytest.raises(TypeError) as exc_info:
    cards.CardsDB()
assert "missing 1 required" in str(exc_info.value)
```
- `exc_info` is of type `ExceptionInfo`

##### Structuring Test Functions
- **Arrange-Act-Assert** (Bill Wake) / **Given-When-Then** (BDD, Dan North)
  - **Given/Arrange** — set up data/state
  - **When/Act** — perform the action under test
  - **Then/Assert** — verify the outcome
- Avoid interleaved assert patterns (`Arrange-Assert-Act-Assert-...`); keep assertions at the end

##### Grouping Tests with Classes
```python
class TestEquality:
    def test_equality(self):
        ...
    def test_inequality(self):
        ...
```
- Run a class: `pytest test_file.py::TestEquality`
- Run a method: `pytest test_file.py::TestEquality::test_equality`
- Use classes primarily for grouping; avoid complex inheritance

##### Running a Subset of Tests
| Subset | Syntax |
|--------|--------|
| Single function | `pytest path/test_mod.py::test_func` |
| Single class | `pytest path/test_mod.py::TestClass` |
| Single method | `pytest path/test_mod.py::TestClass::test_method` |
| Single module | `pytest path/test_mod.py` |
| Directory | `pytest path/` |
| Keyword pattern | `pytest -k "pattern"` |

- `-k` supports `and`, `or`, `not`, and parentheses:
  ```bash
  pytest -k "(dict or ids) and not TestEquality"
  ```

---

#### 3. pytest Fixtures

##### Getting Started with Fixtures
```python
@pytest.fixture()
def some_data():
    return 42

def test_some_data(some_data):    # pytest injects by name
    assert some_data == 42
```
- **Fixture**: a `@pytest.fixture()` decorated function run by pytest before (and sometimes after) tests
- Exception in a fixture → test reports **Error**, not Fail

##### Using Fixtures for Setup and Teardown
```python
@pytest.fixture()
def cards_db():
    with TemporaryDirectory() as db_dir:
        db = cards.CardsDB(Path(db_dir))
        yield db          # test runs here
        db.close()        # teardown — guaranteed to run
```
- Code **before** `yield` = setup; code **after** `yield` = teardown
- Teardown runs regardless of test pass/fail

##### Tracing Fixture Execution with --setup-show
```bash
pytest --setup-show test_count.py
```
- Shows `SETUP` / `TEARDOWN` around each test, with scope letter (`F`=function, `M`=module, `S`=session)

##### Specifying Fixture Scope
| Scope | Runs once per... |
|-------|-----------------|
| `function` (default) | each test function |
| `class` | each test class |
| `module` | each test module (.py file) |
| `package` | each test directory |
| `session` | entire test session |

```python
@pytest.fixture(scope="session")
def db():
    ...
```
- Scope is defined at the fixture, not where it's used
- Fixtures can only depend on fixtures of **equal or wider** scope

##### Sharing Fixtures through conftest.py
- Place fixtures in `conftest.py` to share across multiple test files
- pytest reads `conftest.py` automatically — **never import it**
- Can have `conftest.py` at any directory level

##### Finding Where Fixtures Are Defined
- `pytest --fixtures` — list all available fixtures with source locations
- `pytest --fixtures-per-test test_file.py::test_name` — fixtures used by a specific test

##### Using Multiple Fixture Levels
- Use a session-scoped DB fixture + a function-scoped fixture that calls `delete_all()`
- Gives you one DB connection but clean state per test

##### Using Multiple Fixtures per Test or Fixture
- Tests and fixtures can depend on multiple fixtures in their parameter lists

##### Deciding Fixture Scope Dynamically
```python
def db_scope(fixture_name, config):
    if config.getoption("--func-db", None):
        return "function"
    return "session"

@pytest.fixture(scope=db_scope)
def db():
    ...
```
- Pass a callable to `scope=` for runtime decisions

##### Using autouse for Fixtures That Always Get Used
```python
@pytest.fixture(autouse=True, scope="session")
def footer_session_scope():
    yield
    print(f"finished: {time.strftime(...)}")
```
- Runs for every test in scope without being named in the test's parameter list
- Use sparingly

##### Renaming Fixtures
```python
@pytest.fixture(name="app")
def _app():
    yield app()
```

---

#### 4. Builtin Fixtures

##### Using tmp_path and tmp_path_factory
- **`tmp_path`** (function scope) — returns a `pathlib.Path` to a temp directory
- **`tmp_path_factory`** (session scope) — call `.mktemp("name")` to get temp dirs
- `--basetemp=mydir` to override the base temp directory
- Legacy equivalents: `tmpdir` / `tmpdir_factory` (return `py.path.local`)

##### Using capsys
```python
def test_version(capsys):
    cards.cli.version()
    output = capsys.readouterr().out.rstrip()
    assert output == cards.__version__
```
- `.readouterr()` returns a namedtuple with `.out` and `.err`
- `capsys.disabled()` context manager temporarily turns off capture
- `-s` / `--capture=no` flag disables capture globally
- Variants: `capfd`, `capsysbinary`, `capfdbinary`, `caplog`

##### Using monkeypatch
- **Monkeypatch**: dynamic modification of code/environment during a test, automatically undone after
- Methods:
  - `setattr(target, name, value)` / `delattr(target, name)`
  - `setitem(dic, name, value)` / `delitem(dic, name)`
  - `setenv(name, value)` / `delenv(name)`
  - `syspath_prepend(path)`
  - `chdir(path)`

```python
def test_patch_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("CARDS_DB_DIR", str(tmp_path))
    assert run_cards("config") == str(tmp_path)
```

##### Remaining Builtin Fixtures
- `cache` — persist values across pytest runs (enables `--last-failed`, `--failed-first`)
- `pytestconfig` — access config values and plugin hooks
- `request` — info on executing test; used in fixture parametrization
- `recwarn` — test warning messages
- `pytester` / `testdir` — for testing pytest plugins
- `record_property` / `record_testsuite_property` — add metadata to XML reports

---

#### 5. Parametrization

##### Testing Without Parametrize
- Writing separate functions for each test case is redundant
- Combining into a loop loses individual reporting and stops at first failure

##### Parametrizing Functions
```python
@pytest.mark.parametrize("start_state", ["done", "in prog", "todo"])
def test_finish(cards_db, start_state):
    c = Card("write a book", state=start_state)
    ...
```
- First arg: comma-separated string or list of param names
- Second arg: list of values (or tuples for multiple params)
- Each value becomes a separate test case

##### Parametrizing Fixtures
```python
@pytest.fixture(params=["done", "in prog", "todo"])
def start_state(request):
    return request.param

def test_finish(cards_db, start_state):
    ...
```
- Useful when setup/teardown must run per parameter value
- All tests using the fixture get parametrized

##### Parametrizing with pytest_generate_tests
```python
def pytest_generate_tests(metafunc):
    if "start_state" in metafunc.fixturenames:
        metafunc.parametrize("start_state", ["done", "in prog", "todo"])
```
- Hook function called during test collection
- Most powerful: can use command-line flags, combine parameters dynamically

##### Using Keywords to Select Test Cases
```bash
pytest -k "todo and not (play or create)"
```
- Works on parametrized test IDs (the bracket portion)
- Quote expressions with spaces/brackets for shell safety

---

#### 6. Markers

##### Using Builtin Markers
- `@pytest.mark.skip(reason=None)` — unconditional skip
- `@pytest.mark.skipif(condition, *, reason)` — conditional skip
- `@pytest.mark.xfail(condition, *, reason, run=True, raises=None, strict=False)` — expected failure
- `@pytest.mark.parametrize(...)` — covered in Ch5
- `@pytest.mark.usefixtures(...)` — apply fixtures to tests
- `@pytest.mark.filterwarnings(warning)` — add warning filter

##### Skipping Tests with pytest.mark.skip
```python
@pytest.mark.skip(reason="Feature not implemented yet")
def test_less_than():
    ...
```
- `-ra` flag shows reasons for all non-passing tests

##### Skipping Tests Conditionally with pytest.mark.skipif
```python
@pytest.mark.skipif(
    parse(cards.__version__).major < 2,
    reason="Not supported in 1.x",
)
```
- Uses **`packaging`** library (`pip install packaging`) for version parsing

##### Expecting Tests to Fail with pytest.mark.xfail
- `strict=False` (default): passing xfail → XPASS (not a failure)
- `strict=True`: passing xfail → FAILED
- Recommendation: set `xfail_strict = true` in `pytest.ini`

##### Selecting Tests with Custom Markers
```python
@pytest.mark.smoke
def test_start(cards_db):
    ...
```
- Register markers in `pytest.ini` to avoid typo warnings:
  ```ini
  [pytest]
  markers =
      smoke: subset of tests
      exception: check for expected exceptions
  ```

- Select: `pytest -m smoke`

##### Marking Files, Classes, and Parameters
- **File-level**: `pytestmark = pytest.mark.finish` (or a list)
- **Class-level**: `@pytest.mark.smoke` on the class
- **Parameter-level**: `pytest.param("in prog", marks=pytest.mark.smoke)`

##### Using "and," "or," "not," and Parentheses with Markers
```bash
pytest -m "(exception or smoke) and (not finish)"
```
- Can combine `-m` and `-k` flags

##### Being Strict with Markers
- `--strict-markers` turns unknown marker warnings into errors
- Add to `addopts` in `pytest.ini` for always-on behavior

##### Combining Markers with Fixtures
```python
@pytest.mark.num_cards(3)
def test_three_cards(cards_db):
    assert cards_db.count() == 3
```
- In the fixture, use `request.node.get_closest_marker("num_cards")` to read the marker
- Access args via `marker.args` and `marker.kwargs`
- **Faker** library (`pip install Faker`): provides a `faker` fixture for generating fake data
  - `faker.sentence()`, `faker.first_name()`, `faker.seed_instance(101)`

##### Listing Markers
```bash
pytest --markers
```

---

### Part II — Working with Projects

#### 7. Strategy

##### Determining Test Scope
- Consider: security, performance, load testing, input validation
- Start with user-visible functionality testing; defer other concerns until needed

##### Considering Software Architecture
- Cards has 3 layers: **CLI** (cli.py) → **API** (api.py) → **DB** (db.py)
- CLI and DB layers intentionally thin; most logic in API
- Strategy: test features through the API; test CLI just enough to verify it calls the API correctly

##### Evaluating the Features to Test
- Prioritize by: **Recent**, **Core**, **Risk**, **Problematic**, **Expertise**
- Core features get thorough testing; non-core get at least one test case

##### Creating Test Cases
- Start with a non-trivial **happy path** test case
- Then consider: interesting inputs, interesting starting states, interesting end states, error states
- Example for `count`: empty DB, one item, more than one item
- Example for `delete`: delete one of many, delete the last card, delete non-existent

##### Writing a Test Strategy
- Document the strategy so you and your team can refer to it later
- Cards strategy summary:
  1. Test user-visible features through the API
  2. Test CLI just enough to verify API integration
  3. Test core features thoroughly (`add`, `count`, `delete`, `finish`, `list`, `start`, `update`)
  4. Cursory tests for `config` and `version`

---

#### 8. Configuration Files

##### Understanding pytest Configuration Files
| File | Purpose |
|------|---------|
| `pytest.ini` | Primary config; its location defines **rootdir** |
| `conftest.py` | Fixtures and hook functions; can exist at any level |
| `__init__.py` | Prevents test filename collisions across subdirectories |
| `tox.ini` | tox config; can include a `[pytest]` section |
| `pyproject.toml` | Modern Python packaging; uses `[tool.pytest.ini_options]` |
| `setup.cfg` | Legacy packaging; uses `[tool:pytest]` |

##### Saving Settings and Flags in pytest.ini
```ini
[pytest]
addopts =
    --strict-markers
    --strict-config
    -ra
testpaths = tests
markers =
    smoke: subset of tests
```
- `--strict-config` raises errors for config file parsing issues

##### Using tox.ini, pyproject.toml, or setup.cfg in place of pytest.ini
- **tox.ini**: identical `[pytest]` section syntax
- **pyproject.toml**: `[tool.pytest.ini_options]`; values are quoted strings or lists
- **setup.cfg**: `[tool:pytest]` section; beware parser differences

##### Determining a Root Directory and Config File
- pytest searches upward from test path for a config file → that directory becomes **rootdir**
- Tip: always place at least an empty `pytest.ini` at the project root

##### Sharing Local Fixtures and Hook Functions with conftest.py
- Anything in `conftest.py` applies to tests in that directory and below
- Try to stick to one `conftest.py` for easy fixture discovery

##### Avoiding Test File Name Collision
- `__init__.py` in test subdirs allows duplicate filenames like `tests/api/test_add.py` and `tests/cli/test_add.py`
- Without it: `import file mismatch` error

---

#### 9. Coverage

> **Key libraries:** **coverage.py** (`pip install coverage`) and **pytest-cov** (`pip install pytest-cov`)

##### Using coverage.py with pytest-cov
```bash
pytest --cov=cards ch7                          # basic report
pytest --cov=cards --cov-report=term-missing ch7  # show missed lines
```
- Equivalent without pytest-cov:
  ```bash
  coverage run --source=cards -m pytest ch7
  coverage report --show-missing
  ```

- `.coveragerc` config maps installed package paths to local source:
  ```ini
  [paths]
  source =
      cards_proj/src/cards
      */site-packages/cards
  ```

##### Generating HTML Reports
```bash
pytest --cov=cards --cov-report=html ch7
# or
coverage html
```
- Output: `htmlcov/index.html` — color-coded line-by-line coverage

##### Excluding Code from Coverage
```python
if __name__ == '__main__':  # pragma: no cover
    main()
```
- `# pragma: no cover` excludes a line or block

##### Running Coverage on Tests
```bash
pytest --cov=cards --cov=ch7 ch7
```
- Catches duplicate test function names (only last one in a file runs)
- Catches unused fixtures / dead code in fixtures

##### Running Coverage on a Directory
```bash
pytest --cov=ch9/some_code ch9/some_code
```

##### Running Coverage on a Single File
```bash
pytest --cov=single_file single_file.py   # no .py in --cov
```

---

#### 10. Mocking

> **Key library:** `unittest.mock` (stdlib since Python 3.3)

##### Isolating the Command-Line Interface
- Cards CLI accesses: `cards.__version__`, `cards.CardsDB`, `cards.InvalidCardId`, `cards.Card`
- **Typer** provides `CliRunner` for in-process CLI testing:
  ```python
  from typer.testing import CliRunner
  runner = CliRunner()
  result = runner.invoke(cards.app, ["version"])
  ```

##### Testing with Typer
```python
import shlex
def cards_cli(command_string):
    result = runner.invoke(cards.app, shlex.split(command_string))
    return result.stdout.rstrip()
```

##### Mocking an Attribute
```python
from unittest import mock

def test_mock_version():
    with mock.patch.object(cards, "__version__", "1.2.3"):
        result = runner.invoke(app, ["version"])
        assert result.stdout.rstrip() == "1.2.3"
```

##### Mocking a Class and Methods
```python
with mock.patch.object(cards, "CardsDB") as MockCardsDB:
    MockCardsDB.return_value.path.return_value = "/foo/"
```
- Calling a mock returns `mock.return_value` (another mock)
- Set `.return_value` on chained mocks for method calls

##### Keeping Mock and Implementation in Sync with Autospec
```python
with mock.patch.object(cards, "CardsDB", autospec=True) as CardsDB:
    ...
```
- **Always use `autospec=True`** — prevents mock drift (misspelled methods, wrong params)
- Without it, mocks silently accept any attribute or call

##### Making Sure Functions Are Called Correctly
```python
def test_add_with_owner(mock_cardsdb):
    cards_cli("add some task -o brian")
    expected = cards.Card("some task", owner="brian", state="todo")
    mock_cardsdb.add_card.assert_called_with(expected)
```
- Variants: `assert_called()`, `assert_called_once()`, `assert_called_once_with(...)`, `assert_not_called()`

##### Creating Error Conditions
```python
mock_cardsdb.delete_card.side_effect = cards.api.InvalidCardId
out = cards_cli("delete 25")
assert "Error: Invalid card id 25" in out
```

##### Testing at Multiple Layers to Avoid Mocking
- Alternative: call CLI, then use the real API to verify state
- Tests **behavior** instead of implementation → more resilient to refactoring
- **Change detector tests**: tests that break during valid refactoring (avoid these)

##### Using Plugins to Assist Mocking
- **pytest-mock**: provides a `mocker` fixture (thin wrapper around `unittest.mock`)
- Domain-specific: `pytest-postgresql`, `pytest-mongo`, `pytest-httpserver`, `responses`, `betamax`

---

#### 11. tox and Continuous Integration

##### What Is Continuous Integration?
- Automated build + test triggered on code changes
- Allows frequent integration, reducing merge conflicts

##### Introducing tox
> **tox** (`pip install tox`): local CI automation tool

- For each environment: creates venv → installs deps → builds package → installs package → runs tests

##### Setting Up tox
```ini
[tox]
envlist = py310
isolated_build = True       # required for pyproject.toml-based packages

[testenv]
deps =
    pytest
    faker
commands = pytest
```

##### Running tox
```bash
tox                         # run all environments
tox -e py310                # run one environment
tox -p                      # run environments in parallel
```

##### Testing Multiple Python Versions
```ini
envlist = py37, py38, py39, py310
skip_missing_interpreters = True
```

##### Adding a Coverage Report to tox
- Add `pytest-cov` to `deps`, change commands to `pytest --cov=cards`
- Use `.coveragerc` with `[paths]` to unify source paths

##### Specifying a Minimum Coverage Level
```ini
commands = pytest --cov=cards --cov=tests --cov-fail-under=100
```

##### Passing pytest Parameters Through tox
```ini
commands = pytest --cov=cards {posargs}
```
```bash
tox -e py310 -- -k test_version --no-cov
```
- `--` separates tox args from pytest args

##### Running tox with GitHub Actions
```yaml
# .github/workflows/main.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.7", "3.8", "3.9", "3.10"]
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python }}
      - run: pip install tox
      - run: tox -e py
```
- CI alternatives: GitLab CI, Bitbucket Pipelines, CircleCI, Jenkins

---

#### 12. Testing Scripts and Applications

##### Testing a Simple Python Script
```python
from subprocess import run
def test_hello():
    result = run(["python", "hello.py"], capture_output=True, text=True)
    assert result.stdout == "Hello, World!\n"
```
- For tox with non-packaged code: set `skipsdist = true`

##### Testing an Importable Python Script
- Wrap logic in `main()`, guard with `if __name__ == "__main__": main()`
- Now tests can `import hello` and call `hello.main()` with `capsys`

##### Separating Code into src and tests Directories
```ini
# pytest.ini
[pytest]
pythonpath = src
testpaths = tests
```
- `pythonpath` (pytest 7+) adds directories to `sys.path` during test collection
- For pytest 6.2: use the **pytest-srcpaths** plugin

##### Defining the Python Search Path
- `sys.path` = list of directories Python searches during import
- pytest adds test directories automatically; `pythonpath` adds source directories

##### Testing requirements.txt-Based Applications
- In `tox.ini`, add `-rrequirements.txt` to `deps` to install dependencies

---

#### 13. Debugging Test Failures

##### Installing Cards in Editable Mode
```bash
pip install -e "./cards_proj/[test]"   # editable + optional test deps
```

##### Debugging with pytest Flags

**Test selection/ordering:**

- `--lf` / `--last-failed` — rerun only failures
- `--ff` / `--failed-first` — run all, failures first
- `-x` / `--exitfirst` — stop after first failure
- `--maxfail=num` — stop after N failures
- `--sw` / `--stepwise` — stop at first failure; resume from there next time
- `--nf` / `--new-first` — order by file modification time

**Output control:**

- `-v` / `--verbose`
- `--tb=[auto/long/short/line/native/no]`
- `-l` / `--showlocals` — display local variables in tracebacks

**Debugger:**

- `--pdb` — drop into pdb at point of failure
- `--trace` — drop into pdb at start of each test
- `--pdbcls=IPython.terminal.debugger:TerminalPdb` — use IPython debugger

##### Re-Running Failed Tests
```bash
pytest --lf --tb=no          # verify failures reproduce
pytest --lf -x               # stop at first, show traceback
pytest --lf -x -l --tb=short # also show local variables
```

##### Debugging with pdb
- `breakpoint()` in code → pytest stops there
- **pdb commands:**
  - `l(ist)` / `ll` — show source; `w(here)` — stack trace
  - `p expr` / `pp expr` — print/pretty-print
  - `n(ext)` — next line; `s(tep)` — step into; `r(eturn)` — continue to return
  - `c(ontinue)` — run to next breakpoint; `unt(il) lineno` — run to line
  - `q(uit)` — exit

##### Combining pdb and tox
```bash
tox -e py310 -- --pdb --no-cov
```

---

### Part III — Booster Rockets

#### 14. Third-Party Plugins

##### Finding Plugins
- https://docs.pytest.org/en/latest/reference/plugin_list.html
- https://pypi.org — search for `pytest-`
- https://github.com/pytest-dev

##### Installing Plugins
```bash
pip install pytest-cov     # or any plugin
```

##### Exploring the Diversity of pytest Plugins

**Test flow:**

- **pytest-order** — specify run order via marker
- **pytest-randomly** — randomize order (also seeds Faker/Factory Boy)
- **pytest-repeat** — repeat tests N times (`--count=10`)
- **pytest-rerunfailures** — rerun flaky tests
- **pytest-xdist** — parallel execution (`-n=auto`)

**Output:**

- **pytest-instafail** — show failures immediately
- **pytest-sugar** — green checkmarks + progress bar
- **pytest-html** — HTML test reports

**Web:**

- **pytest-selenium**, **pytest-splinter** — browser testing
- **pytest-django**, **pytest-flask** — framework integration

**Fake data:**

- **Faker** — general fake data
- **model-bakery** — Django model objects
- **pytest-factoryboy** — Factory Boy fixtures
- **pytest-mimesis** — faster alternative to Faker

**Misc:**

- **pytest-cov** — coverage
- **pytest-benchmark** — timing benchmarks
- **pytest-timeout** — enforce time limits
- **pytest-asyncio** — async tests
- **pytest-bdd** — BDD-style tests
- **pytest-freezegun** — freeze time
- **pytest-mock** — thin `unittest.mock` wrapper

##### Running Tests in Parallel
```bash
pip install pytest-xdist
pytest -n=auto              # use all CPU cores
pytest --looponfail         # watch mode: rerun failures on file changes
```

##### Randomizing Test Order
```bash
pip install pytest-randomly
pytest -v                   # order is now randomized
pytest -p no:randomly       # disable temporarily
```

---

#### 15. Building Plugins

##### Starting with a Cool Idea
- Example: skip `@pytest.mark.slow` tests by default; include with `--slow` flag
- Default behavior change: no flag = exclude slow; `--slow` = include all

##### Building a Local conftest Plugin
Three **hook functions** used:
```python
# 1. Declare the marker
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

# 2. Add --slow CLI flag
def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="include tests marked slow")

# 3. Skip slow tests unless --slow is passed
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if item.get_closest_marker("slow"):
                item.add_marker(skip_slow)
```

##### Creating an Installable Plugin
- Move conftest code into `pytest_skip_slow.py`
- Use **Flit** (`pip install flit`) to scaffold `pyproject.toml` with `flit init`
- Key `pyproject.toml` additions:
  - `[project.entry-points.pytest11]` with `skip_slow = "pytest_skip_slow"`
  - Classifier: `"Framework :: Pytest"`
- Build: `flit build` → creates `.whl` in `dist/`
- Install: `pip install dist/pytest_skip_slow-0.0.1-py3-none-any.whl`

##### Testing Plugins with pytester
```python
# tests/conftest.py
pytest_plugins = ["pytester"]

# tests/test_plugin.py
@pytest.fixture()
def examples(pytester):
    pytester.copy_example("examples/test_slow.py")

def test_skip_slow(pytester, examples):
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(["*test_slow SKIPPED*"])
    result.assert_outcomes(passed=1, skipped=1)
```
- **pytester** fixture: creates temp dir, provides `runpytest()`, `copy_example()`, `makepyfile()`, etc.
- `fnmatch_lines()` — glob-style matching on stdout lines
- `assert_outcomes()` — check pass/fail/skip counts
- `parseoutcomes()` — returns dict for manual assertions

##### Testing Multiple Python and pytest Versions with tox
```ini
[tox]
envlist = py{37,38,39,310}-pytest{62,70}

[testenv]
deps =
    pytest62: pytest==6.2.5
    pytest70: pytest==7.0.0
commands = pytest {posargs:tests}
```
- Curly braces + dashes create a matrix of environments

##### Publishing Plugins
- Git repository: `pip install git+https://github.com/user/repo`
- Shared directory: `pip install pkg --no-index --find-links=path/`
- PyPI: see Python packaging docs and Flit upload docs

---

#### 16. Advanced Parametrization

##### Using Complex Values
```python
@pytest.mark.parametrize("starting_card", [
    Card("foo", state="todo"),
    Card("foo", state="in prog"),
    Card("foo", state="done"),
])
def test_card(cards_db, starting_card):
    ...
```
- Object values get numbered IDs by default (`starting_card0`, `starting_card1`, ...)

##### Creating Custom Identifiers

**`ids` as a function:**
```python
@pytest.mark.parametrize("starting_card", card_list, ids=lambda c: c.state)
```

**`ids` as a list:**
```python
@pytest.mark.parametrize("starting_card", card_list, ids=["todo", "in prog", "done"])
```

**`pytest.param` with explicit `id`:**
```python
pytest.param(Card("foo", state="in prog"), id="special")
```

**Dictionary technique** (keeps IDs and values together):
```python
text_variants = {"Short": "x", "With Spaces": "x y z", ...}
@pytest.mark.parametrize(
    "variant", text_variants.values(), ids=text_variants.keys()
)
```

##### Parametrizing with Dynamic Values
```python
def text_variants():
    variants = {"Short": "x", "With Spaces": "x y z", ...}
    for key, value in variants.items():
        yield pytest.param(value, id=key)

@pytest.mark.parametrize("variant", text_variants())
def test_summary(cards_db, variant):
    ...
```
- Generator function can read from files, databases, APIs, etc.

##### Using Multiple Parameters
**Explicit tuples:**
```python
@pytest.mark.parametrize("summary, owner, state", [
    ("short", "First", "todo"),
    ("short", "First", "in prog"),
])
```

**Stacking decorators** (creates a matrix):
```python
@pytest.mark.parametrize("state", states)
@pytest.mark.parametrize("owner", owners)
@pytest.mark.parametrize("summary", summaries)
def test_stacking(cards_db, summary, owner, state):
    ...
```
- 2 summaries × 2 owners × 3 states = 12 test cases

##### Using Indirect Parametrization
```python
@pytest.fixture()
def user(request):
    role = request.param
    print(f"\nLog in as {role}")
    yield role
    print(f"\nLog out {role}")

@pytest.mark.parametrize("user", ["admin", "team_member", "visitor"], indirect=["user"])
def test_access_rights(user):
    ...
```
- `indirect=["user"]` routes the param through the `user` fixture instead of directly to the test
- Useful for: setup/teardown per param, selecting a subset of fixture params

**Optional indirect fixture** (works with and without parametrize):
```python
@pytest.fixture()
def user(request):
    role = getattr(request, "param", "visitor")   # default if not parametrized
    ...
```

---

### Appendices

#### A1. Virtual Environments
- `python -m venv venv --prompt .` — creates venv; `--prompt .` uses parent dir name
- Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate.bat` (Windows)
- `deactivate` to exit

#### A2. pip
- `pip install package` — install from PyPI
- `pip install ./local_dir/` — install local package
- `pip install -e ./local_dir/` — install in editable/development mode
- `pip install -r requirements.txt` — install from requirements file
- `pip install git+https://github.com/user/repo` — install from git
- `pip list` — show installed packages
- `pip uninstall package` — remove a package
