#!/bin/bash

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

py.test -s tests/
