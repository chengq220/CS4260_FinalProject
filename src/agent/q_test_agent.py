import pygame
import pickle
from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.utils.reward_function import RewardFunction
from src.simulation.render import Renderer
import random

pygame.init()

# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
Q_TABLE_FILE = "q_table.pkl"
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


class QLearningTester:
    def __init__(self):
        """Initialize the Q-Learning testing environment."""
        self.environment = Environment(grid_size=GRID_SIZE, cell_size=CELL_SIZE)
        self.event_simulator = EventSimulator(grid_size=GRID_SIZE, config_path="src/configs/event_patterns.json")
        self.environment.set_event_simulator(self.event_simulator)

        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.environment.set_locations_manager(self.locations_manager)

        self.reward_function = RewardFunction()
        self.renderer = Renderer(grid_size=GRID_SIZE, cell_size=CELL_SIZE, colors=COLORS, window_size=WINDOW_SIZE)

        # Load the Q-table from a file
        with open(Q_TABLE_FILE, "rb") as f:
            self.q_table = pickle.load(f)

    def choose_action(self, state, last_action=None):
        """Choose the best action based on the Q-table."""
        valid_neighbors = self.get_neighbors(state)
        if not valid_neighbors:
            return last_action  # Continue in the last valid direction
        return max(valid_neighbors.keys(), key=lambda action: self.q_table[state][action])

    def get_neighbors(self, state):
        """Determine valid neighboring states."""
        x, y = state
        neighbors = {
            "UP": (x, y - 1),
            "DOWN": (x, y + 1),
            "LEFT": (x - 1, y),
            "RIGHT": (x + 1, y)
        }
        valid_neighbors = {}
        for action, neighbor in neighbors.items():
            if (0 <= neighbor[0] < GRID_SIZE
                and 0 <= neighbor[1] < GRID_SIZE
                and neighbor not in self.environment.obstacles
                and neighbor not in self.environment.no_fly_zones):
                valid_neighbors[action] = neighbor
        return valid_neighbors

    def run(self):
        """Run the Q-Learning agent in the environment."""
        self.environment.reset()
        self.reward_function.reset()
        self.locations_manager.reset()
        self.environment.update_dynamic_events()

        state = self.environment.drone_pos
        total_reward = 0
        last_action = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])  # Default starting direction

        while self.locations_manager.get_pick_up_points() or self.environment.is_carrying_package:
            valid_neighbors = self.get_neighbors(state)

            if not valid_neighbors:
                action = last_action  # Keep moving in the last valid direction
            else:
                action = self.choose_action(state, last_action)

            next_state = valid_neighbors[action] if action in valid_neighbors else state
            last_action = action

            self.environment.drone_pos = next_state

            # Handle pick-up and drop-off logic
            action_type = "move"
            if (
                next_state in self.locations_manager.get_pick_up_points()
                and not self.environment.is_carrying_package
            ):
                task_id = self.locations_manager.get_pick_up_points()[next_state]
                self.locations_manager.pick_up_points.pop(next_state)
                self.environment.is_carrying_package = True
                self.environment.current_delivery = task_id
                action_type = "pick-up"
            elif (
                next_state in self.locations_manager.get_drop_off_points()
                and self.environment.is_carrying_package
                and self.locations_manager.get_drop_off_points()[next_state] == self.environment.current_delivery
            ):
                task_id = self.locations_manager.get_drop_off_points()[next_state]
                self.locations_manager.drop_off_points.pop(next_state)
                self.environment.is_carrying_package = False
                self.environment.current_delivery = None
                action_type = "drop-off"
            elif next_state in self.environment.obstacles:
                action_type = "obstacle"
            elif next_state in self.environment.no_fly_zones:
                action_type = "no-fly-zone"

            # Calculate reward
            reward = self.reward_function.calculate_reward(
                next_state, self.environment, {"type": action_type, "success": True}
            )
            total_reward += reward

            # Check for termination condition
            if total_reward < -500:
                print(f"Terminating early: Total Reward: {total_reward}")
                break

            # Advance time and update environment
            self.environment.advance_time()
            self.environment.update_dynamic_events()
            state = next_state

            self.renderer.render(
                environment=self.environment,
                pick_up_points=self.locations_manager.get_pick_up_points(),
                drop_off_points=self.locations_manager.get_drop_off_points()
            )
            pygame.time.wait(100)

            print(f"Moved to {state}, Total Reward: {total_reward}")


        print(f"Final Total Reward: {total_reward}")

if __name__ == "__main__":
    tester = QLearningTester()
    tester.run()
    pygame.quit()
