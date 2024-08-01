# 概要

# セットアップ

- python3

```sh
# 一応仮想環境作成
python -m venv venv
source venv/bin/activate
# 抜ける時は
deactivate
```

pip

```
pip install -r requirements.txt
```

# ラズパイへの接続

以下の接続情報を使う

- ホスト名(ipアドレス） 192.168.1.107
- 公開鍵: [office raspberry pi](https://start.1password.com/open/i?a=LO3ZLCHHVRHERBRDXROJT67EYY&v=nrsanojccv3mg777l7kxxv2mp4&i=3udwz4yxjiw3v4zkn6o4otjtxu&h=covelline.1password.com)を1Passwordで管理している

1passwordのssh-agentを使っていないなら`~/.ssh/config`に

```
Host *
        IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```
を書く。その上で、`~/.config/1Password/ssh/agent.toml`に以下を追記する。

```
[[ssh-keys]]
account = "covelline"
```

その後、`ssh raspberrypi@192.168.1.107`を実行。


# 開発について

macで開発してラズパイにコードを送っている

```sh
./send_raspberypi.sh
```

