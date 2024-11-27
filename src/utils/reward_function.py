class RewardFunction:
    def __init__(self):
        self.total_reward = 0

    def reset(self):
        self.total_reward = 0

    def calculate_reward(self, new_pos, env, action_result):
        """Calculate the reward based on the tile type and action result."""
        reward = 0

        # Check the type from the action result
        action_type = action_result.get("type")
        if action_type == "obstacle":
            reward -= 10
        elif action_type == "no-fly-zone":
            reward -= 20
        elif action_type == "pick-up":
            reward += 10 if action_result["success"] else -1
        elif action_type == "drop-off":
            reward += 50 if action_result["success"] else -1
        else:
            # Default penalty for moving to a neutral tile
            reward -= 1

        self.total_reward += reward
        return reward
