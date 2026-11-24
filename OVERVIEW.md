This folder contains the design for an analog LED driver that lets arbitrary audio-rate signals be sent down an optical link: soundcard (or other source) → LED → air → phototransistor pickup → soundcard.

The existing pickup side (phototransistors on phantom power, light high-pass at ~50 Hz) is already built and working; this project is only the transmit side.

## Goals
Each channel should be a fairly general optical "audio link", usable for:
- solid / full brightness (and anything in between) with no input
- low frequency oscillators and slow control signals
- speech, noise, music - reasonably intelligible
- feedback loops (LED → pickup → processing → LED) that can go interestingly nonlinear

With nothing plugged in, a channel should sit at a sensible idle brightness (set by a pot). Overdriving the input should clip cleanly at off and at full, and never over-drive the LED.

## LEDs
10 mm round LEDs, 3.7 V, 100 mA max. Run from a 12 V supply, with a linear regulator for the 5 V control side.

## Approach
A linear voltage-controlled current sink per channel (op-amp + transistor + sense resistor), so that light output follows the signal rather than the LED's exponential V/I curve. The input is a balanced difference amplifier whose reference is the bias (idle brightness) control, so audio rides on top of a DC level. The output of that stage is clamped by the 0-5 V rails, which gives a hard, safe ceiling on LED current.

See WORKING.md for the current circuit, values and open questions.

## Control
The board has its own ESP32 and joins the I2C network as a Peripheral, with the LED channels as an Element. A DAC on the board sets each channel's idle brightness, so levels, on/off and LFOs work without the soundcard.
