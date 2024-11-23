from src.simulation.environment import Environment

if __name__ == "__main__":
    env = Environment()
    print("Starting simulation...")

    # Reset the environment
    env.reset()

    # Simulate a few omnipotent manual actions for testing
    actions = [
        (0, 1),  # Move down
        (1, 1),  # Move right to pick up a package
        (10, 10),  # Move to drop-off location
        (3, 3),  # Move to another pick-up location
        (15, 15)  # Move to another drop-off location
    ]

    for action in actions:
        env.update_drone_position(action)

    # Print total reward
    print(f"Total Reward: {env.reward_function.get_total_reward()}")
