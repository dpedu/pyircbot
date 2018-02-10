#!/bin/sh -ex

docker build -t pybdocbuilder -f docs/builder/Dockerfile .
