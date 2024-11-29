import pygame
from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.utils.reward_function import RewardFunction
from src.simulation.render import Renderer
from heapq import heappop, heappush

pygame.init()

# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
TIME_STEP = 10  # Each drone move advances time by 10 minutes
ZONE_CHANGE_INTERVAL = 120  # Zones change every 2 hours (120 minutes)

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


class CSPAgent:
    def __init__(self, render=True):
        """Initialize the CSP agent environment."""
        self.environment = Environment(grid_size=GRID_SIZE, cell_size=CELL_SIZE)
        self.event_simulator = EventSimulator(grid_size=GRID_SIZE, config_path="src/configs/event_patterns.json")
        self.environment.set_event_simulator(self.event_simulator)

        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.environment.set_locations_manager(self.locations_manager)

        self.reward_function = RewardFunction()
        self.renderer = Renderer(grid_size=GRID_SIZE, cell_size=CELL_SIZE, colors=COLORS, window_size=WINDOW_SIZE)
        self.render = render

    def find_path(self, start, target):
        """Find a path from start to target."""
        self.environment.update_dynamic_events()  # Ensure dynamic zones are up-to-date

        # Priority queue for CSP-based search
        queue = [(0, start)]  # (cost, position)
        came_from = {}
        cost_so_far = {start: 0}

        while queue:
            current_cost, current = heappop(queue)

            # Stop if target is reached
            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for neighbor in self.get_neighbors(current, cost_so_far[current]):
                new_cost = current_cost + 1  # Uniform cost for valid moves
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.helper(neighbor, target)
                    heappush(queue, (priority, neighbor))
                    came_from[neighbor] = current

        return []  # No valid path found

    def get_neighbors(self, position, current_cost):
        """
        Get valid neighboring positions, excluding zones that will be active
        by the time the drone reaches them.
        """
        x, y = position
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        # Calculate the estimated time the drone will reach each neighbor
        time_to_reach = self.environment.current_time + (current_cost + 1) * TIME_STEP

        valid_neighbors = [
            n for n in neighbors
            if 0 <= n[0] < self.environment.grid_size
            and 0 <= n[1] < self.environment.grid_size
            and n not in self.environment.obstacles
            and n not in self.environment.no_fly_zones
            and not self.will_zone_be_active(n, time_to_reach)
        ]
        return valid_neighbors

    def will_zone_be_active(self, position, estimated_time):
        """
        Check if a position will be part of an active zone by the estimated time.
        """
        future_zones = self.environment.future_obstacles | self.environment.future_no_fly_zones
        if position not in future_zones:
            return False

        # Calculate when the future zone becomes active
        current_interval = (self.environment.current_time // ZONE_CHANGE_INTERVAL)
        activation_time = (current_interval + 1) * ZONE_CHANGE_INTERVAL

        # If the zone will be active by the time the drone reaches it, return True
        return estimated_time >= activation_time

    def helper(self, position, target):
        """Helper function to help calculate target distance."""
        return abs(position[0] - target[0]) + abs(position[1] - target[1])

    def move_to_target(self, path, target):
        """Move along the path step by step, retrying or waiting when necessary."""
        for current_pos in path:
            self.environment.drone_pos = current_pos

            # Determine the current tile type
            if current_pos in self.environment.obstacles:
                action_type = "obstacle"
            elif current_pos in self.environment.no_fly_zones:
                action_type = "no-fly-zone"
            elif current_pos in self.environment.future_obstacles:
                action_type = "future-obstacle"
            elif current_pos in self.environment.future_no_fly_zones:
                action_type = "future-no-fly-zone"
            else:
                action_type = "move"

            # Apply rewards/penalties
            self.reward_function.calculate_reward(
                current_pos, self.environment, {"type": action_type, "success": True}
            )

            # Update time and dynamic events
            self.environment.advance_time()
            self.environment.update_dynamic_events()

            if self.render:
                self.renderer.render(
                    environment=self.environment,
                    pick_up_points=self.locations_manager.get_pick_up_points(),
                    drop_off_points=self.locations_manager.get_drop_off_points()
                )
                pygame.time.wait(100)  # Add delay for visualization
            print(f"Moved to {current_pos}, Current Total Reward: {self.reward_function.total_reward}")

        # Retry if the path becomes blocked
        if self.environment.drone_pos != target:
            print(f"Path blocked. Waiting or recalculating path to {target}...")
            return False  # Indicate failure to reach target
        return True  # Successfully reached target

    def run(self):
        """Run the CSP agent to complete all deliveries."""
        self.environment.reset()
        self.reward_function.reset()
        self.locations_manager.reset()

        while self.locations_manager.get_pick_up_points():
            current_pos = self.environment.drone_pos
            pick_up_points = list(self.locations_manager.get_pick_up_points().keys())
            drop_off_points = {v: k for k, v in self.locations_manager.get_drop_off_points().items()}

            # Find the closest pick-up point
            closest_pickup = self.find_closest(current_pos, pick_up_points)

            # Keep trying to reach the pick-up point
            print(f"Heading to pick-up point: {closest_pickup}")
            success = False
            while not success:
                path_to_pickup = self.find_path(current_pos, closest_pickup)
                if not path_to_pickup:
                    self.environment.advance_time()
                    self.environment.update_dynamic_events()
                    print("No path available. Waiting...")
                else:
                    success = self.move_to_target(path_to_pickup, closest_pickup)

            # Perform pick-up
            self.environment.is_carrying_package = True
            task_id = self.locations_manager.get_pick_up_points()[closest_pickup]
            self.locations_manager.pick_up_points.pop(closest_pickup)
            reward = self.reward_function.calculate_reward(
                closest_pickup, self.environment, {"type": "pick-up", "success": True}
            )
            print(f"Picked up package {task_id} at {closest_pickup}, Current Total Reward: {self.reward_function.total_reward}")

            # Keep trying to reach the drop-off point
            drop_off_pos = drop_off_points[task_id]
            print(f"Heading to drop-off point: {drop_off_pos}")
            success = False
            while not success:
                path_to_dropoff = self.find_path(self.environment.drone_pos, drop_off_pos)
                if not path_to_dropoff:
                    self.environment.advance_time()
                    self.environment.update_dynamic_events()
                    print("No path available. Waiting...")
                else:
                    success = self.move_to_target(path_to_dropoff, drop_off_pos)

            # Perform drop-off
            self.environment.is_carrying_package = False
            self.locations_manager.drop_off_points.pop(drop_off_pos)
            reward = self.reward_function.calculate_reward(
                drop_off_pos, self.environment, {"type": "drop-off", "success": True}
            )
            print(f"Dropped off package {task_id} at {drop_off_pos}, Current Total Reward: {self.reward_function.total_reward}")

        print("All deliveries completed!")
        print(f"Final Total Reward: {self.reward_function.total_reward}")

    def find_closest(self, current_pos, points):
        """Find the closest point to the current position."""
        return min(points, key=lambda p: abs(p[0] - current_pos[0]) + abs(p[1] - current_pos[1]))


if __name__ == "__main__":
    game = CSPAgent(render=True)
    game.run()
    pygame.quit()
