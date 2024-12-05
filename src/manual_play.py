import pygame
from agent.agent import Agent
from agent.input_handler import InputHandler

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
        """Initialize the manual play environment."""
        self.agent = Agent(grid_size=GRID_SIZE, cell_size=CELL_SIZE, colors=COLORS)
        self.input_handler = InputHandler(agent=self.agent)
        self.clock = pygame.time.Clock()

    def run(self, mode="manual", agent_action=None):
        """
        Main loop for playing or simulating the environment.
        Args:
            mode: The input mode ("manual" for user input, "agent" for automated input).
            agent_action: The agent's next action, used in "agent" mode.
        """
        self.agent.reset()
        running = True

        while running:
            action_taken = self.input_handler.get_next_action(mode=mode, agent_action=agent_action)

            if action_taken:  # Only process if a valid action is taken
                _, reward = self.agent.perform_action(action_taken)
                print(f"Current Total Reward: {self.agent.reward_function.total_reward}")

            self.agent.render_environment()

            if self.agent.check_completion():
                print("All deliveries completed!")
                running = False

            self.clock.tick(10)

        print(f"Final Total Reward: {self.agent.reward_function.total_reward}")
        pygame.quit()


if __name__ == "__main__":
    game = ManualPlay()
    game.run(mode="manual")  # Use mode="agent" and provide `agent_action` for automated play
