# Watchdog and hangs

## APSS watchdog

The commits "dt-bindings: watchdog: qcom-wdt: Document MSM8953 APSS watchdog"
and "arm64: dts: qcom: msm8953: Describe the APSS watchdog" add the watchdog at
0xb017000: `qcom,apss-wdt-msm8953` with the `qcom,kpss-wdt` fallback, bark and
bite on SPI 3 and 4, and `sleep_clk`. The kernel needs `CONFIG_QCOM_WDT=y`,
which the config in `pmaports/` has.

`thinksmart-view-extras` installs
`/usr/lib/systemd/system.conf.d/80-apss-watchdog.conf`:

```
[Manager]
WatchdogDevice=/dev/watchdog0
RuntimeWatchdogSec=30s
RebootWatchdogSec=30s
```

The driver allows at most 31 s, so `RebootWatchdogSec=2min` is rejected
("Failed to set watchdog hardware timeout to 2min: Invalid argument").

With idle CPUs, the reset comes later than programmed: about 115 s for a 30 s
timeout and 56 s for 10 s. Our guess is that the counter pauses while all
cores are in power collapse. We have not verified this. A bite test (holding
`/dev/watchdog0` open without feeding it) did reset the tablet.

## GPU hangs

The Adreno 506 (freedreno) can hang. The kernel log then repeats
`hangcheck detected gpu lockup` every second, the display client sits in D
state and `reboot` hangs. We saw it once in weeks of use. Our workaround is a
userspace guard that watches `/dev/kmsg` and does a SysRq sync + reboot after
60 s of lockup, at most 3 times per hour. A hang that stops PID 1 is now also
caught by the watchdog.

The TrustZone watchdog resets the board about 45 s after a hard hang of the
whole SoC, independent of Linux.
