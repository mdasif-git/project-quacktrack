# QuackTrack 🦆

A Python script to parse bank statements from Gmail emails and store them in DuckDB for analysis.

## Features

- Connect to Gmail using app-specific password
- Parse debit and credit emails from multiple banks
- Store transactions in DuckDB database
- Query and analyze transactions
- Pre-commit hooks for code quality

## Quick Start

### Prerequisites

- Python 3.10+
- Gmail account with app-specific password enabled
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/mdasif-git/project-quacktrack.git
cd project-quacktrack

# Install dependencies
make install-dev

# Setup pre-commit hooks
make pre-commit

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### Usage

```bash
# Run the application
make run

# Run tests
make test

# Format code
make format

# Run linting checks
make lint
```

## Project Structure

```
project-quacktrack/
├── src/quacktrack/           # Source code
│   ├── parsers/              # Email parsers for different banks
│   ├── database/             # DuckDB connection & models
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration
│   └── main.py               # Entry point
├── tests/                    # Unit tests
├── data/                     # Local data storage
├── docs/                     # Documentation
└── README.md
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here
DUCKDB_PATH=./data/bank_statements.duckdb
LOG_LEVEL=INFO
```

## Development

### Code Quality

This project uses:
- **Black** - Code formatting
- **Flake8** - Linting
- **isort** - Import sorting
- **Pre-commit** - Git hooks for automatic checks

### Running Tests

```bash
make test              # Run all tests
make lint              # Check code quality
make format            # Auto-format code
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.