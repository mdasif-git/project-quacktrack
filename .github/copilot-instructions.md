# QuackTrack: AI Coding Agent Instructions

## Project Overview
**QuackTrack** is a Python application that parses bank statement emails from Gmail using IMAP, extracts transaction data, and stores it in DuckDB for analysis. The project prioritizes production-ready practices with modern Python packaging, comprehensive CI/CD, and strict code quality standards.

## Architecture

### Core Components
1. **Email Fetcher** (`src/quacktrack/main.py`)
   - Connects to Gmail via IMAP4_SSL
   - Filters emails by sender (bank addresses: `alerts@axis.bank.in`, `credit_cards@icicibank.com`, `alerts@hdfcbank.net`)
   - Extracts RFC822 email data with multipart support
   - Parses HTML and plain text bodies using BeautifulSoup
   - Decodes headers with proper encoding handling (UTF-8 → Latin-1 fallback)

2. **Config Management** (`src/quacktrack/config.py`)
   - Loads environment variables from `.env` file
   - Manages Gmail credentials, DuckDB path, and logging level
   - All credentials sourced from `GMAIL_USER` and `GMAIL_APP_PASSWORD` env vars (never hardcoded)

3. **Data Storage** (`src/quacktrack/database/`)
   - DuckDB integration (currently stubbed, ready for implementation)
   - Planned models for transaction persistence

4. **Parsers** (`src/quacktrack/parsers/`)
   - Bank-specific email parsing logic (HDFC, ICICI, Axis templates)
   - Each parser extracts debit/credit info from email body

### Data Flow
```
Gmail IMAP → Email Extraction → HTML/Text Parsing → DataFrame Creation → CSV Export (→ DuckDB)
```

## Development Workflow

### Essential Commands (via Makefile)
```bash
make install-dev      # Install dev dependencies (includes black, flake8, isort, pytest, pre-commit)
make pre-commit       # Set up git pre-commit hooks (runs linting automatically)
make run              # Execute: python -m quacktrack.main
make format           # Auto-format: black + isort
make lint             # Check: black --check + flake8 + isort --check
make test             # pytest with coverage reports
make clean            # Remove build artifacts and cache
```

### Pre-Commit Hooks
Code is auto-checked before commit using `.pre-commit-config.yaml`:
- **Black** (line-length=120): Code formatting
- **Flake8** (max-line-length=120, extend-ignore=E203): Linting
- **isort** (profile=black): Import sorting
- **Security checks**: Detect private keys

**Never commit without running `make pre-commit` once on setup.**

### CI/CD
- **python-lint.yml**: Runs Black, Flake8, isort checks on push/PR
- **python-tests.yml**: Pytest across Python 3.10, 3.11, 3.12
- **codacy.yml**: Existing quality gate

## Project Conventions

### Code Style
- **Line length**: 120 characters (Black, Flake8, isort configured)
- **Import order**: Standard library → Third-party → Local (isort + Black)
- **Quotes**: Double quotes preferred (enforced by Black)
- **Type hints**: Encouraged but not required in early stages

### Package Structure
```
src/quacktrack/
├── __init__.py        # Package metadata (__version__ = "0.1.0")
├── main.py            # Entry point (cli-like interface)
├── config.py          # Config loader (uses python-dotenv)
├── parsers/           # Bank-specific email parsers (stub)
├── database/          # DuckDB models and connections (stub)
└── utils/             # Shared utilities (logging, validation, etc.)
```

### Logging
- Configured in `config.py` via `LOG_LEVEL` env var
- Use `logger.info()`, `logger.error()` instead of `print()` (except for user-facing output)
- Logger instance: `logger = logging.getLogger(__name__)`

### Dependencies
- **Core**: pandas, duckdb, python-dotenv, google-api (for future OAuth2 migration)
- **Parsing**: beautifulsoup4, email.header (stdlib)
- **Dev**: pytest, black, flake8, isort, pre-commit

### Configuration via Environment
```bash
# .env file (copy from .env.example, never commit actual credentials)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here  # Gmail app-specific password
DUCKDB_PATH=./data/bank_statements.duckdb
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Critical Patterns

### Email Parsing (Current Implementation)
```python
# Pattern: IMAP search, RFC822 fetch, multipart iteration
status, data = mail.search(None, f'FROM "{bank_sender}"')
if status == "OK":
    for uid in mail_ids:
        status, data = mail.fetch(uid, "(RFC822)")
        if status == "OK":
            msg = email.message_from_bytes(data[0][1])
            # Extract headers: From, Subject, Date
            # Iterate msg.walk() for multipart parts
            # Check content_type in ["text/plain", "text/html"]
            # Decode with error='ignore' for robustness
```

### DataFrame Construction
```python
# Pattern: Accumulate email data in dict, concat to DataFrame
df = pd.DataFrame(columns=["From", "Subject", "Date", "email_body_from_html", "email_body_from_plain"])
for uid in mail_ids:
    tmp_dict = {
        "From": header_value,
        "Subject": subject_value,
        # ... other fields
    }
    df = pd.concat([df, pd.DataFrame([tmp_dict])], ignore_index=True)
df.to_csv(f'{bank_name}_bank_emails.csv', index=False)
```

### Error Handling (Encoding Issues)
```python
# Pattern: UTF-8 first, fallback to Latin-1
try:
    body = body.decode("utf-8", errors="ignore")
except:
    body = body.decode("latin-1", errors="ignore")
```

## Security Practices

- ✅ **`.gitignore` configured**: Blocks `*.txt`, `*.csv`, `.env` files
- ✅ **No hardcoded credentials**: All sourced from environment variables
- ✅ **Pre-commit hooks**: Detect private keys before commit
- ✅ **Read-only IMAP**: `mail.select("inbox", readonly=True)`
- ✅ **App-specific passwords**: Never store full Gmail password

## Testing

- **Location**: `tests/` directory
- **Framework**: pytest with coverage (`pytest.ini` configured)
- **Coverage target**: Aim for >80% (view HTML reports in `htmlcov/`)
- **Run**: `make test` or `pytest tests/ -v --cov=src/quacktrack`

**Example test structure**:
```python
# tests/test_email_fetcher.py
import pytest
from unittest.mock import Mock
from src.quacktrack.main import main

def test_email_parsing():
    # Mock IMAP connection
    # Assert DataFrame structure and content
```

## Common Tasks for AI Agents

### Add a New Bank Parser
1. Create `src/quacktrack/parsers/{bank_name}.py`
2. Follow existing RFC822 parsing pattern in `main.py`
3. Bank-specific field extraction (different email templates)
4. Add tests in `tests/test_{bank_name}_parser.py`
5. Run `make format && make lint` before commit

### Migrate to DuckDB
1. Implement `src/quacktrack/database/models.py` (e.g., `BankTransaction` dataclass)
2. Implement `src/quacktrack/database/connection.py` (DuckDB manager with CRUD ops)
3. Replace CSV export with `db.insert_transaction(transaction_obj)`
4. Keep backward compatibility (optional CSV export)

### Fix Linting Errors
- `black --check` → Run `make format` to auto-fix
- `flake8` violations → Manually fix (line length, imports, shadowing)
- `isort` issues → Run `make format` to auto-fix

### Debug Email Parsing
- Set `LOG_LEVEL=DEBUG` in `.env`
- Add print statements in `main.py` loop (temporary debugging only)
- Check `data/` folder for generated CSV files
- Verify email headers are extracted correctly before body parsing

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/quacktrack/main.py` | Email fetching & parsing logic |
| `src/quacktrack/config.py` | Config loader + env var management |
| `pyproject.toml` | Package metadata, dependencies, tool config |
| `Makefile` | Development commands |
| `.pre-commit-config.yaml` | Git hook configuration |
| `.github/workflows/` | CI/CD pipeline definitions |
| `tests/` | Unit & integration tests |
| `.env.example` | Environment variable template |

## Gotchas & Anti-patterns

❌ **DON'T**: Use `print()` instead of `logger.info()` (violates logging standards)  
❌ **DON'T**: Commit actual `.env` file (use `.gitignore` + `.env.example`)  
❌ **DON'T**: Hardcode bank sender emails (use configurable list or enum)  
❌ **DON'T**: Ignore encoding errors without fallback (use `errors='ignore'`)  
❌ **DON'T**: Skip `make pre-commit` setup (hooks prevent bad commits)  

✅ **DO**: Use Black/isort/Flake8 for consistency  
✅ **DO**: Add env var support for all configuration  
✅ **DO**: Write tests before refactoring core logic  
✅ **DO**: Handle multipart emails gracefully  
✅ **DO**: Run `make format && make lint` before every commit  

---

**Last Updated**: 2026-01-21  
**Python Target**: 3.10+  
**Maintained By**: QuackTrack Contributors
