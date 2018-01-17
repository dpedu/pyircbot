#!/bin/bash

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

py.test --fulltrace --cov=pyircbot --cov-report html -n 4 tests/
