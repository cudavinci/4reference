# Serious Python — Black-Belt Advice on Deployment, Scalability, Testing, and More
**Author:** Julien Danjou | **Publisher:** No Starch Press, 2019

---

## Chapter 1: Starting Your Project

### Versions of Python
- Python 2 reached EOL in 2020 — **always target Python 3** for new projects
- Each minor version gets **18 months bug-fix** + **5 years security** support
- Target the latest stable release; ensure compat with `N-1` if your OS ships it

### Laying Out Your Project

#### What to Do
- Keep hierarchy **flat but logical** — deep nesting is hard to navigate, flat gets bloated
- Place unit tests **inside** your package as a subpackage (e.g. `mylib/tests/`) so they ship with the module and don't accidentally install as a top-level `tests` module
- Mirror your module hierarchy in your test tree: `mylib/foobar.py` → `mylib/tests/test_foobar.py`

**Standard project layout:**
```
setup.py
setup.cfg
README.rst
docs/
    conf.py
    index.rst
foobar/
    __init__.py
    cli.py
    storage.py
    tests/
        __init__.py
        test_cli.py
        test_storage.py
    data/
        image.png
```

Other common top-level dirs: `etc/` (sample config), `tools/` (shell scripts), `bin/` (binary scripts)

#### What Not to Do
- **Don't organize by code type** (e.g. `functions.py`, `exceptions.py`) — organize by **feature**
- **Don't create a directory with only `__init__.py`** — use a single file instead (e.g. `hooks.py` not `hooks/__init__.py`)
- **Keep `__init__.py` empty** unless you have a specific reason — code there runs on first import of anything in that package
- Don't remove `__init__.py` entirely though — Python requires it to recognize a directory as a package

### Version Numbering
- Follow **PEP 440**: `N[.N]+[{a|b|rc}N][.postN][.devN]`
- `1.2` == `1.2.0`; `1.2a1` = alpha; `1.2b2` = beta; `1.2rc1` = release candidate
- `.postN` = post-release (minor publication errors, **not** bug fixes — bump minor version for those)
- `.devN` = dev/pre-release (discouraged, hard to parse)
- **Semantic Versioning** partially overlaps with PEP 440 but is **not fully compatible** (e.g. `1.0.0-alpha+001` is invalid PEP 440)

### Coding Style and Automated Checks
- **PEP 8** is the canonical style guide: 4-space indents, 79-char lines, `CamelCase` classes, `snake_case` functions, `_private` prefix
- **Always enforce PEP 8 from day one** via CI — easier than retrofitting later

#### Tools to Catch Style Errors
- `pycodestyle` (formerly `pep8`): checks PEP 8 conformance
- `--ignore=E3` to suppress categories incrementally

#### Tools to Catch Coding Errors
- **Pyflakes**: static analysis, extendable via plugins
- **Pylint**: PEP 8 + code error checks, plugin-based
- **flake8** (**recommended**): combines `pyflakes` + `pycodestyle`, supports `# noqa` inline suppression, rich plugin ecosystem
  - `flake8-import-order`: checks alphabetical imports
  - Can write custom AST-based plugins (see Chapter 9)

---

## Chapter 2: Modules, Libraries, and Frameworks

### The Import System
- `import foo` is syntactic sugar for `foo = __import__("foo")`
- `__import__` is useful for **dynamic imports** where the module name isn't known until runtime:
  ```python
  mod = __import__("RANDOM".lower())  # imports 'random'
  ```
- Imported modules are objects — their attributes (classes, functions, variables) are all objects

#### The sys Module
- `sys.modules`: dict of all currently loaded modules (key = name, value = module object)
- `sys.builtin_module_names`: tuple of modules compiled into the interpreter

#### Import Paths
- `sys.path`: ordered list of directories Python searches for modules
- Can modify at runtime: `sys.path.append('/foo/bar')` or via `PYTHONPATH` env var
- **Order matters** — first match wins. Common pitfall: naming your file `random.py` shadows the stdlib module

#### Custom Importers
- **PEP 302** import hooks: extend the import system via `sys.meta_path` (meta path finders) or `sys.path_hooks` (path entry finders)
- A meta path finder exposes `find_module(fullname, path=None)` → returns a loader with `load_module(fullname)`

### Useful Standard Libraries
Key modules to know: `atexit`, `argparse`, `bisect`, `collections`, `concurrent.futures`, `copy`, `csv`, `datetime`, `fnmatch`, `glob`, `io`, `json`, `logging`, `multiprocessing`, `operator`, `os`, `random`, `re`, `sched`, `select`, `shutil`, `signal`, `tempfile`, `threading`, `urllib`, `uuid`

> **Rule of thumb:** Before writing a utility function, check if the stdlib already provides it.

### External Libraries

#### The External Libraries Safety Checklist
Before adopting an external library, evaluate:

1. **Python 3 compatibility**
2. **Active development** (check GitHub activity)
3. **Active maintenance** (bug tracker responsiveness)
4. **Packaged with OS distributions** (indicates broader adoption)
5. **API compatibility commitment** (history of breaking changes?)
6. **License compatibility** with your project

#### Protecting Your Code with an API Wrapper
- **Never let an external library's API leak into your codebase** — write a thin wrapper/adapter layer
- If the library dies or changes its API, you only rewrite the wrapper, not your entire application

### Package Installation: Getting More from pip
- `pip install --user <pkg>`: install to home directory
- `pip freeze`: list installed packages + versions
- `pip install -e .`: **editable install** — egg-link to local source (changes reflect immediately)
- `pip install -e git+https://github.com/user/repo.git#egg=name`: install directly from VCS

### Using and Choosing Frameworks
- Framework = your code extends it (vs. library = you call it)
- **Replacing a framework is orders of magnitude harder** than replacing a library — choose very carefully
- Lighter frameworks (Flask) give more freedom; heavier ones (Django) do more but lock you in

---

## Chapter 3: Documentation and Good API Practice

### Documenting with Sphinx
- **Sphinx** is the de facto standard; uses **reStructuredText (reST)** markup
- Minimum docs: problem statement, license, quick-start example, install instructions, links to community/bugs/source

#### Getting Started with Sphinx and reST
```bash
pip install sphinx
sphinx-quickstart       # creates docs/source/conf.py + index.rst
sphinx-build doc/source doc/build   # build HTML
```

#### Sphinx Modules
- **`sphinx.ext.autodoc`**: extracts docstrings from code into `.rst` files
- **`sphinx.ext.autosummary`**: auto-generates table of contents for module APIs
- **`sphinx.ext.doctest`**: runs code examples in docs as tests — enables **Documentation-Driven Development (DDD)**

#### Writing a Sphinx Extension
- Custom extensions implement `setup(app)` and use Sphinx event/directive APIs
- Rule: **if you can extract documentation from code, automate it**

### Managing Changes to Your APIs
- Convention: `foo` is public, `_bar` is private

#### Documenting Your API Changes
- Always document: new elements, deprecated elements, migration instructions
- **Keep old interfaces available** as long as feasible after deprecation

#### Marking Deprecated Functions with the warnings Module
```python
import warnings

def old_function():
    warnings.warn("old_function is deprecated, use new_function",
                   DeprecationWarning)
    return new_function()
```
- The `debtcollector` library provides decorators to automate deprecation

---

## Chapter 4: Handling Timestamps and Time Zones

### The Problem of Missing Time Zones
- **A timestamp without a timezone is meaningless**
- **Never store timestamps after TZ conversion** — store in original TZ, convert at display time
- `datetime.datetime` objects are **timezone-unaware by default**

### Building Default datetime Objects
```python
import datetime
# WRONG — returns naive (no timezone) datetime:
datetime.datetime.utcnow()          # tzinfo is None!
datetime.datetime.now()              # also tzinfo is None!
```

### Time Zone-Aware Timestamps with dateutil
```python
from dateutil import tz
import datetime

# CORRECT — always attach timezone:
def utcnow():
    return datetime.datetime.now(tz=tz.tzutc())

paris = tz.gettz("Europe/Paris")
local = tz.gettz()  # auto-detect local timezone
```

### Serializing Time Zone-Aware datetime Objects
- **Always use ISO 8601**: `datetime_obj.isoformat()` / `iso8601.parse_date(string)`

### Solving Ambiguous Times
- During DST transitions, same wall-clock time occurs twice
- Python 3.6+ `fold` attribute (PEP 495): `fold=0` = first, `fold=1` = second
- **Best practice: stick to UTC internally**

---

## Chapter 5: Distributing Your Software

### A Bit of setup.py History
- **Use `setuptools`** — it's the current standard

### Packaging with setup.cfg
```python
# setup.py — minimal:
import setuptools
setuptools.setup()
```
```ini
# setup.cfg — metadata:
[metadata]
name = foobar
author = Dave Null
license = MIT
long_description = file: README.rst
requires-python = >=3.6
```
- **pbr**: auto-generates docs, AUTHORS, ChangeLog from git, manages versions via git tags

### The Wheel Format Distribution Standard
- **Wheel** (PEP 427): official `.whl` distribution format
- `python setup.py bdist_wheel` / `--universal` for Py2+3
- Can run directly: `python mypackage.whl/module`

### Sharing Your Work with the World
- `python setup.py sdist` → upload to PyPI
- Use **TestPyPI** for dry runs

### Entry Points
- Metadata declaring discoverable features organized into groups

#### Using Console Scripts
```python
setup(entry_points={"console_scripts": ["mycommand = mypackage.cli:main"]})
```

#### Using Plugins and Drivers
- `pkg_resources.iter_entry_points('group_name')` for runtime discovery
- **stevedore** library: `ExtensionManager` (all plugins), `DriverManager` (single named plugin)

---

## Chapter 6: Unit Testing

### The Basics of Testing

#### Some Simple Tests
```python
def test_addition():
    assert 1 + 1 == 2
```
- Run: `pytest -v`; pytest provides **rich failure diffs** automatically

#### Skipping Tests
```python
@pytest.mark.skip("reason")
@pytest.mark.skipif(condition, reason="...")
pytest.skip("runtime skip")
```

#### Running Particular Tests
- By file/name/marker: `pytest -k name`, `pytest -m marker`

#### Running Tests in Parallel
- `pytest-xdist`: `pytest -n auto`

#### Creating Objects Used in Tests with Fixtures
```python
@pytest.fixture
def database():
    db = create_connection()
    yield db        # teardown after test
    db.close()

@pytest.fixture(scope="module")   # shared across module
@pytest.fixture(autouse=True)     # auto-applied
```
Scopes: `function` (default), `class`, `module`, `session`

#### Running Test Scenarios
```python
@pytest.fixture(params=["mysql", "postgresql"])
def database(request):
    d = connect(request.param)
    yield d
    d.close()
```

#### Controlled Tests Using Mocking
```python
from unittest import mock

m = mock.Mock()
m.method.return_value = 42
m.method.side_effect = some_function

# Patch external dependencies:
with mock.patch('os.unlink', fake_unlink):
    os.unlink('file')

@mock.patch('requests.get', fake_get)
def test_http(): ...

# Verify:
m.method.assert_called_once_with('foo', 'bar')
```

#### Revealing Untested Code with coverage
```bash
pytest --cov=mypackage --cov-report=html tests/
```

### Virtual Environments
- `python3 -m venv myvenv` → `source myvenv/bin/activate` → `deactivate`

#### Using virtualenv with tox
```ini
[tox]
envlist = py39, py310, pep8

[testenv]
deps = pytest
commands = pytest

[testenv:pep8]
deps = flake8
commands = flake8
```
- `tox --recreate`, `tox -e py310`, **detox** for parallel

### Testing Policy
- **Zero tolerance for untested code**; automate via CI

---

## Chapter 7: Methods and Decorators

### Decorators and When to Use Them
```python
import functools

def my_decorator(f):
    @functools.wraps(f)  # ALWAYS use this
    def wrapper(*args, **kwargs):
        # before
        result = f(*args, **kwargs)
        # after
        return result
    return wrapper
```
- Stacking: bottom decorator applied first, executed first (innermost)

### How Methods Work in Python
- Instance access → auto-bound; class access → unbound function

### Static Methods
- `@staticmethod`: no `self`/`cls`; operates only on params; faster, clearer intent

### Class Methods
- `@classmethod`: receives `cls`; primary use = **factory methods**

### Abstract Methods
```python
import abc
class Base(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def method(self): ...
```
- Cannot instantiate class with unimplemented abstract methods (`TypeError`)
- Abstract methods **can have implementations** accessible via `super()`

### The Truth About super
- `super()` delegates via **MRO** (Method Resolution Order)
- Python 3: no-arg `super()` auto-detects context
- **Always use `super()`** for parent calls

---

## Chapter 8: Functional Programming

### Creating Pure Functions
- No side effects; same input → same output; return copies, don't mutate

### Generators
```python
def gen():
    yield 1
    yield 2
```
- Lazy evaluation; memory efficient; `send()` for coroutine pattern
- Generator expressions: `(x for x in items)`

### List Comprehensions
```python
[x**2 for x in range(10) if x % 2 == 0]
{k: v for k, v in items}
{x for x in items}
```

### Functional Functions Functioning
- `map`, `filter`, `enumerate`, `sorted`, `any`/`all`, `zip`
- Prefer `functools.partial` over `lambda`

### Useful itertools Functions
- `chain`, `groupby`, `combinations`, `permutations`, `product`, `accumulate`, `dropwhile`, `takewhile`, `cycle`, `count`, `repeat`, `compress`

---

## Chapter 9: The Abstract Syntax Tree, Hy, and Lisp-like Attributes

### Looking at the AST
```python
import ast
ast.dump(ast.parse("x = 42"))
```
- `ast.walk()`, `ast.NodeTransformer`, `ast.literal_eval()` (safe eval)

### Extending flake8 with AST Checks
- Write plugins that walk AST to detect code patterns (e.g. missing `@staticmethod`)
- Register via entry points

### A Quick Introduction to Hy
- Lisp dialect → Python AST → fully interoperable with Python

---

## Chapter 10: Performances and Optimizations

### Data Structures
- `dict.get()`, set operations, `collections.defaultdict`, `collections.Counter`

### Profiling
- `cProfile`: `python -m cProfile -s time script.py`; visualize with KCacheGrind
- `dis.dis(fn)`: bytecode disassembly

### Defining Functions Efficiently
- Cache attribute lookups as locals in hot loops (`LOAD_FAST` > `LOAD_GLOBAL`)

### Ordered Lists and bisect
- O(log n) binary search; `bisect.insort()` maintains sorted order

### namedtuple and Slots
- `namedtuple`: lightweight immutable; `__slots__`: ~50% memory savings

### Memoization
```python
@functools.lru_cache(maxsize=128)
def expensive(n): ...
```

### Faster Python with PyPy
- JIT compilation; 10-100x faster for CPU-bound pure Python

### Achieving Zero Copy with the Buffer Protocol
```python
view = memoryview(data)
chunk = view[5:10]  # no copy
```

---

## Chapter 11: Scaling and Architecture

### Multithreading in Python and Its Limitations
- **GIL**: one thread executes bytecode at a time; threads useful for I/O only

### Multiprocessing vs. Multithreading
- I/O-bound → threads/async; CPU-bound → `multiprocessing`

### Event-Driven Architecture / asyncio
- `asyncio`: native `async`/`await` for high-concurrency I/O

### Service-Oriented Architecture
- Independent services with well-defined APIs; scale/deploy/fail independently

### Interprocess Communication with ZeroMQ
- Lightweight messaging: req/rep, pub/sub, push/pull

---

## Chapter 12: Managing Relational Databases

### RDBMSs, ORMs, and When to Use Them
- **SQLAlchemy**: gold standard (Core + ORM layers); know when to drop to raw SQL

### Database Backends
- **PostgreSQL** (recommended), SQLite (dev/test), MySQL

### Streaming Data with Flask and PostgreSQL
- `LISTEN/NOTIFY` for real-time event streaming without polling

---

## Chapter 13: Write Less, Code More

### Single Dispatch
```python
@functools.singledispatch
def process(arg): ...

@process.register(int)
def _(arg): ...
```

### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def resource():
    r = acquire()
    try:
        yield r
    finally:
        release(r)
```

### Less Boilerplate with attrs / dataclasses
```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0
```
- **Always prefer `dataclasses` (stdlib, 3.7+) or `attrs` over hand-written boilerplate**