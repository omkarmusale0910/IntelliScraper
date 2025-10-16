#!/bin/bash
set -e 

echo "Cleaning old builds..."
rm -rf dist build *.egg-info

echo "Building package..."
uv build

echo "Publishing to PyPI..."
uv publish

echo "Successfully published!"