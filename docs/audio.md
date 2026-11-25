# Audio

## Speaker (TAS5782M)

The speaker amplifier is a TAS5782M, driven by the tas5805m driver with Felix
Kaechele's TAS5782M support. On `tsv/device` this is the commit "ASoC: tas5805m:
add TAS5782M support from Felix Kaechele's tree", adapted from his
work-in-progress commit. Felix calls it a stopgap: a proper TAS5782M driver is
still needed, and the volume control still uses the TAS5805M register layout.
The DSP program it loads comes from the postmarketOS `firmware-qcom-msm8953`
package.

`soc-qcom-msm8953`: raise the UCM `provider_priority` (we use 10). Otherwise
apk may pick `alsa-ucm-conf-unisoc-ums9230`.

## Full duplex and echo cancellation

The commit "ASoC: qcom: q6asm-dai: close the DSP stream before reopening it"
fixes the ADSP dying after a few stream restarts. Before it, a second prepare
after STOP opened the same ASM session again without closing it. The ADSP
refused that with error 9 (`ADSP_EALREADY`), and audio was dead until reboot.
Full-duplex use such as an echo canceller hit it within a few cycles. The fix
was diagnosed and written by Codex from the kernel sources and our logs, then
built and tested on the device.

With the fix, PipeWire's WebRTC echo canceller passed 20/20 full-duplex
cycles and removes about 40 dB of speaker echo. During loud playback it also
ducks near-end speech, as echo cancellers do with the speaker this close to the
microphones. `thinksmart-view-extras-echo-cancel` installs the configuration
(`60-echo-cancel.conf`: mono, WebRTC, default source and sink) and pulls in
`pipewire-echo-cancel` and `pipewire-webrtc`.

## Microphones

The two DMICs are quiet. Without echo cancellation we apply a software gain of
4 (`volume volume=4.0`) before encoding. With echo cancellation, do not add the
gain on top, since the canceller has its own gain control. Not done:
beamforming with the two DMICs.
