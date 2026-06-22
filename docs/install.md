1. download pwnhyve to your home directory
```
cd ~
git clone https://github.com/whatotter/pwnhyve && cd pwnhyve
```

2. download required tools, libraries
```
sudo apt install bettercap golang-go
sudo apt install liblgpio-dev python3-lgpio
```

3. create a venv and install requirements
```
python3 -m venv .
pip install -r requirements.txt
```

4. build FastIO
```
cd ./core/pio
go build pio.go
cd ../..
```

5. sudo
```
sudo su
```

6. setup DWC2 (for USB gadget)
```
echo dtoverlay=dwc2 | sudo tee -a /boot/firmware/config.txt
echo dwc2 | sudo tee -a /etc/modules
echo "libcomposite" | sudo tee -a /etc/modules
```

7. enable SPI
```
echo dtparam=spi=on | sudo tee -a /boot/firmware/config.txt
```

8. setup special SPI CS pins
```
dtc -I dts -O dtb -o 3spi.dtbo ./core/install/spi-cs-extend.dts
sudo cp 3spi.dtbo /boot/firmware/overlays/
echo "dtoverlay=3spi" >> /boot/firmware/config.txt
```

9. add `pwnhyveUSB` setup to /bin/ for pwnhyve to run
```
cp ./core/install/pwnhyveUSB /bin/ 
chmod +x /bin/pwnhyveUSB
```

10. setup a filesystem to use for USB mass storage mode (skip this if you'll never use it, otherwise take the time to do it now)
```
sudo dd if=/dev/zero of=/piusb.bin bs=65535 count=65535 status=progress # 4gb file
mkdosfs /piusb.bin
```

11. setup pwnhyve run service
```
sed -i "s@cwd@$(pwd)@g" ./core/install/pwnhyve.service
cp ./core/install/pwnhyve.service /etc/systemd/system/
```

12. enable it as a service
```
systemctl daemon-reload
systemctl enable pwnhyve.service
```

13. reboot
```
reboot now
```

14. profit