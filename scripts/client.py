#!/usr/bin/env python
import time
import evdev
import os
import sys
import socket
import json

INPUT_DIR = "/dev/input"
WIIMOTE_NAME = "Nintendo Wii Remote Accelerometer"
WIIMOTE_MAX = 103
WIIMOTE_MIN = -105

SERVER_IP = "192.168.1.100"  # Replace with the receiver Raspberry Pi's IP
SERVER_PORT = 12345


def get_wiimote_accel():
    for evnode in os.scandir(INPUT_DIR):
        if evnode.is_dir():
            continue

        try:
            device = evdev.InputDevice(os.path.join(INPUT_DIR, evnode.name))
            if device.name == WIIMOTE_NAME:
                return device
        except:
            continue

    return None


def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
    return sock


wiimote = get_wiimote_accel()
sock = create_socket()

if wiimote:
    print("Found Wiimote: {}".format(wiimote))
    x, y, z = 0, 0, 0
    button_states = {}
    for event in wiimote.read_loop():
        if event.type == evdev.ecodes.EV_ABS:
            adj = float(event.value) / (
                WIIMOTE_MAX if event.value >= 0 else WIIMOTE_MIN
            )
            if event.code == evdev.ecodes.ABS_RX:
                x = adj
            elif event.code == evdev.ecodes.ABS_RY:
                y = adj
            elif event.code == evdev.ecodes.ABS_RZ:
                z = adj

        if event.type == evdev.ecodes.EV_KEY:  # Handle button presses
            button_states[event.code] = event.value

        # Prepare data payload
        payload = {"x": x, "y": y, "z": z, "buttons": button_states}
        # Send data as JSON over the network
        sock.sendto(json.dumps(payload).encode("utf-8"), (SERVER_IP, SERVER_PORT))

        sys.stdout.write(
            "X: {:0.3f}, Y: {:0.3f}, Z: {:0.3f}, Buttons: {}   \r".format(
                x, y, z, button_states
            )
        )
