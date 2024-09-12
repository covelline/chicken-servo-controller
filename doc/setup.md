# 初回セットアップ

基本はセットアップ終わってるのでここは飛ばして大丈夫です
ラズパイのOS再インストールしたり新規のラズパイにセットアップする際に行います


自分のPCにソースを落としてきて

```bash
# ラズパイ側にコードを送信(~/srcに送信してる)
cd chicken-servo-controller
./tools/send_raspberypi.sh
```

ラズパイにsshでアクセスして

```bash
cd src/chicken-servo-controller
# pythonの環境作成
python -m venv venv
source venv/bin/activate
# 必要なライブラリ導入
pip install -r requirements.txt
```

# 予備のラズパイについて

ホスト名: raspberrypi@chicken-raspberrypi2.local

でセットアップしてある。
(ssh鍵も共通)