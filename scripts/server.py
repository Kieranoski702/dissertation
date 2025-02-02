#!/usr/bin/env python
import socket
import json
import uinput
import evdev

# Listening configuration
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 12345


# Create a socket to receive data
def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
    sock.bind((LISTEN_IP, LISTEN_PORT))
    return sock


# Map Wiimote accelerometer data to mouse movements
def map_to_mouse(value, min_val=-1, max_val=1, scale=10):
    """Map Wiimote accelerometer range (-1 to 1) to mouse movement range."""
    return int((value - min_val) / (max_val - min_val) * scale)


# Setup the virtual mouse device
device = uinput.Device(
    [
        uinput.REL_X,  # Mouse X movement
        uinput.REL_Y,  # Mouse Y movement
        uinput.BTN_LEFT,  # Left mouse button
        uinput.BTN_RIGHT,  # Right mouse button
    ]
)

sock = create_socket()
print(f"Listening for data on {LISTEN_IP}:{LISTEN_PORT}")

while True:
    data, addr = sock.recvfrom(1024)
    payload = json.loads(data.decode("utf-8"))

    x, y, z = payload.get("x", 0), payload.get("y", 0), payload.get("z", 0)
    buttons = payload.get("buttons", {})

    # Map accelerometer data to mouse movement
    dx = map_to_mouse(x)
    dy = map_to_mouse(y)

    # Emit mouse movement
    if dx != 0:
        device.emit(uinput.REL_X, dx, syn=False)
    if dy != 0:
        device.emit(uinput.REL_Y, dy, syn=False)

    # Handle mouse button presses (example: mapping certain Wiimote buttons)
    if buttons.get(evdev.ecodes.BTN_A, 0):  # Example: A button mapped to left-click
        device.emit_click(uinput.BTN_LEFT)
    if buttons.get(evdev.ecodes.BTN_B, 0):  # Example: B button mapped to right-click
        device.emit_click(uinput.BTN_RIGHT)

    print(f"Received: X={x:.3f}, Y={y:.3f}, Z={z:.3f}, Buttons={buttons}")
