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

Without the q6asm-dai fixes the ADSP died after a few stream restarts: a
second prepare after STOP opened the same ASM session again without closing
it, the ADSP refused that with error 9 (`ADSP_EALREADY`), and audio was dead
until reboot. Full-duplex use such as an echo canceller hit it within a few
cycles. Mainline has since fixed most of it. On 7.0.9 `tsv/device` carries
those five commits as backports (7.1.3 already has three of them), plus two of ours: tearing down a partially set up stream
(a failed media format used to leave the stream open) and checking capture
buffer queueing in prepare. Since r120 two more: the buffer token in data done
events from the DSP is checked before use, and capture reads are no longer
queued again after STOP. Tested on one unit with XRUN, drop/prepare and
hw_params changes for playback and capture.

With the fix, PipeWire's WebRTC echo canceller passed 20/20 full-duplex
cycles and removes about 40 dB of speaker echo. During loud playback it also
ducks near-end speech, as echo cancellers do with the speaker this close to the
microphones. `thinksmart-view-extras-echo-cancel` installs the configuration
(`60-echo-cancel.conf`: mono, WebRTC, default source and sink) and pulls in
`pipewire-echo-cancel` and `pipewire-webrtc`.

## Microphones

The two DMICs come up as one stereo capture device (DMIC1 left, DMIC2 right;
UCM `CaptureChannels 2`), so beamforming in userspace is possible. The
channels differ but are close (correlation about 0.97 on ambient sound), as
the microphones sit close together. The echo cancellation setup below uses
mono. The two DMICs are quiet. Without echo cancellation we apply a software gain of
4 (`volume volume=4.0`) before encoding. With echo cancellation, do not add the
gain on top, since the canceller has its own gain control. Not done:
beamforming with the two DMICs.
