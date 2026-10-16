# CustomLauncher

Simple tray launcher for Windows and Linux.

## Features

- System tray integration
- Recursive menu generation from directory tree
- Configurable file extensions
- Launch external applications with selected files
- Multiple independent instances
- Refresh menu without restart

## Configuration

Example:

{
  "base_dir": "/home/user/workspaces",
  "extensions": [".code-workspace"],
  "program": "code",
  "args_template": "{file}",
  "name": "VSCode"
}

## Requirements

- Python 3.13+
- pystray
- pillow

## Installation

pip install -r requirements.txt

## Run

python launcher.py config.json
