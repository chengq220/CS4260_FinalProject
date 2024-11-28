import pygame
from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.utils.reward_function import RewardFunction
from src.simulation.render import Renderer

pygame.init()

# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE

# Colors
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GRAY": (200, 200, 200),
    "RED": (255, 0, 0),
    "BLUE": (0, 0, 255),
    "GREEN": (0, 255, 0),
    "YELLOW": (255, 255, 0),
    "PURPLE": (128, 0, 128),
    "ORANGE": (255, 165, 0),
}


class BadAgent:
    def __init__(self, render=True):
        """Initialize the bad agent environment."""
        self.environment = Environment(grid_size=GRID_SIZE, cell_size=CELL_SIZE)
        self.event_simulator = EventSimulator(grid_size=GRID_SIZE, config_path="src/configs/event_patterns.json")
        self.environment.set_event_simulator(self.event_simulator)

        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.environment.set_locations_manager(self.locations_manager)

        self.reward_function = RewardFunction()
        self.renderer = Renderer(grid_size=GRID_SIZE, cell_size=CELL_SIZE, colors=COLORS, window_size=WINDOW_SIZE)
        self.render = render

    def find_closest(self, current_pos, points):
        """Find the closest point to the current position."""
        return min(points, key=lambda p: abs(p[0] - current_pos[0]) + abs(p[1] - current_pos[1]))

    def move_to_target(self, current_pos, target_pos):
        """Move step by step to the target position."""
        path = []
        while current_pos != target_pos:
            x, y = current_pos
            if x < target_pos[0]:
                current_pos = (x + 1, y)
            elif x > target_pos[0]:
                current_pos = (x - 1, y)
            elif y < target_pos[1]:
                current_pos = (x, y + 1)
            elif y > target_pos[1]:
                current_pos = (x, y - 1)

            path.append(current_pos)
            # Move drone position and calculate rewards
            self.environment.drone_pos = current_pos

            # Determine the current tile type
            if current_pos in self.environment.obstacles:
                action_type = "obstacle"
            elif current_pos in self.environment.no_fly_zones:
                action_type = "no-fly-zone"
            else:
                action_type = "move"

            # Apply rewards/penalties
            reward = self.reward_function.calculate_reward(
                current_pos, self.environment, {"type": action_type, "success": True}
            )

            # Update time and dynamic events
            self.environment.advance_time()
            self.environment.update_dynamic_events()  # Ensure dynamic zones are updated

            if self.render:
                self.renderer.render(
                    environment=self.environment,
                    pick_up_points=self.locations_manager.get_pick_up_points(),
                    drop_off_points=self.locations_manager.get_drop_off_points()
                )
                pygame.time.wait(100)  # Add delay for visualization
            print(f"Moved to {current_pos}, Current Total Reward: {self.reward_function.total_reward}")

        return path

    def run(self):
        """Run the bad agent to complete all deliveries."""
        self.environment.reset()
        self.reward_function.reset()
        self.locations_manager.reset()

        while self.locations_manager.get_pick_up_points():
            current_pos = self.environment.drone_pos
            pick_up_points = list(self.locations_manager.get_pick_up_points().keys())
            drop_off_points = {v: k for k, v in self.locations_manager.get_drop_off_points().items()}

            # Find the closest pick-up point
            closest_pickup = self.find_closest(current_pos, pick_up_points)

            # Move to the pick-up point
            print(f"Heading to pick-up point: {closest_pickup}")
            self.move_to_target(current_pos, closest_pickup)

            # Perform pick-up
            self.environment.is_carrying_package = True
            task_id = self.locations_manager.get_pick_up_points()[closest_pickup]
            self.locations_manager.pick_up_points.pop(closest_pickup)
            reward = self.reward_function.calculate_reward(
                closest_pickup, self.environment, {"type": "pick-up", "success": True}
            )
            print(f"Picked up package {task_id} at {closest_pickup}, Current Total Reward: {self.reward_function.total_reward}")

            # Move to the corresponding drop-off point
            drop_off_pos = drop_off_points[task_id]
            print(f"Heading to drop-off point: {drop_off_pos}")
            self.move_to_target(self.environment.drone_pos, drop_off_pos)

            # Perform drop-off
            self.environment.is_carrying_package = False
            self.locations_manager.drop_off_points.pop(drop_off_pos)
            reward = self.reward_function.calculate_reward(
                drop_off_pos, self.environment, {"type": "drop-off", "success": True}
            )
            print(f"Dropped off package {task_id} at {drop_off_pos}, Current Total Reward: {self.reward_function.total_reward}")

        print("All deliveries completed!")
        print(f"Final Total Reward: {self.reward_function.total_reward}")


if __name__ == "__main__":
    game = BadAgent(render=True)
    game.run()
    pygame.quit()
