#!/bin/bash

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

find pyircbot tests -name '*.pyc' -delete
find pyircbot tests -name __pycache__ -exec rm -rf {} \;

py.test --cov=pyircbot --cov-report html -n 4 tests/ $@
