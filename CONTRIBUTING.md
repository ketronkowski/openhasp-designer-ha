# Contributing to openHASP Designer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

See [Development Guide](docs/development_testing_guide.md) for detailed setup instructions.

**Quick start:**
```bash
# Backend
cd backend-python
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run tests
pytest

# Run backend
uvicorn app.main:app --reload
```

## Code Style

**Python:**
- Follow PEP 8
- Use Black for formatting: `black app/ tests/`
- Use type hints
- Maximum line length: 100 characters

**Testing:**
- Write tests for all new features
- Maintain >80% coverage for backend
- Run tests before submitting PR: `pytest`

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write/update tests
5. Run tests and linting
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

## Commit Messages

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example: `feat: add entity browser component`

## Testing

All PRs must include tests:
- Unit tests for services/utilities
- Component tests for UI components
- Integration tests for critical paths

Run tests:
```bash
# Backend
cd backend-python
pytest

# Frontend (when available)
cd frontend
npm run test
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check [FAQ](docs/faq.md) for common questions

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
