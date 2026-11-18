"""
generate_sfx.py — Generate all SFX WAV files for Reel Editor.
Run: python engine/assets/generate_sfx.py
"""

import numpy as np
from scipy.io.wavfile import write as wav_write
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sfx")
os.makedirs(OUTPUT_DIR, exist_ok=True)

sr = 44100


def save(name, sig):
    path = os.path.join(OUTPUT_DIR, name)
    wav_write(path, sr, sig)
    print(f"  ✓  {name}  ({len(sig)} samples)")


print("Generating SFX files...")

# --- vine_boom.wav ---
dur = 0.5
t = np.linspace(0, dur, int(sr * dur), endpoint=False)
f_start, f_end = 220, 40
f_t = f_start * (f_end / f_start) ** (t / dur)
phase = 2 * np.pi * np.cumsum(f_t) / sr
sig = 0.9 * np.sin(phase) * np.exp(-t * 1.5)
save("vine_boom.wav", (sig * 32767).astype(np.int16))

# --- bruh.wav ---
dur = 0.6
t = np.linspace(0, dur, int(sr * dur), endpoint=False)
noise = np.random.randn(len(t))
f = 100
vibrato = np.sin(2 * np.pi * 8 * t) * 20
sig = 0.6 * np.sin(2 * np.pi * (f + vibrato) * t) + 0.3 * noise
sig = sig * np.exp(-t * 3)
save("bruh.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))

# --- bubble_pop.wav ---
dur = 0.08
t = np.linspace(0, dur, int(sr * dur), endpoint=False)
f = np.linspace(800, 200, len(t))
phase = 2 * np.pi * np.cumsum(f) / sr
sig = 0.7 * np.sin(phase) * np.exp(-t * 30)
save("bubble_pop.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))

# --- cash_register.wav ---
dur = 0.3
t = np.linspace(0, dur, int(sr * dur), endpoint=False)
sig = 0.5 * np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 15)
sig += 0.4 * np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 20)
save("cash_register.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))

# --- level_up.wav ---
notes = [261.63, 329.63, 392.00, 523.25]
note_dur = 0.12
sig = np.array([], dtype=np.float32)
for freq in notes:
    t_note = np.linspace(0, note_dur, int(sr * note_dur), endpoint=False)
    tone = 0.6 * np.sin(2 * np.pi * freq * t_note) * np.exp(-t_note * 8)
    sig = np.append(sig, tone)
save("level_up.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))

# --- sad_trombone.wav ---
notes = [233.08, 196.00, 155.56]  # Bb3, G3, Eb3
note_dur = 0.25
sig = np.array([], dtype=np.float32)
for freq in notes:
    t_note = np.linspace(0, note_dur, int(sr * note_dur), endpoint=False)
    vibrato = 1 + 0.01 * np.sin(2 * np.pi * 5 * t_note)
    tone = 0.5 * np.sin(2 * np.pi * freq * vibrato * t_note) * (1 - t_note / note_dur)
    sig = np.append(sig, tone)
save("sad_trombone.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))

# --- ding.wav (generated version, only if not already copied) ---
ding_path = os.path.join(OUTPUT_DIR, "ding.wav")
if not os.path.exists(ding_path):
    dur = 0.6
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    sig = 0.7 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 5)
    sig += 0.3 * np.sin(2 * np.pi * 3600 * t) * np.exp(-t * 8)
    save("ding.wav", np.clip(sig * 32767, -32767, 32767).astype(np.int16))
else:
    print(f"  ✓  ding.wav  (already exists, skipped)")

print("\nAll SFX generated successfully.")
