import pygame
import random
import pickle
from collections import defaultdict
from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.utils.reward_function import RewardFunction

pygame.init()

# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
TIME_STEP = 10
ZONE_CHANGE_INTERVAL = 120
ALPHA = 0.050006675157307896
GAMMA = 0.7090138948652172
INITIAL_EPSILON = 0.8232899215037156
MIN_EPSILON = 0.016014465144631326
EPSILON_DECAY = 0.9994591930101796
Q_TABLE_FILE = "q_table.pkl"

class QLearningTrainer:
    def __init__(self):
        """Initialize the Q-Learning training environment."""
        self.environment = Environment(grid_size=GRID_SIZE, cell_size=CELL_SIZE)
        self.event_simulator = EventSimulator(grid_size=GRID_SIZE, config_path="src/configs/event_patterns.json")
        self.environment.set_event_simulator(self.event_simulator)

        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.environment.set_locations_manager(self.locations_manager)

        self.reward_function = RewardFunction()

        self.q_table = defaultdict(lambda: defaultdict(float))  # Q-table
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        self.training_episodes = 10000
        self.epsilon = INITIAL_EPSILON

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

    def choose_action(self, state):
        """Choose an action using an epsilon-greedy policy."""
        valid_neighbors = self.get_neighbors(state)
        if not valid_neighbors:
            return None
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(list(valid_neighbors.keys()))
        return max(valid_neighbors.keys(), key=lambda action: self.q_table[state][action])

    def update_q_value(self, state, action, reward, next_state):
        """Update the Q-value for a state-action pair."""
        next_valid_actions = self.get_neighbors(next_state).keys()
        next_best_action = max(next_valid_actions, key=lambda a: self.q_table[next_state][a], default=None)
        next_q_value = self.q_table[next_state][next_best_action] if next_best_action else 0
        self.q_table[state][action] += ALPHA * (reward + GAMMA * next_q_value - self.q_table[state][action])

    def train(self):
        """Train the Q-Learning agent."""
        for episode in range(self.training_episodes):
            self.environment.reset()
            self.reward_function.reset()
            self.locations_manager.reset()
            self.environment.update_dynamic_events()

            state = self.environment.drone_pos
            total_reward = 0

            while self.locations_manager.get_pick_up_points() or self.environment.is_carrying_package:
                valid_neighbors = self.get_neighbors(state)
                if not valid_neighbors:
                    break

                action = self.choose_action(state)
                if not action:
                    break

                next_state = valid_neighbors[action]
                self.environment.drone_pos = next_state

                # Handle pick-up and drop-off logic
                action_type = "move"
                reward = 0  # Base reward for the action
                if (
                    next_state in self.locations_manager.get_pick_up_points()
                    and not self.environment.is_carrying_package
                ):
                    task_id = self.locations_manager.get_pick_up_points()[next_state]
                    self.locations_manager.pick_up_points.pop(next_state)
                    self.environment.is_carrying_package = True
                    self.environment.current_delivery = task_id
                    action_type = "pick-up"
                    reward += 50  # Reward for successfully picking up a package
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
                    reward += 100  # Reward for successfully delivering a package
                elif next_state in self.environment.obstacles:
                    action_type = "obstacle"
                elif next_state in self.environment.no_fly_zones:
                    action_type = "no-fly-zone"

                # Reward for moving closer to the goal
                if self.environment.is_carrying_package:
                    goal = self.locations_manager.get_drop_off_points().get(self.environment.current_delivery)
                else:
                    goal = self.get_closest_pick_up_point()

                if goal:
                    prev_distance = abs(state[0] - goal[0]) + abs(state[1] - goal[1])
                    new_distance = abs(next_state[0] - goal[0]) + abs(next_state[1] - goal[1])
                    if new_distance < prev_distance:
                        reward += 10  # Reward for moving closer
                    else:
                        reward -= 5  # Penalty for moving further away

                # Update Q-values and total reward
                self.update_q_value(state, action, reward, next_state)
                total_reward += reward

                # Advance time and update environment
                self.environment.advance_time()
                self.environment.update_dynamic_events()
                state = next_state

            # Add bonus reward if all packages are delivered
            if not self.locations_manager.get_pick_up_points() and not self.environment.is_carrying_package:
                total_reward += 1000
                print("All packages delivered! Bonus reward added.")
                self.update_q_value(state, action, 1000, state)

            # Dynamic epsilon decay based on performance
            if total_reward > 0:  # Decay faster for positive rewards
                self.epsilon = max(MIN_EPSILON, self.epsilon * 0.99)
            else:
                self.epsilon = max(MIN_EPSILON, self.epsilon * EPSILON_DECAY)

            print(f"Episode {episode + 1}/{self.training_episodes}: Total Reward: {total_reward}")

        # Save the Q-table to a file
        with open(Q_TABLE_FILE, "wb") as f:
            pickle.dump(dict(self.q_table), f)
        print(f"Q-table saved to {Q_TABLE_FILE}")

    def get_closest_pick_up_point(self):
        """Get the closest pick-up point."""
        pick_up_points = self.locations_manager.get_pick_up_points()
        if not pick_up_points:
            return None
        current_pos = self.environment.drone_pos
        return min(
            pick_up_points.keys(),
            key=lambda p: abs(current_pos[0] - p[0]) + abs(current_pos[1] - p[1])
        )

if __name__ == "__main__":
    trainer = QLearningTrainer()
    trainer.train()
    pygame.quit()
