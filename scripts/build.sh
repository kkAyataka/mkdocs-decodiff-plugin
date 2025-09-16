#!/bin/bash

set -e

cd "$(dirname "$0")/.."

# Activate venv
if [ -z "${VIRTUAL_ENV}" ]; then
    source .venv/bin/activate
fi

# cleanup
rm -rf ./build
rm -rf ./dist
rm -rf ./src/*.egg-info

python3 -m build
