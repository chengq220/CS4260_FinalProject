import pygame
import json
import os
from src.simulation.event_simulator import EventSimulator
from src.utils.reward_function import RewardFunction

# Constants for the grid environment
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)


class Environment:
    def __init__(self, time_step=10, config_path="pick_up_drop_off_config.json"):
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Drone Delivery Environment")
        self.clock = pygame.time.Clock()

        # Drone and grid setup
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drone_pos = (0, 0)
        self.is_carrying_package = False
        self.package_count = 0
        self.current_delivery = None

        # Load delivery points
        config_path = os.path.join(os.path.dirname(__file__), "../configs", os.path.basename(config_path))
        self.delivery_tasks = self.load_deliveries_from_config(config_path)
        self.pick_up_points = {tuple(task["pick_up"]): task["id"] for task in self.delivery_tasks}
        self.drop_off_points = {tuple(task["drop_off"]): task["id"] for task in self.delivery_tasks}

        # Time and dynamic events
        self.current_time = 0
        self.time_step = time_step
        self.event_simulator = EventSimulator(GRID_SIZE, "src/configs/event_patterns.json")

        # Obstacles and no-fly zones dictionaries for consistency
        self.obstacles = {}
        self.no_fly_zones = {}

        # Reward function
        self.reward_function = RewardFunction()
        self.reset()

    def load_deliveries_from_config(self, config_path):
        with open(config_path, 'r') as file:
            return json.load(file)["deliveries"]

    def reset(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drone_pos = (0, 0)
        self.is_carrying_package = False
        self.package_count = 0
        self.current_delivery = None
        self.pick_up_points = {tuple(task["pick_up"]): task["id"] for task in self.delivery_tasks}
        self.drop_off_points = {tuple(task["drop_off"]): task["id"] for task in self.delivery_tasks}
        self.current_time = 0
        self.update_dynamic_events()
        self.reward_function.reset()

    def update_dynamic_events(self):
        """Synchronize obstacles and no-fly zones with event simulator."""
        self.event_simulator.update_events(self.current_time)
        self.obstacles = {tuple(pos): "obstacle" for pos in self.event_simulator.get_obstacles()}
        self.no_fly_zones = {tuple(pos): "no-fly-zone" for pos in self.event_simulator.get_no_fly_zones()}

    def render(self):
        self.window.fill(WHITE)

        for x in range(0, WINDOW_SIZE, CELL_SIZE):
            for y in range(0, WINDOW_SIZE, CELL_SIZE):
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.window, GRAY, rect, 1)

        for obs in self.obstacles:
            rect = pygame.Rect(obs[0] * CELL_SIZE, obs[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.window, RED, rect)

        for no_fly in self.no_fly_zones:
            rect = pygame.Rect(no_fly[0] * CELL_SIZE, no_fly[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.window, YELLOW, rect)

        for pick_up, task_id in self.pick_up_points.items():
            rect = pygame.Rect(pick_up[0] * CELL_SIZE, pick_up[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.window, PURPLE, rect)
            font = pygame.font.Font(None, 24)
            id_surface = font.render(str(task_id), True, WHITE)
            self.window.blit(id_surface, (pick_up[0] * CELL_SIZE + 5, pick_up[1] * CELL_SIZE + 5))

        for drop_off, task_id in self.drop_off_points.items():
            rect = pygame.Rect(drop_off[0] * CELL_SIZE, drop_off[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.window, ORANGE, rect)
            font = pygame.font.Font(None, 24)
            id_surface = font.render(str(task_id), True, WHITE)
            self.window.blit(id_surface, (drop_off[0] * CELL_SIZE + 5, drop_off[1] * CELL_SIZE + 5))

        rect = pygame.Rect(self.drone_pos[0] * CELL_SIZE, self.drone_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        drone_color = BLUE if not self.is_carrying_package else GREEN
        pygame.draw.rect(self.window, drone_color, rect)

        font = pygame.font.Font(None, 36)
        time_surface = font.render(f"Time: {self.get_formatted_time()}", True, BLACK)
        package_surface = font.render(f"Packages: {self.package_count}", True, BLACK)
        self.window.blit(time_surface, (10, 10))
        self.window.blit(package_surface, (10, 50))
        pygame.display.flip()

    def update_drone_position(self, new_pos):
        action_result = {"type": "move", "success": True, "target": None}

        if 0 <= new_pos[0] < GRID_SIZE and 0 <= new_pos[1] < GRID_SIZE:
            self.drone_pos = new_pos  # Move drone regardless of the zone
            if new_pos in self.obstacles:
                action_result.update({"type": "move", "success": True, "target": "obstacle"})
            elif new_pos in self.no_fly_zones:
                action_result.update({"type": "move", "success": True, "target": "no-fly-zone"})
            self.check_delivery_status(action_result)
        else:
            action_result.update({"type": "move", "success": False, "target": "out-of-bounds"})

        reward = self.reward_function.calculate_reward(new_pos, self, action_result)
        print(f"Action: {action_result}, Reward: {reward}")
        self.advance_time()

    def check_delivery_status(self, action_result):
        if self.is_carrying_package and self.drone_pos in self.drop_off_points:
            task_id = self.drop_off_points[self.drone_pos]
            if task_id == self.current_delivery:
                self.drop_off_points.pop(self.drone_pos)
                self.is_carrying_package = False
                self.package_count -= 1
                self.current_delivery = None
                action_result.update({"type": "drop-off", "success": True, "target": task_id})
        elif not self.is_carrying_package and self.drone_pos in self.pick_up_points:
            task_id = self.pick_up_points.pop(self.drone_pos)
            self.is_carrying_package = True
            self.package_count += 1
            self.current_delivery = task_id
            action_result.update({"type": "pick-up", "success": True, "target": task_id})

    def advance_time(self):
        self.current_time = (self.current_time + self.time_step) % (24 * 60)
        self.update_dynamic_events()

    def get_formatted_time(self):
        hours = self.current_time // 60
        minutes = self.current_time % 60
        return f"{hours:02d}:{minutes:02d}"

    def run_simulation(self):
        self.reset()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.update_drone_position((self.drone_pos[0], self.drone_pos[1] - 1))
                    elif event.key == pygame.K_DOWN:
                        self.update_drone_position((self.drone_pos[0], self.drone_pos[1] + 1))
                    elif event.key == pygame.K_LEFT:
                        self.update_drone_position((self.drone_pos[0] - 1, self.drone_pos[1]))
                    elif event.key == pygame.K_RIGHT:
                        self.update_drone_position((self.drone_pos[0] + 1, self.drone_pos[1]))

            self.render()
            if not self.pick_up_points and not self.is_carrying_package:
                print("All deliveries completed!")
                running = False

            self.clock.tick(10)
        pygame.quit()


if __name__ == "__main__":
    env = Environment()
    env.run_simulation()
