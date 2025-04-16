<p align="center">
   <h1 align="center">pwnhyve</h1>
   <img src="./images/pwnhyve-min.png">
</p>
<h4 align="center">a little offensive appliance that mimics some features from the flipper zero and more, under $50</h4>
<h4 align="center">https://otter-1.gitbook.io/pwnhyve</h4>

## feature set
- extremely modular plugin system
- built on Kali Linux
- WiFi
    - Deauthentication attacks
        - pwnagotchi-like UI
    - AP scanner
    - EAPHammer toolset
        - Harvest credentials using Evil Twin APs
        - [KARMA attacks](https://en.wikipedia.org/wiki/KARMA_attack)
        - Captive Portal
        - Wifi bruteforcing
- Bluetooth
    - Access to bettercap's bluetooth stack
    - Search for devices by RSSI strength
    - Search for devices by specifics (mac, uuids, types)
    - GATT BLE hacking
        - [With this, you can unlock bluetooth locks - click me!](https://youtu.be/kzRCGxDKPFA?t=31)
- USB
    - Togglable USB mass storage, act as a normal pen drive
        - readable inside of kali aswell
    - Keyboard and Mouse emulation
    - Duckyscript-like Jinja2 scripting support
    - USB stealer, steal valuable files from a USB drive immediately after plug-in
    - File exfiltration, without mass storage, using [Hak5's Keystroke Reflection](https://cdn.shopify.com/s/files/1/0068/2142/files/hak5-whitepaper-keystroke-reflection.pdf?v=1659317977)

- RF hacking
    - Jamming
    - Replay
    - Use and save as Flipper Zero files
        - Can use Flipper Zero `.sub` files
        - Can also save recorded frames as `.sub` files
- IO
    - 2 channel 1.5mHz Logic analyzer, compatible with sigrok/pulseview (by CSV export)
    - Flipper Zero-like breakout
    - IO playground (PWM, input/output)
    - ~~SPI flash dumping~~ WIP
    - ~~Serial to TTL converter~~ WIP
- other
    - looks cool

# docs
https://otter-1.gitbook.io/pwnhyve

# feature matrix against the flipper zero
| Feature         | Pwnhyve              | Flipper Zero         |
|-----------------|----------------------|----------------------|
| NFC/RFID        | No                   | Yes                  |
| IR              | W.I.P                | Yes                  |
| 1Wire           | No, but possible     | Yes                  |
| RF              | Yes                  | Yes                  |
| BLE             | Yes                  | Yes                  |
| Converter       | No (for now)         | Yes (SPI, UART, I2C) |
| Linux           | Yes (Kali)           | No                   |
| Logic Analyzer  | Yes (1.5mhz)         | No                   |
| WiFi            | Yes                  | No                   |
| BadUSB          | Yes (KBM, storage)   | Yes (KBM only)       |
| Modularity      | Very (python)        | Yes, but hard        |


# disclaimers
This tool may be used for legal purposes only. Users take full responsibility for any actions performed using this tool. The author accepts no liability for damage caused by this tool. If these terms are not acceptable to you, then do not use this tool.

*wifi sometimes doesn't work because of nexmon; it is out of my ability to fix it*
