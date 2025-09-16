# Development

## Build

```
scripts/build.sh
```

## Automatic Test Reruns

```
python3 -m venv .venv
pip install -e ".[dev]"
scripts/pytest-watch.sh tests
```
