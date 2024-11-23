class RewardFunction:
    def __init__(self):
        self.total_reward = 0

    def reset(self):
        self.total_reward = 0

    def calculate_reward(self, new_pos, env, action_result):
        reward = 0
        if action_result["type"] == "pick-up":
            reward += 10 if action_result["success"] else -5
        elif action_result["type"] == "drop-off":
            reward += 50 if action_result["success"] else -10
        elif action_result["type"] == "move":
            if action_result["target"] == "obstacle":
                reward -= 10
            elif action_result["target"] == "no-fly-zone":
                reward -= 20
            else:
                reward -= 1
        self.total_reward += reward
        return reward
