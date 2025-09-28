#/bin/bash

cd "$(dirname "${0}")"

# make workspace
rm -rf test-pypi
mkdir test-pypi
cd test-pypi

# initialize Python
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip

# install
pip install mkdocs

if [ ${PYPI_PRODUCTION} == 1 ]; then
  pip install mkdocs-decodiff-plugin
else
  pip install -i https://test.pypi.org/simple/ mkdocs-decodiff-plugin
fi

# make
mkdocs new .
echo "# Changes" > docs/changes.md
echo "
plugins:
  - decodiff:
      base: main
      dir: docs
      change_list_file: docs/changes.md" >> mkdocs.yml

# git commit
git init .
git add .
git commit -m commit

# change
echo "
## new heading
* new list
* new list

new paragraph" >> docs/index.md

# build
mkdocs serve
