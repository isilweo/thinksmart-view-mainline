# Installing postmarketOS on a ThinkSmart View

This is the path we used on five CD-18781Y units, from the stock Teams
firmware (Android 8.1) to postmarketOS v26.06 with systemd and the patched
kernel. It keeps the stock partitions (modem, persist, calibration) and puts
lk2nd on `boot` and the whole system image on `userdata`.

> **Warning.** Flashing replaces the boot image and erases the contents of
> `userdata`. Back up each device separately before writing, verify the
> backup checksums and keep the backup private. Recovery depends on working
> hardware, EDL access and a compatible programmer. A failed flash can leave
> the device unusable even if you have a backup. Check the manufacturer's
> warranty terms before proceeding. You do this at your own risk.

## 0. What you need

- A Linux machine or a Mac with Docker (we built in an arm64 Alpine container
  on an Apple Silicon Mac; any host that runs pmbootstrap works).
- [bkerler/edl](https://github.com/bkerler/edl) and `fastboot`.
- A compatible MSM8953 eMMC Firehose programmer that you are authorised to use
  with this device. The commands below use the filename
  `prog_emmc_firehose_8953_ddr.mbn`. Obtain the programmer separately from an
  authorised source; it is not included here.
- A USB 2 hub between the computer and the tablet. Over USB 3 we got Sahara
  errors.
- lk2nd from Felix Kaechele: `https://felix.kaechele.ca/projects/thinksmart`
  (we use `lk2nd-lenovo-cd-18781y-20240628.img`). The stock postmarketOS lk2nd
  image did not enable touch for us.

## 1. Full eMMC backup over EDL (every unit separately)

`persist`, `modemst1`, `modemst2`, `fsg` and `devinfo` are unique per unit
(Wi-Fi MAC, calibration). Keep a full backup of each unit before writing
anything. On our units EDL was always reachable with the buttons.

1. Unplug power. Hold **Vol+ and Vol-** and plug the power in. The screen stays
   black and the host sees `05c6:9008` (Qualcomm HS-USB QDLoader).
2. Read the GPT and dump all partitions:
   ```bash
   L="--loader=prog_emmc_firehose_8953_ddr.mbn --memory=emmc"
   edl printgpt $L
   edl rl backup/partitions $L --genxml
   ```
   In zsh, pass the options directly instead of `$L` (zsh does not split it, the
   programmer is not loaded and the tablet stays in Sahara). Reading takes
   about 4 minutes at ~33 MB/s. Write down checksums of the files.
3. To restore later use the generated `rawprogram0.xml`, **only on the same
   unit** (userdata is encrypted with a key bound to the device).

## 2. Build the image

pmbootstrap (git main) with pmaports branch `v26.06`.

1. Copy the overlay from this repository into pmaports, replacing the
   packages of the same name:
   ```bash
   cp -r pmaports/device/community/linux-postmarketos-qcom-msm8953 \
         pmaports/device/community/thinksmart-view-extras \
         "$(pmbootstrap config aports)"/device/community/
   cp -r pmaports/temp/libcamera pmaports/temp/pipewire "$(pmbootstrap config aports)"/temp/
   ```
   - `linux-postmarketos-qcom-msm8953` (7.0.9-r39) is the postmarketOS kernel
     package with one patch, `git diff v7.0.9-r0 tsv-v7.0.9-r39` of
     [isilweo/linux](https://github.com/isilweo/linux), and the matching
     config (APSS watchdog included);
   - `libcamera` is libcamera 0.8.0 (pmaports master `temp/libcamera`) with the
     S5KC505A helper from rebrch/tsv-nura and our tuning file. If the build runs
     out of memory in a container, build without the Python bindings
     (`-Dpycamera=disabled`);
   - `pipewire` is PipeWire 1.6.11 from Alpine edge (it carries a libcamera
     0.8 compatibility patch), without the onnx filter-graph subpackage. On
     v26.06 the Alpine 3.24 PipeWire is built against libcamera 0.7 and blocks
     the upgrade. Build it after libcamera;
   - `thinksmart-view-extras`: Wi-Fi boot guard and the systemd watchdog
     setting; `thinksmart-view-extras-echo-cancel`: PipeWire echo cancellation.
2. `soc-qcom-msm8953`: set the UCM `provider_priority=10`, otherwise apk may pick
   `alsa-ucm-conf-unisoc-ums9230`.
3. Build:
   ```bash
   pmbootstrap checksum soc-qcom-msm8953
   pmbootstrap build linux-postmarketos-qcom-msm8953 libcamera soc-qcom-msm8953 thinksmart-view-extras --force
   pmbootstrap build pipewire --force
   ```
4. Add `thinksmart-view-extras` (and `thinksmart-view-extras-echo-cancel` if you
   want it) to `extra_packages` below.
5. The relevant parts of our `pmbootstrap_v3.cfg`:
   ```ini
   [pmbootstrap]
   device = qcom-msm8953
   ui = console
   systemd = always
   boot_size = 512
   extra_packages = thinksmart-view-extras,libcamera-gstreamer,gst-plugins-good,gst-plugins-bad,cage,openssh-server,v4l-utils,i2c-tools,pipewire,wireplumber,pipewire-pulse,alsa-utils,libcamera-tools,iio-sensor-proxy,mesa-dri-gallium,mesa-egl,mesa-gbm,rsync

   [providers]
   alsa-ucm-conf = soc-qcom-msm8953-ucm
   postmarketos-base-ui-audio-backend = postmarketos-base-ui-audio-backend-pipewire
   ```
   Do not add `sudo` to `extra_packages` (v26.06 uses `sudo-rs`). Set `ssh_keys`
   if you want key login right away.
6. `pmbootstrap install`. The image is in the native chroot
   (`/home/pmos/rootfs/qcom-msm8953.img`, about 1.5 GB). After changing packages run
   `pmbootstrap zap` first, otherwise the old rootfs is reused.
7. Optional: put a NetworkManager `.nmconnection` file into
   `/etc/NetworkManager/system-connections/` of the image (mode 600, root) so
   the tablet joins Wi-Fi on first boot.

Pitfalls when building in Docker: there is no udev, so the partition device
nodes of the loop device (`/dev/loopNpM`) have to be created by hand while
pmbootstrap runs; the container needs `--privileged`.

## 3. Flash

1. EDL as in step 1, then write lk2nd to `boot` and reboot:
   ```bash
   edl w boot lk2nd-lenovo-cd-18781y-20240628.img --loader=prog_emmc_firehose_8953_ddr.mbn --memory=emmc
   edl reset --resetmode=reset --loader=prog_emmc_firehose_8953_ddr.mbn
   ```
   Use `edl reset` without `--memory` (with it edl only prints the help). A final
   `USBError(5)` is normal. If `edl reset` hangs although the tablet is
   already in fastboot, interrupt it. If the tablet ends up with nothing on
   USB and a black screen, unplug and replug power without buttons.
2. lk2nd finds no system on `userdata` (still encrypted Android) and stays in
   fastboot. `fastboot getvar lk2nd:version` should answer.
3. Flash the system and reboot:
   ```bash
   fastboot flash userdata qcom-msm8953.img
   fastboot reboot
   ```
   This takes about 1.5 minutes. The first boot takes about 45 s.

To get back into lk2nd fastboot from a running system:
`systemctl reboot --reboot-argument=bootloader`.

To roll back, write `boot` and `userdata` from your backup over EDL.

## 4. First boot

```bash
sudo systemctl disable --now qbootctl.service   # Android A/B slots, always fails here
sudo systemctl reset-failed
ROOT=$(findmnt -no SOURCE /)                    # on our units: /dev/loop0p2
findmnt -no FSTYPE /                            # must be ext4
lsblk                                           # check that the partition fills userdata
sudo resize2fs "$ROOT"                          # grow the root fs to the end of that partition
```

- The speaker amplifier starts at its minimum (-110 dB). Set 0 dB once:
  `amixer -c0 cset name="Speaker Amp Master Playback Volume" 110,110 && alsactl store`.
- Touch in landscape (screen rotated 90 degrees with `wlr-randr --output DSI-1 --transform 90`):
  ```
  # /etc/udev/rules.d/99-tsv-touch.rules
  ACTION=="add|change", KERNEL=="event[0-9]*", ATTRS{name}=="generic ft5x06*", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 -1 1 1 0 0"
  ```
- The Venus, ADSP and Wi-Fi firmware are linked from the stock `modem`
  partition by `msm-firmware-loader` (`/run/msm-firmware-loader/target`);
  nothing to copy.
- The Wi-Fi MAC comes from each unit's own `persist`, so one image works for
  several units. SSH host keys and `machine-id` are created on first boot.
- Blank the screen with the backlight (`bl_power`), not with DPMS: the panel is
  a TDDI (display and touch in one chip), and DPMS turns touch off as well.

## 5. Check

- `apk info -v linux-postmarketos-qcom-msm8953` shows `7.0.9-r39` (`uname -r`
  says `7.0.9-msm8953` for any build); `systemctl --failed` is empty.
- Wi-Fi: `cat /sys/bus/mmc/devices/mmc1:0001/power/runtime_suspended_time` is
  more than zero (the card was powered off before the driver probed);
  `systemctl is-enabled wifi-guard.service` says `enabled`, and
  `journalctl -b -u wifi-guard.service` shows whether it had to act.
- Watchdog: `cat /sys/class/watchdog/watchdog0/state` says `active`.
- GPU: `/dev/dri/renderD128` exists and Mesa uses freedreno, not llvmpipe.
- Sensors: `monitor-sensor` shows orientation and light;
  `/sys/bus/iio/devices/*/in_proximity_raw` rises with a hand in front of the
  top bezel.
- Camera: `cam -l` lists one camera ("Internal front camera"); preview through
  SoftISP:
  `cam -c1 --capture=60 -s width=1304,height=980,pixelformat=BGR888`.
- GStreamer:
  `gst-launch-1.0 libcamerasrc ! video/x-raw,width=1304,height=980 ! videoconvert ! fpsdisplaysink video-sink=fakesink text-overlay=false -v`.
- Venus: the `qcom-venus-encoder` and `qcom-venus-decoder` video nodes exist
  (their `/dev/videoN` numbers can swap between boots, look them up by name).

## Known issues

- Encoding needs a width that is a multiple of 16: 1304x980 straight from the
  camera hangs the encoder until reboot. Scale to 1280x960.
- Never use `frame_skip_mode` on the encoder; with VBR_VFR the tablet hung when
  frames were skipped.
- `filesink` holds V4L2 buffers and can starve the encoder with small frames;
  use `filesink buffer-mode=unbuffered`.
- Reading decoder output with the CPU is slow (uncached memory, ~14 MB/s), so
  hand the frames to the GPU as DMABuf (`glimagesink`) instead of
  `videoconvert`.
- A hung GPU (`hangcheck detected gpu lockup` repeated in the kernel log) does
  not reboot by itself unless it also stops PID 1; see
  [docs/watchdog.md](docs/watchdog.md).
