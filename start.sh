#!/bin/bash

# MAX_CONCURRENT_TASKSが指定されている場合、それを使用し、指定されていない場合はデフォルトの3を使用する
MAX_CONCURRENT_TASKS=${1:-3}

# 環境変数として渡してPythonスクリプトを実行
MAX_CONCURRENT_TASKS=$MAX_CONCURRENT_TASKS venv/bin/python main.py
