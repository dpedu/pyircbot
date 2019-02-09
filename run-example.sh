#!/bin/bash

CONFPATH=${1:-examples/config.json}
shift || true

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

pyircbot -c $CONFPATH --debug $@
