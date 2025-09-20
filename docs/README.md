# mkdocs-decodiff-plugin

## Overview

This program inserts HTML tags into Markdown files to decorate diff lines using `git-diff` diff information.

When combined with a Markdown-to-HTML conversion program, it can automatically change the background color of diff lines to emphasize them.

## How to Use

### Install

```shell
pip install mkdocs-decodiff-plugin
```

### mkdocs.yml

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
    * `<span id="decodiff-hunk-1" class="decodiff">text</span>`
    * Preserve leading markup, such as headings (`#`) and bullet points (`*`)
* Create a diff list file containing a list of links

## LICENSE

[MIT License](../LICENSE)
