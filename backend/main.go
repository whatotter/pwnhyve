package main

import (
	"fmt"
	"time"

	"github.com/stianeikeland/go-rpio/v4"
)

var RST_PIN = rpio.Pin(25)
var DC_PIN = rpio.Pin(24)
var CS_PIN = rpio.Pin(8)
var BL_PIN = rpio.Pin(18)

func spiCommand(command byte) {
	DC_PIN.Low()
	rpio.SpiTransmit(command)
}

func reset() {
	// reset display
	RST_PIN.High()
	time.Sleep(100)
	RST_PIN.Low()
	time.Sleep(100)
	RST_PIN.High()
	time.Sleep(100)
}

func initDisplay() {
	reset()

	rpio.SpiTransmit(0xAE) // --turn off oled panel
	rpio.SpiTransmit(0x02) // ---set low column address
	rpio.SpiTransmit(0x10) // ---set high column address
	rpio.SpiTransmit(0x40) // --set start line address  Set Mapping RAM Display Start Line (0x00~0x3F)
	rpio.SpiTransmit(0x81) // --set contrast control register
	rpio.SpiTransmit(0xA0) // --Set SEG/Column Mapping
	rpio.SpiTransmit(0xC0) // Set COM/Row Scan Direction
	rpio.SpiTransmit(0xA6) // --set normal display
	rpio.SpiTransmit(0xA8) // --set multiplex ratio(1 to 64)
	rpio.SpiTransmit(0x3F) // --1/64 duty
	rpio.SpiTransmit(0xD3) // -set display offset    Shift Mapping RAM Counter (0x00~0x3F)
	rpio.SpiTransmit(0x00) // -not offset
	rpio.SpiTransmit(0xd5) // --set display clock divide ratio/oscillator frequency
	rpio.SpiTransmit(0x80) // --set divide ratio, Set Clock as 100 Frames/Sec
	rpio.SpiTransmit(0xD9) // --set pre-charge period
	rpio.SpiTransmit(0xF1) // Set Pre-Charge as 15 Clocks & Discharge as 1 Clock
	rpio.SpiTransmit(0xDA) // --set com pins hardware configuration
	rpio.SpiTransmit(0x12)
	rpio.SpiTransmit(0xDB) // --set vcomh
	rpio.SpiTransmit(0x40) // Set VCOM Deselect Level
	rpio.SpiTransmit(0x20) // -Set Page Addressing Mode (0x00/0x01/0x02)
	rpio.SpiTransmit(0x02) //
	rpio.SpiTransmit(0xA4) //  Disable Entire Display On (0xa4/0xa5)
	rpio.SpiTransmit(0xA6) //  Disable Inverse Display On (0xa6/a7)
	time.Sleep(100)
	rpio.SpiTransmit(0xAF) // --turn on oled panel
}

func showImg(data byte) {
	width := 128
	//height := 64

	for page := 0; page < 8; page++ {
		fmt.Println(page)

		rpio.SpiTransmit(byte(0xB0 + page)) // set page addr
		rpio.SpiTransmit(0x02)              // low column address
		rpio.SpiTransmit(0x10)              // high column address
		DC_PIN.High()                       // make display start reading

		for i := 0; i < width; i++ {
			// [~pBuf[i+self.width*page]]
			rpio.SpiTransmit(data)
		}
	}
}

func main() {
	if err := rpio.Open(); err != nil {
		panic(err)
	}

	if err := rpio.SpiBegin(rpio.Spi0); err != nil {
		panic(err)
	}

	rpio.SpiChipSelect(0) // Select CE0 slave
	fmt.Println("opened CE0")

	initDisplay()

	fmt.Println("inited")

	fmt.Println("this should be a full color (either black or white)")
	showImg(0xFF)
	time.Sleep(5 * time.Second)
	fmt.Println("this should be a different color (also either black or white, but not the same as before)")
	showImg(0x00)
	time.Sleep(5 * time.Second)

	fmt.Println("please report your findings to the github repo, as of 2/20/2024 my oled is broken and i cannot check myself - thanks :)")
}
