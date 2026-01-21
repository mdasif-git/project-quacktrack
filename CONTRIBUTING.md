# Contributing to QuackTrack

Thank you for interest in contributing! Here are guidelines:

## Setup Development Environment

```bash
make install-dev
make pre-commit
```

## Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "Description"`
3. Push to branch: `git push origin feature/your-feature`
4. Open a Pull Request

## Code Standards

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests for new features
- Run `make format` and `make lint` before committing

## Pre-commit Hooks

Hooks run automatically before each commit:
- Code formatting (Black)
- Import sorting (isort)
- Linting (Flake8)
- Security checks

If hooks fail, fix issues and stage changes again.

## Tests

Write tests in `tests/` directory using pytest:

```bash
make test
```

## Questions?

Open an issue or discussion in the repository.
