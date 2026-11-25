# Sensors and touch

| Part | Status |
|---|---|
| Proximity (VCNL4200) | Enabled; the IR LED no longer runs hot. A hand at 5-10 cm gives about 800-1800 counts. The background is 0-3 with a clean window but up to about 60 under incandescent lamps, so wake thresholds below that latch "near". |
| Ambient light (VCNL4200) | Works, but the window has a narrow field of view straight ahead: it reads light from in front of the screen, not the room. Rough check against a phone: 15 lx gives 3, 158 lx gives 91, 260 lx gives 255 at 400 ms integration time. Good for dark/dim/bright, not for lux. |
| Accelerometer BMA253 | Mount matrix added; iio-sensor-proxy reports the right orientation. |
| Touch | Both FT8201 and HX83100A nodes enabled; the fitted one probes. The other one fails with -16, which is harmless. |

Both sensors sit on a GPIO I²C bus. The base DT used the wrong pins (14/15)
for it; it is on GPIO 6/7. The VCNL4200 LED settings (8T duty, two pulses,
75 mA, 1/1280) come from the stock ADSP sensor driver.

Review notes on the VCNL4200 patches (sample delay after an IIO integration
time change, and threshold events after autosuspend) are in
[upstream-status.md](upstream-status.md).
