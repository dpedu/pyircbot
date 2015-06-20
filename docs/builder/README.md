Docs Builder
============

A docker image for building pyircbot's docs.

**Usage:**

* Create image: `cd docs/builder ; docker build -t pybdocbuilder .
* Build docs: `docker run --rm -v /local/path/to/doc/output/:/tmp/docs/ pybdocbuilder /start`
