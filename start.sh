#!/bin/bash

# デフォルトの値
MAX_CONCURRENT_TASKS=3
ENABLE_INPUT=true

# オプションの処理
while [[ "$1" != "" ]]; do
    case $1 in
        --max-tasks )     shift
                          MAX_CONCURRENT_TASKS=$1
                          ;;
        --no-input )      ENABLE_INPUT=false
                          ;;
        * )               echo "Usage: $0 [--max-tasks <num>] [--no-input]"
                          exit 1
    esac
    shift
done

# 仮想環境の有効化
source /home/raspberrypi/src/chicken-servo-controller/venv/bin/activate

# 環境変数として渡してPythonスクリプトを実行
MAX_CONCURRENT_TASKS=$MAX_CONCURRENT_TASKS ENABLE_INPUT=$ENABLE_INPUT python /home/raspberrypi/src/chicken-servo-controller/main.py
