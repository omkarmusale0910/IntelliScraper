#!/bin/bash
set -eu

echo "Cleaning old builds..."
rm -rf dist build *.egg-info

echo "Building package..."
uv build

if [[ "$1" == "--publish" ]]; then
  echo "Publishing to PyPI..."
  uv publish
  echo "Successfully published!"
fi
