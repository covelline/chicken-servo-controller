import time

# 定数の定義
PWM_FREQUENCY = 50  # PWM信号の周波数 (Hz)
PERIOD_MS = 1000 / PWM_FREQUENCY  # 周期 (ms) = 1000ms / 周波数
MIN_PULSE_WIDTH = 500  # 最小パルス幅 (µs)
MAX_PULSE_WIDTH = 2500  # 最大パルス幅 (µs)
ANGLE_RANGE = 180  # サーボモーターの角度範囲

# デューティ比の計算
MIN_DUTY = (MIN_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最小デューティ比（%）
MAX_DUTY = (MAX_PULSE_WIDTH / (PERIOD_MS * 1000)) * 100  # 最大デューティ比（%）
DUTY_RANGE = MAX_DUTY - MIN_DUTY  # デューティ比の範囲

def main():
    test()

def test():
    angles = [0, 90, 180]
    # PWMの周波数を50Hzに設定
    # pwm = PWM(Pin(0))  # PWMを設定するピン
    # pwm.freq(PWM_FREQUENCY)  # 周波数を50Hzに設定
    while True:
        for angle in angles:
            duty = get_duty(angle)  # 角度に対応するデューティ比を取得
            print(f"Moving to {angle} degrees with duty cycle: {duty:.2f}%")
            # サーボモーターを制御するコードをここに追加
            # 例: pwm.duty_u16(duty)  # 実際のPWM制御
            time.sleep(1)

def get_duty(degree: int):
    # デューティ比を計算する関数
    return (degree * DUTY_RANGE / ANGLE_RANGE) + MIN_DUTY

if __name__ == "__main__":
    main()
