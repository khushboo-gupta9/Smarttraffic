"""
Mic-based ambulance siren detector with graceful fallback.

- If PyAudio + microphone available: listens in real-time and detects siren-like energy
  in ~500–1500 Hz with simple modulation check.
- Else: falls back to random simulation (so demo continues to work).

Usage:
    from sound_sensor import start_siren_listener
    start_siren_listener(on_detect_callback, cooldown=15)
"""

import time
import math
import random
import threading

# Try to import mic deps
try:
    import pyaudio
    import numpy as np
    HAVE_MIC = True
except Exception:
    HAVE_MIC = False
    # lazy import numpy only if needed elsewhere
    try:
        import numpy as np  # might be present anyway
    except Exception:
        np = None

# Config
RATE = 44100
CHUNK = 4096
LOW_F = 500
HIGH_F = 1500

def _band_energy(fft_abs, freqs, low, high):
    """Sum of magnitude in [low, high] Hz band."""
    band = (freqs >= low) & (freqs <= high)
    if not np.any(band):
        return 0.0
    return float(np.sum(fft_abs[band]))


def _mic_loop(on_detect, cooldown):
    """
    Simple heuristic: if band energy (500–1500 Hz) dominates overall energy,
    and shows temporal modulation over consecutive frames -> siren detected.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
    last_trigger = 0
    modulation_history = []

    print("[siren] Mic listener started.")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            if audio.size == 0:
                continue

            # FFT
            fft = np.fft.rfft(audio)
            mag = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio), 1.0 / RATE)

            # Energies
            band_e = _band_energy(mag, freqs, LOW_F, HIGH_F)
            total_e = float(np.sum(mag) + 1e-9)
            ratio = band_e / total_e  # how dominant siren band is

            # track modulation (siren usually wails up/down)
            modulation_history.append(ratio)
            if len(modulation_history) > 12:
                modulation_history.pop(0)

            # simple modulation check: std dev above threshold + strong band
            mod_ok = (np.std(modulation_history) > 0.02)
            strong_band = ratio > 0.35

            now = time.time()
            if mod_ok and strong_band and (now - last_trigger) > cooldown:
                last_trigger = now
                # choose a direction (in real-world, map cam/sensor → approach road)
                direction = random.choice(['North', 'East', 'South', 'West'])
                on_detect(direction)
            time.sleep(0.01)
    except Exception as e:
        print("[siren] Mic loop error:", e)
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        try:
            p.terminate()
        except Exception:
            pass
        print("[siren] Mic listener stopped.")


def _random_fallback_loop(on_detect, cooldown):
    print("[siren] PyAudio not available. Using RANDOM fallback detection.")
    last = 0
    while True:
        now = time.time()
        if now - last > cooldown:
            # ~25% chance to trigger per window
            if random.random() < 0.25:
                last = now
                direction = random.choice(['North', 'East', 'South', 'West'])
                on_detect(direction)
        time.sleep(1)


def start_siren_listener(on_detect, cooldown=15):
    """
    Starts a background thread that calls on_detect(direction) when siren detected.
    Returns immediately.
    """
    target = _mic_loop if HAVE_MIC else _random_fallback_loop
    t = threading.Thread(target=target, args=(on_detect, cooldown), daemon=True)
    t.start()
    return t
