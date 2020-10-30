import time
import board
from os import listdir

import board
import microcontroller
from digitalio import DigitalInOut, Pull
from adafruit_matrixportal.matrixportal import MatrixPortal

# Timer length
TIMER_MINUTES = 30

# Folder under /bmps to choose character
BMP_CHARACTER = 'mario'

# Allow timer to be reset on device
# If disabled timer will only reset
# when it's a new day
UP_BUTTON_RESETS = False

bmps_path = 'bmps/{}/'.format(BMP_CHARACTER)
all_bmps = listdir(bmps_path)

BMPS = {
    'START': [],
    'GO': [],
    'END': []
}
for bmp in all_bmps:
    if not bmp.endswith('.bmp'):
        continue
    bmp_path = '{}{}'.format(bmps_path, bmp)
    if bmp.startswith('start'):
        BMPS['START'].append(bmp_path)
    elif bmp.startswith('go'):
        BMPS['GO'].append(bmp_path)
    elif bmp.startswith('end'):
        BMPS['END'].append(bmp_path)

timer_status = 'START'

matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)
matrixportal.add_text(
    text_font="fonts/Arial-12.bdf",
    text_position=(4, (matrixportal.graphics.display.height // 2) - 1),
    text_color=0xFFFFFF,
)

# Show character while we connect and get time
matrixportal.set_text('--:--')
matrixportal.set_background(BMPS[timer_status][0], position=(48, 8))
matrixportal.get_local_time()

now = time.time()
day_of_month = time.localtime(now)[2]
if day_of_month == microcontroller.nvm[0]:
    timer_status = 'END'

timer_seconds = TIMER_MINUTES * 60

button_down = DigitalInOut(board.BUTTON_DOWN)
button_up = DigitalInOut(board.BUTTON_UP)

i = 0
while True:
    button_up.switch_to_input(pull=Pull.UP)
    if UP_BUTTON_RESETS and not button_up.value:
        print('Timer reset by button press')
        microcontroller.nvm[0] = 35
        timer_status = 'START'
        continue
    now = time.time()
    if timer_status == 'START':
        remaining = timer_seconds
        button_down.switch_to_input(pull=Pull.UP)
        if not button_down.value:
            print("Timer started by button press")
            day_of_month = time.localtime(now)[2]
            microcontroller.nvm[0] = day_of_month
            timer_status = 'GO'
            i = 0
            now = time.time()
            print('Now: {}'.format(now))
            timer_start = time.time()
            timer_end = timer_start + timer_seconds
    elif timer_status == 'GO':
        remaining = timer_end - now
    elif timer_status == 'END':
        remaining = 0
        day_of_month = time.localtime(now)[2]
        if day_of_month != microcontroller.nvm[0]:
            timer_status = 'START'
            i = 0
            continue
    if remaining <= 0:
        timer_status = 'END'
        i = 0
        remaining_hours = remaining_minutes = remaining_seconds = 0
    else:
        remaining_seconds = remaining % (24 * 3600)
        remaining_hours = remaining_seconds // 3600
        remaining_seconds %= 3600
        remaining_minutes = remaining_seconds // 60
        remaining_seconds %= 60
    if remaining_hours > 0:
        text = '{}:{:02d}'.format(remaining_hours, remaining_minutes)
    else:
        text = '{}:{:02d}'.format(remaining_minutes, remaining_seconds)
    matrixportal.set_background(BMPS[timer_status][i], position=(48, 8))
    matrixportal.set_text(text)
    i += 1
    if i == len(BMPS[timer_status]):
        i = 0
    time.sleep(0.1)