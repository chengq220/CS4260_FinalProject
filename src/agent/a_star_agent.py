import pygame
from agent import Agent
import heapq
from simulation.environment import Environment

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

class AStar(Agent):
    def __init__(self, grid_size = GRID_SIZE, cell_size = CELL_SIZE, colors = COLORS):
        # Base class initializer.
        super().__init__(grid_size = GRID_SIZE, cell_size = CELL_SIZE, colors = COLORS)

    # Find path to next goal (pick-up/drop-off). Return computed path, or None if no goal
    # available.
    def find_path_to_next_goal(self):
        if self.check_completion():
            print("All deliveries completed.")
            return None
        
        # Determine next goal dynamically.
        if self.environment.is_carrying_package:
            # If carrying a package, find closest drop off point for that package.
            package_id = self.environment.current_delivery
            goal = self.get_closest_drop_off_point(package_id)
        else:
            # No package carried. Next goal is closest pick-up point.
            goal = self.get_closest_pick_up_point()
        
        # If no valid goal exists, return None.
        if goal is None:
            print("No valid goal found.")
            return None
        
        # Use A* to calculate the path to the goal
        path = self.a_star_algorithm(self.environment.drone_pos, goal)
        return path

    # Get the closest pick-up point.
    def get_closest_pick_up_point(self):
        pick_up_points = self.locations_manager.get_pick_up_points()
        return self.get_closest_point(self.environment.drone_pos, pick_up_points)
    
    # Get the closest drop-off point matching given package ID.
    def get_closest_drop_off_point(self, package_id):
        drop_off_points = self.locations_manger.get_drop_off_points()
        valid_drop_offs = {point: id for point, id in drop_off_points.items() if id == package_id}

        return self.get_closest_point(self.environment.drone_pos, valid_drop_offs)
    
    # Get closest point from a set of points.
    # Points are expected to be a dictionary of position:id
    def get_closest_point(self, current_pos, points):
        if not points:
            return None
        
        closest_point = None
        min_distance = float('inf')
        for point in points.keys():
            distance = self.heuristic(current_pos, point)
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        return closest_point
    
    # Implementation of A* search factoring in arbitrary rewards to dissuade
    # flying through obstacles / restricted-fly zones.
    def a_star_algorithm(self, start, goal):
        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)

            # If goal is reached, reconstruct and return the path.
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            # Process neighbors.
            for neighbor in self.get_neighbors(current):
                # Might have to modify this part if restricted zone.
                movement_cost = self.get_movement_cost(neighbor)
                tentative_g_score = g_score[current] + movement_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, goal)

                    # Push the neighbor to the heap with updated f_score.
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        # No path is found.
        return None


    
    # Use Manhattan distance as heuristic funtion.
    def heuristic(self, position, goal):
        return abs(position[0] - goal[0]) + abs(position[1] - goal[1])
    
    # Obtain all valid neighbors for current position.
    def get_neighbors(self, position):
        x, y = position
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        neighbors = []
        for dx, dy in directions:
            neighbor = (x + dy, y + dy)
            if 0 <= neighbor[0] < self.environment.grid_size and 0 <= neighbor[1] < self.environment.grid_size:
                neighbors.append(neighbor)
        return neighbors
    
    def get_movement_cost(self, position):
        # No-fly zone.
        if position in self.environment.obstacles:
            return 10
        # Obstacle zone.
        elif position in self.environment.no_fly_zones:
            return 20
        # General movement cost.
        else:
            return 1

    # Reconstruct the path taken from start to goal.
    def reconstruct_path(self, came_from, current):
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        print(path)
        return path
    
    # Follow the calculated path step by step.
    def follow_path(self, path):
        for step in path:
            dx, dy = step[0] - self.environment.drone_pos[0], step[1] - self.environment.drone_pos[1]
            action = (
                "RIGHT" if dx == 1 else
                "LEFT" if dx == -1 else
                "DOWN" if dy == 1 else
                "UP"
            )
        pygame.time.wait(100)  # Add delay for visualization
        self.perform_action(action)
        self.render_environment()

    def run(self):
        # Run the A* agent to complete all deliveries.
        self.environment.reset()
        self.reward_function.reset()
        self.locations_manager.reset()
        next_objective = self.find_path_to_next_goal()
        while next_objective != None:
            self.follow_path(next_objective)

if __name__ == "__main__":
    game = AStar()
    game.run()
    pygame.quit()