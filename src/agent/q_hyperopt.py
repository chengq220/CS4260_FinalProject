import pygame
import pickle
import random
from collections import defaultdict
from src.simulation.environment import Environment
from src.simulation.event_simulator import EventSimulator
from src.simulation.locations_manager import LocationsManager
from src.utils.reward_function import RewardFunction
import optuna

pygame.init()

# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
TIME_STEP = 10
ZONE_CHANGE_INTERVAL = 120
Q_TABLE_FILE = "q_table.pkl"

class QLearningHyperopt:
    def __init__(self, alpha, gamma, initial_epsilon, min_epsilon, epsilon_decay, training_episodes=5000):
        """Initialize the Q-Learning training environment with hyperparameters."""
        self.environment = Environment(grid_size=GRID_SIZE, cell_size=CELL_SIZE)
        self.event_simulator = EventSimulator(grid_size=GRID_SIZE, config_path="src/configs/event_patterns.json")
        self.environment.set_event_simulator(self.event_simulator)

        self.locations_manager = LocationsManager(config_path="src/configs/pick_up_drop_off_config.json")
        self.environment.set_locations_manager(self.locations_manager)

        self.reward_function = RewardFunction()

        self.q_table = defaultdict(lambda: defaultdict(float))  # Q-table
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT"]

        # Hyperparameters
        self.alpha = alpha
        self.gamma = gamma
        self.initial_epsilon = initial_epsilon
        self.min_epsilon = min_epsilon
        self.epsilon_decay = epsilon_decay
        self.training_episodes = training_episodes
        self.epsilon = self.initial_epsilon

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
        self.q_table[state][action] += self.alpha * (reward + self.gamma * next_q_value - self.q_table[state][action])

    def train(self):
        """Train the Q-Learning agent."""
        total_rewards = []

        for episode in range(self.training_episodes):
            self.environment.reset()
            self.reward_function.reset()
            self.locations_manager.reset()
            self.environment.update_dynamic_events()

            state = self.environment.drone_pos
            total_reward = 0
            steps_without_progress = 0
            visited_states = set()

            while self.locations_manager.get_pick_up_points():
                valid_neighbors = self.get_neighbors(state)
                if not valid_neighbors:
                    break

                action = self.choose_action(state)
                if not action:
                    break

                next_state = valid_neighbors[action]
                self.environment.drone_pos = next_state
                visited_states.add(next_state)

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
                    steps_without_progress = 0
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
                    steps_without_progress = 0
                elif next_state in self.environment.obstacles:
                    action_type = "obstacle"
                elif next_state in self.environment.no_fly_zones:
                    action_type = "no-fly-zone"

                # Calculate reward
                reward = self.reward_function.calculate_reward(
                    next_state, self.environment, {"type": action_type, "success": True}
                )
                # Penalize revisiting states unnecessarily
                if next_state in visited_states:
                    reward -= 5
                self.update_q_value(state, action, reward, next_state)
                total_reward += reward

                # Advance time and update environment
                self.environment.advance_time()
                self.environment.update_dynamic_events()
                state = next_state

                # Track progress inefficiency
                steps_without_progress += 1
                if steps_without_progress > 500:
                    break

            # Decay epsilon
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
            total_rewards.append(total_reward)

        return sum(total_rewards) / len(total_rewards)  # Average reward


def objective(trial):
    """Objective function for hyperparameter optimization."""
    alpha = trial.suggest_float("alpha", 0.001, 0.1, log=True)
    gamma = trial.suggest_float("gamma", 0.5, 0.99)
    initial_epsilon = trial.suggest_float("initial_epsilon", 0.1, 1.0)
    min_epsilon = trial.suggest_float("min_epsilon", 0.01, 0.1)
    epsilon_decay = trial.suggest_float("epsilon_decay", 0.95, 0.9999)

    agent = QLearningHyperopt(
        alpha=alpha,
        gamma=gamma,
        initial_epsilon=initial_epsilon,
        min_epsilon=min_epsilon,
        epsilon_decay=epsilon_decay,
        training_episodes=2000
    )

    average_reward = agent.train()
    return average_reward


if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)

    print("Best hyperparameters:")
    print(study.best_params)
    print(f"Best average reward: {study.best_value}")

    # Save the best Q-table
    with open(Q_TABLE_FILE, "wb") as f:
        pickle.dump(study.best_params, f)

    pygame.quit()
