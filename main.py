import time
import board
import rtmidi
from adafruit_pca9685 import PCA9685

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
# サーボモータの取り付けた方向の関係により0度→180度がチキンを押す方向と逆なので
# スタート位置を45度として0度でなるように調整している
START_ANGLE = 45  # スタート位置の角度
ORIGIN_ANGLE = 0  # 原点
TARGET_ANGLE = 75  # 目標角度
SLEEP_TIME_MS = 1000  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)

# PCA9685の設定
i2c = board.I2C()  # uses board.SCL and board.SDA
pca = PCA9685(i2c)
pca.frequency = PWM_FREQUENCY

# サーボのチャンネル番号
servo_channels = [pca.channels[i] for i in range(16)]

# グローバル変数
moving = False  # サーボモーターが動いているかどうか
should_send_signal = True  # 実際にサーボを動かすかどうか

def get_pulse_width(degree):
    """角度に対応するパルス幅を計算する関数"""
    pulse_width = MIN_PULSE_WIDTH + (MAX_PULSE_WIDTH - MIN_PULSE_WIDTH) * (degree / ANGLE_RANGE)
    return pulse_width

def get_duty_cycle(degree):
    """角度に対応するデューティサイクルを計算する関数"""
    pulse_width = get_pulse_width(degree)
    duty_cycle = int((pulse_width / 1000000) * pca.frequency * 65535)
    return duty_cycle

def move_servo(channel, target_angle):
    global moving
    if moving:
        print("Already moving, ignoring input.")
        return
    moving = True
    try:
        print(f"Moving to {target_angle} degrees on channel {channel}")
        duty_cycle = get_duty_cycle(target_angle)
        print(f"Duty Cycle: {duty_cycle}, Pulse Width: {get_pulse_width(target_angle)}")
        if should_send_signal:
            servo_channels[channel].duty_cycle = duty_cycle
        time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換
    finally:
        moving = False  # 動作終了後にフラグをリセット

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
    global moving
    if moving:
        print("Ignoring input, servo is already moving.")
        return

    status, note_number, _  = message[0]
    # Note On(144)のみイベントを流す
    if status == 144:
        note_name = note_number_to_name(note_number)
        print(f"MIDI Note On received - Note: {note_name}({note_number})")
        channel = note_to_channel(note_number)
        if channel != -1:
            move_servo(channel, ORIGIN_ANGLE)
            move_servo(channel, TARGET_ANGLE)
            move_servo(channel, START_ANGLE)
        else:
            print(f"Note {note_name} is out of the channel mapping range.")

def check_key_press():
    while True:
        try:
            channel = int(input("Enter a channel (0-15): "))
            if 0 <= channel <= 15:
                if not moving:
                    move_servo(channel, ORIGIN_ANGLE)
                    move_servo(channel, TARGET_ANGLE)
                    move_servo(channel, START_ANGLE)
                else:
                    print("Ignoring input, servo is already moving.")
            else:
                print("Please enter a valid channel number between 0 and 15.")
        except ValueError:
            print("Please enter a valid channel number between 0 and 15.")

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
