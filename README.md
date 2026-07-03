# PyPureLink Matrix

A modern Python library for connecting to and managing PureLink matrix switching devices.

## Features

- 🔐 Secure authentication with base64 encoding
- 🔗 Simple connection management
- ⚙️ Device API client for PureLink matrix devices
- 📝 Full type hints and documentation
- ✅ Input validation following device requirements
- 🎯 Context manager support for automatic resource cleanup

## 🤖 AI Assistance Disclosure

Parts of this project were developed with the assistance of Artificial Intelligence. AI tools were utilized as an accelerator to:
* Co-author and refine segments of the core library code.
* Help parse and structure raw data payloads during the reverse-engineering of the original hardware protocol.
* Transform early functional prototypes into a structured, production-ready package architecture.
* Generate test suites (`pytest`) and draft structural documentation.

While AI assisted in speeding up the development workflow, all architectural decisions, hardware testing, protocol verification, and final code reviews were executed entirely by the author to ensure reliability and accuracy.

---

## Installation

### Using UV (recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Quick Start

```python
from pypurelinkmatrix import PureLinkClient

# Create a client instance
client = PureLinkClient(
    host="192.168.1.100",
    username="admin",
    password="password123"
)

# Authenticate with the device
try:
    if client.login():
        print("Successfully connected!")
        # Device is now authenticated and ready for commands
except Exception as e:
    print(f"Authentication failed: {e}")

# Always cleanup
client.close()
```

### Using Context Manager (recommended)

```python
from pypurelinkmatrix import PureLinkClient

with PureLinkClient(host="192.168.1.100") as client:
    if client.login("admin", "password123"):
        print("Connected to device")
        # Your code here
```

## Credential Requirements

Based on PureLink device specifications:

- **Username**: 1-15 characters (letters, numbers, underscore only)
- **Password**: 1-15 characters (letters, numbers, underscore only)

## Configuration

Create a `.env` file for sensitive credentials:

```env
PURELINK_HOST=192.168.1.100
PURELINK_USERNAME=admin
PURELINK_PASSWORD=secure_password
```

Then use in your code:

```python
import os
from dotenv import load_dotenv
from pypurelinkmatrix import PureLinkClient

load_dotenv()

client = PureLinkClient(
    host=os.getenv("PURELINK_HOST"),
    username=os.getenv("PURELINK_USERNAME"),
    password=os.getenv("PURELINK_PASSWORD")
)
```

## API Reference

### PureLinkClient

#### Constructor

```python
PureLinkClient(
    host: str,
    username: str = "",
    password: str = "",
    timeout: int = 30,
    use_https: bool = False,
    verify_ssl: bool = True
)
```

- **host**: Device IP address or hostname
- **username**: Username for authentication
- **password**: Password for authentication
- **timeout**: Request timeout in seconds (default: 30)
- **use_https**: Use HTTPS for connection (default: False)
- **verify_ssl**: Verify SSL certificates (default: True)

#### Methods

##### `login(username: Optional[str] = None, password: Optional[str] = None) -> bool`

Authenticate with the PureLink device.

Returns `True` if authentication succeeds.

Raises:
- `ValidationError`: Invalid credential format
- `AuthenticationError`: Authentication failed
- `PureLinkConnectionError`: Cannot connect to device

##### `logout() -> bool`

Logout from the device. Returns `True`.

##### `close() -> None`

Close the client session and cleanup resources.

## Error Handling

```python
from pypurelinkmatrix import PureLinkClient
from pypurelinkmatrix.exceptions import (
    ValidationError,
    AuthenticationError,
    PureLinkConnectionError
)

try:
    client = PureLinkClient(host="192.168.1.100")
    client.login("admin", "password")
except ValidationError as e:
    print(f"Invalid credentials: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except PureLinkConnectionError as e:
    print(f"Cannot connect to device: {e}")
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/pypurelinkmatrix

# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src/pypurelinkmatrix
```

### Project Structure

```
pypurelinkmatrix/
├── src/pypurelinkmatrix/
│   ├── __init__.py           # Package initialization
│   ├── client.py             # Main connection client
│   └── exceptions.py         # Custom exceptions
├── tests/                    # Test suite
├── examples/                 # Examples
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Contributing

Contributions are welcome! Please ensure:

1. Code passes `black` formatting
2. Code passes `ruff` linting
3. Code passes `mypy` type checking
4. Tests pass with good coverage

## License

GPL-3.0 License - see LICENSE file for details

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/matteogheza/pypurelinkmatrix).

## Special Thanks
Many thanks to:
- PureLink for hardware (and less for their documentation)
- [HTTP Toolkit](https://httptoolkit.com/) for making reverse engineering so much easier
- [Github Copilot](https://github.com/features/copilot) for helping me writing a prototype (and unit testing) faster
