# Wii remote connection to pi
https://blog.malware.re/2023/07/04/Wiimote-on-Linux-with-dev-input/index.html
1. Corroded Wii remote mac address is 00:1F:C5:6D:AE:A6
2. Run `bluetoothctl`
3. Type `trust [address]` but press the 1 and 2 key on Wii remote before running
4. Type `connect [address]` but press a button before running

# Running Wii remote emulator (Seems to only work with GUI)
https://github.com/rnconrad/WiimoteEmulator
1. `sudo systemctl disable bluetooth`
2. `sudo systemctl stop bluetooth`
3. `sudo systemctl status bluetooth`
4. `sudo ./bluez-4.101/dist/sbin/bluetoothd`
5. `sudo ./wmemulator`
6. press sync button on Wii
7. After finishing :
   - `sudo killall bluetoothd`
   - `sudo systemctl enable bluetooth`
   - `sudo systemctl start bluetooth`
   - `sudo systemctl status bluetooth`
   
# Streaming Wii video to other raspberry pi (Seems to only work in headless)
1. On client pi (Pi 2) run `./play-rtp.sh`
2. On host pi (Pi 1) run `./broadcast-rtp.sh`
3. When finished press q on client pi then ctrl c on host pi

