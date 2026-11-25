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
Venus issues (2, 8, 9) are fixed on the local branch `fix/venus`; see
[Venus fixes](#venus-fixes-branch-fixvenus). The others are not fixed yet.

| Commits | Topic | State |
|---|---|---|
| 1, 3 | gcc-msm8953 HW_CTRL, Venus software power collapse | Candidates together; 3 should use one SoC flag instead of two `compatible` checks. |
| 2 | Venus HFI parser | Fixed on `fix/venus` (was: copies a property before checking its length against the remaining bytes). |
| 4, 5, 7 | Venus encoder rate and buffers | Too broad for upstream as they are (4 replaces both limits when one is missing, 5 applies to all Venus 3.x encoders, 7 raises the minimum for all clients). |
| 6 | Venus LTR mode | Good candidate after a test with LTR frames. |
| 8 | Venus EOS drain | Fixed on `fix/venus` (was: state changed without `inst->lock`; the decoder can miss the end of stream). Still needs one more capture QBUF after the EOS. |
| 9 | Venus decoder command PM | Fixed on `fix/venus` (was: the PM reference is dropped before the command is sent). |
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

`fix/vcnl` is `tsv/device` with the VCNL4200 commits redone (40 commits). It
was reviewed with Codex (gpt-6.2-astra) and independently with Claude Fable,
in full on the final code and again on each later change, and cleaned up
with a `/simplify` pass; the findings were fixed. Built as package r57 and
tested on unit 5 on 2026-11-25 (then put back on r39):

- probe with `vdd`/`vio` (dummy `vled`); runtime PM `active` while
  `alfred-wake` has events enabled, `suspended` 3 s after they are disabled
  (r39 showed `suspended` with events enabled); no usage count warnings;
- a threshold event enabled on the suspended sensor, without a read, fires
  at once;
- sample wait 369 ms at 8T and 47 ms at 1T (duty 1/1280); the first read
  after an integration time change takes about 415 ms and already returns a
  sample with the new settings (on r52 the first two reads after 8T to 1T
  still returned the 8T value: the sensor completes the measurement in
  progress); writing the current integration time does not delay reads;
- `in_proximity_thresh_either_period` is 0.3072 s per sample (1-4 samples,
  up to 1.2288 s), negative values are rejected;
- registers PS_CONF1 0x08c9 and PS_CONF3 0x0120 (as in the stock ADSP
  driver); background 12-13 counts at 8T, as on r39;
- on r54: a hand at 5-10 cm wakes the screen within a second after it was
  blanked through the `alfred-wake` socket (later changes were refactors and
  checked with the threshold event test above).

| `fix/vcnl` | Commit | Change |
|---|---|---|
| 23 | dt-bindings: iio: light: vcnl4000: add regulators | Backport of upstream d674752564bf. |
| 24 | iio: light: vcnl4000: add support for regulators | Backport of upstream 773a5dc613ed with 091e7a67a908 (`vdd`, `vio`, `vled`); replaces our `vdd`/`vddio` change and its undocumented 10 ms sleep. |
| 25 | iio: light: vcnl4000: wait for the VCNL4040/4200 to start up after power-up | 2.5 ms before the first I²C access (Vishay application notes 84307 and 84327), as a field in the chip description. |
| 26 | iio: light: vcnl4000: keep measuring while threshold events are enabled | Upstream bug since 7e87ab38eed0: a runtime PM reference is held while any threshold event is enabled; interrupts are disabled at init so that a driver rebind cannot unbalance it. Before the LED change, so it stands on its own. |
| 27 | iio: light: vcnl4000: power the sensor down when probe fails late | Failures after init (buffer, IRQ, trigger) power ALS and PS down; with shared supplies the LED kept pulsing. |
| 28 | iio: light: vcnl4000: use low-power IR LED settings on the VCNL4200 | One nominal PS period from PS_IT and PS_Duty; set after a successful write; the first read after a change waits for the end of the measurement in progress plus one new period; an unchanged write does nothing; runtime resume keeps a pending deadline; the read sleeps without the channel lock. |
| 29 | iio: light: vcnl4000: base the PS event period on the sample period | `thresh_period` = persistence x sample period (was persistence x integration time, about 400x too short with duty 1/1280). |
| 33 | arm64: dts: qcom: apq8053-lenovo-cd-18781y: enable the proximity sensor | `vio-supply`, `proximity-near-level` 8 (128 counts, between the background of up to 60 and a hand at 800-1800), no `interrupt-names`, the explanation in the commit message. |

The old commit 25 (autosuspend right after probe) is dropped: after probe
the driver core calls `pm_request_idle()`, which already suspends the device.

Known limitations, left as they are:

- The LED settings change the proximity range and response of every
  VCNL4200 (period 4.8 ms to 307 ms). The LED current, pulse count and
  integration time can still be set through IIO, the duty ratio cannot;
  upstream would need a firmware property.
- 27 and 29 fix old upstream behaviour but carry no `Fixes:` tag yet (the
  shallow clone cannot verify the hashes); 29 depends on 28.
- A failure inside init() after ALS was already enabled still returns
  without powering down: init may fail because the device is not a
  supported sensor, which must not be written to.
- From upstream: after a driver rebind the ALS sample wait and scale are
  reset to the defaults even if the chip keeps another ALS integration time;
  ALS `last_measurement` is set without its channel lock; IIO is registered
  before runtime PM is enabled (upstream has since reordered probe,
  de1839edfe36 and following); during system sleep with events enabled the
  sensor keeps measuring, but its interrupt is not a wakeup source.

## Where the values come from

The individual commit messages identify the source of board wiring, operating
parameters and register sequences. Values marked "stock" were read from the
original Lenovo software on the device: its device tree (supplies, GPIOs, QoS
settings), the ADSP sensor driver (VCNL4200 LED settings) and the camera
library `libmmcamera_s5kc505a.so` (the S5KC505A register tables, which are
also published in rebrch/tsv-nura). Measurements on our units are identified
separately.
