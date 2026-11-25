# Venus video encoder and decoder

## What works

| | |
|---|---|
| H.264 encoder | `v4l2h264enc`: bitrate control works (a 1 Mb/s target gives 931-959 kb/s); 640x480 at 30 fps costs about 1.3 of 8 cores including the camera. Width must be a multiple of 16. |
| H.264 decoder | `v4l2h264dec`: 1280x960 at about 238 fps using 0.1 core. A stream that is cut off no longer hangs the SoC in the case we hit; the review still found a locking issue in the EOS handling. |
| H.265 decoder | `v4l2h265dec`: a 960x720 20 fps RTSP stream at about 6% of one core. |

## Notes

- Stop GStreamer pipelines with EOS (`gst-launch-1.0 -e` and SIGINT, or
  `timeout -s INT`). Killing the decoder mid-stream used to hang the SoC. The
  vdec patches fix the case we hit, but EOS is still the safe way. Note the
  open review points on those patches in [upstream-status.md](upstream-status.md).
- Encoder pipeline we use (camera to RTP):
  ```
  libcamerasrc ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=NV12
    ! v4l2h264enc extra-controls="controls,video_bitrate=1000000,video_gop_size=30"
    ! 'video/x-h264,level=(string)4,profile=(string)baseline' ! h264parse config-interval=-1
    ! rtph264pay pt=96 mtu=1200 ! udpsink host=... port=5000
  ```
  The soft ISP outputs RGBA and `videoconvert` turns it into NV12 on the CPU.
  With libcamera 0.7.1 that limited us to 640x480; with 0.8.0, 1280x960 runs at
  30 fps into Venus using about one of the eight cores. Converting on the GPU
  instead (`glupload ! glcolorconvert ! gldownload`) only reached 15 fps,
  because of the download from GPU memory.
- Decoder: `rtph264depay ! h264parse ! v4l2h264dec ! glimagesink`. Its own
  latency is about 4 ms for streams without B-frames. Enabling
  `display_delay_enable` (decode-order output) changes that by well under a
  millisecond, so it is not worth setting. `waylandsink` gave a black screen
  in cage for us. We only tested streams encoded without B-frames.
- `pipewiresrc` together with the camera in one pipeline lost its clock for us;
  run audio and video as separate processes, `pipewiresrc provide-clock=false`.
- Re-encoding frames to JPEG only reaches about 7 fps, so it is not an option
  for live video.

## Playing camera streams (RTSP, H.265)

A UniFi Protect doorbell stream (H.265, 960x720 at 20 fps) plays on the tablets
through Venus:

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
- Use the explicit chain: `decodebin` after `rtspsrc` failed with "Internal
  data stream error" (caps negotiation with the H.265 depayloader).
- `h265parse` is not needed: `rtph265depay` already outputs byte-stream in
  whole access units. That matters because `h265parse` lives in
  gst-plugins-bad, which a fresh image does not have.
- When an element is missing, `gst_parse_launch()` returns a partial pipeline
  together with a recoverable error instead of NULL. Code that only checks for
  NULL then waits forever without frames and without an error; check the
  `GError`.
- UniFi Protect: drop `?enableSrtp` from the stream URL. With SRTP the
  depayloader reports "The stream is in the wrong format".
