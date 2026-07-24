package main

import (
	"bufio"
	"fmt"
	"io"
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

var spinUntil func(time.Time)

func init() {
	spinUntil = func(target time.Time) {
		for time.Now().Before(target) {
		}
	}
}

type pinSample struct {
	pin     rpio.Pin
	name    int
	samples []bool
}

func bits2Bytes(boolList []bool) []byte {
	byteLen := (len(boolList) + 7) / 8
	bytes := make([]byte, byteLen)

	for i, b := range boolList {
		if b {
			bytes[i/8] |= 1 << (7 - (i % 8))
		}
	}
	return bytes
}

func write(data []byte, filename string) error {
	return os.WriteFile(filename, data, 0644)
}

func dump(binfile string, pinSamples []pinSample) {
	for _, ps := range pinSamples {
		write(
			bits2Bytes(ps.samples),
			binfile+"-"+strconv.Itoa(ps.name)+".bin",
		)
	}
}

func readAndAdd(ps *pinSample) {
	r := ps.pin.Read()
	if r == rpio.High {
		ps.samples = append(ps.samples, true)
	} else {
		ps.samples = append(ps.samples, false)
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
			words := strings.Fields(line)
			for _, word := range words {
				ch <- word
			}
		}

		if err := scanner.Err(); err != nil {
			fmt.Println("Error reading file:", err)
		}
	}()

	return ch, nil
}

func main() {

	parser := argparse.NewParser("fastio", "this does io faster than python's IO - in an executable\nflipper mode must have --file set and must be RAW_Data only")
	samples := parser.Int("s", "samples", &argparse.Options{Required: false, Help: "samples to record", Default: -1})
	binfile := parser.String("f", "file", &argparse.Options{Required: false, Help: "file to use for operations", Default: "samples.bin"})

	pinsNum := parser.IntList("p", "pin", &argparse.Options{Required: true, Help: "pin(s) to use"})
	pmode := parser.String("m", "mode", &argparse.Options{Required: true, Help: "pin mode (rx or tx or flp (flipper))"})
	ns := parser.Int("n", "sleep", &argparse.Options{Required: false, Help: "nanoseconds to sleep between each read (already 500ns delay between each read)", Default: 7500})

	err := parser.Parse(os.Args)
	if err != nil {
		fmt.Print(parser.Usage(err))
		os.Exit(4)
	}

	if err := rpio.Open(); err != nil {
		fmt.Println(err)
		os.Exit(4)
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	pinSamples := make([]pinSample, len(*pinsNum))
	for i, pin := range *pinsNum {
		pinSamples[i] = pinSample{
			pin:     rpio.Pin(pin),
			name:    pin,
			samples: nil,
		}
	}

	if *samples > 0 {
		for i := range pinSamples {
			pinSamples[i].samples = make([]bool, 0, *samples)
		}
	}

	go func() {
		<-sigs

		dump(*binfile, pinSamples)

		rpio.Close()
		os.Exit(0)
	}()

	if *pmode == "rx" {
		for i := range pinSamples {
			pinSamples[i].pin.Input()
		}

		if *samples == -1 {
			for {
				for i := range pinSamples {
					readAndAdd(&pinSamples[i])
				}
				time.Sleep(time.Duration(*ns))
			}
		} else {
			start := time.Now()
			period := time.Duration(*ns)
			for i := 0; i < *samples; i++ {
				for j := range pinSamples {
					readAndAdd(&pinSamples[j])
				}
				spinUntil(start.Add(time.Duration(i+1) * period))
			}
		}

		dump(*binfile, pinSamples)
		rpio.Close()

	} else if *pmode == "tx" {
		fmt.Println("tx")

		pin := pinSamples[0].pin
		pin.Output()

		file, err := os.Open(*binfile)
		if err != nil {
			log.Fatal(err)
		}
		defer file.Close()

		buffer := make([]byte, 4096)
		period := time.Duration(*ns)

		for {
			n, err := file.Read(buffer)
			if n > 0 {
				for i := 0; i < n; i++ {
					b := buffer[i]
					for j := 7; j >= 0; j-- {
						if b&(1<<j) != 0 {
							pin.Write(rpio.High)
						} else {
							pin.Write(rpio.Low)
						}
						time.Sleep(period)
					}
				}
			}
			if err != nil {
				if err == io.EOF {
					break
				}
				log.Fatal(err)
			}
		}

		pin.Write(rpio.Low)
		rpio.Close()

	} else if *pmode == "txflp" {
		fmt.Println("tx flipper")

		pin := pinSamples[0].pin
		pin.Output()

		samples, err := SampleGen(*binfile)
		if err != nil {
			fmt.Println("Error:", err)
			return
		}

		for sample := range samples {
			sampleInt, _ := strconv.Atoi(sample)

			if 0 > sampleInt {
				pin.Write(rpio.Low)
				time.Sleep(time.Duration(sampleInt * -1 * int(time.Microsecond)))
			} else {
				pin.Write(rpio.High)
				time.Sleep(time.Duration(sampleInt * int(time.Microsecond)))
			}
		}

		pin.Write(rpio.Low)
		rpio.Close()
	}

	os.Exit(0)
}
