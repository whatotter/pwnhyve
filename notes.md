this is notes mostly for me but u can use this

# GPIO
- **use raw BCM pinouts** - gpiozero uses raw BCM pinouts, and so does FastIO
- gpiozero has 100khz polling rate; FastIO has 2mhz polling rate (tested with `./debug/gzmaxio.py` and `./core/pio/fastio.py`, respectively)

shim IO pinout:
```
pins face this way ->
pins with * are recommended to not be used

+----------+----+
| Ground   | 1  |
| GPIO4    | 2  |
| *GPIO17  | 3  | note: used as chip select
| SPI-CLK  | 4  |
| *GPIO7   | 5  | note: used as chip select
| MISO     | 6  |
| MOSI     | 7  |
| +5V      | 8  |
|          |    |
|          |    |
| GND      | 9  |
| NC       | 10 |
| SCL      | 11 |
| SDA      | 12 |
| UART_RX  | 13 |
| UART_TX  | 14 |
| NC       | 15 |
| GND      | 16 |
| NC       | 17 |
| 3V3      | 18 |
+----------+----+
```

# spi
~~add `dtoverlay=spi0-2cs,cs0=8,cs1=18` to `/boot/config.txt`~~  
- GPIO8 (phys. pin 24) would be for `spidev0.0` (display)
- GPIO18 (phys. pin 12) would be for `spidev0.1` (CC1101)
- GPIO7 (phys. pin 26) would be for `spidev0.2` (other things)

run ```
dtc -I dts -O dtb -o 3spi.dtbo ./core/installation/spi-cs-extend.dts
sudo cp 3spi.dtbo /boot/overlays/
echo "dtoverlay=3spi" >> /boot/config.txt

sudo reboot
```

# programming
```
               // PIL.ImageDraw
               ||
tinyPillow -> draw, disp, image  
                     ||    \\
                     ||     PIL.Image
                     ||
                 DisplayDriver (e.g. ./core/screens/sh1106.py)
                     ||
               DisplayDriver.gui
                     \\
                      BasePwnhyveScreen (e.g. ./menus/flipper.py)
```

6/19/24 pls get python3-dev using apt