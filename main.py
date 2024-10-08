import atexit
import datetime
import os
import time
import board
import rtmidi
from adafruit_pca9685 import PCA9685
import threading
from colorama import Fore, init
import subprocess
import logging
import logging.handlers

# coloramaの初期化
init(autoreset=True)

# 調整でさわりそうな変数
TARGET_ANGLE = 75  # リセットするために引っ張るための角度
SLEEP_TIME_MS = 200  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)
MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', 3)) #同時に動かせる数、デフォルトは3

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
START_ANGLE = 45  # スタート位置の角度
ORIGIN_ANGLE = 0  # 原点(チキンが鳴る位置)

should_send_signal = True  # 実際にサーボを動かすかどうか
in_calibration_mode = False  # キャリブレーションモードのフラグ
use_target_angle = False  # TARGET_ANGLEを使用するかどうかのフラグ
semaphore = threading.Semaphore(MAX_CONCURRENT_TASKS)  # セマフォの初期化

# PCA9685の設定
if should_send_signal:
    i2c = board.I2C()  # uses board.SCL and board.SDA
    pca = PCA9685(i2c)
    pca.frequency = PWM_FREQUENCY
    servo_channels = [pca.channels[i] for i in range(16)]

# ロガーの設定
logger = logging.getLogger("ServoControl")
logger.setLevel(logging.INFO)

# Syslogへのハンドラ設定 (address="/dev/log" を指定)
syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
syslog_handler.setLevel(logging.INFO)

# ログフォーマットの設定
logger.addHandler(syslog_handler)

# コンソールにも出力するハンドラ設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

def get_temp():
    """ラズパイのCPU温度を取得する関数"""
    try:
        # vcgencmd measure_temp コマンドの出力を取得
        temp_output = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
        # 正規表現で温度のみを抽出
        temp = temp_output.split('=')[1].split("'")[0]
        return f"{temp}°C"
    except Exception as e:
        return "-"

def timestamped_print(*args, error=False):
    """現在の時刻とラズパイの温度を含むメッセージを出力する関数"""
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    temp = get_temp()  # 温度を取得
    message = f"[{current_time}] [{temp}] {' '.join(map(str, args))}"
    if error:
        logger.error(message)  # エラーメッセージをsyslogに送信
        print(Fore.RED + message, flush=True)
    else:
        logger.info(message)  # 通常メッセージをsyslogに送信
        print(message, flush=True)

def worker(channel):
    """セマフォで制御されたワーカースレッド"""
    if not semaphore.acquire(blocking=False):
        timestamped_print("Max concurrent tasks reached, ignoring this call.", error=True)
        return
    try:
        perform_servo_movement(channel)
    finally:
        semaphore.release()

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
        timestamped_print(f"An error occurred: {str(e)}", error=True)
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
    if in_calibration_mode:
        timestamped_print("MIDI input ignored during calibration mode.", error=True)
        return

    status, note_number, _ = message[0]
    # Note On(144)のみイベントを流す
    if status == 144:
        note_name = note_number_to_name(note_number)
        timestamped_print("---------------------------------------------------")
        timestamped_print(f"MIDI Note On received - Note: {note_name}({note_number})")
        channel = note_to_channel(note_number)
        if channel != -1:
            worker_thread = threading.Thread(target=worker, args=(channel,))
            worker_thread.start()
        else:
            timestamped_print(f"Note {note_name} is out of the channel mapping range.", error=True)

def toggle_movement_mode():
    """TARGET_ANGLEとSTART_ANGLEのどちらを使うかを切り替える関数"""
    global use_target_angle
    use_target_angle = not use_target_angle
    mode = "TARGET_ANGLE" if use_target_angle else "START_ANGLE"
    timestamped_print(f"Movement mode switched to: {mode}")

def calibrate_servos():
    """全チャンネルのサーボをキャリブレーションする関数"""
    global in_calibration_mode
    in_calibration_mode = True
    timestamped_print("Calibration mode activated. MIDI input will be ignored.")

    for channel in range(9):  # 0から8のチャンネルに対して動作
        timestamped_print(f"Calibrating channel {channel}")
        move_servo(channel, ORIGIN_ANGLE)
        time.sleep(SLEEP_TIME_MS / 1000)
        move_servo(channel, TARGET_ANGLE)
        time.sleep(SLEEP_TIME_MS / 1000)
        move_servo(channel, START_ANGLE)

    timestamped_print("Calibration mode deactivated.")
    in_calibration_mode = False

def calibrate_servos_stop():
    """全チャンネルのサーボをキャリブレーションする関数"""
    global in_calibration_mode
    in_calibration_mode = True
    timestamped_print("Calibration mode activated. MIDI input will be ignored.")

    for channel in range(9):  # 0から8のチャンネルに対して動作
        timestamped_print(f"Calibrating channel {channel}")
        move_servo(channel, ORIGIN_ANGLE)
        time.sleep(SLEEP_TIME_MS / 1000)
        move_servo(channel, TARGET_ANGLE)
        time.sleep(SLEEP_TIME_MS / 1000)

    timestamped_print("Calibration mode deactivated.")
    in_calibration_mode = False

def check_key_press():
    """キーボード入力を処理する関数"""
    enable_input = os.getenv('ENABLE_INPUT', 'true') == 'true'
    # キーボード入力のスレッドを起動、inputが無効な場合は何もしない
    if enable_input:
        while True:
            try:
                command = input("Enter a channel (0-15), 't' to toggle mode, or 'c' for calibration or 'm' for pinch chicken: ")
                if command.lower() == 't':
                    toggle_movement_mode()
                elif command.lower() == 'c':
                    calibrate_servos()
                elif command.lower() == 'm':
                    calibrate_servos_stop()
                else:
                    channel = int(command)
                    if 0 <= channel <= 15:
                        worker_thread = threading.Thread(target=worker, args=(channel,))
                        worker_thread.start()
                    else:
                        timestamped_print("Please enter a valid channel number between 0 and 15.", error=True)
            except ValueError:
                timestamped_print("Please enter a valid channel number between 0 and 15.", error=True)
    else:
        timestamped_print("Input is disabled. Running without interactive mode.")

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
        except (rtmidi.InvalidPortError, IndexError) as e:
            timestamped_print(f"Error opening MIDI port: {e}", error=True)
            timestamped_print("No real MIDI input ports available. Switching to keyboard input only.")
    
    keyboard_thread = threading.Thread(target=check_key_press)
    keyboard_thread.daemon = True
    keyboard_thread.start()

    try:
        while True:
            time.sleep(1)  # メインスレッドを生かしておく
    except KeyboardInterrupt:
        timestamped_print("Exiting...")

    if should_send_signal:
        pca.deinit()
    timestamped_print("Program exit.")

def shutdown_worker():
    """ワーカースレッドを終了させるための関数"""
    # セマフォをリリースするために空のタスクを実行させる
    for _ in range(MAX_CONCURRENT_TASKS):
        semaphore.release()

# プログラム終了時にワーカースレッドを停止
atexit.register(shutdown_worker)

if __name__ == "__main__":
    main()
