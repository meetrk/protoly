# Protoly

## Project Setup

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Development

- Use Poetry to manage dependencies:
  ```bash
  poetry add package-name  # Add a new package
  poetry add -G dev package-name  # Add a dev dependency
  ```

- Run tests:
  ```bash
  poetry run pytest
  ```

## Code Quality

This project uses:
- Black for code formatting
- Ruff for linting
- MyPy for type checking
- Pre-commit hooks for automated checks

## Project Structure

```
protoly/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── protoly/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── .pre-commit-config.yaml
├── pyproject.toml
└── README.md
```
