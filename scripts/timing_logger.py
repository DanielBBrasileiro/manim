import json
import time

class TimingLogger:
    def __init__(self, output_path="timing.json"):
        self.output_path = output_path
        self.events = []
        self.start_time = 0

    def start(self):
        self.start_time = 0 # In Manim, we use internal time (seconds)

    def log(self, event_name, timestamp):
        """Log an event with a timestamp in seconds."""
        self.events.append({
            "event": event_name,
            "timestamp_ms": int(timestamp * 1000)
        })
        print(f"DEBUG: Logged {event_name} at {timestamp}s")

    def save(self):
        with open(self.output_path, "w") as f:
            json.dump(self.events, f, indent=2)
        print(f"✅ Timing exported to {self.output_path}")

# Global logger instance for scenes
logger = TimingLogger()
