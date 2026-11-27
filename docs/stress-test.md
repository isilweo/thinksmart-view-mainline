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

## GPU hangs (solved)

Under `EGL_PLATFORM=surfaceless peglgears`, which renders offscreen without
any frame limit, the msm hangcheck reported `gpu lockup` and reset the GPU in
almost every 5 s run: 6 in 11 on 7.0.9, 10 in 10 on 7.3. Neither the GPU clock
(320-650 MHz) nor a single ringbuffer nor `FD_MESA_DEBUG=sysmem`/`nobin` made a
difference. After a reset our Flutter display app stopped drawing until it
was restarted.

It was not a hang. With `hangcheck_period_ms` (debugfs) raised from 500 to
1000 or 2000 ms the same runs finished with the same frame rate and no reset,
0 in 20. Single submits simply took longer than the period. drm/msm can ask
the GPU whether the CP still makes progress before it declares a hang, but
only a6xx implements that callback.

"drm/msm/a5xx: add a progress callback for hang detection" adds it for a5xx.
With it, at the default period: 0 resets in 15 runs on 7.3 (unit 5) and 0 in
5 on 7.1.3 (unit 4), at the same frame rate. A CP that is really stuck reads
the same registers and is still reset after the progress retries; that case
was not reproduced.

The analysis of a devcoredump (Codex, with Mesa's `crashdec`) is what pointed
to a long submit; the dump itself was truncated before the register section.
