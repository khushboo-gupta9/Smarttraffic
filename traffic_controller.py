class TrafficController:
    def __init__(self):
        self.directions = ["north", "east", "south", "west"]
        self.index = 0
        self.state = {d: "red" for d in self.directions}

        # Timer config
        self.green_time = 15
        self.yellow_time = 3
        self.countdown = self.green_time
        self.phase = "green"  # green → yellow

        self.mode = "auto"
        self.emergency_direction = None
        self.emergency_active = False

    def auto_cycle(self):
        if self.emergency_active:
            self.handle_emergency()
            return

        self.countdown -= 1

        if self.phase == "green" and self.countdown <= 0:
            self.phase = "yellow"
            self.countdown = self.yellow_time

        elif self.phase == "yellow" and self.countdown <= 0:
            self.phase = "green"
            self.index = (self.index + 1) % 4
            self.countdown = self.green_time

        self._set_all_red()
        if self.phase in ["green", "yellow"]:
            self.state[self.directions[self.index]] = self.phase

    def set_emergency(self, direction):
        """Activate emergency mode for given direction"""
        self.emergency_direction = direction
        self.emergency_active = True
        self.countdown = self.green_time  # reset timer for emergency

    def handle_emergency(self):
        self._set_all_red()
        if self.emergency_direction:
            self.state[self.emergency_direction] = "green"
        self.countdown -= 1
        if self.countdown <= 0:
            self.emergency_active = False
            self.emergency_direction = None
            self.phase = "green"
            self.countdown = self.green_time

    def get_status(self):
        return {
            **self.state,
            "mode": self.mode,
            "countdown": self.countdown,
            "phase": self.phase,
            "emergency": self.emergency_active,
            "emergency_direction": self.emergency_direction
        }

    def set_mode(self, mode):
        self.mode = mode

    def set_timer(self, time_val):
        self.green_time = time_val
        self.countdown = self.green_time

    def _set_all_red(self):
        for d in self.directions:
            self.state[d] = "red"


controller = TrafficController()
