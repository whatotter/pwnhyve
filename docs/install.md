this is for a kali install, assuming your non sudo user is `kali`

0. enable prerequisites, like SPI and DWC2
    - ```echo dtoverlay=dwc2 | sudo tee -a /boot/firmware/config.txt```
    - ```echo dwc2 | sudo tee -a /etc/modules```
    - ```echo "libcomposite" | sudo tee -a /etc/modules```
    - ```echo dtparam=spi=on | sudo tee -a /boot/firmware/config.txt```
1. git clone pwnhyve to home (DO NOT CLONE PWNHYVE TO ROOT): 
    - ```cd ~ && git clone https://github.com/whatotter/pwnhyve && cd pwnhyve```
2. enable special SPI CS pins:
    - ```dtc -I dts -O dtb -o 3spi.dtbo ./core/install/spi-cs-extend.dts```
    - ```sudo cp 3spi.dtbo /boot/firmware/overlays/```
    - ```echo "dtoverlay=3spi" >> /boot/firmware/config.txt```
3. download required tools:
    - ```apt install bettercap eaphammer golang-go```
4. build fastio:
    - ```cd ./core/pio```
    - ```go build pio.go```
    - ```cd ~/pwnhyve```
5. setup usb gadget script
    - ```cp ./core/install/pwnhyveUSB /bin/ && chmod +x /bin/pwnhyveUSB```
6. setup usb filesystem image *adjust size to your liking
    - ```sudo dd if=/dev/zero of=/pwnhyve.bin bs=65535 count=65535 status=progress && mkdosfs /pwnhyve.bin```
7. create a venv: 
    - ```python3 -m venv .```
8. activate the venv: 
    - ```source ./bin/activate```
9. install all packages: 
    - ```pip install -r requirements.txt```
10. start pwnhyve, confirm it works before moving onto the next step: 
    - ```python3 main.py```
11. once confirmed working, copy `pwnhyve.service` to systemd folder, restart daemon and enable: 
    - ```sed -i "s@cwd@$(pwd)@g" ./core/install/pwnhyve.service```
    - ```cp ./core/install/pwnhyve.service /etc/systemd/system/```
    - ```systemctl daemon-reload```
    - ```systemctl enable pwnhyve.service```

## if you are running on a different OS, or your user is not named `kali`
go to your pwnhyve folder, and edit `pwnhyve.service` using your favorite editor. change the line `ExecStart=/home/kali/pwnhyve/bin/ /home/kali/pwnhyve/main.py` to match the directory of wherever pwnhyve is