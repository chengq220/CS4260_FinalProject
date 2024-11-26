import pygame
from agent.agent import Agent

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


class ManualPlay:
    def __init__(self):
        """Initialize the agent for manual play."""
        self.agent = Agent(grid_size=GRID_SIZE, cell_size=CELL_SIZE, colors=COLORS)
        self.clock = pygame.time.Clock()

    def handle_input(self, event):
        """Handle keyboard input to manually control the drone."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.agent.perform_action("UP")
            elif event.key == pygame.K_DOWN:
                self.agent.perform_action("DOWN")
            elif event.key == pygame.K_LEFT:
                self.agent.perform_action("LEFT")
            elif event.key == pygame.K_RIGHT:
                self.agent.perform_action("RIGHT")

    def run(self):
        """Main loop for manual play."""
        self.agent.reset()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_input(event)

            self.agent.render_environment()

            if self.agent.check_completion():
                print("All deliveries completed!")
                running = False

            self.clock.tick(10)

        pygame.quit()


if __name__ == "__main__":
    game = ManualPlay()
    game.run()
