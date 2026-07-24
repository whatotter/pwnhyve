//go:build cgo && (arm || arm64)
// +build cgo,arm cgo,arm64

package main

/*
#include <stdint.h>

static inline uint64_t read_cycle_counter() {
#if defined(__aarch64__)
    uint64_t cnt;
    __asm__ volatile("mrs %0, cntvct_el0" : "=r"(cnt));
    return cnt;
#else
    uint32_t cc;
    __asm__ volatile("mrc p15, 0, %0, c9, c13, 0" : "=r"(cc));
    return (uint64_t)cc;
#endif
}
*/
import "C"
import "time"

var cpuKHz uint64 = 0
var baseCycles uint64 = 0
var baseTime time.Time

func init() {
	baseCycles = uint64(C.read_cycle_counter())
	baseTime = time.Now()
	time.Sleep(50 * time.Millisecond)
	elapsed := uint64(C.read_cycle_counter()) - baseCycles
	cpuKHz = elapsed / 50

	spinUntil = func(target time.Time) {
		deltaNS := target.Sub(baseTime).Nanoseconds()
		if deltaNS <= 0 {
			return
		}
		targetCycles := baseCycles + (cpuKHz*uint64(deltaNS))/1000000
		for uint64(C.read_cycle_counter()) < targetCycles {
		}
	}
}
