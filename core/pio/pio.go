package main

// being fr most of the golang code is gonna be AI w some modifications
// i lost all knowledge of golang after my year long hiatus with it
// ball up top though

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"os/signal"
	"strings"
	"syscall"

	"github.com/akamensky/argparse"
	"github.com/stianeikeland/go-rpio/v4"
)

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

func readAndAdd(pinObject rpio.Pin, slice []bool) []bool {
	r := pinObject.Read()

	// this isn't right, but idc
	if r == rpio.High {
		slice = append(slice, true)
	} else {
		slice = append(slice, false)
	}

	return slice
}

func dump(binfile string, bigSampleMap map[rpio.Pin][]bool, pinNames map[rpio.Pin]int) {
	for pinObject, samples := range bigSampleMap {
		pinName := pinNames[pinObject]

		write(
			bits2Bytes(samples),
			binfile+"-"+strconv.Itoa(pinName)+".bin",
		)
	}
}

func SampleGen(filePath string) (<-chan string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}

	ch := make(chan string)

	go func() {
		defer file.Close()
		defer close(ch)

		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			line := scanner.Text()
			words := strings.Fields(line) // Split the line into words

			for _, word := range words {
				ch <- word // Yield each word
			}
		}

		if err := scanner.Err(); err != nil {
			fmt.Println("Error reading file:", err)
		}
	}()

	return ch, nil
}

func main() {

	// argparse init
	parser := argparse.NewParser("fastio", "this does io faster than python's IO - in an executable\nflipper mode must have --file set and must be RAW_Data only")
	samples := parser.Int("s", "samples", &argparse.Options{Required: false, Help: "samples to record", Default: -1})
	binfile := parser.String("f", "file", &argparse.Options{Required: false, Help: "file to use for operations", Default: "samples.bin"})

	pinsNum := parser.IntList("p", "pin", &argparse.Options{Required: true, Help: "pin(s) to use"})
	pmode := parser.String("m", "mode", &argparse.Options{Required: true, Help: "pin mode (rx or tx or flp (flipper))"})
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

	// create ctrl+c handler
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)

	// sample handler
	pinObjects := []rpio.Pin{}                // generate rpio.Pin objects for every pin
	pinNames := make(map[rpio.Pin]int)        // make a map so every pin has it's name, for writing
	pinSampleMap := make(map[rpio.Pin][]bool) // make another map so every pin has it's sample list
	for _, pin := range *pinsNum {
		x := rpio.Pin(pin)
		pinObjects = append(pinObjects, x)
		pinNames[x] = pin
	}

	for _, pinObject := range pinObjects {
		pinSampleMap[pinObject] = []bool{} // Initialize each key with an empty slice
	}

	go func() {
		<-sigs

		dump(*binfile, pinSampleMap, pinNames)

		rpio.Close()
		os.Exit(0)
	}()

	if *pmode == "rx" { // recieve samples
		for _, pin := range pinObjects { // make every pin an input
			pin.Input()
		}

		if *samples == -1 { // if we DONT have a set amount of samples to record
			for { // read until ctrl+c
				for pinObject, pinSlice := range pinSampleMap { // qr: key,value
					pinSampleMap[pinObject] = readAndAdd(pinObject, pinSlice)
				}
				time.Sleep(time.Duration(*ns))
			}
		} else { // if we do have a set amount of samples to record..
			for i := 0; i < *samples; i++ { // record for those samples
				for pinObject, pinSlice := range pinSampleMap { // qr: key,value
					pinSampleMap[pinObject] = readAndAdd(pinObject, pinSlice)
				}
				time.Sleep(time.Duration(*ns))
			}
		}

		dump(*binfile, pinSampleMap, pinNames)
		rpio.Close()

	} else if *pmode == "tx" { // send bytes
		fmt.Println("tx")

		pin := pinObjects[0]
		pin.Output()

		// Open the file
		file, err := os.Open(*binfile)
		if err != nil {
			fmt.Println("err")
			log.Fatal(err)
		}

		buffer := make([]byte, 1)

		// read the file byte by byte
		for {
			n, err := file.Read(buffer)
			if err != nil {
				// if eof
				if err.Error() == "EOF" {
					fmt.Println("eof")
					break
				}
				log.Fatal(err)
			}

			// no bytes were read
			if n == 0 {
				fmt.Println("no bytes")
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

				time.Sleep(time.Duration(*ns))
			}
		}

		file.Close()
		pin.Write(rpio.Low)
		rpio.Close()

	} else if *pmode == "txflp" { // send bytes, the flipper way
		fmt.Println("tx flipper")

		pin := pinObjects[0]
		pin.Output()

		samples, err := SampleGen(*binfile)
		if err != nil {
			fmt.Println("Error:", err)
			return
		}

		for sample := range samples {
			sampleInt, _ := strconv.Atoi(sample)

			if 0 > sampleInt { // negative value, pin goes down
				pin.Write(rpio.Low)
				time.Sleep(time.Duration((sampleInt * -1) * int(time.Microsecond))) // invert sample int as it's negative, then sleep
			} else { // positive value, pin goes up
				pin.Write(rpio.High)
				time.Sleep(time.Duration(sampleInt * int(time.Microsecond))) // sleep as normal
			}
		}

		pin.Write(rpio.Low)
		rpio.Close()
	}

	os.Exit(1)
}
