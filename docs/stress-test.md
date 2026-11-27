# Stress test and GPU hangs

## Stress test

Unit 5, kernel 7.1.3, 27 November 2026. First each part alone for a few
minutes, then everything at once for 27 minutes: four cores of `stress-ng`
(all CPU methods, with verification) and 300 MB of `stress-ng --vm` with
verification, the GPU (`peglgears`), Venus H.264 encode and decode at 720p in a
loop, the camera at 1304x980 and 30 fps, recording and playback through the
echo canceller and RNNoise, and `iperf3` over Wi-Fi.

| Part | Result |
|---|---|
| CPU, 8 cores, 5 min | No computation errors, 1.8 GHz the whole time, at most 52 °C |
| Memory | `stress-ng --vm` 4x800 MB and one `memtester` pass over 400 MB: no errors |
| Venus | 720p encode and decode in a loop: no errors, suspends afterwards |
| eMMC | `fio` 4 KiB random read/write with CRC verification: no errors, 5.4 MB/s read, 3.4 MB/s write |
| Wi-Fi | 80 Mbit/s alone, 28-63 Mbit/s under full load |
| All at once, 27 min | No errors from CPU, memory, Venus or camera; at most 60 °C (trip point 80 °C), no throttling; at least 393 MB memory available |

CPU frequency is capped at 1.8 GHz (`boost` is 0). The display app gets very
little CPU and GPU time while everything runs at once.

## GPU hangs

The Adreno 506 hangs under `EGL_PLATFORM=surfaceless peglgears`, which renders
offscreen without any frame limit. The msm hangcheck detects the hang
mid-render (about 2-3 s into a run) and recovers the GPU, and the program goes
on. It happens in almost every run:

| Kernel | Hangs |
|---|---|
| 7.0.9 (r120) | 6 in 11 runs |
| 7.3 | 10 in 10 runs |
| 7.3 with one ringbuffer (no preemption) | 11 in 10 runs |

It is independent of the GPU clock: capped at 650, 560, 510, 400 and 320 MHz
the runs still hang. `FD_MESA_DEBUG=sysmem` and `nobin` (Mesa 26.1.6) do not
avoid it either. So it is neither a clock or voltage problem nor new in 7.x.
Normal use (the display app, `es2gears` at 60 fps) had no hangs in a week on
five units.

After a recovery our Flutter display app stopped drawing until it was
restarted. A devcoredump from 7.3 shows ring 2 with 160 dwords written and
none read (`rptr 0`, `wptr 160`). It is not decoded yet; `crashdec` from Mesa
would show the state of the command processor.
