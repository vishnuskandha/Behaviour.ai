# Contributing to BehaviourAI

Thank you for your interest in contributing to BehaviourAI! We welcome contributions of all kinds.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vishnuskandha/Behaviour.ai.git
   cd Behaviour.ai
   ```

2. **Start the development server**
   - **Windows**: Run `run.bat`
   - **Unix/Linux/macOS**: Run `scripts/run.sh` (or manually create venv and run `python app.py`)

3. **Run tests**
   ```bash
   python -m pytest tests/ -v --cov
   ```

4. **Run the full quality gate** (same commands run in CI)
   ```bash
   black . && flake8 . && mypy . && bandit -r app.py ml/ data/ -c .bandit && pytest tests/
   ```

## Code Standards

- **Python**: PEP 8 compliant, black-formatted, type hints recommended
- **Logging**: Use the logger module for all output
- **Testing**: Minimum 80% code coverage required
- **Commits**: Use conventional commits format (`feat:`, `fix:`, `docs:`, etc.)

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure the full quality gate passes (see above) and `python test_app.py`
5. Submit a PR with a clear description

## Security Issues

Do **not** report security issues in public issues. See [SECURITY.md](SECURITY.md)
for the private reporting process.

## Reporting Issues

Please report bugs and suggest features via GitHub Issues. Include:
- Clear description of the problem
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the same license as this project (see LICENSE file).
