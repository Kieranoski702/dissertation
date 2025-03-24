#!/bin/bash
# setup.sh - Automated setup script for Wii Remote Emulator environment
#
# This script performs the following tasks:
#   - Configures the system to load necessary kernel modules (e.g., hid-wiimote) on boot.
#   - Edits /etc/bluetooth/input.conf to include "ClassicBondedOnly=false".
#   - Sets the LD_LIBRARY_PATH environment variable.
#   - Installs dependencies and builds xwiimote and its Python bindings.
#   - Clones and compiles the custom Wii Remote Emulator.
#   - Disables and stops the default Bluetooth service and starts a custom bluetoothd.
#
# Usage: Run this script as root or using sudo.
#
# IMPORTANT: This script modifies system configuration files and services.
# Ensure you understand the changes before running in a production environment.

# Check for root privileges.
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Try using sudo."
    exit 1
fi

set -e # Exit immediately if a command exits with a non-zero status

echo "=== Configuring Kernel Modules ==="
# Ensure the hid-wiimote module is loaded on boot.
echo "hid-wiimote" >/etc/modules-load.d/wiimote.conf
modprobe hid-wiimote

echo "=== Configuring Bluetooth Input Settings ==="
# Append "ClassicBondedOnly=false" to /etc/bluetooth/input.conf if not already present.
BLUETOOTH_CONF="/etc/bluetooth/input.conf"
if ! grep -q "ClassicBondedOnly=false" "$BLUETOOTH_CONF"; then
    echo "ClassicBondedOnly=false" >>"$BLUETOOTH_CONF"
    echo "Added 'ClassicBondedOnly=false' to $BLUETOOTH_CONF."
else
    echo "'ClassicBondedOnly=false' already present in $BLUETOOTH_CONF."
fi

echo "=== Setting LD_LIBRARY_PATH ==="
# Set LD_LIBRARY_PATH for libraries installed to /usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
echo "LD_LIBRARY_PATH set to /usr/local/lib."

echo "=== Installing Dependencies ==="
# Update package list and install necessary packages.
apt-get update
apt-get install -y swig autoconf libtool python-dev libdbus-1-dev libglib2.0-dev libsdl1.2-dev git

echo "=== Installing xwiimote ==="
# Clone, build, and install xwiimote.
cd /tmp
if [ -d "xwiimote" ]; then
    rm -rf xwiimote
fi
git clone https://github.com/xwiimote/xwiimote.git
cd xwiimote
./configure
make
make install
cd ..

echo "=== Installing xwiimote-bindings ==="
# Clone, build, and install xwiimote Python bindings.
if [ -d "xwiimote-bindings" ]; then
    rm -rf xwiimote-bindings
fi
git clone https://github.com/xwiimote/xwiimote-bindings.git
cd xwiimote-bindings
./autogen.sh
make
make install
cd ..

echo "=== Installing Custom Wii Remote Emulator ==="
# Clone and compile the custom Wii Remote Emulator.
if [ -d "WiimoteEmulator" ]; then
    rm -rf WiimoteEmulator
fi
git clone https://github.com/Kieranoski702/WiimoteEmulator.git
cd WiimoteEmulator
# Run the custom build script for the emulator.
source ./build-custom.sh

echo "=== Configuring Bluetooth Service ==="
# Disable and stop the default Bluetooth service.
systemctl disable bluetooth
systemctl stop bluetooth

# Start the custom Bluetooth daemon.
echo "Starting custom bluetoothd..."
./bluez-4.101/dist/sbin/bluetoothd

echo "=== Setup Complete ==="
