#!/bin/bash

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

py.test --cov=pyircbot --cov-report html -s tests/
