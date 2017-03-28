Docs Builder
============

A docker image for building pyircbot's docs.

**Usage:**

* Create image: `cd docs/builder ; docker build -t pybdocbuilder .`
* Build docs: `docker run --rm -v /local/path/to/doc/output/:/tmp/docs/ pybdocbuilder /start`

Or, use a local directory instead of git master and build docs into `docs/_build/html`:

* `mkdir docs/_build`
* `docker run -it --rm -v /localpath/to/pyircbot/repo/:/tmp/pyircbot/ pybdocbuilder`
