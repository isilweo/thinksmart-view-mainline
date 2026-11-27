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

## Noise suppression

`thinksmart-view-extras-noise-suppression` adds RNNoise after the echo
canceller (`61-noise-suppression.conf`: a filter-chain with the
`noise_suppressor_mono` LADSPA plugin from `noise-suppression-for-voice`, voice
activity gate off). Its output, `noise-suppression-source`, becomes the default
microphone. If a default source was already chosen, WirePlumber keeps it; set
the new one with `wpctl set-default <id>`. The filter-chain module needs
`pipewire-filter-graph` and `pipewire-filter-graph-ladspa` built from the same
PipeWire as the rest; on v26.06 that is the 1.6.11 overlay in `temp/pipewire`,
not the 1.6.8 package from the repository. The module is loaded with
`nofail`, so PipeWire still starts if a piece is missing.

Measured on one unit with the same 30 s of speech at about 1 m, levelled to
the same speech level (noise in the pauses between words):

| Chain | Noise in pauses |
|---|---|
| one microphone | -36 dBFS |
| both microphones, mono downmix | -40 dBFS |
| + WebRTC (echo cancellation, noise suppression, gain control) | -57 dBFS |
| + RNNoise | -83 dBFS |

RNNoise and WebRTC together take about 5% of one core.

## Microphones

The two DMICs come up as one stereo capture device (DMIC1 left, DMIC2 right;
UCM `CaptureChannels 2`), so beamforming in userspace is possible. The echo cancellation setup above
uses mono, and the mono downmix of the two channels is already the best
two-microphone beam towards someone in front of the screen: the microphones
lie in the screen plane, at least 6.4 cm apart (the speaker reaches one of
them 187 us before the other), so speech from the front arrives at both at
once. The sum lowers the uncorrelated microphone noise by about 3 dB and
the speaker signal by 3-7 dB between 1 and 6 kHz before echo cancellation.
WebRTC no longer has a beamformer (it was dropped in webrtc-audio-processing
1.0). The two DMICs are quiet. Without echo cancellation we apply a software gain of
4 (`volume volume=4.0`) before encoding. With echo cancellation, do not add the
gain on top, since the canceller has its own gain control. Steered
beamforming with the two DMICs is not done; see above.
