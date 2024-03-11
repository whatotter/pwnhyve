# pwnhyve
![pwnhyve](https://user-images.githubusercontent.com/42103041/209862002-9ef1712c-38c5-424d-8017-fc9f119492af.png)
a pi-zero powered hacking tool, with badusb capabilities, on the fly hoaxshell payload generation, 802.11 deauthing, bettercap support, and (crude) duckyscript support, all in the size of a flipper zero (or raspberry pi depending on your setup)

some of it's features:

- [duckyscript's iconic keystroke reflection](https://docs.hak5.org/hak5-usb-rubber-ducky/advanced-features/exfiltration#the-keystroke-reflection-attack)
- remote control
- jinja2 enabled duckyscript support (WIP, but enough to use most scripts)
- deauthing and sniffing attacks (EAPOL supported (thanks bettercap)), access point spamming, evil portal
- usb mass storage emulation, mouse emulation
- ~~BLE hacking~~ work in progress
- infinite amount of plugins
- reverse shell hosting
- literal entire kali linux system in your pocket

with the shim (WIP, not released to public *yet*)
- RF hacking (rolljam, sniffing, jamming, replay)
- IR hacking (replay, jamming)
- wireless charging
- pin fuzzing (SPI, IIC/I2C, UART)
- ~~nfc~~ space constrained and also very hard to make

***
### DISCLAIMER
i am not responsible for what you do with this thing; this can actually be used for really bad purposes in the right hands  
this also isn't meant to be better than the p4wnp1-aloa - the aloa has way more support for everything than me
if support/something you want isn't implemented yet, look at making plugins  
unless its something else, like a bug - in that case, [PLEASE make an issue](https://github.com/whatotter/pwnhyve/issues/new)
***

# NOTICE
- deauthing works, but can sometimes go silent (see https://github.com/evilsocket/pwnagotchi/issues/267)
- this is in the middle of a rewrite, bugs are to be expected

# BILL OF MATERIALS
- a raspberry pi zero w (can also be a 2)

## OPTIONAL
### battery (DO NOT BUY IF YOUR GETTING A USB STEM)
- [pisugar 2 portable](https://www.tindie.com/products/pisugar/pisugar-2-battery-for-raspberry-pi-zero/)
- [waveshare ups hat](https://www.waveshare.com/ups-hat-c.htm)
- [or create your own battery](https://github.com/nototter/pwnhyve/wiki/making-your-own-pi-zero-battery-ups)
- [you could plug it into your phone](https://www.amazon.com/Cable-Matters-Micro-Braided-Jacket/dp/B0746NHSCZ) 

### display
- [waveshare 1.3inch oled](https://www.waveshare.com/wiki/1.3inch_OLED_HAT)
### usb stems for quick insertion (DO NOT BUY IF YOUR GETTING A BATTERY PACK)
- [pi zero stem 1](https://zerostem.io/)
- [pi zero stem 2 w/o battery support](https://www.amazon.com/risingsaplings-Connector-Expansion-Breakout-Raspberry/dp/B0924TM6NJ)

- note: you could use a tiny micro-usb cable with sync support and plug that in to the victim

## why battery?
if you try to use your pi as a ducky usb, it will take (minimum) 25 seconds to boot up and start pwnhyve, and a couple of minutes to start everything else up; not very stealthy

you could use it without a battery though, just not reccomended

# How to Install

1. First, download the Kali Linux Raspberry Pi image from the official Kali Linux website. You can get it from [here](https://www.kali.org/get-kali/#kali-arm).
2. Write the downloaded image to an SD card using the following command in your terminal: ```xzcat kali-linux-2024.1-raspberry-pi-zero-2-w-armhf.img.xz | sudo dd of=/dev/sdX bs=4M status=progress``` 
Alternatively, you can use a tool like [Balena Etcher](https://www.balena.io/etcher/) to write the image to the SD card.
To make it headless, you can add a ```wpa_supplicant.conf``` file to the first partition of the microSD card to connect to a wireless network. You can create this file on another Linux system by running: ```wpa_passphrase YOURNETWORK > wpa_supplicant.conf```  [Documentation](https://www.kali.org/docs/arm/raspberry-pi-zero-2-w/)
3. Power it on and SSH into it (Default Credentials: ```kali/kali```)
4. Upgrade and update the Pi: ```sudo apt-get update && sudo apt-get upgrade```
5. Turn Pi into usb gadget mode: 
```
echo dtoverlay=dwc2 | sudo tee -a /boot/config.txt
echo dwc2 | sudo tee -a /etc/modules
echo dtparam=spi=on | sudo tee -a /boot/config.txt
echo "libcomposite" | sudo tee -a /etc/modules
```
6. Reboot the Pi
7. Clone the repo and run setup.sh: ```git clone https://github.com/nototter/pwnhyve && cd pwnhyve && bash setup.sh```

# credit
- 98% of this was made by me
- some of it was from [pwnagotchi](https://github.com/evilsocket/pwnagotchi/) for deauthing
