# Front camera (Samsung S5KC505A)

## Kernel

- `ccs` driver with an S5KC505A quirk (its own init and mode tables), plus
  `enum_frame_size` and `CROP_DEFAULT` on the pixel array, which libcamera
  needs.
- CAMSS on MSM8953: its own CSIPHY and VFE clock tables, the VFE VBIF region
  described in the DT, per-SoC QoS/DS settings and UB size, write master
  geometry in frame based mode, and the link frequency read from the
  transmitter subdev instead of the pixel array.

Result: 1304x980 at 30 fps without dropped frames, through the libcamera
SoftISP with GPU debayer, using about one CPU core. In a dark room the AGC
lengthens the exposure past the frame time, and the frame rate drops (we saw
about 17 fps in the evening).

The S5KC505A register tables come from the stock camera library
`libmmcamera_s5kc505a.so`. They are also published in
[rebrch/tsv-nura](https://github.com/rebrch/tsv-nura). See
[upstream-status.md](upstream-status.md) for what that means before
distribution.

## libcamera

We use libcamera 0.8.0, the `temp/libcamera` package of pmaports master;
`pmaports/temp/libcamera/` here is that package with two additions:

- the S5KC505A sensor helper (linear analogue gain, code 32 = 1x; black level
  64 at 10 bits), fetched from rebrch/tsv-nura at a pinned commit;
- our tuning file `s5kc505a.yaml`, installed as
  `/usr/share/libcamera/ipa/softisp/s5kc505a.yaml`.

On v26.06, PipeWire from Alpine 3.24 is built against libcamera 0.7 and blocks
the upgrade. We rebuilt PipeWire 1.6.11 from Alpine edge (it carries a
libcamera 0.8 compatibility patch) without the onnx filter-graph subpackage,
which needs onnxruntime.

libcamera 0.7.1 works too: put `libcamera/s5kc505a-libcamera-0.7.yaml` under
`/usr/share/libcamera/ipa/simple/s5kc505a.yaml`. Its soft ISP AGC has no manual
exposure, exposure compensation or highlight protection, so bright objects on a
dark background clip. 0.8.0 moved that to the common libipa AGC, where manual
`ExposureTime`/`AnalogueGain` and `ExposureValue` work on this camera (EV -1
cut clipped pixels from 1.06% to 0.02% in a desk scene), and it adds lens
shading correction.

## Colour calibration

Colour matrices and AWB gains were measured on a Datacolor SpyderCheckr 24
under an Elgato Key Light at 2900, 4000, 5000 and 6500 K. The images were
flat-fielded with the grey back of the chart. The median CIE76 error after
correction is 3.9-5.8.

`libcamera/s5kc505a.yaml` (0.8.0) uses the full matrices and Bayesian AWB along
the measured light curve instead of grey world. With libcamera 0.7.x the soft
ISP turns clipped highlights pink with the full matrices, so
`libcamera/s5kc505a-libcamera-0.7.yaml` blends them 50/50 with the identity
and keys them on the soft ISP's `estimateCCT()` values.

## Encoding the camera

See [venus.md](venus.md) for the GStreamer pipelines.
