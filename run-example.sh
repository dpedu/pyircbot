#!/bin/bash

CONFPATH=${1:-examples/config.json}

export PYTHONUNBUFFERED=1
export PYTHONPATH=.

./bin/pyircbot -c $CONFPATH --debug
