import RPi.GPIO as GPIO
import time
import rtmidi
import threading

# GPIOピンの設定
LED_PIN = 13

# PWMの初期設定
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
pwm = GPIO.PWM(LED_PIN, 1000)  # 周波数を1000Hzに設定
pwm.start(0)  # 初期Duty比を0に設定

# GPIOが一つだけなので、LED点灯中の入力は無視するためのフラグ
# LED点灯はMIDIコールバックと異なるスレッドで実施してMIDIコールバック自体は呼び出されるようにする
led_active = False
led_lock = threading.Lock()

# ノート番号を音階に変換するための辞書
note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def note_number_to_name(note_number):
    octave = note_number // 12 - 1
    note_name = note_names[note_number % 12]
    return f"{note_name}{octave}"

def midi_callback(message, _):
    message, _ = message
    if message[0] == 144:  # Note Onメッセージ (144はNote Onのステータスバイト)
        note_number = message[1]
        velocity = message[2]
        note_name = note_number_to_name(note_number)
        print(f"Note On: {note_name} (velocity: {velocity})")
        with led_lock:
            if not led_active:
                threading.Thread(target=fade_led, args=(velocity,)).start()

def fade_led(velocity):
    global led_active
    with led_lock:
        if led_active:
            return
        led_active = True

    duty_cycle = velocity / 127 * 100  # ベロシティに基づいてDuty比を計算。最大ベロシティは127
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # 0.5秒間待機してDuty比の切り替わりを待つ
    for i in range(int(duty_cycle), -1, -1):  # Duty比を0まで徐々に減らす
        pwm.ChangeDutyCycle(i)
        time.sleep(0.01)
    with led_lock:
        led_active = False        

def main():
    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()

    if ports:
        midi_in.open_port(1)
        midi_in.set_callback(midi_callback)
        print("Listening for MIDI input... Press Ctrl+C to exit.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            midi_in.close_port()
            pwm.stop()
            GPIO.cleanup()
    else:
        print("No MIDI input ports available.")

if __name__ == "__main__":
    main()