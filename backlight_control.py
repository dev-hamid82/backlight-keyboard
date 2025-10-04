#!/usr/bin/env python3
from time import sleep
from multiprocessing import Process, Value
from evdev import InputDevice, ecodes
import os


BACKLIGHT_PATH = "/sys/class/leds/dell::kbd_backlight/brightness"


MODES = ['off', 'blink1', 'blink', 'breath', 'keystroke', 'sound']
BLINK_INTERVAL = 0.5
BREATH_CYCLE_DURATION = 10.0


def set_backlight(val):
    os.system(f"echo {val} | sudo tee {BACKLIGHT_PATH} > /dev/null")


def blink_loop1(active):
    while active.value:
        set_backlight(4)
        sleep(BLINK_INTERVAL)
        set_backlight(0)
        sleep(BLINK_INTERVAL)


def blink_loop(active):
    while active.value:
        set_backlight(4)
        sleep(BLINK_INTERVAL)
        set_backlight(3)
        sleep(BLINK_INTERVAL)
        set_backlight(2)
        sleep(BLINK_INTERVAL)
        set_backlight(1)
        sleep(BLINK_INTERVAL)
        set_backlight(0)
        sleep(BLINK_INTERVAL)


def breath_loop(active):
    levels = [0, 1, 2, 3, 4, 3, 2, 1]
    interval = BREATH_CYCLE_DURATION / len(levels)
    while active.value:
        for level in levels:
            if not active.value: return
            set_backlight(level)
            sleep(interval)


def keystroke_loop(active):
    toggle = False
    keyboard = InputDevice('/dev/input/event4')  # ← مسیر کیبورد رو درست بذار
    for event in keyboard.read_loop():
        if not active.value: break
        if event.type == ecodes.EV_KEY and event.value == 1:
            toggle = not toggle
            set_backlight(2 if toggle else 0)


def sound_loop(active):
    while active.value:
        set_backlight(4)
        sleep(0.5)
        set_backlight(2)
        sleep(0.5)


def off_loop(active):
    set_backlight(0)
    while active.value:
        sleep(1)


MODE_FUNCTIONS = {
    'off': off_loop,
    'blink1': blink_loop1,
    'blink': blink_loop,
    'breath': breath_loop,
    'keystroke': keystroke_loop,
    'sound': sound_loop
}


def listen_keys(mode_index, active):
    keyboard = InputDevice('/dev/input/event4')  # ← مسیر دقیق کیبورد رو بذار
    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY and event.code == ecodes.KEY_INSERT and event.value == 1:
            active.value = 0
            sleep(0.1)
            mode_index.value = (mode_index.value + 1) % len(MODES)
            active.value = 1


def mode_manager(mode_index, active):
    last_mode = None
    p = None
    while True:
        mode = MODES[mode_index.value]
        if mode != last_mode:
            if p and p.is_alive():
                active.value = 0
                p.terminate()
                p.join()
            active.value = 1
            p = Process(target=MODE_FUNCTIONS[mode], args=(active,))
            p.start()
            last_mode = mode
        sleep(0.1)


if __name__ == "__main__":
    mode_index = Value('i', 0)
    active = Value('i', 1)

    Process(target=listen_keys, args=(mode_index, active)).start()
    mode_manager(mode_index, active)
