# Status of the kernel changes

All changes live as commits in
[isilweo/linux](https://github.com/isilweo/linux), a fork of
[msm8953-mainline/linux](https://github.com/msm8953-mainline/linux):

- `tsv/device`: msm8953-mainline `v7.0.9-r0` plus the 36 commits below, one
  change each;
- `tsv/debug`: `tsv/device` plus three local debug commits (ramoops and a
  Venus `fw_debug` parameter, qdsp6 dynamic debug traces, the SDIO probe stage
  on -110);
- tag `tsv-v7.0.9-r39`: `tsv/debug` as built into the postmarketOS package
  `linux-postmarketos-qcom-msm8953-7.0.9-r39` that runs on our tablets.

Only the final state was built and tested; the intermediate commits were not
built one by one. The commits have no `Signed-off-by:` yet. Before upstream
submission, each human contributor must be able to certify their contribution
under the [Developer's Certificate of Origin](https://developercertificate.org/)
and add their own `Signed-off-by:`. Use of AI tools is recorded with
`Assisted-by:`.

## Where it would go

The generic driver changes would go to the mainline kernel lists, each series
rebased on its subsystem tree. The board DTS (`apq8053-lenovo-cd-18781y`) is
not in mainline Linux, only in msm8953-mainline, so the board commits belong
there, together with its author Felix Kaechele.

## Review

A review of the whole series with Codex (OpenAI, gpt-6.2-astra) found these
issues. They are not fixed yet.

| Commits | Topic | State |
|---|---|---|
| 1, 3 | gcc-msm8953 HW_CTRL, Venus software power collapse | Candidates together; 3 should use one SoC flag instead of two `compatible` checks. |
| 2 | Venus HFI parser | **Bug:** copies a property before checking its length against the remaining bytes. |
| 4, 5, 7 | Venus encoder rate and buffers | Too broad for upstream as they are (4 replaces both limits when one is missing, 5 applies to all Venus 3.x encoders, 7 raises the minimum for all clients). |
| 6 | Venus LTR mode | Good candidate after a test with LTR frames. |
| 8 | Venus EOS drain | **Bug:** state changed without `inst->lock`; the decoder can miss the end of stream. |
| 9 | Venus decoder command PM | **Bug:** the PM reference is dropped before the command is sent. |
| 10, 13 | ccs pixel array sizes and default crop | Candidates after `v4l2-compliance`. |
| 11 | ccs S5KC505A quirk | Needs agreement with the CCS maintainer. The register tables come from the stock camera library: the legal basis for using them must be settled before submitting or redistributing binaries built from them. |
| 12, 14 | CAMSS sensor walk and link frequency | Both use "first subdev outside camss" as the boundary, which also stops at an external bridge; 12 needs a different design. |
| 15-22 | CAMSS on MSM8953 | Reviewed earlier with Codex; the issues found then were fixed before testing. |
| 23 | VCNL4000 supplies | Replace with the upstream `devm_regulator_bulk_get_enable()` change (`vdd`, `vio`, `vled`). |
| 24 | VCNL4200 LED settings | **Bug:** after the integration time is written through IIO, the sample delay is computed for the wrong duty cycle. |
| 25 | VCNL4000 autosuspend | **Bug:** a threshold event enabled after autosuspend may not restart measurements. |
| 26 | Both touchscreens | Keep local: both controllers share reset and IRQ lines; better to pick the variant from lk2nd. |
| 27, 28 | Accelerometer mount matrix, sensor I²C pins | The closest to being sendable (board DTS, so to msm8953-mainline). |
| 29, 30 | Proximity and camera nodes | After 23-25; 30 needs `bus-type`, a binding extension for rotation 270 and a clean description of the camera standby line. |
| 31, 32 | APSS watchdog binding and node | Can go to mainline (`msm8953.dtsi` is upstream). |
| 33, 34 | WLAN I/O supply and `cap-power-off-card` | Board DTS, to msm8953-mainline. |
| 35 | TAS5782M | Downstream adaptation of Felix Kaechele's work; volume uses TAS5805M registers and I²C errors are not propagated. Authorship to be sorted out with Felix. |
| 36 | q6asm-dai stream lifetime | Written with Codex; not yet reviewed by a second party. |

## Where the values come from

The individual commit messages identify the source of board wiring, operating
parameters and register sequences. Values marked "stock" were read from the
original Lenovo software on the device: its device tree (supplies, GPIOs, QoS
settings), the ADSP sensor driver (VCNL4200 LED settings) and the camera
library `libmmcamera_s5kc505a.so` (the S5KC505A register tables, which are
also published in rebrch/tsv-nura). Measurements on our units are identified
separately.
