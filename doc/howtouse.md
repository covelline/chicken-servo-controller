# 使い方

基本はすでにセットアップされてるのでパスで平気

[初回セットアップ](./setup.md)

## 起動方法

自動起動するようになっている

### 手動で起動する場合


```bash
# sshの設定方法はREADME参照
ssh raspberrypi@chicken-raspberrypi.local
# ここからラズパイ側
# 自動起動しているプログラムを止める
sudo systemctl stop chicken.service
# 移動
cd src/chicken-servo-controller
./start.sh
# ちなみにデフォルトは同時に鳴らせるのは3音になっているが増やしたい場合は
# ./start.sh --max-tasks 4
# のように起動することもできる(多くしすぎると電力が足らなくなるので注意)
# ctrl + cで終わらせたあと再びプログラムを動かすためにラズパイを再起動する
sudo reboot
```

個人的にはvscodeのリモートエクステンションを使うのがおすすめ<br>
(コードを見ながら起動できるから)

## キャリブレーション

チキンが凹みすぎた時の戻すプログラム。起動中に`c`を押すと全ての音を鳴らしつつ引っ張る動作を行う

## 調整用の説明

コードは全て[main.py](../main.py)に記載している

いじりそうなものだけ説明

```py
# 調整でさわりそうな変数
TARGET_ANGLE = 75  # リセットするために引っ張るための角度
SLEEP_TIME_MS = 200  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)
MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', 3)) #同時に動かせる数、デフォルトは3
```

### TARGET_ANGLE

これはチキンを引っ張る角度になります。主に凹みすぎたチキンを戻す時に使う角度になります。
**もしチキンを戻しが弱ければここを大きくしてください。**

### SLEEP_TIME_MS

サーボモータは0度→45度→0度のように複数の動作に分けて動かしています。
この命令の間に待機時間がないとうまく動かないのでsleep時間を設定しています。
現状の200msはいい感じに動く値ですがもっと早くしたい場合はもう少し小さくできるかも？
(ちなみに0では動かなかった)

### MAX_CONCURRENT_TASKS

同時に動かせるサーボの数。デフォルトでは3になっている。
スクリプト起動時の引数(`./start.sh --max-tasks 4`)のように指定することもできる
多すぎると電力不足で動かないかも？