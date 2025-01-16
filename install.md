# please use the wiki instead https://github.com/whatotter/pwnhyve/wiki/installing

helllllllllllloooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo

become super cow
```
sudo su
```
update the system aswell pls


1. Clone this repository
    ```
    cd ~
    git clone https://github.com/whatotter/pwnhyve && cd pwnhyve
    ```

2. Setup `dwc2` for usb gadget mode in /boot/config.txt
    ```
    echo dtoverlay=dwc2 | sudo tee -a /boot/config.txt
    echo dwc2 | sudo tee -a /etc/modules
    echo "libcomposite" | sudo tee -a /etc/modules
    ```

3. Enable SPI
    ```
    echo dtparam=spi=on | sudo tee -a /boot/config.txt
    ```

4. Setup special SPI pins
    ```
    dtc -I dts -O dtb -o 3spi.dtbo ./core/installation/spi-cs-extend.dts
    sudo cp 3spi.dtbo /boot/overlays/
    echo "dtoverlay=3spi" >> /boot/config.txt
    echo "dtoverlay=spi0-2cs,cs0=8,cs1=18" >> /boot/config.txt
    ```

5. Install requirements using pip
    ```
    sudo pip install -r requirements.txt # running pip as sudo because pwnhyve runs as sudo
    ```

6. Install required tools
    ```
    apt install bettercap eaphammer
    ```

7. Put the USB gadget script in `/bin`
    ```
    cp ./core/install/pwnhyveUSB /bin/ 
    chmod +x /bin/pwnhyveUSB
    ```

8. No need to setup the USB script to run on boot, pwnhyve already runs it when started

9. Setup pwnhyve's systemctl service
    ```
    sed -i "s@cwd@$(pwd)@g" ./core/install/pwnhyve.service
    cp ./core/install/pwnhyve.service /etc/systemd/system/
    ```

10. Restart systemctl's daemon and enable pwnhyve
    ```
    systemctl daemon-reload
    systemctl enable pwnhyve.service
    ```

11. reboot
    ```
    sudo reboot now
    ```

congratulations u have pwnhyve installed now that's great  
here's ur reward 🐈

# optional

## boot a little faster
```
echo "disable_splash=1" | sudo tee -a /boot/config.txt
echo "boot_delay=0" | sudo tee -a /boot/config.txt
echo "initial_turbo=30" | sudo tee -a /boot/config.txt
```

## disable unnecesary services
```
systemctl disable cloud-init-main
systemctl disable plocate-updatedb.service
systemctl disable plocate-updatedb.timer
systemctl disable NetworkManager-wait-online.service
```
