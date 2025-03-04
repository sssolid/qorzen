# Contributing to Qorzen

Thank you for considering contributing to Qorzen! This document outlines the process for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `tox`
5. Commit your changes: `git commit -m 'Add my feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Submit a pull request

## Development Environment

We use Pip for dependency management and tox for testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
tox
```

## Code Style

We follow these coding standards:

- PEP 8 for Python code style
- Google style for docstrings
- Type hints for all functions and methods
- Black for code formatting
- isort for import sorting
- Ruff and flake8 for linting
- mypy for static type checking

Our pre-commit hooks will check these automatically when you commit.

## Testing

Please include tests for any new features or bug fixes. We use pytest for testing.

## Documentation

Update documentation for any changes to APIs or features. We use Sphinx for documentation.