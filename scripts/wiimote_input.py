#!/usr/bin/env python3
import os
import evdev
import socket
import struct
import sys

# --- Configuration ---
# Change these to match your network settings
EMULATOR_IP = "192.168.20.10"  # IP address where the emulator is running
EMULATOR_PORT = 5000  # Port number for socket input mode

# Define the event type for pointer update.
# (You can define other event types for button presses, hotplug events, etc.)
EVENT_TYPE_POINTER = 0x01

# --- Input device parameters ---
INPUT_DIR = "/dev/input"
WIIMOTE_NAME = "Nintendo Wii Remote Accelerometer"
# Adjust these values based on your device’s min/max ranges
WIIMOTE_MAX = 103
WIIMOTE_MIN = -105


def get_wiimote_device():
    """Find and return an evdev InputDevice that matches the Wii Remote accelerometer."""
    for entry in os.scandir(INPUT_DIR):
        if not entry.is_file():
            continue
        try:
            device = evdev.InputDevice(entry.path)
            if WIIMOTE_NAME in device.name:
                return device
        except Exception:
            continue
    return None


def normalize_value(raw_val):
    """
    Normalize the raw value to a 0.0 - 1.0 range.
    Assumes positive values scale from 0 to WIIMOTE_MAX and
    negative from 0 to WIIMOTE_MIN (a negative number).
    """
    if raw_val >= 0:
        return float(raw_val) / float(WIIMOTE_MAX)
    else:
        return float(raw_val) / float(WIIMOTE_MIN)


def main():
    device = get_wiimote_device()
    if not device:
        sys.exit("Wii Remote device not found!")

    # Create a UDP socket to send binary packets.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Initialize pointer coordinates.
    x, y = 0.5, 0.5  # default to center (you can adjust as needed)

    print(f"Streaming pointer data to {EMULATOR_IP}:{EMULATOR_PORT}")

    # Read events in an infinite loop.
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_ABS:
            # Check for events that we will use to update pointer state.
            if event.code == evdev.ecodes.ABS_RX:
                x = normalize_value(event.value)
            elif event.code == evdev.ecodes.ABS_RY:
                y = normalize_value(event.value)

            # Pack the data into a binary packet.
            # Packet format: [event type (1 byte)] + [x (4 bytes float)] + [y (4 bytes float)]
            packet = struct.pack("!Bff", EVENT_TYPE_POINTER, x, y)
            sock.sendto(packet, (EMULATOR_IP, EMULATOR_PORT))

            # Print the current pointer state to the console.
            sys.stdout.write(f"Sent pointer update: x = {x:.3f}, y = {y:.3f}\r")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
