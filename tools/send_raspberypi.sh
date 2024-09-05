#!/bin/bash

# デフォルトのホスト名
HOST="chicken-raspberrypi.local"

# オプション処理
while [[ "$1" != "" ]]; do
    case $1 in
        --host2 )         HOST="chicken-raspberrypi2.local"
                          ;;
        * )               echo "Usage: $0 [--host2]"
                          exit 1
    esac
    shift
done

# rsyncコマンド実行
rsync -av --delete --exclude=".git" --exclude=".vscode" --exclude=".gitignore" --exclude="venv" ../chicken-servo-controller raspberrypi@$HOST:~/src
