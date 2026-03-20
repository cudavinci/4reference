# Publishing Python Packages
*by Dane Hillard (Manning, 2023)*

---

## Part 1: Foundations

### Chapter 1: The What and Why of Python Packages

#### What Is a Package?

- **Import package**: A directory of Python modules that can be imported (contains `__init__.py`). Provides a namespace for organizing related code.
- **Distribution package**: An archive of one or more import packages intended for installation (e.g., a `.whl` or `.tar.gz` file). This is what you upload to PyPI.
- The PyPA (Python Packaging Authority) uses these terms to disambiguate. "Package" in casual use often means either.

#### How Packaging Helps You

- **Package manager**: A tool that automates installing, upgrading, and removing packages (e.g., `pip`).
- **Software repository**: A centralized location for storing and distributing packages (e.g., PyPI — the Python Package Index at https://pypi.org).
- Publishing to PyPI makes code available to the entire Python ecosystem via `pip install <package>`.

#### The Packaging Lifecycle

1. Write code
2. Add packaging metadata and configuration
3. Build distributions (source and/or wheel)
4. Publish to a repository (PyPI)
5. Others install via `pip`

#### Cohesion

- **Cohesion**: The degree to which elements of a module belong together.
- High cohesion = module does one thing well. Functions and classes in a module should be tightly related.
- Low cohesion = module is a grab-bag of unrelated functionality (anti-pattern).

#### Encapsulation

- **Encapsulation**: Hiding internal implementation details and exposing only the intended public interface.
- In Python: use leading underscores (`_private_func`) for private APIs, expose public names via `__init__.py`.
- Encapsulation lets you refactor internals without breaking consumers.

#### Ownership and Maintenance

- Packaging code gives you ownership boundaries — a clear line between your library and its consumers.
- Versioned releases communicate stability and change.

#### Loose Coupling

- **Loose coupling**: Minimizing dependencies between components so changes in one don't cascade to others.
- Tightly coupled code is fragile — a change in one module breaks many others.
- Prefer passing data/interfaces over reaching into another module's internals.

#### Composition

- **Composition**: Building complex behavior by combining simple, focused components rather than deep inheritance hierarchies.
- Favor composition over inheritance — it's more flexible and promotes loose coupling.
- Small, focused packages that compose together are easier to test, maintain, and reuse.

---

### Chapter 2: Preparing for Package Development

#### Managing Python Versions

- Multiple Python versions may coexist on a system. Use tools like `asdf` or `pyenv` to manage them.
- **python-launcher** (`py` command): A cross-platform tool to select Python versions. `py -3.11` runs Python 3.11.
  - Respects `PY_PYTHON` environment variable for default version.
  - See Appendix A for installation.

#### Virtual Environments

- **Virtual environment**: An isolated Python environment with its own `site-packages` directory, preventing dependency conflicts between projects.
- Create with:
  ```bash
  python -m venv venv/
  ```
- Activate:
  ```bash
  # macOS/Linux
  source venv/bin/activate
  # Windows
  venv\Scripts\activate.bat
  ```
- **`site-packages`**: The directory where `pip install` places installed packages. A venv has its own, separate from the system Python.
- Always use virtual environments for project development to isolate dependencies.

#### The `pip` Package Manager

- `pip` is Python's standard package manager.
- `pip install <package>` fetches from PyPI and installs into the active environment's `site-packages`.
- `pip install --upgrade pip` to keep pip current.
- `pip list` shows installed packages; `pip freeze` outputs `requirements.txt` format.

---

### Chapter 3: The Anatomy of a Minimal Package

#### The Package Directory Structure

- Recommended **src layout**:
  ```
  my-project/
  ├── src/
  │   └── my_package/
  │       └── __init__.py
  ├── tests/
  │   └── test_my_package.py
  ├── pyproject.toml
  ├── setup.cfg
  └── README.md
  ```
- The `src/` layout prevents accidentally importing the local source tree during testing (forces installation).
- `__init__.py` marks a directory as a Python import package and can expose the package's public API.

#### The Build System

- **Build frontend**: A tool the user runs to trigger a build (e.g., `build`, `pip`).
- **Build backend**: The tool that does the actual work of building distributions (e.g., `setuptools`, `flit-core`, `hatchling`, `poetry-core`).
- The build frontend reads `pyproject.toml` to discover the build backend.

#### `pyproject.toml`

- **PEP 517/518**: Standardized how to declare build dependencies.
- Minimal `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=67.6.0", "wheel"]
  build-backend = "setuptools.build_meta"
  ```
- `requires`: List of packages needed to build (installed in an isolated environment).
- `build-backend`: Dotted path to the backend's entry point.

#### `setup.cfg`

- Declarative configuration for `setuptools` (preferred over `setup.py` for static metadata).
- Key sections:

##### `[metadata]`

```ini
[metadata]
name = my-package
version = 0.1.0
description = A short summary
long_description = file: README.md
long_description_content_type = text/markdown
license = MIT
url = https://github.com/user/my-package
author = Your Name
author_email = you@example.com
classifiers =
    Development Status :: 3 - Alpha
    License :: OSI Approved :: MIT License
    Programming Language :: Python :: 3
```

- `long_description = file: README.md` reads the README as the PyPI description page.
- **Classifiers**: Standardized tags for categorizing packages on PyPI (must match PyPI's accepted list).

##### `[options]` — Source Code Discovery

```ini
[options]
package_dir =
    = src
packages = find:
python_requires = >=3.9

[options.packages.find]
where = src
```

- `package_dir = = src` tells setuptools the root of packages is `src/`.
- `packages = find:` auto-discovers all packages under `src/`.
- `python_requires` constrains supported Python versions.

#### MANIFEST.in

- Controls which non-Python files are included in source distributions (sdist).
- Directives:
  ```
  include LICENSE
  recursive-include src *.txt *.rst
  global-include *.png
  graft docs
  ```
  - `include`: Add specific files
  - `recursive-include`: Add matching files within a directory tree
  - `global-include`: Add matching files anywhere
  - `graft`: Add an entire directory tree

#### Building Distributions

```bash
python -m build
```

- Produces two artifacts in `dist/`:
  - **Source distribution (sdist)**: `.tar.gz` — contains raw source code. Requires a build step on install.
  - **Wheel (bdist_wheel)**: `.whl` — a pre-built distribution. Faster to install, no build step needed.

#### `setup.py` (Legacy)

- The older imperative approach to configuration. Still needed for:
  - **C extensions** via Cython
  - Dynamic build logic
- Example for Cython:
  ```python
  from setuptools import setup
  from Cython.Build import cythonize

  setup(ext_modules=cythonize("src/my_package/*.pyx"))
  ```

---

## Part 2: Creating a Viable Package

### Chapter 4: Handling Package Dependencies, Entry Points, and Extensions

#### Dependencies

- Declared in `setup.cfg` under `[options]`:
  ```ini
  [options]
  install_requires =
      requests>=2.28.0,<3
      pyyaml>=6.0
  ```
- **Loose version specifiers**: Use lower bounds and (optionally) upper bounds. Avoid pinning to exact versions in libraries — that causes conflicts downstream.
- `>=1.1.0,<2` means "at least 1.1.0, but less than 2.0.0" (compatible with semver major version).

#### Entry Points

- **Entry points** let packages register CLI commands or plugin interfaces.
- Declared in `setup.cfg`:
  ```ini
  [options.entry_points]
  console_scripts =
      my-cli = my_package.cli:main
  ```
- After install, `my-cli` is available as a shell command that calls `my_package.cli.main()`.
- Entry points are also used for plugin systems (e.g., `my_package.plugins` group).

#### C Extensions with Cython

- **Cython**: A superset of Python that compiles to C for performance. Files use `.pyx` extension.
- Requires `setup.py` with `cythonize()` for compilation.
- Produces **binary wheels** — platform-specific.

#### Binary Wheel Filename Anatomy

```
my_package-1.0.0-cp311-cp311-manylinux_2_17_x86_64.whl
```

- `{package}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl`
- **Python tag**: e.g., `cp311` = CPython 3.11
- **ABI tag**: Application Binary Interface compatibility
- **Platform tag**: e.g., `manylinux_2_17_x86_64`, `macosx_11_0_arm64`, `win_amd64`
- Pure-Python wheels use `py3-none-any` (any Python 3, no ABI dependency, any platform).

---

### Chapter 5: Testing Your Package

#### Why Test?

- Tests provide confidence that code works as expected.
- Tests enable refactoring — you can change internals and verify behavior is preserved.
- Tests serve as documentation of intended behavior.

#### pytest Fundamentals

- **pytest**: The de facto standard Python testing framework.
- **Test discovery** conventions:
  - Files named `test_*.py` or `*_test.py`
  - Classes prefixed with `Test`
  - Functions/methods prefixed with `test_`
- Basic test:
  ```python
  def test_addition():
      assert 1 + 1 == 2
  ```
- Run tests:
  ```bash
  python -m pytest
  ```

#### pytest Configuration

- In `setup.cfg`:
  ```ini
  [tool:pytest]
  testpaths = tests
  ```
- Or in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  ```

#### Happy Path and Unhappy Path Testing

- **Happy path**: Testing expected, normal usage — inputs are valid, everything works.
- **Unhappy path**: Testing edge cases, invalid inputs, error conditions — verifying the code fails gracefully.
- Both are essential for robust packages.

#### Parametrized Testing

- **`@pytest.mark.parametrize`**: Run the same test with multiple input/output combinations.
  ```python
  import pytest

  @pytest.mark.parametrize("input_val,expected", [
      (1, 2),
      (2, 4),
      (0, 0),
      (-1, -2),
  ])
  def test_double(input_val, expected):
      assert input_val * 2 == expected
  ```
- Reduces boilerplate when testing many cases with the same logic.

#### Test Coverage

- **`pytest-cov`**: Plugin that measures code coverage during test runs.
  ```bash
  python -m pytest --cov=my_package
  ```
- Configuration in `setup.cfg`:
  ```ini
  [coverage:run]
  branch = True

  [coverage:report]
  show_missing = True
  skip_covered = True

  [coverage:paths]
  source =
      src/my_package
      */site-packages/my_package
  ```
- **Branch coverage** (`branch = True`): Ensures both branches of conditionals are tested, not just line coverage.
- `show_missing = True`: Shows which lines lack coverage.
- `skip_covered = True`: Hides fully-covered files from the report for readability.
- **Coverage thresholds**:
  ```bash
  python -m pytest --cov=my_package --cov-fail-under=80
  ```
  Fails the test run if coverage drops below the threshold.

#### pytest-randomly

- **`pytest-randomly`**: Randomizes the order of test execution.
- Purpose: Exposes **stateful test dependencies** — tests that only pass because of the order they run in.
- Seeds are printed so failures can be reproduced with `--randomly-seed=<seed>`.

#### Strict Markers

- `--strict-markers`: Makes pytest error on unregistered markers (catches typos like `@pytest.mark.skiip`).
- `xfail_strict = True`: Makes `@pytest.mark.xfail` tests fail if they unexpectedly pass (ensures you remove the marker when the bug is fixed).
- Register custom markers in `setup.cfg`:
  ```ini
  [tool:pytest]
  markers =
      slow: marks tests as slow
  ```

---

### Chapter 6: Automating Testing and Quality Assurance

#### tox

- **tox**: A tool for automating testing across multiple Python environments in isolation.
- Configuration in `setup.cfg`:
  ```ini
  [tox:tox]
  isolated_build = True
  envlist = py39,py310,py311

  [testenv]
  deps =
      pytest
      pytest-cov
      pytest-randomly
  commands =
      python -m pytest {posargs}
  ```
- `isolated_build = True`: Required for src layout packages — builds the package in an isolated environment before testing.
- `envlist`: Defines which Python versions/environments to test against.
- `{posargs}`: Passes through any additional command-line arguments.

#### Named Environments

- Custom environments for specific tasks (linting, type checking, etc.):
  ```ini
  [testenv:lint]
  skip_install = True
  deps = flake8
  commands = flake8 src/ tests/

  [testenv:typecheck]
  deps =
      mypy
      {[testenv]deps}
  commands = mypy src/
  ```
- `skip_install = True`: Don't install the package (useful for tools that don't need it).
- `{[testenv]deps}`: Reference dependencies from another section to avoid repetition.

#### Parallel Execution

```bash
tox -p
```

- Runs all environments in parallel for faster feedback.

#### Type Checking with mypy

- **mypy**: Static type checker for Python.
- Configuration in `setup.cfg`:
  ```ini
  [mypy]
  python_version = 3.11
  warn_unused_configs = True
  show_error_context = True
  pretty = True
  namespace_packages = True
  check_untyped_defs = True
  ```
- **`py.typed` marker file**: A zero-byte file placed in your package directory (e.g., `src/my_package/py.typed`) that signals to type checkers that the package includes inline type annotations. Must be declared in `MANIFEST.in`.

#### Code Formatting with black

- **black**: An opinionated, deterministic code formatter ("The Uncompromising Code Formatter").
- Configuration in `pyproject.toml`:
  ```toml
  [tool.black]
  line-length = 79
  target-version = ["py39", "py310", "py311"]
  ```
- Key behaviors:
  - Reformats code to a canonical style — no configuration wars.
  - Uses trailing commas to reduce diff noise.
  - Preserves AST (abstract syntax tree) — formatting never changes code behavior.

#### Linting with flake8

- **flake8**: A wrapper around three tools:
  - **pyflakes**: Detects logical errors (unused imports, undefined names)
  - **pycodestyle**: Checks PEP 8 style compliance
  - **mccabe**: Measures cyclomatic complexity
- **flake8-bugbear**: A popular plugin that catches additional common bugs and design issues.
- Configuration in `setup.cfg`:
  ```ini
  [flake8]
  max-line-length = 79
  extend-ignore = E203
  per-file-ignores =
      __init__.py:F401
  ```
- `E203` is ignored for compatibility with black's formatting of slices.
- `F401` in `__init__.py` suppresses "imported but unused" for public re-exports.

#### Alternative Tools

| Category | Tools |
|---|---|
| Type checkers | `pyright`, `pyre`, `pytype` |
| Formatters | `autopep8`, `yapf` |
| Linters | `pylint`, `prospector`, `bandit` (security), `vulture` (dead code) |

#### pyupgrade

- **pyupgrade**: Automatically modernizes Python syntax for newer versions.
- Example: Converts `dict()` to `{}`, old-style string formatting to f-strings, `typing.List` to `list`, etc.
- AST-safe — only changes syntax, never behavior.
- Typically run as a pre-commit hook.

#### pre-commit Hooks

- **pre-commit**: A framework for managing and running Git pre-commit hooks.
- Configuration in `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.4.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
    - repo: https://github.com/psf/black
      rev: "23.3.0"
      hooks:
        - id: black
    - repo: https://github.com/asottile/pyupgrade
      rev: v3.4.0
      hooks:
        - id: pyupgrade
          args: ["--py39-plus"]
  ```
- Install hooks: `pre-commit install`
- Run on all files: `pre-commit run --all-files`
- Hooks run automatically on `git commit`, catching issues before they enter the repo.

---

## Part 3: Going Public

### Chapter 7: Setting Up a CI Pipeline

#### GitHub Actions

- **GitHub Actions**: CI/CD platform built into GitHub.
- Workflows live in `.github/workflows/*.yml`.
- Key concepts:
  - **Trigger**: Event that starts a workflow (e.g., `push`, `pull_request`)
  - **Job**: A set of steps that run on a single runner
  - **Step**: An individual task (run a command or use an action)
  - **Runner**: The virtual machine that executes a job (e.g., `ubuntu-latest`)

#### Workflow Structure

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install tox
      - run: tox -e py
```

#### Strategy Matrix

- **`strategy.matrix`**: Runs the job multiple times with different configurations.
- Common use: testing across multiple Python versions and operating systems.
- **`${{ matrix.python-version }}`**: Expression syntax for referencing matrix variables.

#### cibuildwheel

- **cibuildwheel**: A tool for building binary wheels across Linux, macOS, and Windows in CI.
- Handles the complexity of cross-platform C extension compilation.
- Typically used as a GitHub Actions step for packages with native extensions.

#### Publishing to PyPI

- **twine**: The standard tool for uploading distributions to PyPI.
  ```bash
  twine upload dist/*
  ```
- Uses **API tokens** for authentication (preferred over username/password).
- Automated publishing via GitHub Actions:
  ```yaml
  - uses: pypa/gh-action-pypi-publish@1.5.0
    with:
      password: ${{ secrets.PYPI_API_TOKEN }}
  ```
- **Tag-based triggers**: Publish only when a version tag is pushed:
  ```yaml
  on:
    push:
      tags:
        - "v*"
  ```

---

### Chapter 8: Documentation

#### Sphinx

- **Sphinx**: The standard documentation generator for Python projects.
- Builds HTML (and other formats) from reStructuredText (`.rst`) source files.
- Run:
  ```bash
  sphinx-build -b html docs/ docs/_build/html
  ```

#### sphinx-apidoc

- **`sphinx-apidoc`**: Auto-generates `.rst` stubs from Python docstrings.
  ```bash
  sphinx-apidoc \
      --force \
      --implicit-namespaces \
      --module-first \
      --separate \
      -o docs/api/ \
      src/my_package/
  ```
  - `--force`: Overwrite existing files
  - `--implicit-namespaces`: Support PEP 420 namespace packages
  - `--module-first`: Place module docstring before submodule listing
  - `--separate`: Create a separate page per module

#### Sphinx Extensions

- **`sphinx.ext.autodoc`**: Pulls docstrings from source code into documentation.
- **`sphinx.ext.autodoc.typehints`**: Renders type annotations in the docs.
- Configured in `docs/conf.py`:
  ```python
  extensions = [
      "sphinx.ext.autodoc",
      "sphinx.ext.autodoc.typehints",
  ]
  ```

#### sphinx-autobuild

- **`sphinx-autobuild`**: Watches for changes and auto-rebuilds docs with live reload.
  ```bash
  sphinx-autobuild docs/ docs/_build/html
  ```

#### reStructuredText Basics

- reST is Sphinx's native markup language.
- **`toctree` directive**: Creates the documentation's table of contents / navigation tree:
  ```rst
  .. toctree::
     :maxdepth: 2

     getting-started
     api/index
     changelog
  ```

#### Read the Docs

- **Read the Docs (RTD)**: Free hosting for open-source documentation, integrated with GitHub.
- Configuration in `.readthedocs.yaml`:
  ```yaml
  version: 2
  build:
    os: ubuntu-22.04
    tools:
      python: "3.11"
  sphinx:
    configuration: docs/conf.py
  python:
    install:
      - method: pip
        path: .
  ```
- **`builder-inited` event hook**: Run `sphinx-apidoc` automatically during RTD builds (since RTD doesn't run it by default):
  ```python
  # docs/conf.py
  import os
  import subprocess

  def run_apidoc(_):
      docs_dir = os.path.dirname(__file__)
      subprocess.check_call([
          "sphinx-apidoc",
          "--force",
          "--implicit-namespaces",
          "--module-first",
          "--separate",
          "-o", os.path.join(docs_dir, "api"),
          os.path.join(docs_dir, "..", "src", "my_package"),
      ])

  def setup(app):
      app.connect("builder-inited", run_apidoc)
  ```
- RTD can build documentation for pull requests for review.

#### The Diátaxis Documentation Framework

- **Diátaxis**: A systematic framework for organizing technical documentation into four quadrants:

| | Studying | Working |
|---|---|---|
| **Practical** | **Tutorials** — Learning-oriented, guided lessons | **How-to Guides** — Task-oriented, step-by-step recipes |
| **Theoretical** | **Discussions/Explanations** — Understanding-oriented, conceptual | **Reference** — Information-oriented, precise technical details |

- Each type serves a different user need. Good documentation includes all four.

#### Documentation Best Practices

- **What to document**: Public API, installation, quickstart, configuration, common patterns, migration guides.
- **Link over repetition**: Use **intersphinx** to link to other projects' docs rather than duplicating content.
- **Consistent language**: Use the same terms throughout. Avoid jargon where possible.
- **Empathetic writing**: Don't assume prior knowledge. Avoid "simply" or "just".
- **Visual structure**: Use headings, code blocks, and admonitions to guide the reader.
- **MyST**: A Markdown-based alternative to reStructuredText for Sphinx — useful if your team prefers Markdown.

---

### Chapter 9: Versioning and Dependency Management

#### Semantic Versioning (SemVer)

- **Semantic versioning**: `MAJOR.MINOR.PATCH`
  - **MAJOR**: Incremented for breaking/incompatible API changes
  - **MINOR**: Incremented for new features that are backward-compatible
  - **PATCH**: Incremented for backward-compatible bug fixes
- Example: `1.4.2` → `2.0.0` (breaking change), `1.4.2` → `1.5.0` (new feature), `1.4.2` → `1.4.3` (bug fix).
- Initial development uses `0.x.y` — the API is not considered stable.

#### Calendar Versioning (CalVer)

- **Calendar versioning**: Uses dates instead of semantic meaning. E.g., `2023.03.15`.
- Useful for projects with time-based releases (e.g., Ubuntu `22.04`).
- Provides a predictable release timeline but doesn't communicate compatibility.

#### Single-Sourcing the Version

- **Problem**: Version string defined in multiple places (setup.cfg, `__init__.py`, docs) leads to drift.
- **Preferred approach** — use `importlib.metadata`:
  ```python
  # src/my_package/__init__.py
  from importlib.metadata import version

  __version__ = version("my-package")
  ```
- Reads the version from the installed package metadata (which comes from `setup.cfg`).
- Avoids the `__version__` attribute anti-pattern where it's manually maintained.

#### Direct vs. Indirect Dependencies

- **Direct dependency**: A package your code imports directly (declared in `install_requires`).
- **Indirect (transitive) dependency**: A package that one of your direct dependencies depends on. You don't declare these — they're resolved automatically.
- **Dependency graph**: The full tree of direct and transitive dependencies.

#### Dependency Hell and Diamond Dependencies

- **Dependency hell**: When conflicting version requirements between packages make resolution impossible.
- **Diamond dependency**: A and B both depend on C, but require incompatible versions:
  ```
       Your Package
        /       \
    A (needs C>=2)   B (needs C<2)
        \       /
          C  ← conflict!
  ```
- Mitigations: Use loose version specifiers in libraries, let the resolver find a compatible set.

#### PEP 440 Version Specifiers

| Specifier | Meaning |
|---|---|
| `==1.2.3` | Exact pin |
| `>=1.2.0` | Lower bound only |
| `>=1.2.0,<2` | Lower and upper bound |
| `~=1.2.0` | Compatible release (>=1.2.0, <1.3.0) |
| `!=1.2.5` | Exclusion |

- **For libraries**: Use loose bounds (`>=1.2.0,<2`) — give consumers flexibility.
- **For applications**: Pinning or tighter constraints may be appropriate (use `pip freeze` + `requirements.txt`).

#### GitHub Dependency Graph and Dependabot

- **GitHub dependency graph**: Visualizes your project's dependencies and flags known vulnerabilities.
- **Dependabot**: Automated bot that:
  - Opens PRs to fix security vulnerabilities in dependencies
  - Opens PRs to keep dependencies updated
- Configuration in `.github/dependabot.yml`:
  ```yaml
  version: 2
  updates:
    - package-ecosystem: pip
      directory: "/"
      schedule:
        interval: weekly
    - package-ecosystem: github-actions
      directory: "/"
      schedule:
        interval: weekly
  ```

---

## Part 4: The Long Haul

### Chapter 10: Scaling and Solidifying Your Project

#### cookiecutter

- **cookiecutter**: A tool for creating projects from templates.
- Templates use **Jinja2 placeholders**: `{{cookiecutter.project_name}}`.
- Configuration in `cookiecutter.json`:
  ```json
  {
      "project_name": "my-project",
      "package_name": "{{ cookiecutter.project_name.replace('-', '_') }}",
      "author": "Your Name",
      "python_version": "3.11"
  }
  ```
- Usage:
  ```bash
  cookiecutter https://github.com/user/my-template
  ```
- Ensures consistency across multiple packages — all start with the same structure, CI config, linting setup, etc.

#### Namespace Packages

- **Namespace package** (PEP 420): A package spread across multiple directories/distributions that share a common top-level namespace.
- **Key rule**: The shared namespace directory must **not** contain an `__init__.py` file. This is what makes it "implicit."
- Example structure (two separate distributions sharing the `company` namespace):
  ```
  # Distribution 1: company-auth
  src/
  └── company/           # NO __init__.py here!
      └── auth/
          └── __init__.py

  # Distribution 2: company-billing
  src/
  └── company/           # NO __init__.py here!
      └── billing/
          └── __init__.py
  ```
- In `setup.cfg`, use `find_namespace:` instead of `find:`:
  ```ini
  [options]
  package_dir =
      = src
  packages = find_namespace:

  [options.packages.find]
  where = src
  ```
- Use cases: Large organizations splitting a monolithic package into independently versioned/deployed sub-packages.

#### Private Package Repositories

- Not all packages should be public. Organizations often need private repositories.
- **pypiserver**: A minimal PyPI-compatible server you can self-host.
  ```bash
  pip install pypiserver
  pypi-server run -p 8080 ~/packages/
  ```
- **Artifactory**: Enterprise-grade artifact repository with PyPI support.
- **Uploading** with twine:
  ```bash
  twine upload --repository-url http://localhost:8080 dist/*
  ```
- **Installing** from a private repo:
  ```bash
  pip install --index-url http://localhost:8080/simple/ my-package
  # Or combine with PyPI:
  pip install --extra-index-url http://localhost:8080/simple/ my-package
  ```
- tox environment for publishing:
  ```ini
  [testenv:publish]
  skip_install = True
  deps = twine
  commands =
      twine upload --repository-url {env:PYPI_URL} dist/*
  ```

---

### Chapter 11: Building a Community

#### The README as Value Proposition

- The README is the first thing potential users see. It should answer:
  - **What** does this package do?
  - **Why** should I use it (over alternatives)?
  - **How** do I get started quickly?
- A great README converts browsers into users.

#### The User Funnel

- Users progress through stages of engagement:
  1. **Potential users** → discover the package (README, search, word-of-mouth)
  2. **Users** → install and use it (quickstart, tutorials)
  3. **Superusers** → deeply invested, pushing boundaries (advanced docs, discussions)
  4. **Contributors** → submit bug reports, PRs, documentation (contributing guide)
  5. **Maintainers** → co-own the project (governance, commit access)
- Good documentation serves each stage differently.

#### Code of Conduct

- **Contributor Covenant**: The most widely adopted open-source code of conduct.
- Sets expectations for respectful behavior in the community.
- Establishes enforcement mechanisms for violations.
- Signal to potential contributors that the project is welcoming and safe.

#### Architectural Decision Records (ADRs)

- **ADR**: A document capturing a significant architectural decision, its context, and consequences.
- Structure:
  - **Title**: Short description
  - **Status**: Proposed, accepted, deprecated, superseded
  - **Context**: What situation prompted this decision?
  - **Decision**: What was decided?
  - **Consequences**: What are the tradeoffs?
- Prevents re-litigating settled decisions and onboards new contributors faster.

#### Project Management with GitHub

##### GitHub Projects

- **GitHub Projects**: Built-in kanban boards for tracking work.
- Columns typically: Backlog → In Progress → Review → Done.

##### Labels

- Use labels to communicate PR/issue status:
  - `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`, `breaking change`, etc.
- Labels help contributors find appropriate tasks.

##### CHANGELOG.md

- **CHANGELOG**: A curated, human-readable file documenting notable changes per release.
- Follow the **Keep a Changelog** format (https://keepachangelog.com):
  ```markdown
  # Changelog

  ## [Unreleased]

  ## [1.1.0] - 2023-06-15
  ### Added
  - New authentication module

  ### Fixed
  - Race condition in connection pooling

  ## [1.0.0] - 2023-05-01
  ### Added
  - Initial release
  ```
- Categories: Added, Changed, Deprecated, Removed, Fixed, Security.
- The `[Unreleased]` section accumulates changes until the next release.

##### Issue and PR Templates

- **Issue templates**: Standardize bug reports and feature requests with required fields.
- **PR template** (`PULL_REQUEST_TEMPLATE.md`): Placed in `.github/` directory. Auto-populates PR descriptions with a checklist:
  ```markdown
  ## Description
  <!-- What does this PR do? -->

  ## Checklist
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] CHANGELOG updated
  ```

---

## Appendices

### Appendix A: Installing asdf and python-launcher

- **asdf**: A version manager that supports multiple languages/tools via plugins.
  ```bash
  git clone https://github.com/asdf-vm/asdf.git ~/.asdf
  asdf plugin add python
  asdf install python 3.11.4
  asdf global python 3.11.4
  ```
- **python-launcher** (`py`): Cross-platform Python version selector.
  ```bash
  # macOS
  brew install python-launcher
  # Usage
  py -3.11 -m pytest
  ```

### Appendix B: Installing pipx and Build Tools

- **pipx**: Installs Python CLI tools in isolated environments (prevents polluting global site-packages).
  ```bash
  pip install pipx
  pipx ensurepath
  ```
- Install tools via pipx:
  ```bash
  pipx install build
  pipx install tox
  pipx install pre-commit
  pipx install cookiecutter
  ```
- Each tool gets its own virtual environment but is available globally on `PATH`.