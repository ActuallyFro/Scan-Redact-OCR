#!/bin/bash

# Define the path to your logo file
logo_path="/home/numbat/My_Programming/OCR-Scanner-Form2s/resources/PRISM-Logo.png"

# Check if feh is installed
if ! command -v feh &> /dev/null; then
  echo "feh is not installed. Please install it using:"
  echo "sudo apt-get update && sudo apt-get install feh"
  echo "Press Enter to continue after installing..."
  read
fi

# Display the logo in fullscreen and hide the pointer
feh --fullscreen --hide-pointer "$logo_path" &
icon_pid=$!

# Wait for 2 seconds
sleep 2

# Check if the process is still running before attempting to kill
if ps -p "$icon_pid" > /dev/null; then
  kill "$icon_pid"
fi

# Activate the virtual environment and run your Python script in a new terminal
gnome-terminal -- bash -c 'source ./scan-env/bin/activate && python3 ./PRISM.py; bash'
