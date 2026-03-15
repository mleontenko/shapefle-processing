## Running the program

After cloning the repositoy (main branch) run:

```bash
poetry install
poetry run python -m shapefile_processing
```

or

```bash
poetry run python src/shapefile_processing/__main__.py
```

### Unit tests

```bash
poetry run python -m unittest
```

or

```bash
poetry run python -m unittest discover -s tests -p "test_*.py" -v
```

### Running one specific unit test

```bash
poetry run python -m unittest tests.test_shapefile_manager
```

### Running mypy analysis (check type hints)

```bash
poetry run mypy
```

### Running ruff chack (see pyproject.toml for configuration)

- E - pycodestyle errors (style issues)
- F - Pyflakes (logic issues like unused imports, undefined names)
- I - import sorting rules (isort-style checks)
- D - docstring rules (pydocstyle)

```bash
poetry run ruff check src
```

#### Run specific ruff check e.g. missing docstrings (D1xx rules)

```bash
poetry run ruff check --select D1 src
```