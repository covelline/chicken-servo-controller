import time
import RPi.GPIO as GPIO
import rtmidi

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
PERIOD_MS = 1000 / PWM_FREQUENCY  # 周期 (ms)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
MAX_ANGLE = 180  # 最大角度
SLEEP_TIME_MS = 1000  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)

# デューティ比の計算
MIN_DUTY = (MIN_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最小デューティ比（%）
MAX_DUTY = (MAX_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最大デューティ比（%）
DUTY_RANGE = MAX_DUTY - MIN_DUTY  # デューティ比の範囲

# グローバル変数
moving = False  # サーボモーターが動いているかどうか
should_move = False  # 実際にサーボを動かすかどうか

# GPIOピンの設定
PWM_PIN = 13
if should_move:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PWM_PIN, GPIO.OUT)
    pwm = GPIO.PWM(PWM_PIN, PWM_FREQUENCY)  # 周波数を50Hzに設定
    pwm.start(0)

def get_duty(degree: int):
    """角度に対応するデューティ比を計算する関数"""
    return (degree * DUTY_RANGE / ANGLE_RANGE) + MIN_DUTY

def move_servo():
    global moving
    if moving:
        print("Already moving, ignoring input.")
        return
    moving = True
    try:
        duty = get_duty(MAX_ANGLE)
        print(f"Moving to {MAX_ANGLE} degrees with duty cycle: {duty:.2f}%")
        if should_move:
            pwm.ChangeDutyCycle(duty)
        time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換

        duty = get_duty(0)
        print(f"Moving to 0 degrees with duty cycle: {duty:.2f}%")
        if should_move:
            pwm.ChangeDutyCycle(duty)
        time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換

        if should_move:
            pwm.ChangeDutyCycle(0)  # デューティ比を0にして停止
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
    move_servo()         

def check_key_press():
    while True:
        input("Press Enter to move servo: ")  # キー入力の待機
        if not moving:
            move_servo()
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

    if should_move:
        pwm.stop()
        GPIO.cleanup()
        print("GPIO cleanup and program exit.")

if __name__ == "__main__":
    main()
