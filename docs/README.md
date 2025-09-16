# decodiff

## Overview

This program inserts HTML tags into Markdown files to decorate diff lines using `git-diff` diff information.

When combined with a Markdown-to-HTML conversion program, it can automatically change the background color of diff lines to emphasize them.

## How to use

### Install

```shell
pip install decodiff
```

### CLI

```shell
# hash
python3 -m decodiff --base=8f8bf35

# tag or branch
python3 -m decodiff --base=v1.0.0 --dir=docs --change-list-file=docs/diff.md
```

### MkDocs

```yml
plugins:
  - decodiff:
      base: 8f8bf35
      dir: docs
```

## Structure

* Python 3 script
* PyPI package
* It works as a plugin for MkDocs and runs in the background during builds.
* It can be run as a CLI and processes Markdown.

## Behavior

* Retrieve diff data using `git diff`
* Add an HTML tag to each diff line. For example:
    * `<span id="decodiff-hunk-1" class="decodiff-diff">text</span>`
    * Preserve leading markup, such as headings (`#`) and bullet points (`*`)
* Create a diff list file containing a list of links

## LICENSE

[MIT License](../LICENSE)
