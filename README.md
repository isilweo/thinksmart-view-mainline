# Lenovo ThinkSmart View on a mainline-based kernel

Independent community project for the Lenovo ThinkSmart View CD-18781Y
(APQ8053/MSM8953). The manufacturers mentioned here do not sponsor or endorse
this project.

postmarketOS on the ThinkSmart View with a working front camera, the Venus
hardware video encoder and decoder, proximity/light sensor, full-duplex audio
with echo cancellation, a hardware watchdog and reliable Wi-Fi. We run it on
five CD-18781Y units; the notes say how many units each result was measured
on.

- **Kernel source:** [isilweo/linux](https://github.com/isilweo/linux), a fork
  of [msm8953-mainline/linux](https://github.com/msm8953-mainline/linux).
  Branch `tsv/device` (one commit per change on `v7.0.9-r0`), `tsv/debug`
  (plus local debug commits), tag `tsv-v7.0.9-r120` (what runs on our tablets).
- **This repository:** how to build and install it, a postmarketOS overlay in
  `pmaports/`, and notes per topic in `docs/`.

## What works

| Part | Status | Notes |
|---|---|---|
| Front camera S5KC505A | 1304x980 at 30 fps, libcamera 0.8.0 SoftISP, calibrated colour | [docs/camera.md](docs/camera.md) |
| Venus H.264 encoder, H.264/H.265 decoder | Hardware encode and decode, RTSP doorbell streams | [docs/venus.md](docs/venus.md) |
| Speaker, microphones | TAS5782M speaker; full duplex with WebRTC echo cancellation (20/20 cycles on one unit) | [docs/audio.md](docs/audio.md) |
| Proximity and light (VCNL4200), accelerometer, touch | Working; light reads only straight ahead | [docs/sensors.md](docs/sensors.md) |
| Wi-Fi (QCA9379) | No boot failures in 30 warm reboots each on two units (it used to fail in up to half of the boots on one) | [docs/wifi.md](docs/wifi.md) |
| APSS watchdog | systemd feeds `/dev/watchdog0` | [docs/watchdog.md](docs/watchdog.md) |

Not done: beamforming with the two DMICs. The kernel changes are not upstream
yet; a review of the whole series found bugs, which are fixed since r80, r93 and r120, and
points the maintainers would still raise: see
[docs/upstream-status.md](docs/upstream-status.md).

## Install

Step by step from the stock firmware (EDL backup, build, flashing, first
boot): [INSTALL.md](INSTALL.md). Bootloader: lk2nd from Felix Kaechele
(`https://felix.kaechele.ca/projects/thinksmart`), which enables touch; the
stock pmOS lk2nd image did not for us.

**No firmware is included.** The installation uses firmware already present
on your device (Venus, ADSP and Wi-Fi firmware from its own `modem` partition,
linked by `msm-firmware-loader` in postmarketOS) and an amplifier DSP file
supplied separately by the postmarketOS `firmware-qcom-msm8953` package. Keep
partition dumps private. This repository grants no rights to redistribute
those files.

## Layout

```
INSTALL.md
docs/                    notes per topic, upstream status
pmaports/                postmarketOS overlay (pmaports v26.06):
  device/community/linux-postmarketos-qcom-msm8953/   kernel 7.0.9-r120: patch from isilweo/linux + config
  device/community/thinksmart-view-extras/           Wi-Fi boot guard, watchdog setting, echo cancellation
  temp/libcamera/                                      libcamera 0.8.0 with the S5KC505A helper and tuning
  temp/pipewire/                                       PipeWire 1.6.11 (Alpine edge) for libcamera 0.8 on v26.06
libcamera/               S5KC505A tuning files (0.8.0 and 0.7.x) for manual use
LICENSES/                full license texts
```

## How this was made

I used AI coding assistants to develop and document these changes, and the
commits record that with `Assisted-by:`. Claude Code (Anthropic,
claude-opus-5-5) worked on the tablets over SSH. It read the vendor device
tree and logs, wrote code, comments and changelogs, and built and tested each
kernel on the device. I directed the work, checked the results and decided
what to keep. Codex (OpenAI, gpt-6.2-astra) wrote the q6asm-dai fix and the
watchdog patches, took apart the stock WLAN stack that led to the Wi-Fi fix,
and reviewed the CAMSS rework, the Wi-Fi guard and the whole series. Testing:
`checkpatch.pl --strict`, kernel builds without warnings in the changed files,
and on the device libcamera `cam`, GStreamer pipelines, sensor sysfs
interfaces and series of warm reboots. The commits have no `Signed-off-by:`
yet; see [docs/upstream-status.md](docs/upstream-status.md).

## Credits

- Felix Kaechele: the ThinkSmart View device tree, lk2nd, and the TAS5782M
  support the speaker commit is adapted from.
- rebrch/tsv-nura (reichbc): the S5KC505A libcamera helper (fetched by the
  libcamera package here) and an independent S5KC505A driver with the same
  register tables (https://github.com/rebrch/tsv-nura).
- msm8953-mainline and postmarketOS maintainers.

## License

- The kernel patch in `pmaports/device/community/linux-postmarketos-qcom-msm8953/`
  and the commits in isilweo/linux change Linux kernel files. Each change is
  under the license of the file it changes: GPL-2.0-only for most drivers,
  GPL-2.0-or-later for `drivers/mmc/core/sdio_bus.c`, GPL-2.0-only OR
  BSD-2-Clause for the device tree bindings, and BSD-3-Clause for
  `msm8953.dtsi` (original copyright (c) 2022 The Linux Foundation) and
  `apq8053-lenovo-cd-18781y.dts` (original copyright (c) 2024 Felix
  Kaechele). See `LICENSES/`.
- The kernel and libcamera package recipes (APKBUILDs) come from postmarketOS
  pmaports and are GPL-3.0, like pmaports; see `LICENSES/GPL-3.0.txt`. The
  kernel config is the pmaports `config-postmarketos-qcom-msm8953.aarch64` of
  v26.06 with the APSS watchdog options enabled. The PipeWire recipe in
  `pmaports/temp/pipewire/` is the Alpine edge aports recipe (Alpine's terms)
  with our change for v26.06; its patch is PipeWire code (MIT).
- The two libcamera patches in `pmaports/temp/libcamera/` are libcamera code by
  their respective authors, carried by pmaports, under the licenses of the
  files they touch: LGPL-2.1-or-later (see `LICENSES/LGPL-2.1-or-later.txt`),
  GPL-2.0-or-later for a test, BSD-2-Clause for Raspberry Pi code.
- The libcamera tuning files (`libcamera/*.yaml` and the `*.yaml` in
  `pmaports/temp/libcamera/`) are CC0-1.0, as their headers say.
- `README.md`, `INSTALL.md`, `docs/` and everything in
  `pmaports/device/community/thinksmart-view-extras/`: CC0-1.0, see
  `LICENSES/CC0-1.0.txt`.
