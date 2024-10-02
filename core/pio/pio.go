package main

// being fr most of the golang code is gonna be AI w some modifications
// i lost all knowledge of golang after my year long hiatus with it
// ball up top though

import (
	"fmt"
	"log"
	"os"
	"time"

	"os/signal"
	"syscall"

	"github.com/akamensky/argparse"
	"github.com/stianeikeland/go-rpio/v4"
)

var boolSlice = []bool{}

func bits2Bytes(boolList []bool) []byte {
	// turns bits into bytes

	byteLen := (len(boolList) + 7) / 8
	bytes := make([]byte, byteLen)

	for i, b := range boolList {
		if b {
			// Set the corresponding bit in the byte
			bytes[i/8] |= 1 << (7 - (i % 8))
		}
	}
	return bytes
}

func write(data []byte, filename string) error {
	return os.WriteFile(filename, data, 0644)
}

func byte2Bin(b byte) string {
	return fmt.Sprintf("%08b", b)
}

func readAndAdd(pin rpio.Pin, ns int) {
	r := pin.Read()

	// this isn't right, but idc
	if r == rpio.High {
		boolSlice = append(boolSlice, true)
	} else {
		boolSlice = append(boolSlice, false)
	}

	time.Sleep(time.Duration(ns))
}

func dump(binfile string) {
	l := bits2Bytes(boolSlice)

	write(l, binfile)
}

func main() {

	// argparse init
	parser := argparse.NewParser("fastio", "this does io faster than python's IO - in an executable")
	samples := parser.Int("s", "samples", &argparse.Options{Required: false, Help: "samples to record", Default: -1})
	binfile := parser.String("o", "output", &argparse.Options{Required: false, Help: "output file", Default: "samples.bin"})

	pinNum := parser.Int("p", "pin", &argparse.Options{Required: true, Help: "pin to use"})
	pmode := parser.String("m", "mode", &argparse.Options{Required: true, Help: "pin mode (rx or tx)"})
	ns := parser.Int("n", "sleep", &argparse.Options{Required: false, Help: "nanoseconds to sleep between each read (already 500ns delay between each read)", Default: 7500})

	err := parser.Parse(os.Args)
	if err != nil {
		// In case of error print error and print usage
		// This can also be done by passing -h or --help flags
		fmt.Print(parser.Usage(err))
		os.Exit(4)
	}

	// Open and map memory to access gpio, check for errors
	if err := rpio.Open(); err != nil {
		fmt.Println(err)
		os.Exit(4)
	}

	// create ctrl+c
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)

	go func() {
		<-sigs

		dump(*binfile)

		os.Exit(0)
	}()

	// Unmap gpio memory when done
	defer rpio.Close()

	pin := rpio.Pin(*pinNum)

	fmt.Println("1")
	if *pmode == "rx" { // recieve samples
		pin.Input()

		if *samples == -1 { // if we DONT have a set amount of samples to record
			for { // read until ctrl+c
				readAndAdd(pin, *ns)
			}
		} else { // if we do have a set amount of samples to record..
			for i := 0; i < *samples; i++ { // record for those samples
				readAndAdd(pin, *ns)
			}
		}
	} else if *pmode == "tx" { // send bytes
		pin.Output()

		// Open the file
		file, err := os.Open(*binfile)
		if err != nil {
			log.Fatal(err)
		}
		defer file.Close()

		buffer := make([]byte, 1)

		// read the file byte by byte
		for {
			n, err := file.Read(buffer)
			if err != nil {
				// if eof
				if err.Error() == "EOF" {
					break
				}
				log.Fatal(err)
			}

			// no bytes were read
			if n == 0 {
				break
			}

			bin := byte2Bin(buffer[0])

			for i := 0; i < len(bin); i++ {
				bit := bin[i]

				if bit == byte('1') {
					pin.Write(rpio.High)
				} else {
					pin.Write(rpio.Low)
				}
			}
		}
	}

	dump(*binfile)
	os.Exit(1)
}
