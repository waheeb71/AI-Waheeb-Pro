#!/bin/bash

echo "Starting AI Code Editor Pro..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or later"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $python_version is installed, but Python $required_version or later is required"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check for API key
if [ ! -f ".env" ]; then
    echo
    echo "Warning: .env file not found"
    echo "Please create a .env file with your Gemini API key:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo
    echo "You can get an API key from: https://makersuite.google.com/app/apikey"
    echo
    read -p "Press Enter to continue..."
fi

# Start the application
echo "Starting AI Code Editor Pro..."
python enhanced_main.py

if [ $? -ne 0 ]; then
    echo
    echo "Application exited with error"
    read -p "Press Enter to exit..."
fi

