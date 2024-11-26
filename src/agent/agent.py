from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.simulation.render import Renderer
from src.utils.reward_function import RewardFunction


class Agent:
    def __init__(self, grid_size, cell_size, colors):
        """Initialize the agent and dependencies."""
        self.environment = Environment(grid_size=grid_size, cell_size=cell_size)
        self.renderer = Renderer(grid_size=grid_size, cell_size=cell_size, colors=colors, window_size=grid_size * cell_size)
        self.event_simulator = EventSimulator(grid_size=grid_size, config_path="src/configs/event_patterns.json")
        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.reward_function = RewardFunction()

        # Set event simulator in environment
        self.environment.set_event_simulator(self.event_simulator)

        self.reset()

    def reset(self):
        """Reset the agent and dependencies."""
        self.environment.reset()
        self.event_simulator.update_events(self.environment.current_time)
        self.environment.update_dynamic_events()  # Update dynamic events on reset
        self.locations_manager.reset()
        self.reward_function.reset()

    def render_environment(self):
        """Render the environment."""
        pick_up_points = self.locations_manager.get_pick_up_points()
        drop_off_points = self.locations_manager.get_drop_off_points()

        # Update obstacles and no-fly zones from the event simulator
        self.environment.update_dynamic_events()  # Ensure dynamic events are up-to-date

        # Pass updated data to the renderer
        self.renderer.render(
            environment=self.environment,
            pick_up_points=pick_up_points,
            drop_off_points=drop_off_points
        )

    def perform_action(self, action):
        """Perform an action in the environment."""
        current_x, current_y = self.environment.drone_pos
        new_pos = None

        # Determine new position based on action
        if action == "UP":
            new_pos = (current_x, current_y - 1)
        elif action == "DOWN":
            new_pos = (current_x, current_y + 1)
        elif action == "LEFT":
            new_pos = (current_x - 1, current_y)
        elif action == "RIGHT":
            new_pos = (current_x + 1, current_y)
        else:
            raise ValueError(f"Invalid action: {action}")

        action_result = {"type": "move", "success": True, "target": None}
        grid_size = self.environment.grid_size

        # Ensure that new position is within grid bounds
        if 0 <= new_pos[0] < grid_size and 0 <= new_pos[1] < grid_size:
            # Update drone position since we allow it to move into any cell within bounds
            self.environment.drone_pos = new_pos

            # Check for event zones or special tiles
            if new_pos in self.environment.obstacles:
                # Obstacle encountered
                action_result.update({"type": "obstacle", "success": True, "target": "obstacle"})
            elif new_pos in self.environment.no_fly_zones:
                # No-fly zone encountered
                action_result.update({"type": "no-fly-zone", "success": True, "target": "no-fly-zone"})
            elif new_pos in self.locations_manager.get_pick_up_points():
                # Handle a valid pickup
                self._handle_pickup(new_pos, action_result)
            elif new_pos in self.locations_manager.get_drop_off_points():
                # Handle a valid drop-off
                self._handle_dropoff(new_pos, action_result)
            else:
                # Valid move to a neutral tile
                action_result.update({"type": "move", "success": True, "target": None})
        else:
            # Out-of-bounds move attempted
            action_result.update({"type": "move", "success": False, "target": "out-of-bounds"})

        # Calculate reward based on the tile and action result
        reward = self.reward_function.calculate_reward(
            new_pos, self.environment, action_result
        )
        print(f"Action: {action_result}, Reward: {reward}")
        self.environment.advance_time()

        return action_result, reward


    def _handle_event_zone(self, new_pos, zone_type, action_result):
        """Handle actions when the drone enters an event zone (e.g., obstacle, no-fly-zone)."""
        action_result.update({"type": zone_type, "success": True, "target": zone_type})

    def _handle_pickup(self, new_pos, action_result):
        """Handle picking up a package."""
        pick_up_points = self.locations_manager.get_pick_up_points()
        if not self.environment.is_carrying_package and new_pos in pick_up_points:
            task_id = pick_up_points[new_pos]
            self.locations_manager.pick_up_points.pop(new_pos)
            self.environment.is_carrying_package = True
            self.environment.current_delivery = task_id
            action_result.update({"type": "pick-up", "success": True, "target": task_id})
        else:
            action_result.update({"type": "pick-up", "success": False})

    def _handle_dropoff(self, new_pos, action_result):
        """Handle dropping off a package."""
        drop_off_points = self.locations_manager.get_drop_off_points()
        if (
                self.environment.is_carrying_package
                and new_pos in drop_off_points
                and drop_off_points[new_pos] == self.environment.current_delivery
        ):
            task_id = drop_off_points[new_pos]
            self.locations_manager.drop_off_points.pop(new_pos)
            self.environment.is_carrying_package = False
            self.environment.current_delivery = None
            action_result.update({"type": "drop-off", "success": True, "target": task_id})
        else:
            action_result.update({"type": "drop-off", "success": False})

    def _check_delivery_status(self, new_pos, action_result):
        """Check if the drone has reached a pick-up or drop-off point."""
        pick_up_points = self.locations_manager.get_pick_up_points()
        drop_off_points = self.locations_manager.get_drop_off_points()

        if self.environment.is_carrying_package:
            if new_pos in drop_off_points and drop_off_points[new_pos] == self.environment.current_delivery:
                task_id = drop_off_points[new_pos]
                self.locations_manager.drop_off_points.pop(new_pos)
                self.environment.is_carrying_package = False
                self.environment.package_count -= 1
                self.environment.current_delivery = None
                action_result.update({"type": "drop-off", "success": True, "target": task_id})
            else:
                action_result.update({"type": "drop-off", "success": False})
        elif not self.environment.is_carrying_package:
            if new_pos in pick_up_points:
                task_id = pick_up_points[new_pos]
                self.locations_manager.pick_up_points.pop(new_pos)
                self.environment.is_carrying_package = True
                self.environment.package_count += 1
                self.environment.current_delivery = task_id
                action_result.update({"type": "pick-up", "success": True, "target": task_id})
            else:
                action_result.update({"type": "pick-up", "success": False})

    def check_completion(self):
        """Check if all deliveries are completed."""
        return not self.locations_manager.get_pick_up_points() and not self.environment.is_carrying_package
