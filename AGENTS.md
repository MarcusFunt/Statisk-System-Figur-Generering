## Project Context

A Python project with 29 files across 7 directories.

## Stack

**Languages:**
- Python (89%)
- TOML (11%)

**Frameworks & Tools:**
- pytest (testing)

## Commands

```bash
pytest  # test
```

## Conventions

- **Naming**: snake_case
- **File organization**: flat
- **Config files**: pyproject.toml
- **CI/CD**: .github/workflows/ci.yml

## Architecture

**Key directories:**
- `examples/` - Example code
- `src/` - Source code
- `tasks/`
- `tests/` - Test files

## Boundaries

**Always:**
- Run `pytest` before committing changes
- Follow snake_case naming convention
- Follow flat file organization

**Ask first:**
- Adding new dependencies
- Changing project configuration files
- Modifying CI/CD pipelines

**Never:**
- Commit secrets, API keys, or .env files
- Delete or overwrite test files without understanding them
- Force push to main/master branch

<!-- agentseed:meta {"sha":"c569465b75d0ff0c72f3a757d70d84be44e8189c","timestamp":"2026-09-01T07:30:30.797Z","format":"agentseed-v1"} -->
