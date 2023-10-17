# pwnhyve
![pwnhyve](https://user-images.githubusercontent.com/42103041/209862002-9ef1712c-38c5-424d-8017-fc9f119492af.png)
a pi-zero powered hacking tool, with badusb capabilities, on the fly hoaxshell payload generation, 802.11 deauthing, bettercap support, and (crude) duckyscript support, all in the size of a flipper zero (or raspberry pi depending on your setup)

***
### DISCLAIMER
i am not responsible for what you do with this thing; this can actually be used for really bad purposes in the right hands  
this also isn't meant to be better than the p4wnp1-aloa - the aloa has way more support for everything than me
if support/something you want isn't implemented yet, look at making plugins unless its something else - in that case, [make an issue](https://github.com/woahotter/pwnhyve/issues/new)
***

# NOTICE
- deauthing works, but can sometimes go silent (see https://github.com/evilsocket/pwnagotchi/issues/267)

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

# how install?
go into the wiki to install

# credit
- 98% of this was made by me
- some of it was from [pwnagotchi](https://github.com/evilsocket/pwnagotchi/) for deauthing
