# artemis
![rsz_hero2](https://github.com/nototter/artemis/blob/main/github/images/artemis.png?raw=true)
a pi-zero powered hacking tool, with badusb capabilities, on the fly hoaxshell payload generation, 802.11 deauthing, bettercap support, and (crude) duckyscript support, all in the size of a flipper zero (or raspberry pi depending on your setup)

also has nyan cat built in

# NOTICE
- **still in heavy development, expect rage notes in random areas of code**
- badusb capabilties are functional, but can sometimes break
- deauthing works, but can sometimes go silent (see https://github.com/evilsocket/pwnagotchi/issues/267)
- web control panel is bad, but i'm not a front end developer so its expected

# BILL OF MATERIALS
- a raspberry pi zero w (can also be a 2)

note: actually, it can be anything with the same gpio as the pi zero and has usb gadget support, but dont blame me if it doesnt work on your radxa
## optionals, only get one of each
### battery
- [pisugar 2 portable](https://www.tindie.com/products/pisugar/pisugar-2-battery-for-raspberry-pi-zero/)
- [waveshare ups hat](https://www.waveshare.com/ups-hat-c.htm)

note: you could also use a mini usb battery pack, but i'd rather use a built in battery, or [you could plug it into your phone](https://www.amazon.com/Cable-Matters-Micro-Braided-Jacket/dp/B0746NHSCZ) and it would still power the pi (depends on your phone obviously)
### display
- [waveshare 1.3inch oled](https://www.waveshare.com/wiki/1.3inch_OLED_HAT) (i plan to add support to more displays in the future)
### usb stems for quick insertion
- [pi zero stem 1](https://zerostem.io/)
- [pi zero stem 2 w/o battery support (maybe)](https://www.amazon.com/risingsaplings-Connector-Expansion-Breakout-Raspberry/dp/B0924TM6NJ)

note: you could use a tiny micro-usb cable with sync+charge support, but charge isnt required since your powering it off of a battery (i hope)

## why battery?
if you try to use your pi as a ducky usb, it will take (minimum) 45 seconds to boot up and start artemis, and a couple of minutes to start everything else up; not very stealthy

you could use it without a battery though, just not reccomended

# how install?
- make sure you're root
```bash
git clone https://github.com/nototter/artemis/
cd artemis
python3 main.py
```

# credit
- 95% of this was made by me
- some of it was from [pwnagotchi](https://github.com/evilsocket/pwnagotchi/) for deauthing
