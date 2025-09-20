#!/bin/bash

set -e

cd "$(dirname "${0}")"
cd ../

# Activate venv
if [ -z "${VIRTUAL_ENV}" ]; then
    source .venv/bin/activate
fi

# load env file
if [ -e ./scripts/.env ]; then
  source ./scripts/.env
fi

# checks env
if [ -z ${PYPI_USER} -o -z ${PYPI_TOKEN} ]; then
  echo PYPI_USER or PYPI_PASS is not setuped
  exit 1
fi

# build
./scripts/build.sh

# upload
if [ ${PYPI_PRODUCTION} == 1 ]; then
  python3 -m twine upload -u ${PYPI_USER} -p ${PYPI_TOKEN} dist/*
else
  python3 -m twine upload -u ${PYPI_USER} -p ${PYPI_TEST_TOKEN} --repository-url https://test.pypi.org/legacy/ dist/*
fi
