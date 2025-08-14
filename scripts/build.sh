#!/bin/bash

cd "$(dirname "$0")/.."

# Activate venv
if [ -z "${VIRTUAL_ENV}" ]; then
    source .venv/bin/activate
fi

python3 -m build
