# pwnhyve
![pwnhyve](https://user-images.githubusercontent.com/42103041/209862002-9ef1712c-38c5-424d-8017-fc9f119492af.png)
a pi-zero powered hacking tool, with badusb capabilities, on the fly hoaxshell payload generation, 802.11 deauthing, bettercap support, and (crude) duckyscript support, all in the size of a flipper zero (or raspberry pi depending on your setup)

## Features
- **Networking**: Includes features such as disconnecting devices from their WiFi network (Deauthing) and creating numerous fake WiFi networks to cause confusion and disruption (SSID Spamming).
- **USB Rubber Ducky**: Emulates a keyboard and executes pre-programmed keystroke payloads at superhuman speeds.
- **USB Mass Storage**: Acts as a USB drive for easy payload and loot transfer.
- **USB Gadget Mode**: Turns your device into a headless pocket computer, allowing you to perform tasks without a display.
- **Modular Design**: Easily add new features and tools thanks to the modular design.

with the shim (WIP, not released to public *yet*)
- RF hacking (rolljam, sniffing, jamming, replay)
- IR hacking (replay, jamming)
- wireless charging
- pin fuzzing (SPI, IIC/I2C, UART)
- ~~nfc~~ space constrained and also very hard to make

## Disclaimer
PwnHyve is a powerful tool intended for educational purposes only. The author is not responsible for any misuse or potential damage caused by this tool. It's important to understand that it can be used for malicious purposes if it falls into the wrong hands.

While PwnHyve is a robust tool, it is not intended to be a replacement for or superior to P4wnP1-Aloa. P4wnP1-Aloa has a broader support base and more extensive features. If you find that a feature you need is not yet implemented in PwnHyve, consider creating plugins to add this functionality.

If you encounter any bugs or issues, please do not hesitate to create an issue on the project's GitHub page. Your contributions help improve PwnHyve for everyone.

# Notice
- The deauthentication feature is functional, but it may occasionally become unresponsive. For more information, refer to this [issue](https://github.com/evilsocket/pwnagotchi/issues/267).
- Please be aware that this project is currently undergoing a rewrite. As such, the presence of bugs is anticipated.

## BILL OF MATERIALS
- A Raspberry Pi Zero 1/2 W 

## Optional Components

### Battery (Only required if you're not using a USB stem)
- [PiSugar 2 Portable](https://www.tindie.com/products/pisugar/pisugar-2-battery-for-raspberry-pi-zero/)
- [Waveshare UPS HAT](https://www.waveshare.com/ups-hat-c.htm)
- [DIY Battery](https://github.com/nototter/pwnhyve/wiki/making-your-own-pi-zero-battery-ups)
- [Micro-USB Cable for Phone Connection](https://www.amazon.com/Cable-Matters-Micro-Braided-Jacket/dp/B0746NHSCZ)

### Display
- [Waveshare 1.3-inch OLED](https://www.waveshare.com/wiki/1.3inch_OLED_HAT)

### USB Stems (Don't buy if you're getting a battery pack)
- [ZeroStem for Pi Zero](https://zerostem.io/)
- [Pi Zero Stem without Battery Support](https://www.amazon.com/risingsaplings-Connector-Expansion-Breakout-Raspberry/dp/B0924TM6NJ)

- Note: Alternatively, you can use a compact micro-USB cable with sync support to connect to the target device.

### Why a Battery?
If you plan to use your Pi as a USB Rubber Ducky, it will take a minimum of 25 seconds to boot up and start PwnHyve, and a few more minutes to start everything else. This isn't very stealthy. 

While it's possible to use it without a battery, it's not recommended for optimal performance.

## How to Install

1. First, download the Kali Linux Raspberry Pi image from the official Kali Linux website. You can get it from [here](https://www.kali.org/get-kali/#kali-arm).
2. Write the downloaded image to an SD card using the following command in your terminal: ```xzcat kali-linux-2024.1-raspberry-pi-zero-2-w-armhf.img.xz | sudo dd of=/dev/sdX bs=4M status=progress``` 
Alternatively, you can use a tool like [Balena Etcher](https://www.balena.io/etcher/) to write the image to the SD card.
To make it headless, you can add a ```wpa_supplicant.conf``` file to the first partition of the microSD card to connect to a wireless network. You can create this file on another Linux system by running: ```wpa_passphrase YOURNETWORK > wpa_supplicant.conf```  [Documentation](https://www.kali.org/docs/arm/raspberry-pi-zero-2-w/)
3. Power it on and SSH into it (Default Credentials: ```kali/kali```)
4. Upgrade and update the Pi: ```sudo apt-get update && sudo apt-get upgrade```
5. Turn Pi into usb gadget mode / [Documentation](https://learn.adafruit.com/turning-your-raspberry-pi-zero-into-a-usb-gadget/ethernet-gadget):

```
echo dtoverlay=dwc2 | sudo tee -a /boot/config.txt
echo dwc2 | sudo tee -a /etc/modules
echo dtparam=spi=on | sudo tee -a /boot/config.txt
echo "libcomposite" | sudo tee -a /etc/modules
```
6. Reboot the Pi
7. Clone the repo and run setup.sh: ```git clone https://github.com/nototter/pwnhyve && cd pwnhyve && bash setup.sh```

## Configuration
TODO:
config.toml