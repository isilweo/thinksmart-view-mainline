# Wi-Fi (QCA9379, ath10k_sdio)

## The problem

`ath10k_sdio` sometimes could not talk to the card at boot. The driver logged
-110 in one of three places:

- "timed out while setting default block size": the SDIO bus probe, before
  ath10k itself runs (located with the `DEBUG: mmc: sdio` patch on `tsv/debug`);
- "unable to reset sdio" (the reset after the firmware test);
- "Could not init hif", repeated every 10 s; `wlan0` exists but never comes up.

On one of our five units it happened in up to half of the boots, on the others
rarely. Once broken, the card stayed broken across warm reboots, because
nothing removed its supply. Rebinding the SDIO function did not help; only
pulling the plug did.

## What the stock firmware does

Codex took apart the stock WLAN stack from the device (the qcacld-2.0 module
`qca_cld_wlan.ko` and the msm-3.18 kernel). Android powers the card down
right after enumeration (`mmc_power_save_host()`). It powers the card up again
with a full SDIO reinitialization (`mmc_power_restore_host()`) only when the
WLAN driver registers, which is when Wi-Fi is switched on. Self recovery
(`gEnableSelfRecovery`) is off in the stock configuration. In practice the card
always got a full power cycle before use.

## The fix

Three commits on `tsv/device` do the same in the standard way (the first point is two commits: 1.8 V, then always on):

1. **Keep the SDHC2 I/O supply at 1.8 V and on.** L12 (SDHC2 VDD-IO) is fixed
   at 1.8 V (with the old 1.8-2.95 V range sdhci-msm started the lines at
   2.95 V) and always on, as in the stock DT (`qcom,vdd-io-always-on`).
2. **`cap-power-off-card` on SDHC2.** The MMC core runtime suspends the card
   after enumeration (vmmc L11 off, reset GPIO 75 low through `wlan_pwrseq`).
   It resumes the card with a full reinitialization just before `ath10k_sdio`
   probes. On a normal boot the card is off for about 20-35 s.

The first commit is needed. With only `cap-power-off-card`, resuming the card
failed with -EBUSY in about half of the boots on two other units, because the
host also switched L12 off.

Results with both commits: 30 warm reboots each on the affected unit and on one
of the -EBUSY units brought Wi-Fi up every time, and Bluetooth (same chip, over
UART) set up normally. Before, the affected unit had 2-7 timeouts in 15 boots.
Check it on your unit with
`cat /sys/bus/mmc/devices/mmc1:0001/power/runtime_suspended_time`: it should
be more than zero after boot.

Things that made no difference before that: `max-frequency` 100 MHz instead of
177 MHz, keeping the unused `wlan_3v3` regulator (GPIO 77) on, disabling
runtime PM of the MMC host, loading `ath10k_sdio` earlier, and an extra power
cycle of the slot when the host starts.

## Safety net

`thinksmart-view-extras` installs `wifi-guard`, a oneshot service that runs at
boot. It acts when the card is not bound to the driver 15 s after the driver
loaded, or when the driver logged -110 for the card and `wlan0` is not up after
60 s. It then unbinds and binds the MMC host (`7864900.mmc`), which also power
cycles the card, at most twice. A missing link alone (access point down) does
not trigger it. It logs to the journal as `wifi-guard` and keeps the last five
filtered kernel logs in `/var/lib/wifi-guard/`. With the DT fix it has not had
to act in our tests.

## Not solved here

Felix Kaechele mentioned work in mainline ath10k on group re-keying
disconnects and WPA3 performance. Nothing here touches that.
