# AGENTS.md - msearch Development Guide

Multi-modal desktop search system (Python 3.8+, PyTorch, LanceDB, FastAPI).

## Build, Lint, and Test Commands

### Environment Setup
```bash
source venv/bin/activate
pip install -r requirements/dev.txt -r requirements/test.txt
```

### Running Tests
```bash
pytest                              # All tests
pytest tests/unit/test_config.py    # Single test file
pytest tests/unit/test_config.py::TestConfigManager    # Single test class
pytest tests/unit/test_config.py::TestConfigManager::test_init  # Single test
pytest -k "test_config"             # Pattern match
pytest tests/unit/                  # Unit tests only
pytest tests/integration/           # Integration tests only
pytest tests/e2e/                   # E2E tests only
pytest --no-cov                     # Without coverage
pytest -v                           # Verbose output
pytest -n auto                      # Parallel (pytest-xdist)
```

### Code Formatting
```bash
black src/ tests/                   # Format code
black --check src/ tests/           # Check formatting
isort src/ tests/                   # Sort imports
isort --check-only src/ tests/      # Check import order
```

### Linting and Type Checking
```bash
flake8 src/ tests/                  # Linting
mypy src/                           # Type checking
flake8 src/ tests/ && mypy src/     # All checks
```

### Coverage and Startup
```bash
pytest --cov=src --cov-report=html  # HTML coverage report
python src/main.py                  # Run full application
python src/api_server.py            # API server only
python src/cli.py search "query"    # CLI search
bash scripts/run_offline.sh         # Offline mode
```

## Code Style Guidelines

### Imports
- Use absolute imports: `from src.core.config import ConfigManager`
- Group: stdlib → third-party → local application
- Use isort to maintain order

```python
import sys
import signal
import logging
from pathlib import Path
from typing import Dict, Any

from src.core.config.config_manager import ConfigManager
from src.services.file.file_monitor import FileMonitor
```

### Formatting
- Follow Black (88-character line limit)
- 4 spaces for indentation
- Add trailing commas in multi-line structures

### Type Hints
- Use type hints for parameters and return values
- Use `Optional[T]` for Python 3.8 compatibility
- Prefer explicit types over `Any`

```python
from typing import Dict, List, Optional, Any

def initialize(self, config_path: str = "config/config.yml") -> bool:
    self.config_manager: Optional[ConfigManager] = None
    config: Dict[str, Any] = {}
    return True
```

### Naming Conventions
- **Classes**: PascalCase (`ConfigManager`, `FileMonitor`)
- **Functions/Variables**: snake_case (`get_config()`, `max_workers`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_WORKERS`, `DEFAULT_PORT`)
- **Private**: underscore prefix (`_signal_handler`, `_config`)
- **Modules**: snake_case (`vector_store`, `file_monitor`)

### Error Handling
- Use `logging.getLogger(__name__)`
- Log errors with `logger.error(message, exc_info=True)`
- Use try/except with specific exception types
- Provide meaningful error messages

```python
try:
    self.config_manager = ConfigManager(self.config_path)
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to initialize: {e}", exc_info=True)
    return False
```

### Documentation
- Use Google-style docstrings for all public classes/functions
- Include Args and Returns sections

```python
def initialize(self, config_path: str = "config/config.yml") -> bool:
    """
    Initialize the application.

    Args:
        config_path: Path to the configuration file.

    Returns:
        bool: True if initialization successful, False otherwise.
    """
```

### Project Structure
```
src/
├── api/              # API handlers
├── core/             # Core components (config, database, embedding, vector)
├── services/         # Business services (file, search, indexing)
├── interfaces/       # Interface definitions
├── ui/               # PySide6 desktop UI
├── webui/            # Web UI
├── utils/            # Utility functions
├── api_server.py     # API server entry point
├── cli.py            # CLI interface
└── main.py           # Main application entry point

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
├── e2e/              # End-to-end tests
├── conftest.py       # Pytest fixtures
└── pytest.ini        # Pytest configuration
```

### Testing Best Practices
- Use pytest fixtures from `conftest.py`
- Name test classes `Test*` and methods `test_*`
- Mock external dependencies in unit tests
- Test edge cases and error conditions
- Keep tests independent and repeatable

### Async/Await Patterns
```python
async def _create_server():
    return await create_api_server("config/config.yml")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
self.api_server = loop.run_until_complete(_create_server())
```

### Performance
- Use thread pools for CPU-bound and I/O-bound tasks
- Configure worker counts based on hardware
- Implement proper resource cleanup in shutdown
