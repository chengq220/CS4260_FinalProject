import json
import os

# Event pattern to use from the configuration file
pattern = "patterns1"

class EventSimulator:
    def __init__(self, grid_size, config_path):
        """
        Initializes the EventSimulator to generate obstacles and no-fly zones.
        Args:
            grid_size (int): The size of the grid (number of cells).
            config_path (str): Path to the event patterns configuration file.
        """
        self.grid_size = grid_size
        self.obstacles = []  # List of obstacle coordinates
        self.no_fly_zones = []  # List of no-fly zone coordinates

        # Load event patterns from the configuration file
        config_path = os.path.join(os.path.dirname(__file__), "../configs", os.path.basename(config_path))
        with open(config_path, 'r') as file:
            self.event_patterns = json.load(file).get(pattern, [])

    def get_current_pattern(self, current_time):
        """
        Get the obstacle and no-fly zone pattern for the given time.
        Args:
            current_time (int): The current time in the simulation (in minutes).
        Returns:
            dict: The pattern containing obstacles and no-fly zones for the current time.
        """
        for pattern in self.event_patterns:
            start, end = pattern.get("time_range", (0, 0))
            if start <= current_time < end:
                return pattern
        return {}

    def get_next_pattern(self, current_time):
        """
        Get the next obstacle and no-fly zone pattern for the time after the current period.
        Args:
            current_time (int): The current time in the simulation (in minutes).
        Returns:
            dict: The pattern containing obstacles and no-fly zones for the next time slot.
        """
        for i, pattern in enumerate(self.event_patterns):
            start, end = pattern.get("time_range", (0, 0))
            if start <= current_time < end:
                # Return the next pattern if it exists
                return self.event_patterns[i + 1] if i + 1 < len(self.event_patterns) else {}
        return {}

    def update_events(self, current_time):
        """
        Update the obstacles and no-fly zones based on the current time.
        Args:
            current_time (int): The current time in the simulation (in minutes).
        """
        pattern = self.get_current_pattern(current_time)
        self.obstacles = pattern.get("obstacles", [])
        self.no_fly_zones = pattern.get("no_fly_zones", [])

    def get_obstacles(self):
        """
        Returns the current list of obstacles.
        Returns:
            list: A list of (x, y) tuples representing obstacle coordinates.
        """
        return self.obstacles

    def get_no_fly_zones(self):
        """
        Returns the current list of no-fly zones.
        Returns:
            list: A list of (x, y) tuples representing no-fly zone coordinates.
        """
        return self.no_fly_zones
