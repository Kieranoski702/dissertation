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

# Global latency accumulators (in microseconds) and counters for each event type.
total_accel_latency = 0
count_accel = 0

total_ir_latency = 0
count_ir = 0

total_key_latency = 0
count_key = 0


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
    global total_accel_latency, count_accel
    global total_ir_latency, count_ir
    global total_key_latency, count_key

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
        print("No wiimote found")
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

    try:
        # Main loop: poll for events and send updates over UDP
        while True:
            # Poll with a timeout (in milliseconds)
            events = poller.poll(100)
            if not events:
                continue

            for poll_fd, flag in events:
                if flag & select.POLLIN:
                    # Record the start time right before processing the event.
                    start_time = time.monotonic()
                    try:
                        dev.dispatch(evt)
                    except IOError as e:
                        if e.errno != errno.EAGAIN:
                            logger.error("Dispatch error: {}".format(e))
                        continue

                    # Process event types and send corresponding UDP packets.
                    if evt.type == xwiimote.EVENT_ACCEL:
                        # Retrieve raw accelerometer data from channel 0.
                        x_val, y_val, z_val = evt.get_abs(0)
                        logger.debug(
                            "Raw accelerometer: x=%f, y=%f, z=%f", x_val, y_val, z_val
                        )

                        # Normalize the raw values.
                        norm_ax = (x_val / 1.57) + 527.5
                        norm_ay = (y_val / 1.57) + 527.5
                        norm_az = (z_val / 1.57) + 527.5
                        logger.debug(
                            "Normalized accelerometer: ax=%.3f, ay=%.3f, az=%.3f",
                            norm_ax,
                            norm_ay,
                            norm_az,
                        )

                        # Pack a binary accelerometer packet: header 0x02 followed by three big-endian floats.
                        packet = struct.pack("!Bfff", 0x02, norm_ax, norm_ay, norm_az)
                        udp_sock.sendto(packet, emulator_addr)
                        logger.debug(
                            "Sent accelerometer update: ax=%.3f, ay=%.3f, az=%.3f",
                            norm_ax,
                            norm_ay,
                            norm_az,
                        )
                        # Measure latency.
                        end_time = time.monotonic()
                        latency_us = (end_time - start_time) * 1e6
                        total_accel_latency += latency_us
                        count_accel += 1

                    elif evt.type == xwiimote.EVENT_IR:
                        # Retrieve IR data from the wiimote.
                        ir_x, ir_y, ir_z = evt.get_abs(0)
                        logger.debug("IR event: x=%f, y=%f, z=%f", ir_x, ir_y, ir_z)
                        # Normalize coordinates to floats in [0, 1].
                        ir_x = 1.0 - (ir_x / 1023.0)
                        ir_y = 1.0 - (ir_y / 767.0)
                        ir_z = 1.0 - (ir_z / 1023.0)
                        # Pack a binary packet: header 0x01 followed by three floats in network byte order.
                        packet = struct.pack("!Bfff", 0x01, ir_x, ir_y, ir_z)
                        udp_sock.sendto(packet, emulator_addr)
                        logger.debug(
                            "Sent IR update: x=%.3f, y=%.3f, z=%.3f", ir_x, ir_y, ir_z
                        )
                        # Measure latency.
                        end_time = time.monotonic()
                        latency_us = (end_time - start_time) * 1e6
                        total_ir_latency += latency_us
                        count_ir += 1

                    elif evt.type == xwiimote.EVENT_KEY:
                        # Process key (button) events.
                        code, state = evt.get_key()
                        logger.debug("Button event: code=%s, state=%s", code, state)
                        # Example: sending text-based button commands over UDP.
                        if code == xwiimote.KEY_PLUS:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_PLUS", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_PLUS", emulator_addr)
                        elif code == xwiimote.KEY_MINUS:
                            if state == 1:
                                udp_sock.sendto(
                                    b"button 1 WIIMOTE_MINUS", emulator_addr
                                )
                            else:
                                udp_sock.sendto(
                                    b"button 0 WIIMOTE_MINUS", emulator_addr
                                )
                        elif code == xwiimote.KEY_HOME:
                            if state == 1:
                                udp_sock.sendto(b"button 1 HOME", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 HOME", emulator_addr)
                        elif code == xwiimote.KEY_A:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_A", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_A", emulator_addr)
                        elif code == xwiimote.KEY_B:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_B", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_B", emulator_addr)
                        elif code == xwiimote.KEY_UP:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_UP", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_UP", emulator_addr)
                        elif code == xwiimote.KEY_DOWN:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_DOWN", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_DOWN", emulator_addr)
                        elif code == xwiimote.KEY_LEFT:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_LEFT", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_LEFT", emulator_addr)
                        elif code == xwiimote.KEY_RIGHT:
                            if state == 1:
                                udp_sock.sendto(
                                    b"button 1 WIIMOTE_RIGHT", emulator_addr
                                )
                            else:
                                udp_sock.sendto(
                                    b"button 0 WIIMOTE_RIGHT", emulator_addr
                                )
                        elif code == xwiimote.KEY_ONE:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_1", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_1", emulator_addr)
                        elif code == xwiimote.KEY_TWO:
                            if state == 1:
                                udp_sock.sendto(b"button 1 WIIMOTE_2", emulator_addr)
                            else:
                                udp_sock.sendto(b"button 0 WIIMOTE_2", emulator_addr)
                        # Measure latency.
                        end_time = time.monotonic()
                        latency_us = (end_time - start_time) * 1e6
                        total_key_latency += latency_us
                        count_key += 1

    except KeyboardInterrupt:
        logger.info("Exiting...")
        break
    except Exception as e:
        logger.error("Error in main loop: {}".format(e))
        time.sleep(0.1)

    udp_sock.close()

    # Print average latencies upon exit.
    logger.info("Latency statistics:")
    if count_accel > 0:
        avg_accel = total_accel_latency / count_accel
        logger.info(
            "  Accelerometer: average %.0f µs (%d samples)", avg_accel, count_accel
        )
    if count_ir > 0:
        avg_ir = total_ir_latency / count_ir
        logger.info("  IR:            average %.0f µs (%d samples)", avg_ir, count_ir)
    if count_key > 0:
        avg_key = total_key_latency / count_key
        logger.info("  Button:        average %.0f µs (%d samples)", avg_key, count_key)


if __name__ == "__main__":
    main()
