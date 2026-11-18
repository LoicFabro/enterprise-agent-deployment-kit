# Python support

EADK v1.0.1 supports CPython 3.9+ with no third-party runtime dependencies.

- Package metadata: `requires-python = ">=3.9"`.
- Build backend: setuptools with a compatible release resolved by pip.
- GitHub CI matrix: 3.9, 3.10, 3.12, 3.13.
- Python 3.9 has reached end-of-life; prefer Python 3.12+ for production usage and security updates.

## Install from a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
eadk validate --tenant acme --env staging
```

If `python --version` shows an unexpected version, recreate the virtual environment with the explicit Python executable you intend to use. If your virtual environment has a missing pip module, use `python -m ensurepip --upgrade` or recreate the environment.

## Compatibility scope

The project avoids features introduced after 3.9 in its source; source syntax can be parsed using the Python 3.9 grammar. Exact interpreter execution is verified by the GitHub Actions matrix rather than the maintainer's local interpreter alone.
