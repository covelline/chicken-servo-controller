#!/bin/bash

rsync -av --exclude=".git" --exclude=".vscode" --exclude=".gitignore" --exclude="venv" ../chicken-servo-controller raspberrypi@192.168.1.107:~/src
