import time
import threading

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
PERIOD_MS = 1000 / PWM_FREQUENCY  # 周期 (ms)
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲
MAX_ANGLE = 180  # 最大角度
SLEEP_TIME_MS = 500  # サーボモーターが指定角度に到達するまでの待機時間 (ミリ秒)

# デューティ比の計算
MIN_DUTY = (MIN_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最小デューティ比（%）
MAX_DUTY = (MAX_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最大デューティ比（%）
DUTY_RANGE = MAX_DUTY - MIN_DUTY  # デューティ比の範囲

# グローバル変数
moving = False  # サーボモーターが動いているかどうか

def get_duty(degree: int):
    """角度に対応するデューティ比を計算する関数"""
    return (degree * DUTY_RANGE / ANGLE_RANGE) + MIN_DUTY

def move_servo():
    global moving
    if moving:
        return
    moving = True
    print("Moving to MAX angle...")
    duty = get_duty(MAX_ANGLE)
    print(f"Moving to {MAX_ANGLE} degrees with duty cycle: {duty:.2f}%")
    # サーボモーターを制御するコードをここに追加
    # 例: pwm.duty_u16(duty)  # 実際のPWM制御
    time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換

    print("Returning to 0 degrees...")
    duty = get_duty(0)
    print(f"Moving to 0 degrees with duty cycle: {duty:.2f}%")
    # サーボモーターを制御するコードをここに追加
    # 例: pwm.duty_u16(duty)  # 実際のPWM制御
    time.sleep(SLEEP_TIME_MS / 1000)  # ミリ秒を秒に変換
    
    moving = False

def check_key_press():
    while True:
        input("Press Enter to move servo: ")  # キー入力の待機
        move_servo()

def main():
    # PWMの周波数を50Hzに設定
    # pwm = PWM(Pin(0))  # PWMを設定するピン
    # pwm.freq(PWM_FREQUENCY)  # 周波数を50Hzに設定

    key_thread = threading.Thread(target=check_key_press, daemon=True)
    key_thread.start()

    while True:
        # メインスレッドの処理（ここでは特に何もしない）
        time.sleep(1)

if __name__ == "__main__":
    main()
