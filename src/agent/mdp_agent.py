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
EPS = 0.1

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


class MDP_AGENT:
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
        self.util = None
        self.pick_up = None
        self.drop_off = None

    def _init_util(self):
        """Initialize the utility of the map"""
        util = {}
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                state = (x,y)
                util[state] = float('-inf')
        self.util = util 
    
    def get_transition(self, state, action):
        """The transition function between two states"""
        x, y = state
        if action == "LEFT":
            return (x - 1, y)  
        elif action == "RIGHT":
            return (x + 1, y)  
        elif action == "DOWN":
            return (x, y + 1) 
        elif action == "UP":
            return (x, y - 1) 
        return state  

    def get_avail_action(self, state):
        """Find the available moves from the given state"""
        xPos, yPos = state
        actions = []
        if xPos + 1 < GRID_SIZE:  
            actions.append("RIGHT")
        if yPos - 1 >= 0: 
            actions.append("UP")
        if xPos - 1 >= 0: 
            actions.append("LEFT")
        if yPos + 1 < GRID_SIZE:
            actions.append("DOWN")
        return actions

    def reward(self, state, hasPackage):
        """Return the reward if at a specific state given whether package have been picked up or not"""
        noflyzone = self.environment.no_fly_zones
        obstacles = self.environment.obstacles
        reward = 0

        if(state in noflyzone):
            reward = -20
        elif(state in obstacles):
            reward = -10
        elif(state == self.drop_off):
            reward = 30 if hasPackage else -1
        elif(state == self.pick_up):
            reward = -1 if hasPackage else 30
        else:
            reward = -1
        return reward

    def value_iter(self):
        """Value iteration to get the utility for the map"""
        max_change = 1 + EPS 
        while max_change > EPS:
            max_change = 0  
            util_pre = self.util.copy()  # Copy current utility values
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    state = (x, y)
                    # Immediate reward for the current state
                    util = self.reward(state, self.environment.is_carrying_package)
                    action_avail = self.get_avail_action(state)
                    if not action_avail:
                        self.util[state] = util
                        continue
                    
                    # Calculate the best utility over all available actions
                    bestUtil = util
                    prob = 1 / len(action_avail) 
                    for action in action_avail:
                        next_state = self.get_transition(state, action)
                        actUtil = prob * util_pre[next_state]
                        bestUtil = max(bestUtil, actUtil)
                    
                    self.util[state] = bestUtil
                    max_change = max(max_change, abs(self.util[state] - util_pre[state]))

    
    def find_closest(self, current_pos, points):
        """Find the closest point to the current position."""
        return min(points, key=lambda p: abs(p[0] - current_pos[0]) + abs(p[1] - current_pos[1]))

    def move_to_target(self, current_pos, target_pos):
        """Move step by step to the target position."""
        path = []
        while current_pos != target_pos:
            actions = self.get_avail_action(current_pos)
            bestState = current_pos
            bestUtil = float('-inf')
            for act in actions:
                nextState = self.get_transition(current_pos, act)
                if(self.util[nextState] > bestUtil):
                    bestUtil = self.util[nextState]
                    bestState = nextState
            current_pos = bestState

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
        """Run the mdp agent to complete all deliveries."""
        self.environment.reset()
        self.reward_function.reset()
        self.locations_manager.reset()
        pick_up_ppoints = self.locations_manager.get_pick_up_points().copy()
        drop_off_ppoints = self.locations_manager.get_drop_off_points().copy()
        print(pick_up_ppoints)
        print(drop_off_ppoints)

        while self.locations_manager.get_pick_up_points():
            current_pos = self.environment.drone_pos
            pick_up_points = list(self.locations_manager.get_pick_up_points().keys())
            drop_off_points = {v: k for k, v in self.locations_manager.get_drop_off_points().items()}

            # Find the closest pick-up point
            closest_pickup = self.find_closest(current_pos, pick_up_points)
            task_id = self.locations_manager.get_pick_up_points()[closest_pickup]
            self._init_util() #compute the the utility for the picking for specific task_id
            self.value_iter()
            self.pick_up = next(key for key, value in pick_up_ppoints.items() if value == task_id)

            # Move to the pick-up point
            print(f"Heading to pick-up point: {closest_pickup}")
            self.move_to_target(current_pos, closest_pickup)

            # Perform pick-up
            self.environment.is_carrying_package = True
            
            self.locations_manager.pick_up_points.pop(closest_pickup)
            reward = self.reward_function.calculate_reward(
                closest_pickup, self.environment, {"type": "pick-up", "success": True}
            )
            print(f"Picked up package {task_id} at {closest_pickup}, Current Total Reward: {self.reward_function.total_reward}")

            self._init_util() #recompute the utility for the dropoff for specific task_id
            self.drop_off = next(key for key, value in drop_off_ppoints.items() if value == task_id)
            self.value_iter()
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
    game = MDP_AGENT(render=True)
    game.run()
    pygame.quit()
