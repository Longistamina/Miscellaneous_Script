# Building and Publishing a Python Library with `uv`

This is a reusable workflow for creating, developing, documenting, testing,
building, and publishing a Python library. `tidypyrs` is only a representative
name. Replace it, `YOUR_USERNAME`, author details, and URLs for each project.

Commands target Linux/macOS. Secret-token commands use Fish shell.


# 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or, when Rust and Cargo are already installed:

```bash
cargo install --locked uv
```

Verify it and optionally install Python:

```bash
uv --version
uv python install 3.11
```


# 2. Create a library project

```bash
uv init --lib --python 3.11 tidypyrs
cd tidypyrs
uv sync
```

Use `--lib`, not the default application template. The `--python` value becomes
the minimum supported Python version, so choose the oldest version the library
will actually support and test. The initial structure is approximately:

```text
tidypyrs/
├── .git/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
├── src/
│   └── tidypyrs/
│       ├── __init__.py
│       └── py.typed
└── uv.lock
```

`uv sync` creates `.venv/` and `uv.lock`. Never edit `uv.lock` manually.


# 3. Start the Git workflow

`uv init` normally initializes Git. If it did not:

```bash
git init -b main
```

Record the skeleton and create a development branch:

```bash
git add .
git commit -m "Initialize Python library with uv"
git switch -c feature/initial-api
```

After creating an empty remote repository:

```bash
git remote add origin https://github.com/YOUR_USERNAME/tidypyrs.git
git push -u origin main
git push -u origin feature/initial-api
```


# 4. Add dependencies

Runtime dependencies are installed for every library user:

```bash
uv add polars numpy
uv add "polars>=1.30,<2"
```

Useful dependency operations:

```bash
uv add dependency1 dependency2
uv remove dependency1
uv lock --upgrade-package polars
```

Only packages required by the installed library belong in
`[project.dependencies]`.

Development-only tools do not belong in users' installations:

```bash
uv add --dev pytest pytest-cov ruff pyright
```

Keep documentation tools in a separate group:

```bash
uv add --group docs \
    mkdocs \
    mkdocs-material \
    mkdocstrings-python \
    mkdocs-jupyter \
    jupyterlab \
    nbconvert \
    ipykernel
```

Synchronize everything needed for development:

```bash
uv sync --all-groups
```

Development and documentation tools are recorded under `[dependency-groups]`,
not `[project.dependencies]`.


# 5. Write the library code

Keep importable code under `src/tidypyrs/`:

```text
src/tidypyrs/
├── __init__.py
├── core.py
└── py.typed
```

Example `src/tidypyrs/core.py`:

```python
def greet(name: str) -> str:
    """Return a greeting for *name*."""
    if not name:
        raise ValueError("name must not be empty")

    return f"Hello, {name}!"
```

Use package-relative imports between internal modules:

```python
from .core import greet
```

Keep `py.typed` when the package provides inline type information.


# 6. Define the public API in `__init__.py`

Example `src/tidypyrs/__init__.py`:

```python
from importlib.metadata import PackageNotFoundError, version

from .core import greet

try:
    __version__ = version("tidypyrs")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "greet",
]
```

Verify the package import:

```bash
uv run python -c "import tidypyrs; print(tidypyrs); print(tidypyrs.__version__)"
```


# 7. Write tests

```bash
mkdir -p tests
```

Example `tests/test_core.py`:

```python
import pytest

from tidypyrs import greet


def test_greet() -> None:
    assert greet("Ada") == "Hello, Ada!"


def test_greet_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        greet("")
```

Organize larger suites by module or feature:

```text
tests/
├── test_core.py
├── test_io.py
└── test_types.py
```


# 8. Configure development tools

Add these sections to `pyproject.toml`, adjusting supported Python versions:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.coverage.run]
source = ["tidypyrs"]
branch = true

[tool.coverage.report]
show_missing = true
skip_covered = true

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.11"
typeCheckingMode = "standard"
```

Run individual checks:

```bash
uv run pytest
uv run pytest --cov=tidypyrs --cov-report=term-missing
uv run ruff check .
uv run ruff check . --fix
uv run ruff format .
uv run ruff format . --check
uv run pyright
```

Complete local check:

```bash
uv lock --check
uv run ruff format . --check
uv run ruff check .
uv run pyright
uv run pytest --cov=tidypyrs --cov-report=term-missing
```


# 9. Write `README.md`

`README.md` becomes the project description rendered on PyPI. Include at least:

```markdown
# tidypyrs

One-sentence description of the library.

## Installation

```bash
pip install tidypyrs
```

Or with uv:

```bash
uv add tidypyrs
```

## Quick start

```python
from tidypyrs import greet

print(greet("Ada"))
```

## Documentation

Link to the complete documentation site.

## Development

Brief contributor setup instructions.

## License

State the project license.
```

Use relative links for repository files. Avoid website-specific Markdown that
PyPI cannot render. Distribution checks later verify that the README is embedded.


# 10. Create documentation and notebooks

Place documentation beside `pyproject.toml`:

```bash
mkdir -p docs/tutorials
```

Recommended structure:

```text
tidypyrs/
├── docs/
│   ├── index.md
│   ├── getting-started.md
│   ├── api.md
│   └── tutorials/
│       └── getting_started.ipynb
├── mkdocs.yml
├── pyproject.toml
├── README.md
├── src/
└── tests/
```

Example `docs/index.md`:

```markdown
# tidypyrs

Welcome to the project documentation.

## Installation

```bash
pip install tidypyrs
```
```

Example `docs/getting-started.md`:

```markdown
# Getting started

```python
from tidypyrs import greet

greet("Ada")
```
```

Example `docs/api.md`:

```markdown
# API reference

::: tidypyrs
    options:
      show_root_heading: true
      members_order: source
```

Create or edit notebooks in the documentation directory:

```bash
uv run --group docs jupyter lab
```

In JupyterLab:

1. Open `docs/tutorials/`.
2. Create `getting_started.ipynb`.
3. Select the project Python kernel.
4. Write Markdown explanations and executable examples.
5. Run every cell from top to bottom.
6. Save the notebook.

Execute and save a notebook non-interactively:

```bash
uv run --group docs jupyter nbconvert \
    --to notebook \
    --execute \
    --inplace \
    docs/tutorials/getting_started.ipynb
```

Or clear all saved output:

```bash
uv run --group docs jupyter nbconvert \
    --clear-output \
    --inplace \
    docs/tutorials/getting_started.ipynb
```

Choose one notebook-output policy and use it consistently. Saved outputs make
documentation builds deterministic without executing arbitrary notebooks.


# 11. Configure and build MkDocs

Create `mkdocs.yml` at the project root:

```yaml
site_name: tidypyrs
site_description: Documentation for tidypyrs
site_url: https://YOUR_USERNAME.github.io/tidypyrs/
repo_url: https://github.com/YOUR_USERNAME/tidypyrs
repo_name: YOUR_USERNAME/tidypyrs

theme:
  name: material
  features:
    - navigation.sections
    - navigation.top
    - content.code.copy

nav:
  - Home: index.md
  - Getting started: getting-started.md
  - Tutorials:
      - First tutorial: tutorials/getting_started.ipynb
  - API reference: api.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: false
  - mkdocs-jupyter:
      include_source: true
      execute: false

markdown_extensions:
  - admonition
  - attr_list
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - toc:
      permalink: true
```

`mkdocs-jupyter` renders `.ipynb` files as documentation pages. With
`execute: false`, it renders the output already stored in each notebook.

Preview with live reload:

```bash
uv run --group docs mkdocs serve
```

Open the printed URL, normally `http://127.0.0.1:8000/`.

Build strictly:

```bash
uv run --group docs mkdocs build --strict
```

The generated site is written to `site/`. Do not commit it.


# 12. Publish documentation to GitHub Pages

Verify and commit the documentation source first:

```bash
uv run --group docs mkdocs build --strict
git add docs mkdocs.yml pyproject.toml uv.lock README.md
git commit -m "Add project documentation"
git push
```

Deploy the generated site to `gh-pages`:

```bash
uv run --group docs mkdocs gh-deploy
```

If necessary, configure GitHub **Settings → Pages** to deploy from the
`gh-pages` branch. The usual URL is:

```text
https://YOUR_USERNAME.github.io/tidypyrs/
```

Always review a strict local build first. Never manually edit `gh-pages`.


# 13. Finalize `pyproject.toml`

Dependency commands update the dependency lists automatically. Complete the
remaining metadata manually. Representative sections:

```toml
[project]
name = "tidypyrs"
version = "0.1.0"
description = "A concise description of the library"
readme = { file = "README.md", content-type = "text/markdown" }
requires-python = ">=3.11"
license = "MIT"
license-files = ["LICENSE"]
authors = [
    { name = "Your Name", email = "you@example.com" },
]
keywords = ["python", "library"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "numpy>=2",
    "polars>=1.30,<2",
]

[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/tidypyrs"
Documentation = "https://YOUR_USERNAME.github.io/tidypyrs/"
Repository = "https://github.com/YOUR_USERNAME/tidypyrs"
Issues = "https://github.com/YOUR_USERNAME/tidypyrs/issues"
```

`uv add --dev ...` and `uv add --group docs ...` create the corresponding
`[dependency-groups]` entries. Keep the valid `[build-system]` generated by
`uv init`; do not invent or pin an obsolete `uv_build` version.

Only advertise Python versions actually supported and tested. Create the
referenced `LICENSE` file before building.


# 14. Finalize supporting files

Recommended repository contents:

```text
tidypyrs/
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── docs/
├── mkdocs.yml
├── pyproject.toml
├── src/tidypyrs/
├── tests/
└── uv.lock
```

Useful `.gitignore` additions:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
build/
dist/
release/
site/
*.egg-info/
.ipynb_checkpoints/
.env
.env.*
```

Commit `pyproject.toml`, `uv.lock`, `.python-version`, README, license, docs,
MkDocs configuration, source, and tests. Never commit secrets or `.venv/`.

Final development validation:

```bash
uv sync --all-groups
uv lock --check
uv run ruff format . --check
uv run ruff check .
uv run pyright
uv run pytest --cov=tidypyrs --cov-report=term-missing
uv run --group docs mkdocs build --strict
git status
```


# 15. Finish the feature branch and prepare the release

```bash
git add .
git commit -m "Implement initial library release"
git push
git switch main
git merge --no-ff feature/initial-api
```

Set the exact first release version:

```bash
uv version 0.1.0
uv version
```

Run all final checks again. If `uv version` changed `pyproject.toml` or
`uv.lock`, commit those changes:

```bash
git status
# Run the next two commands only when the version/metadata files changed:
git add pyproject.toml uv.lock
git commit -m "Prepare tidypyrs 0.1.0 release"
git status --short
```

When the project was already at `0.1.0`, the merge commit can be the release
commit. Build only from a clean committed state.


# 16. Create TestPyPI and PyPI accounts and tokens

They are separate services with separate accounts and tokens:

```text
TestPyPI: https://test.pypi.org/account/register/
PyPI:     https://pypi.org/account/register/
```

For each service:

1. Register and verify the email address.
2. Enable two-factor authentication.
3. Generate an API token in account settings.
4. Save it in a password manager when displayed.

The first upload may require an account-scoped token because the project does
not exist yet. After the first real release, replace it with a project-scoped
token or configure Trusted Publishing. Never save tokens in project files.


# 17. Build and inspect the release artifacts

Use a version-specific output directory:

```bash
uv build --no-sources --out-dir release/0.1.0
```

Expected artifacts:

```text
release/0.1.0/
├── tidypyrs-0.1.0-py3-none-any.whl
└── tidypyrs-0.1.0.tar.gz
```

Check metadata and README rendering:

```bash
uvx twine check release/0.1.0/*
```

Both files should report `PASSED` without a missing `long_description` warning.

Inspect archive contents:

```bash
unzip -l release/0.1.0/tidypyrs-0.1.0-py3-none-any.whl
tar -tf release/0.1.0/tidypyrs-0.1.0.tar.gz
```

Confirm required modules and metadata are present, and secrets, caches, data,
and unrelated files are absent.


# 18. Test the wheel in isolation

Fish shell:

```fish
set wheel_test_dir (mktemp -d)
uv venv $wheel_test_dir/.venv

uv pip install \
    --python $wheel_test_dir/.venv/bin/python \
    release/0.1.0/tidypyrs-0.1.0-py3-none-any.whl

$wheel_test_dir/.venv/bin/python -c \
    "import tidypyrs; print(tidypyrs.__version__); print(tidypyrs.__file__)"

$wheel_test_dir/.venv/bin/python - <<'PY'
from tidypyrs import greet

assert greet("Ada") == "Hello, Ada!"
print("Isolated wheel test passed")
PY
```

The version must be `0.1.0`; the path must be inside the temporary environment.


# 19. Upload the exact artifacts to TestPyPI

Fish shell:

```fish
read --silent --prompt-str "TestPyPI token: " testpypi_token
echo

env UV_PUBLISH_TOKEN="$testpypi_token" \
    uv publish \
    --publish-url https://test.pypi.org/legacy/ \
    release/0.1.0/*

set -e testpypi_token
```

Inspect:

```text
https://test.pypi.org/project/tidypyrs/0.1.0/
```

Verify the README, metadata, links, Python requirement, dependencies, wheel,
and source distribution.


# 20. Install and test the TestPyPI release

TestPyPI may not contain third-party dependencies. Install dependencies from
real PyPI, then install only this package from TestPyPI:

```fish
set testpypi_dir (mktemp -d)
uv venv $testpypi_dir/.venv

uv pip install \
    --python $testpypi_dir/.venv/bin/python \
    polars numpy

uv pip install \
    --python $testpypi_dir/.venv/bin/python \
    --no-deps \
    --index-url https://test.pypi.org/simple/ \
    tidypyrs==0.1.0

$testpypi_dir/.venv/bin/python -c \
    "import tidypyrs; print(tidypyrs.__version__); print(tidypyrs.__file__)"
```

Run the public-API smoke test again. Uploaded files are immutable: if anything
is wrong, fix it and publish a new version rather than rebuilding `0.1.0`.


# 21. Tag the verified release

After TestPyPI passes, tag the exact release commit:

```bash
git status --short
git tag -a v0.1.0 -m "tidypyrs 0.1.0"
git show --stat v0.1.0
```

Never move or reuse a tag for published source code.


# 22. Upload the same artifacts to real PyPI

Do not rebuild between TestPyPI and PyPI. Publish the exact tested files.

Fish shell:

```fish
read --silent --prompt-str "Real PyPI token: " pypi_token
echo

env UV_PUBLISH_TOKEN="$pypi_token" \
    uv publish \
    --publish-url https://upload.pypi.org/legacy/ \
    release/0.1.0/*

set -e pypi_token
```

Inspect:

```text
https://pypi.org/project/tidypyrs/0.1.0/
```


# 23. Verify the public installation

Move outside the repository so Python cannot import local source:

```fish
cd /tmp
set public_test_dir (mktemp -d)
uv venv $public_test_dir/.venv

uv pip install \
    --refresh \
    --python $public_test_dir/.venv/bin/python \
    tidypyrs==0.1.0

$public_test_dir/.venv/bin/python -c \
    "import tidypyrs; print(tidypyrs.__version__); print(tidypyrs.__file__)"
```

Users can now install it with:

```bash
pip install tidypyrs
```

or add it to a uv project:

```bash
uv add tidypyrs
```


# 24. Push the release commit and tag

Return to the repository, then:

```bash
git push origin main
git push origin v0.1.0
```

Optionally create a GitHub/GitLab release from `v0.1.0`. The source commit, Git
tag, TestPyPI artifacts, and PyPI artifacts should describe the same release.


# 25. Develop future changes

```bash
git switch main
git pull --ff-only
git switch -c feature/new-capability
```

Update source, tests, README, API documentation, and notebooks together. Run:

```bash
uv sync --all-groups
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest --cov=tidypyrs --cov-report=term-missing
uv run --group docs mkdocs build --strict
```

Commit and push the feature:

```bash
git add .
git commit -m "Add new capability"
git push -u origin feature/new-capability
```

Review and merge it before preparing another release.


# 26. Bump or set the next version

Typical semantic version changes:

- patch: compatible bug fix, `0.1.0` → `0.1.1`;
- minor: compatible functionality, `0.1.1` → `0.2.0`;
- major: incompatible API change, `0.2.0` → `1.0.0`.

Commands:

```bash
uv version --bump patch
uv version --bump minor
uv version --bump major
uv version 0.2.0
```

Use only the one command appropriate for the release. Inspect and commit it:

```bash
uv version
git diff -- pyproject.toml uv.lock
git add pyproject.toml uv.lock README.md docs
git commit -m "Release tidypyrs 0.1.1"
```


# 27. Build and publish a future patch

For `0.1.1`:

```bash
uv sync --all-groups
uv lock --check
uv run ruff format . --check
uv run ruff check .
uv run pyright
uv run pytest --cov=tidypyrs --cov-report=term-missing
uv run --group docs mkdocs build --strict

uv build --no-sources --out-dir release/0.1.1
uvx twine check release/0.1.1/*
```

Then repeat the full release path:

1. Test the `0.1.1` wheel in a clean environment.
2. Upload `release/0.1.1/*` to TestPyPI.
3. Install `tidypyrs==0.1.1` from TestPyPI and smoke-test it.
4. Create and inspect tag `v0.1.1`.
5. Upload the exact same files to real PyPI.
6. Install `tidypyrs==0.1.1` from real PyPI and smoke-test it.
7. Push `main` and `v0.1.1`.
8. Redeploy documentation if it changed.

Never overwrite a published version. Every changed release needs a new version.


# 28. Compact release checklist

```text
[ ] Feature branch reviewed and merged
[ ] Version updated with uv version
[ ] Runtime dependencies are correct
[ ] Dev/docs tools are not runtime dependencies
[ ] README, license, metadata, URLs, docs, and notebooks are current
[ ] uv.lock is current and committed
[ ] Formatting, linting, typing, tests, and coverage pass
[ ] mkdocs build --strict passes
[ ] Release commit exists and worktree is clean
[ ] Wheel and sdist built with uv build --no-sources
[ ] twine check passes without README warnings
[ ] Wheel works in an isolated environment
[ ] Exact artifacts uploaded to TestPyPI
[ ] TestPyPI installation and page verified
[ ] Annotated Git tag created from the release commit
[ ] Same artifacts uploaded to real PyPI
[ ] Public installation verified outside the repository
[ ] Release commit and tag pushed
[ ] Documentation deployed
```


# 29. Official references

```text
uv projects:
https://docs.astral.sh/uv/guides/projects/

uv build and publishing:
https://docs.astral.sh/uv/guides/package/

Python Packaging User Guide:
https://packaging.python.org/

TestPyPI:
https://packaging.python.org/en/latest/guides/using-testpypi/

MkDocs:
https://www.mkdocs.org/

MkDocs deployment:
https://www.mkdocs.org/user-guide/deploying-your-docs/

mkdocs-jupyter:
https://mkdocs-jupyter.danielfrg.com/
```
