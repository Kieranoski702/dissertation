#!/usr/bin/env python3
"""
wiimote_to_emulator.py

This script connects to a real Wiimote using the xwiimote Python3 bindings,
reads events (for example, accelerometer data used here as a proxy for pointer
position), and sends binary pointer update packets over UDP to the Wii Remote
Emulator.

The binary packet format is defined as:
   [1 byte event type (0x01)] + [4 bytes float x] + [4 bytes float y]
with floats packed in network (big-endian) order.
"""

import argparse
import logging
import socket
import struct
import select
import sys
import errno
import time

import xwiimote


def init_logging(name):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(name)
    return logger


def setup_udp_socket(emulator_host, emulator_port, logger):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    emulator_addr = (emulator_host, emulator_port)
    logger.info(
        "UDP socket ready; sending to {}:{}".format(emulator_host, emulator_port)
    )
    return sock, emulator_addr


def get_first_wiimote(logger):
    # Create a monitor that watches for wiimotes (both new and removed)
    try:
        mon = xwiimote.monitor(True, True)
    except Exception as e:
        logger.error("Unable to initialize wiimote monitor: {}".format(e))
        return None, None

    # Poll for the first available wiimote path
    wiimote_path = mon.poll()
    if not wiimote_path:
        logger.error("No wiimote found")
        return None, mon

    try:
        dev = xwiimote.iface(wiimote_path)
    except Exception as e:
        logger.error("Failed to create wiimote interface: {}".format(e))
        return None, mon

    return dev, mon


def main():
    parser = argparse.ArgumentParser(
        description="Stream raw Wiimote pointer updates to a Wii Remote Emulator"
    )
    parser.add_argument(
        "--host", type=str, required=True, help="Emulator host IP address"
    )
    parser.add_argument("--port", type=int, required=True, help="Emulator port number")
    parser.add_argument(
        "--debug", action="store_true", default=False, help="Enable debug logging"
    )
    args = parser.parse_args()

    logger = init_logging("wiimote_streamer")
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Set up UDP socket for sending pointer update packets
    udp_sock, emulator_addr = setup_udp_socket(args.host, args.port, logger)

    # Get the wiimote device
    logger.info("Searching for a Wiimote...")
    dev, mon = get_first_wiimote(logger)
    if dev is None:
        sys.exit(1)

    try:
        # Open the device with writable flag so that we can later read events
        dev.open(dev.available() | xwiimote.IFACE_WRITABLE)
    except Exception as e:
        logger.error("Failed to open wiimote: {}".format(e))
        sys.exit(1)

    fd = dev.get_fd()
    logger.info("Wiimote initialized. Starting event loop...")

    # Set up a poll object to wait for events from the wiimote file descriptor
    poller = select.poll()
    poller.register(fd, select.POLLIN)

    # Create an event object that will be reused to receive events
    evt = xwiimote.event()

    # Main loop: poll for events and send pointer updates over UDP
    while True:
        try:
            # Poll with a timeout (in milliseconds)
            events = poller.poll(100)
            if not events:
                continue

            for poll_fd, flag in events:
                if flag & select.POLLIN:
                    try:
                        dev.dispatch(evt)
                    except IOError as e:
                        if e.errno != errno.EAGAIN:
                            logger.error("Dispatch error: {}".format(e))
                        continue

                    # Process event types
                    if evt.type == xwiimote.EVENT_ACCEL:
                        # Retrieve accelerometer data; for example, using channel 0.
                        # (Depending on your device and desired pointer data, you might
                        # choose a different event type or process multiple channels.)
                        x_val, y_val, z_val = evt.get_abs(0)
                        logger.debug(
                            "Raw accelerometer: x=%f, y=%f, z=%f", x_val, y_val, z_val
                        )

                        # Convert these raw values to normalized pointer coordinates.
                        # (For example, assume x_val and y_val are in [-1, 1] and map them
                        # to [0, 1]. Adjust this mapping to your actual device’s output.)
                        norm_x = (x_val + 1) / 2.0
                        norm_y = (y_val + 1) / 2.0

                        # Pack a binary packet: 0x01, followed by norm_x and norm_y as big-endian floats.
                        packet = struct.pack("!Bff", 0x01, norm_x, norm_y)
                        udp_sock.sendto(packet, emulator_addr)
                        logger.debug(
                            "Sent pointer update: norm_x=%.3f, norm_y=%.3f",
                            norm_x,
                            norm_y,
                        )

                    elif evt.type == xwiimote.EVENT_KEY:
                        # Process key (button) events if desired.
                        code, state = evt.get_key()
                        logger.debug("Button event: code=%s, state=%s", code, state)
                        # You might send a separate packet for button events here.

                    # You can add additional event types as needed.

        except KeyboardInterrupt:
            logger.info("Exiting...")
            break
        except Exception as e:
            logger.error("Error in main loop: {}".format(e))
            time.sleep(0.1)

    udp_sock.close()


if __name__ == "__main__":
    main()
