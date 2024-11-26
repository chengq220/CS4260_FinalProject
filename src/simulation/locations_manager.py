import json
import os

class LocationsManager:
    def __init__(self, config_path="pick_up_drop_off_config.json"):
        """
        Initialize the LocationsManager with a configuration file.
        Args:
            config_path (str): Path to the pickup/dropoff configuration file.
        """
        config_path = os.path.join(os.path.dirname(__file__), "../configs", os.path.basename(config_path))
        with open(config_path, "r") as file:
            self.delivery_tasks = json.load(file).get("deliveries1", [])

        self.pick_up_points = {tuple(task["pick_up"]): task["id"] for task in self.delivery_tasks}
        self.drop_off_points = {tuple(task["drop_off"]): task["id"] for task in self.delivery_tasks}

    def get_pick_up_points(self):
        """Return a dictionary of pickup points with their IDs."""
        return self.pick_up_points

    def get_drop_off_points(self):
        """Return a dictionary of dropoff points with their IDs."""
        return self.drop_off_points

    def reset(self):
        """Reset pickup/dropoff points to their initial state."""
        self.pick_up_points = {tuple(task["pick_up"]): task["id"] for task in self.delivery_tasks}
        self.drop_off_points = {tuple(task["drop_off"]): task["id"] for task in self.delivery_tasks}
