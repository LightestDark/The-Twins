import board
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners import DiodeOrientation
from kmk.keys import KC
from kmk.modules.split import Split, SplitType, SplitSide
from kmk.extensions.RGB import RGB
from kmk.extensions.oled import OLED
from kmk.extensions.oled.ssd1306 import SSD1306
from analogio import AnalogIn

# ----------------- LED & helper -----------------
class LedManager:
    def __init__(self, keyboard, fade_steps=6):
        self.keyboard = keyboard
        self.fade_steps = fade_steps
        self.active = {}

    def press(self, index, hsv):
        self.active[index] = [self.fade_steps, hsv]
        self.keyboard.rgb.set_hsv(*hsv, index)

    def release(self, index):
        if index in self.active:
            self.active[index][0] = self.fade_steps

    def update(self):
        for idx, data in list(self.active.items()):
            steps, (h, s, v) = data
            if steps <= 0:
                self.keyboard.rgb.set_hsv(h, s, 0, idx)
                del self.active[idx]
            else:
                brightness = int(v * steps / self.fade_steps)
                self.keyboard.rgb.set_hsv(h, s, brightness, idx)
                data[0] -= 1
        self.keyboard.rgb.show()


class LedKey(KC):
    def __init__(self, key, led_index, hue=280, sat=255, val=255):
        self.key = key
        self.led_index = led_index
        self.hsv = (hue, sat, val)

    def on_press(self, keyboard, coord_int=None):
        keyboard.add_key(self.key)
        keyboard.led_manager.press(self.led_index, self.hsv)

    def on_release(self, keyboard, coord_int=None):
        keyboard.remove_key(self.key)
        keyboard.led_manager.release(self.led_index)


# ----------------- Keyboard -----------------
keyboard = KMKKeyboard()

# Matrix pins
keyboard.col_pins = (board.D1, board.D2, board.D3, board.D4, board.D5, board.D6, board.D7, board.D8)
keyboard.row_pins = (board.D9, board.D10, board.D11, board.D12, board.D13)
keyboard.diode_orientation = DiodeOrientation.COL2ROW

# Split BLE
keyboard.modules.append(Split(split_type=SplitType.BLE, split_side=SplitSide.RIGHT))

# RGB
keyboard.extensions.append(
    RGB(pixel_pin=board.NFC1, num_pixels=42, rgb_order=(1,0,2),
        hue_default=0, sat_default=255, val_default=255, val_limit=255)
)

# LED manager
keyboard.led_manager = LedManager(keyboard)
def before_matrix_scan(kbd):
    kbd.led_manager.update()
keyboard.before_matrix_scan = before_matrix_scan

# OLED
oled = OLED(sda=board.SDA, scl=board.SCL, driver=SSD1306, flip=False)
keyboard.extensions.append(oled)

# ----------------- Battery -----------------
battery_adc = AnalogIn(board.A0)
R1 = 806_000
R2 = 2_000_000

def get_batt_voltage():
    raw = battery_adc.value
    v_adc = (raw / 65535) * 3.3
    return v_adc * (R1 + R2) / R2

def battery_percent():
    v = get_batt_voltage()
    return max(0, min(100, int((v - 3.0) / (4.2 - 3.0) * 100)))

# OLED update
def oled_update(kbd):
    oled.fill(0)
    oled.text("Right Half",0,0)
    ble_status = "OK" if getattr(kbd,'is_ble_connected',False) else "OFF"
    oled.text(f"BLE: {ble_status}",0,10)
    oled.text(f"Batt: {battery_percent()}%",0,20)
    oled.show()

keyboard.before_matrix_scan.append(oled_update)

# LED mapping
led_index_map = list(range(42))

# Keymap
keys = [
    KC.N6, KC.N7, KC.N8, KC.N9, KC.N0, KC.MINUS, KC.EQUAL, KC.BSLASH,
    KC.Y, KC.U, KC.I, KC.O, KC.P, KC.LBRC, KC.RBRC, KC.SCLN,
    KC.H, KC.J, KC.K, KC.L, KC.QUOTE, KC.ENTER, KC.UP, KC.DEL,
    KC.N, KC.M, KC.COMMA, KC.DOT, KC.SLASH, KC.LEFT, KC.DOWN, KC.RIGHT,
    KC.NO, KC.NO, KC.RCTRL, KC.RALT, KC.RSHIFT, KC.SPACE, KC.BSPACE, KC.ENTER
]
keyboard.keymap = [[LedKey(k, led_index_map[i]) for i,k in enumerate(keys)]]

if __name__=="__main__":
    keyboard.go()
