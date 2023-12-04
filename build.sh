#!/bin/bash

# Create a virtual environment
# echo "Creating a virtual environment..."
# python3.9 -m venv venv
# source venv/bin/activate

# Install the latest version of pip
# echo "Installing the latest version of pip..."
# python -m pip install --upgrade pip

# Build the project
echo "Building the project..."
python3 -m pip install -r requirements.txt

echo "Current directory: $(pwd)"

rm /usr/local/lib/python3.9/site-packages/apps.py
mv /home/apps.py /usr/local/lib/python3.9/site-packages/

# Make migrations
echo "Making migrations..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear