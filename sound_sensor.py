import time
import random

last_trigger_time = 0
cooldown = 20  # seconds

def check_emergency_sound(current_emergency):
    global last_trigger_time
    now = time.time()

    if current_emergency or (now - last_trigger_time < cooldown):
        return None

    detected = random.choice([True, False, False, False])
    if detected:
        last_trigger_time = now
        return random.choice(['North', 'East', 'South', 'West'])

    return None
