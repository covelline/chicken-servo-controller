import time
import board
import rtmidi
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
MAX_ANGLE = 180  # 最大角度
SLEEP_TIME_MS = 1000  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)

# グローバル変数
moving = False  # サーボモーターが動いているかどうか
should_send_signal = True  # 実際にサーボを動かすかどうか


# PCA9685の設定
i2c = board.I2C()  # uses board.SCL and board.SDA
pca = PCA9685(i2c)
pca.frequency = PWM_FREQUENCY

# サーボのチャンネル番号
SERVO_CHANNEL = 0
servo_motor = servo.Servo(pca.channels[SERVO_CHANNEL], min_pulse=MIN_PULSE_WIDTH, max_pulse=MAX_PULSE_WIDTH)

def move_servo(channel):
    global moving
    if moving:
        print("Already moving, ignoring input.")
        return
    moving = True
    try:
        print(f"Moving to {MAX_ANGLE} degrees on channel {channel}")
        if should_send_signal:
            servo_motor.angle = MAX_ANGLE
        time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換

        print(f"Returning to 0 degrees on channel {channel}")
        if should_send_signal:
            servo_motor.angle = 0
        time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換

    finally:
        moving = False  # 動作終了後にフラグをリセット

def note_number_to_name(note_number):
    """ノート番号を音名に変換する関数"""
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"

def midi_callback(message, _):
    global moving
    if moving:
        print("Ignoring input, servo is already moving.")
        return

    note_number = message[0][1]
    note_name = note_number_to_name(note_number)
    print(f"MIDI Note On received - Note: {note_name}")
    # TODO: 実際の音階に応じたモーター
    move_servo(SERVO_CHANNEL)

def check_key_press():
    while True:
        input("Press Enter to move servo: ")  # キー入力の待機
        if not moving:
            move_servo(SERVO_CHANNEL)
        else:
            print("Ignoring input, servo is already moving.")

def is_real_midi_device(port_name):
    """実際のMIDIデバイスかどうかを判定する関数"""
    # ここでは、仮想デバイスやミディスルーデバイスを除外する
    return "Midi Through" not in port_name and "Virtual" not in port_name

def main():
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()

    # 実際のMIDIデバイスをフィルタリング
    real_midi_ports = [port for port in ports if is_real_midi_device(port)]

    if real_midi_ports:  # 実際のMIDIデバイスが存在する場合
        try:
            # 最初の実際のMIDIデバイスを使用
            selected_port_index = ports.index(real_midi_ports[0])
            print(f"Opening MIDI port: {real_midi_ports[0]}")
            midi_in.open_port(selected_port_index)
            midi_in.set_callback(midi_callback)
            print("Listening for MIDI input... Press Ctrl+C to exit.")
            try:
                while True:
                    time.sleep(1)  # MIDI入力待ち
            except KeyboardInterrupt:
                print("Exiting...")
            finally:
                midi_in.close_port()
        except (rtmidi.InvalidPortError, IndexError) as e:
            print(f"Error opening MIDI port: {e}")
            print("No real MIDI input ports available. Switching to keyboard input.")
            check_key_press()  # キーボード入力モード
    else:  # 実際のMIDIデバイスが存在しない場合
        print("No real MIDI input ports available. Switching to keyboard input.")
        try:
            check_key_press()  # キーボード入力モード
        except KeyboardInterrupt:
            print("Exiting...")

    pca.deinit()
    print("Program exit.")

if __name__ == "__main__":
    main()
