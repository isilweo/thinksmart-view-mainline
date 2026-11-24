# Lenovo ThinkSmart View on a mainline-based kernel: camera, Venus, sensors

Independent community project for the Lenovo ThinkSmart View CD-18781Y. The
manufacturers mentioned here do not sponsor or endorse this project.

Patches that make the front camera, the Venus hardware video encoder and
decoder, and the proximity/light sensor work on the ThinkSmart View
(APQ8053/MSM8953) with postmarketOS. Tested on five CD-18781Y units.

I used Claude (an AI coding assistant) to help develop and document my
changes. The kernel series and the debug patch record that assistance with
`Assisted-by:`. Third-party contributions are credited below. The test
results describe the configurations I tested. The commits have no
`Signed-off-by:` yet: before upstream submission, each human contributor or
submitter must be able to certify their contribution under the
[Developer's Certificate of Origin](https://developercertificate.org/) and add
their own `Signed-off-by:` where applicable.

**How this was made.** The patches were developed in interactive sessions
with Claude Code (Anthropic, model claude-opus-5-5) working on the
tablets over SSH: it read the vendor device tree and logs, wrote the code,
comments and changelogs, and built and tested each kernel on the device
while I directed the work, checked the results and decided what to keep.
The CAMSS rework (patches 0013-0020) was reviewed with Codex (OpenAI,
gpt-6.2-astra), which found an off-by-one in the UB split, a missing
height limit, a burst length difference on MSM8916/MSM8939 and a probe
behaviour change on MSM8939; those were fixed before testing. Testing:
`checkpatch.pl --strict`, kernel builds without warnings in the changed
files, and on the device libcamera `cam`, GStreamer pipelines and the
sensor sysfs interfaces.

**No firmware is included.** The installation uses firmware already present
on your device (Venus, ADSP and Wi-Fi firmware from its own `modem` partition,
linked by `msm-firmware-loader` in postmarketOS) and an amplifier DSP file
supplied separately by the postmarketOS `firmware-qcom-msm8953` package. Keep
partition dumps private. This repository grants no rights to redistribute
those files.

## What works (tested on our units)

| Part | Status |
|---|---|
| Front camera Samsung S5KC505A | `ccs` driver + quirk, CAMSS on MSM8953 (own CSIPHY and VFE clock tables, VBIF described in the DT, per-SoC QoS/DS and UB size, write master geometry in frame based mode), libcamera SoftISP (GPU debayer): 1304x980 at 30 fps without dropped frames, using about one CPU core. Colour matrices calibrated on a SpyderCheckr 24, used at half strength (see below). |
| Venus H.264 encoder | `v4l2h264enc`: bitrate control works (1 Mb/s target gives 931-959 kb/s), 640x480 at 30 fps costs about 1.3 of 8 cores including the camera. Width must be a multiple of 16. |
| Venus H.264 decoder | `v4l2h264dec`: 1280x960 at about 238 fps using 0.1 core. A stream that is cut off no longer hangs the SoC (that fix is so far tested on one unit; the others still run the version before it). |
| Venus H.265 decoder | `v4l2h265dec`: a 960x720 20 fps RTSP stream at about 6% of one core, see below. |
| Proximity (VCNL4200) | Enabled, IR LED no longer runs hot. A hand at 5-10 cm gives about 800-1800 counts. Background is 0-3 with a clean window but up to about 60 under incandescent lamps, so wake thresholds below that latch "near". |
| Ambient light (VCNL4200) | Works, but the window has a narrow field of view straight ahead: it reads light from in front of the screen, not the room. Rough check against a phone: 15 lx gives 3, 158 lx gives 91, 260 lx gives 255 at 400 ms integration time. Good for dark/dim/bright, not for lux. |
| Accelerometer BMA253 | Mount matrix added; iio-sensor-proxy reports the right orientation. |
| Touch | Both FT8201 and HX83100A nodes enabled; the fitted one probes. |
| Speaker TAS5782M | Uses Felix Kaechele's TAS5782M support (see `kernel/third-party/`). |

Not done: echo cancellation, beamforming with the two DMICs.

**Camera colour.** `libcamera/s5kc505a.yaml` has colour matrices fitted on a
Datacolor SpyderCheckr 24 under an Elgato Key Light at 2900, 4000, 5000 and
6500 K, flat-fielded with the grey back of the chart. Median CIE76 error after
correction is 3.9-5.8 (`libcamera/s5kc505a-full-ccm.yaml`). In live use the
soft ISP of libcamera 0.7.1 turns clipped highlights pink with the full
matrices and amplifies grey-world AWB errors, so the default file blends them
50/50 with the identity. The soft ISP AGC has no manual exposure, exposure
compensation or highlight protection, so bright objects on a dark background
clip.

The two DMICs are quiet: we apply a software gain of 4 (`volume volume=4.0`)
before encoding.

## Layout

```
kernel/series/       28 patches, one change each (git format-patch)
kernel/debug/        ramoops + Venus fw_debug parameter, not for upstream
kernel/third-party/  TAS5782M support adapted from Felix Kaechele's tree
kernel/config.fragment
libcamera/           S5KC505A tuning files (half-strength and full colour matrices)
LICENSES/            full license texts
```

## Base and how to build

Step by step from the stock firmware (EDL backup, image, flashing, first
boot): [INSTALL.md](INSTALL.md).

The patches apply to the msm8953-mainline kernel
`https://github.com/msm8953-mainline/linux` tag `v7.0.9-r0`, which postmarketOS
v26.06 packages as `linux-postmarketos-qcom-msm8953`. They are not rebased
onto torvalds/master yet. Only the final state of the series was built and
tested; the intermediate commits were not built one by one.

In pmaports (v26.06):

1. copy `kernel/series/*.patch` (and `kernel/third-party/tas5782m-support.diff`
   for the speaker) into `device/community/linux-postmarketos-qcom-msm8953/`,
   add them to `source=` and apply `kernel/config.fragment`;
2. libcamera (`temp/libcamera`, 0.7.1): add the S5KC505A sensor helper from
   rebrch/tsv-nura,
   [`camera/libcamera-pmaports/0004-ipa-libipa-add-s5kc505a.patch`](https://github.com/rebrch/tsv-nura/blob/32e84a9f4bf5cbbefc2135b1bf5b57b37e036ae3/camera/libcamera-pmaports/0004-ipa-libipa-add-s5kc505a.patch)
   (we use it unchanged apart from a comment), and `libcamera/s5kc505a.yaml`
   to the tuning files (installed as `/usr/share/libcamera/ipa/simple/s5kc505a.yaml`);
3. `soc-qcom-msm8953`: raise the UCM `provider_priority` (we use 10), otherwise
   apk may pick `alsa-ucm-conf-unisoc-ums9230`;
4. `pmbootstrap checksum`, `pmbootstrap build`.

Bootloader: lk2nd from Felix Kaechele (`https://felix.kaechele.ca/projects/thinksmart`),
which enables touch; the stock pmOS lk2nd image did not for us.

## Notes for using Venus

- Stop GStreamer pipelines with EOS (`gst-launch-1.0 -e` and SIGINT, or
  `timeout -s INT`). Killing the decoder mid-stream used to hang the SoC; the
  last vdec patch fixes the case we hit, but EOS is still the safe way.
- The TrustZone watchdog resets the board about 45 s after a hard hang; there
  is no `/dev/watchdog` in Linux.
- Encoder pipeline we use (camera to RTP):
  ```
  libcamerasrc ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=NV12
    ! v4l2h264enc extra-controls="controls,video_bitrate=1000000,video_gop_size=30"
    ! 'video/x-h264,level=(string)4,profile=(string)baseline' ! h264parse config-interval=-1
    ! rtph264pay pt=96 mtu=1200 ! udpsink host=... port=5000
  ```
  The NV12 conversion runs on the CPU; that is what limits us to 640x480.
- Decoder: `rtph264depay ! h264parse ! v4l2h264dec ! glimagesink`
  (`waylandsink` gave a black screen in cage for us). We only tested streams
  encoded without B-frames.
- `pipewiresrc` together with the camera in one pipeline lost its clock for us;
  run audio and video as separate processes, `pipewiresrc provide-clock=false`.

## Playing camera streams (RTSP, H.265)

A UniFi Protect doorbell stream (H.265, 960x720 at 20 fps) plays on the
tablets through Venus. Working pipeline:

```
rtspsrc location=rtsps://... protocols=tcp
  ! rtph265depay ! video/x-h265,stream-format=byte-stream,alignment=au
  ! v4l2h265dec ! videoconvert n-threads=4 ! video/x-raw,format=RGBA ! appsink
```

- Decoding alone costs about 6% of one core; with the RGBA conversion about
  24%, no dropped frames (about 19 fps measured on three units). The first
  frame arrives about 1.1 s after the pipeline starts.
- Protect uses a self-signed certificate. We currently connect with
  certificate validation turned off (`tls-validation-flags=0`), which means
  the client does not authenticate the camera. A better setup is to make
  `rtspsrc` trust that certificate through its `tls-database` property (set
  from code); we have not tried that yet.
- Use the explicit chain: `decodebin` after `rtspsrc` failed on the tablet with
  "Internal data stream error" (caps negotiation with the H.265 depayloader).
- `h265parse` is not needed: `rtph265depay` already outputs byte-stream in
  whole access units. That matters because `h265parse` lives in
  gst-plugins-bad, which a fresh image does not have.
- When an element is missing, `gst_parse_launch()` returns a partial pipeline
  together with a recoverable error instead of NULL. Code that only checks for
  NULL then waits forever without frames and without an error; check the
  `GError`.
- UniFi Protect: drop `?enableSrtp` from the stream URL. With SRTP the
  depayloader reports "The stream is in the wrong format".
- Re-encoding the frames to JPEG only reaches about 7 fps, so it is not an
  option for live video.

## Known issues

- The Adreno 506 (freedreno) can hang: the kernel log repeats `hangcheck
  detected gpu lockup` every second, the display client sits in D state and
  `reboot` hangs. There is no hardware watchdog in Linux (`CONFIG_WATCHDOG` off,
  no watchdog node in the DT); only kernel panics reboot by themselves
  (`panic=120`). Our workaround is a userspace guard that watches `/dev/kmsg`
  and does a SysRq sync + reboot after 60 s of lockup, at most 3 times per
  hour. A proper watchdog in the DT would be better.
- After long audio sessions the ADSP sometimes stops (`q6asm` error 9, no
  sound); a reboot fixes it.

## Where the values come from

The individual patch descriptions identify the source of board wiring,
operating parameters and register sequences. Values marked "stock" were read
from the original Lenovo software on the device: its device tree (supplies,
GPIOs, QoS settings), the ADSP sensor driver (VCNL4200 LED settings) and the
camera library `libmmcamera_s5kc505a.so` (the S5KC505A register tables in
patch 0011, which are also published in rebrch/tsv-nura). Measurements on our
units are identified separately.

## Credits

- Felix Kaechele: the ThinkSmart View device tree, lk2nd, and the TAS5782M
  support (`kernel/third-party/`).
- rebrch/tsv-nura (reichbc): the S5KC505A libcamera helper and an independent
  S5KC505A driver with the same register tables
  (https://github.com/rebrch/tsv-nura).
- msm8953-mainline and postmarketOS maintainers.

## License

- Kernel driver changes (`kernel/series/0001`-`0013`, `0016`-`0023`, the C
  part of `kernel/debug/`, `kernel/third-party/`): GPL-2.0-only, see
  `LICENSES/GPL-2.0-only.txt`.
- The device tree binding change (`kernel/series/0014`):
  GPL-2.0-only OR BSD-2-Clause, like the binding it changes. See
  `LICENSES/GPL-2.0-only.txt` and `LICENSES/BSD-2-Clause.txt`.
- Device tree changes: `msm8953.dtsi` (`kernel/series/0015`, original
  copyright (c) 2022 The Linux Foundation) and `apq8053-lenovo-cd-18781y.dts`
  (`kernel/series/0024`-`0028` and the DTS part of `kernel/debug/`, original
  copyright (c) 2024 Felix Kaechele): BSD-3-Clause, like the files they
  change. See `LICENSES/BSD-3-Clause.txt`.
- `README.md`, `INSTALL.md`, `kernel/config.fragment` and the
  `libcamera/*.yaml` tuning files: CC0-1.0, see `LICENSES/CC0-1.0.txt`.
