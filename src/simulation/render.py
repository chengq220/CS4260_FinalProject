import pygame

class Renderer:
    def __init__(self, grid_size, cell_size, colors, window_size):
        """Initialize the Renderer."""
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.colors = colors
        self.window = pygame.display.set_mode((window_size, window_size))
        pygame.display.set_caption("Drone Delivery Environment")
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 36)

    def render(self, environment, pick_up_points, drop_off_points):
        """Render the environment."""
        self.window.fill(self.colors["WHITE"])

        # Draw the grid
        for x in range(0, self.grid_size * self.cell_size, self.cell_size):
            for y in range(0, self.grid_size * self.cell_size, self.cell_size):
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.window, self.colors["GRAY"], rect, 1)

        # Draw future obstacles
        for fut_obs in environment.future_obstacles:
            rect = pygame.Rect(fut_obs[0] * self.cell_size, fut_obs[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors.get("LIGHT_RED", (255, 200, 200)), rect)

        # Draw future no-fly zones
        for fut_no_fly in environment.future_no_fly_zones:
            rect = pygame.Rect(fut_no_fly[0] * self.cell_size, fut_no_fly[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors.get("LIGHT_YELLOW", (255, 255, 150)), rect)

        # Draw current obstacles
        for obs in environment.obstacles:
            rect = pygame.Rect(obs[0] * self.cell_size, obs[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors["RED"], rect)

        # Draw current no-fly zones
        for no_fly in environment.no_fly_zones:
            rect = pygame.Rect(no_fly[0] * self.cell_size, no_fly[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors["YELLOW"], rect)

        # Draw pickup points with IDs
        for pick_up, task_id in pick_up_points.items():
            rect = pygame.Rect(pick_up[0] * self.cell_size, pick_up[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors["PURPLE"], rect)
            id_surface = self.font.render(str(task_id), True, self.colors["WHITE"])
            self.window.blit(id_surface, (pick_up[0] * self.cell_size + 5, pick_up[1] * self.cell_size + 5))

        # Draw drop-off points with IDs
        for drop_off, task_id in drop_off_points.items():
            rect = pygame.Rect(drop_off[0] * self.cell_size, drop_off[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.window, self.colors["ORANGE"], rect)
            id_surface = self.font.render(str(task_id), True, self.colors["WHITE"])
            self.window.blit(id_surface, (drop_off[0] * self.cell_size + 5, drop_off[1] * self.cell_size + 5))

        # Draw the drone
        rect = pygame.Rect(environment.drone_pos[0] * self.cell_size, environment.drone_pos[1] * self.cell_size,
                           self.cell_size, self.cell_size)
        drone_color = self.colors["BLUE"] if not environment.is_carrying_package else self.colors["GREEN"]
        pygame.draw.rect(self.window, drone_color, rect)

        # Display current time
        time_surface = self.large_font.render(f"Time: {environment.get_formatted_time()}", True, self.colors["BLACK"])
        self.window.blit(time_surface, (10, 10))

        pygame.display.flip()
