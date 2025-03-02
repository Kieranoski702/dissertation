# Dependecies for everything
## xwiimote

All this information can be found [here](https://github.com/marthjod/wiipy/)

### Build [xwiimote](https://github.com/dvdhrm/xwiimote)

- dependencies: [ref](https://github.com/dvdhrm/xwiimote-bindings/pull/8)
    - swig
    - autoconf
    - libtool
    - python3-dev
    - libncurses-dev
    - libudev-dev
- the pre-compiled package found in the Debian Jessie repo is too old ([ref](https://github.com/dvdhrm/xwiimote-bindings/issues/13))
- `./configure --prefix=/usr` **or** append `LD_LIBRARY_PATH` later on ([ref](https://askubuntu.com/questions/633949/failed-to-build-xwiimote-bindings))


### Build [xwiimote-bindings](https://github.com/dvdhrm/xwiimote-bindings)

```
./autogen.sh
make
sudo make install
```

### Use xwiimote Python binding

```bash
# optional
# export LD_LIBRARY_PATH=/usr/local/lib
python test.py [--debug]
```

## WiimoteEmulator
- libdbus-1-dev
- libglib2.0-dev
- libsdl1.2-dev


# Wii remote connection to pi

https://blog.malware.re/2023/07/04/Wiimote-on-Linux-with-dev-input/index.html

First edit `/etc/bluetooth/input.conf`. Change the line `#ClassicBondedOnly=true` to `ClassicBondedOnly=false`
1. Corroded Wii remote mac address is 00:1F:C5:6D:AE:A6. Other one is 00:22:4C:7A:02:AC
2. Run `bluetoothctl`
3. Type `trust [address]` but press the 1 and 2 key on Wii remote before running
4. Type `connect [address]` but press a button before running

# Running Wii remote emulator (Seems to only work with GUI)

https://github.com/rnconrad/WiimoteEmulator
Wii mac address: 00:22:4C:19:DD:5F

1. `sudo systemctl disable bluetooth`
2. `sudo systemctl stop bluetooth`
3. `sudo systemctl status bluetooth`
4. `sudo ./bluez-4.101/dist/sbin/bluetoothd`
5. `sudo ./wmemulator 00:22:4C:19:DD:5F ip 5001`
6. On a different machine send text packets using `nc -u ip 5001` then typing the messages
7. press sync button on Wii
8. After finishing :
   - `sudo killall bluetoothd`
   - `sudo systemctl enable bluetooth`
   - `sudo systemctl start bluetooth`
   - `sudo systemctl status bluetooth`

# Streaming Wii video to other raspberry pi (Seems to only work in headless)

1. On client pi (Pi 2) run `./play-rtp.sh`
2. On host pi (Pi 1) run `./broadcast-rtp.sh`
3. When finished press q on client pi then ctrl c on host pi
