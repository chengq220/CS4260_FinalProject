import pygame

class InputHandler:
    def __init__(self, agent):
        """
        Initialize the input handler.
        Args:
            agent: The agent controlling the drone (can be a manual or automated agent).
        """
        self.agent = agent

    def handle_manual_input(self, event):
        """
        Handle keyboard input for manually controlling the drone.
        Args:
            event: A Pygame event object.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.agent.perform_action("UP")
            elif event.key == pygame.K_DOWN:
                self.agent.perform_action("DOWN")
            elif event.key == pygame.K_LEFT:
                self.agent.perform_action("LEFT")
            elif event.key == pygame.K_RIGHT:
                self.agent.perform_action("RIGHT")

    def handle_agent_input(self, agent_action):
        """
        Handle automated agent actions.
        Args:
            agent_action: A string representing the agent's intended action (e.g., "UP", "DOWN").
        """
        self.agent.perform_action(agent_action)

    def get_next_action(self, mode="manual", agent_action=None):
        """
        Process the next action based on the mode.
        Args:
            mode: The input mode ("manual" for user input, "agent" for automated input).
            agent_action: The action determined by the agent (only used in "agent" mode).
        Returns:
            A flag indicating whether the program should continue running.
        """
        running = True
        if mode == "manual":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_manual_input(event)
        elif mode == "agent" and agent_action:
            self.handle_agent_input(agent_action)

        return running
