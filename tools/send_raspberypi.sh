#!/bin/bash

rsync -av --delete --exclude=".git" --exclude=".vscode" --exclude=".gitignore" --exclude="venv" ../chicken-servo-controller raspberrypi@chicken-raspberrypi.local:~/src
