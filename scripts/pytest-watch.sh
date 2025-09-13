#/bin/bash

# cd to repo root
cd "$(dirname "${0}")"
cd ../

# run pytest with watchmedo
# https://pypi.org/project/watchdog/
watchmedo shell-command \
    --patterns="*.py" \
    --recursive \
    --command="pytest '${1}'" \
    .
