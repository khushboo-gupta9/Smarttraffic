# traffic_controller.py

import time

class TrafficController:
    def __init__(self):
        self.directions = ["north", "east", "south", "west"]
        self.index = 0
        self.state = {d: "red" for d in self.directions}
        self.timer = 10
        self.countdown = self.timer
        self.mode = "auto"
        self.emergency_direction = None

    def set_mode(self, mode):
        self.mode = mode
        if mode != "emergency":
            self.emergency_direction = None

    def set_timer(self, timer):
        self.timer = timer

    def set_emergency(self, direction):
        self.mode = "emergency"
        self.emergency_direction = direction
        self.countdown = self.timer

    def auto_cycle(self):
        self.countdown -= 1
        if self.countdown <= 0:
            self.index = (self.index + 1) % 4
            self.countdown = self.timer

        self._set_all_red()
        self.state[self.directions[self.index]] = "green"

    def handle_emergency(self):
        self._set_all_red()
        if self.emergency_direction:
            self.state[self.emergency_direction] = "green"

    def get_status(self):
        return {
            **self.state,
            "mode": self.mode,
            "countdown": self.countdown
        }

    def _set_all_red(self):
        for d in self.directions:
            self.state[d] = "red"

# 🔽 Add this at bottom so app.py can import it
controller = TrafficController()
