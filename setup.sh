#!/bin/bash

# Switch to root user
sudo su

# Install requirements
pip install -r requirements.txt

# Install additional packages
sudo apt-get install python3-smbus bettercap

# Setup usb
sudo cp ./core/installation/pwnhyveusb /bin/ && sudo chmod +x /bin/pwnhyveusb
mkdir /mnt/otterusb

# Create usb .bin file
sudo dd if=/dev/zero of=/piusb.bin bs=65535 count=65535 
mkdosfs /piusb.bin

# Add pwnhyveusb to rc.local
# sed -i '$e echo /bin/pwnhyveusb' /etc/rc.local

# Add pwnhyveusb to crontab
echo "@reboot /bin/pwnhyveusb" | sudo tee -a /etc/crontab

# Create pwnhyveStart file
cp ./core/installation/startup.sh /bin/
mv /bin/startup.sh /bin/pwnhyveStart
chmod +x /bin/pwnhyveStart

# Replace all %cwd% in the file with your pwd value
sed -i "s|%cwd%|$(pwd)|g" /bin/pwnhyveStart

# Enable pwnhyve service
cp ./core/installation/pwnhyve.service /etc/systemd/system/
systemctl enable pwnhyve.service

# Echo setup complete
echo "Setup complete. Rebooting the Pi in 5 seconds."

# Sleep for 5 seconds
sleep 5

# Reboot the Pi
reboot