import atexit
import datetime
import time
import board
import rtmidi
from adafruit_pca9685 import PCA9685
import threading
import queue

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
# サーボモータの取り付けた方向の関係により0度→180度がチキンを押す方向と逆なので
# スタート位置を45度として0度で鳴るように調整している
START_ANGLE = 45  # スタート位置の角度
ORIGIN_ANGLE = 0  # 原点(チキンが鳴る位置)
TARGET_ANGLE = 75  # リセットするために引っ張るための角度
SLEEP_TIME_MS = 500  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)

# グローバル変数
should_send_signal = True  # 実際にサーボを動かすかどうか
use_target_angle = False  # TARGET_ANGLEを使用するかどうかのフラグ
task_queue = queue.Queue(maxsize=1) # 最大数の制御に利用

def timestamped_print(*args):
    """現在の時刻を含むメッセージを出力する関数"""
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{current_time}]", *args)

# ワーカースレッドを開始
def worker():
    """キューからタスクを取り出して実行するワーカースレッド"""
    while True:
        channel = task_queue.get()
        if channel is None:
            break  # キューに None が入れられたらスレッドを終了
        perform_servo_movement(channel)
        task_queue.task_done()


worker_thread = threading.Thread(target=worker)
worker_thread.daemon = True
worker_thread.start()

# PCA9685の設定
if should_send_signal:
    i2c = board.I2C()  # uses board.SCL and board.SDA
    pca = PCA9685(i2c)
    pca.frequency = PWM_FREQUENCY
    # サーボのチャンネル番号
    servo_channels = [pca.channels[i] for i in range(16)]

def get_pulse_width(degree):
    """角度に対応するパルス幅を計算する関数"""
    pulse_width = MIN_PULSE_WIDTH + (MAX_PULSE_WIDTH - MIN_PULSE_WIDTH) * (degree / ANGLE_RANGE)
    return pulse_width

def get_duty_cycle(degree):
    """角度に対応するデューティサイクルを計算する関数"""
    pulse_width = get_pulse_width(degree)
    duty_cycle = int((pulse_width / 1000000) * PWM_FREQUENCY * 65535)
    return duty_cycle

def move_servo(channel, target_angle):
    """サーボモーターを指定の角度に動かす関数"""
    duty_cycle = get_duty_cycle(target_angle)
    timestamped_print(f"Moving to {target_angle:>3}° on channel {channel} (Duty Cycle: {duty_cycle}, Pulse Width: {get_pulse_width(target_angle)})")
    if should_send_signal:
        servo_channels[channel].duty_cycle = duty_cycle

def perform_servo_movement(channel):
    """サーボモーターを一連の動作に従って動かす関数"""
    try:
        move_servo(channel, ORIGIN_ANGLE)
        time.sleep(SLEEP_TIME_MS / 1000)
        if use_target_angle:
            move_servo(channel, TARGET_ANGLE)
            time.sleep(SLEEP_TIME_MS / 1000)
        move_servo(channel, START_ANGLE)
    except Exception as e:
        timestamped_print(f"An error occurred: {str(e)}")
    finally:
        timestamped_print("End.")

def note_number_to_name(note_number):
    """ノート番号を音名に変換する関数"""
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"

def note_to_channel(note_number):
    """音階をチャンネルに変換する関数。B3からC4を0-9にマッピング"""
    note_to_channel_map = {
        59: 0,  # B3
        60: 1,  # C4
        62: 2,  # D4
        64: 3,  # E4
        65: 4,  # F4
        67: 5,  # G4
        69: 6,  # A4
        71: 7,  # B4
        72: 8,  # C5
    }
    return note_to_channel_map.get(note_number, -1)  # 該当しない場合は-1を返す

def midi_callback(message, _):
    """MIDI入力を処理するコールバック関数"""
    status, note_number, _ = message[0]
    # Note On(144)のみイベントを流す
    if status == 144:
        note_name = note_number_to_name(note_number)
        timestamped_print("---------------------------------------------------")
        timestamped_print(f"MIDI Note On received - Note: {note_name}({note_number})")
        channel = note_to_channel(note_number)
        if channel != -1:
            if task_queue.full():
                timestamped_print("Task queue is full, ignoring this call.")
            else:
                task_queue.put(channel)
        else:
            timestamped_print(f"Note {note_name} is out of the channel mapping range.")

def toggle_movement_mode():
    """TARGET_ANGLEとSTART_ANGLEのどちらを使うかを切り替える関数"""
    global use_target_angle
    use_target_angle = not use_target_angle
    mode = "TARGET_ANGLE" if use_target_angle else "START_ANGLE"
    timestamped_print(f"Movement mode switched to: {mode}")

def check_key_press():
    """キーボード入力を処理する関数"""
    while True:
        try:
            command = input("Enter a channel (0-15) or 't' to toggle mode: ")
            if command.lower() == 't':
                toggle_movement_mode()
            else:
                channel = int(command)
                if 0 <= channel <= 15:
                    if task_queue.full():
                        timestamped_print("Task queue is full, ignoring this call.")
                    else:
                        task_queue.put(channel)
                else:
                    timestamped_print("Please enter a valid channel number between 0 and 15.")
        except ValueError:
            timestamped_print("Please enter a valid channel number between 0 and 15.")

def is_real_midi_device(port_name):
    """実際のMIDIデバイスかどうかを判定する関数"""
    return "Midi Through" not in port_name and "Virtual" not in port_name

def main():
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()

    real_midi_ports = [port for port in ports if is_real_midi_device(port)]

    if real_midi_ports:  # 実際のMIDIデバイスが存在する場合
        try:
            selected_port_index = ports.index(real_midi_ports[0])
            timestamped_print(f"Opening MIDI port: {real_midi_ports[0]}")
            midi_in.open_port(selected_port_index)
            midi_in.set_callback(midi_callback)
            timestamped_print("Listening for MIDI input... Press Ctrl+C to exit.")
            timestamped_print()
            try:
                while True:
                    time.sleep(1)  # MIDI入力待ち
            except KeyboardInterrupt:
                timestamped_print("Exiting...")
            finally:
                midi_in.close_port()
        except (rtmidi.InvalidPortError, IndexError) as e:
            timestamped_print(f"Error opening MIDI port: {e}")
            timestamped_print("No real MIDI input ports available. Switching to keyboard input.")
            check_key_press()  # キーボード入力モード
    else:  # 実際のMIDIデバイスが存在しない場合
        timestamped_print("No real MIDI input ports available. Switching to keyboard input.")
        try:
            check_key_press()  # キーボード入力モード
        except KeyboardInterrupt:
            timestamped_print("Exiting...")

    if should_send_signal:
        pca.deinit()
    timestamped_print("Program exit.")

def shutdown_worker():
    """ワーカースレッドを終了させるための関数"""
    task_queue.put(None)  # ワーカースレッドに終了を伝えるために None を送る
    worker_thread.join()

# プログラム終了時にワーカースレッドを停止
atexit.register(shutdown_worker)

if __name__ == "__main__":
    main()
