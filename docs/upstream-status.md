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
issues. Commit numbers refer to `tsv/device` as it is now. The VCNL4200
issues (23-25, 29) are fixed on the local branch `fix/vcnl`, which is not in
`tsv/device` yet; see [VCNL4200 fixes](#vcnl4200-fixes-branch-fixvcnl). The
others are not fixed yet.

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
| 23 | VCNL4000 supplies | Fixed on `fix/vcnl`: replaced by the upstream backport. |
| 24 | VCNL4200 LED settings | Fixed on `fix/vcnl` (was: after the integration time is written through IIO, the sample delay is computed for the wrong duty cycle). Still changes the defaults of every VCNL4200. |
| 25 | VCNL4000 autosuspend | Dropped on `fix/vcnl` (the driver core already suspends after probe); the event bug is fixed by a new commit. |
| 26 | Both touchscreens | Keep local: both controllers share reset and IRQ lines; better to pick the variant from lk2nd. |
| 27, 28 | Accelerometer mount matrix, sensor I²C pins | The closest to being sendable (board DTS, so to msm8953-mainline). |
| 29, 30 | Proximity and camera nodes | 29 fixed on `fix/vcnl`; 30 needs `bus-type`, a binding extension for rotation 270 and a clean description of the camera standby line. |
| 31, 32 | APSS watchdog binding and node | Can go to mainline (`msm8953.dtsi` is upstream). |
| 33, 34 | WLAN I/O supply and `cap-power-off-card` | Board DTS, to msm8953-mainline. |
| 35 | TAS5782M | Downstream adaptation of Felix Kaechele's work; volume uses TAS5805M registers and I²C errors are not propagated. Authorship to be sorted out with Felix. |
| 36 | q6asm-dai stream lifetime | Written with Codex; not yet reviewed by a second party. |

## VCNL4200 fixes (branch `fix/vcnl`)

`fix/vcnl` is `tsv/device` with the VCNL4200 commits redone (38 commits). It
was reviewed with Codex (gpt-6.2-astra, three rounds) and independently with
Claude Fable; findings of both were fixed. Built as package r52; not yet
tested on a tablet.

| `fix/vcnl` | Commit | Change |
|---|---|---|
| 23 | dt-bindings: iio: light: vcnl4000: add regulators | Backport of upstream d674752564bf. |
| 24 | iio: light: vcnl4000: add support for regulators | Backport of upstream 773a5dc613ed with 091e7a67a908 (`vdd`, `vio`, `vled`); replaces our `vdd`/`vddio` change and its undocumented 10 ms sleep. |
| 25 | iio: light: vcnl4000: wait for the VCNL4040/4200 to start up after power-up | 2.5 ms before the first I²C access, as given in Vishay application notes 84307 and 84327. |
| 26 | iio: light: vcnl4000: use low-power IR LED settings on the VCNL4200 | The PS sample period is computed in one place from the PS_IT and PS_Duty values written, after a successful write, and the wait restarts; the IIO write and the sample read run under the PS channel lock. |
| 27 | iio: light: vcnl4000: keep measuring while threshold events are enabled | Upstream bug since 7e87ab38eed0: a runtime PM reference is held while any threshold event is enabled; interrupts are disabled at init so that a driver rebind cannot unbalance it. Candidate for upstream on its own. |
| 31 | arm64: dts: qcom: apq8053-lenovo-cd-18781y: enable the proximity sensor | `vio-supply` instead of `vddio-supply`, `proximity-near-level` 8 (128 counts, between the background of up to 60 and a hand at 800-1800), no `interrupt-names`, the explanation moved to the commit message. |

The old commit 25 (autosuspend right after probe) is dropped: after probe
the driver core calls `pm_request_idle()`, which already suspends the device.

Known limitations, left as they are:

- The LED settings change the proximity range and response of every
  VCNL4200 (period 4.8 ms to 307 ms). Upstream would need a firmware
  property for them.
- The PS event period (persistence) is still converted with the integration
  time only, without the duty ratio.
- From upstream: after a driver rebind the ALS sample wait and scale are
  reset to the defaults even if the chip keeps another ALS integration time;
  IIO is registered before runtime PM is enabled; runtime resume sets the PS
  `last_measurement` without the channel lock. Upstream has since reordered
  probe (de1839edfe36 and following).

## Where the values come from

The individual commit messages identify the source of board wiring, operating
parameters and register sequences. Values marked "stock" were read from the
original Lenovo software on the device: its device tree (supplies, GPIOs, QoS
settings), the ADSP sensor driver (VCNL4200 LED settings) and the camera
library `libmmcamera_s5kc505a.so` (the S5KC505A register tables, which are
also published in rebrch/tsv-nura). Measurements on our units are identified
separately.
