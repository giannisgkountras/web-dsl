#!/bin/bash

set -e # Exit immediately if a command fails

# Install all dependencies
echo "Installing requirements..."
pip install -r requirements.txt

# Install WebDSL package
echo "Installing WebDSL..."
pip install .

echo "✅ Installation complete."
