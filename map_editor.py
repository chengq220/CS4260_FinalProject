import pygame
import json
from datetime import timedelta


# Constants
WINDOW_SIZE = 600
GRID_SIZE = 20
CELL_SIZE = WINDOW_SIZE // GRID_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)  # Obstacle
YELLOW = (255, 255, 0)  # No-fly zone
PURPLE = (128, 0, 128)  # Pick-up
ORANGE = (255, 165, 0)  # Drop-off
BLUE = (0, 0, 255)  # Neutral


class MapEditor:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Map Editor")
        self.clock = pygame.time.Clock()

        # Tile states
        self.grid = [["neutral" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.tile_ids = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.mode = "event_patterns"  # Can be "event_patterns" or "locations"
        self.next_id = 1  # ID counter for pick-up/drop-off locations

        # Event Patterns Mode: Time and Configurations
        self.current_time = timedelta(minutes=0)  # Starts at 00:00
        self.patterns = []  # Store time-based patterns

        # Locations Mode: Last changed tile coordinates
        self.last_changed_tile = None

    def draw_grid(self):
        """Render the grid and tiles."""
        self.window.fill(WHITE)

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.grid[x][y] == "obstacle":
                    color = RED
                elif self.grid[x][y] == "no-fly-zone":
                    color = YELLOW
                elif self.grid[x][y] == "pick-up":
                    color = PURPLE
                elif self.grid[x][y] == "drop-off":
                    color = ORANGE
                else:  # Neutral
                    color = WHITE

                pygame.draw.rect(self.window, color, rect)
                pygame.draw.rect(self.window, GRAY, rect, 1)

                # Draw IDs for pick-up/drop-off locations
                if self.grid[x][y] in ["pick-up", "drop-off"] and self.tile_ids[x][y] is not None:
                    font = pygame.font.Font(None, 24)
                    id_surface = font.render(str(self.tile_ids[x][y]), True, WHITE)
                    self.window.blit(id_surface, (x * CELL_SIZE + 5, y * CELL_SIZE + 5))

        # Display mode and time/ID
        font = pygame.font.Font(None, 36)
        mode_surface = font.render(f"Mode: {self.mode}", True, BLACK)
        self.window.blit(mode_surface, (10, 10))

        if self.mode == "event_patterns":
            time_surface = font.render(f"Time: {self.format_time(self.current_time)}", True, BLACK)
            self.window.blit(time_surface, (10, 50))
        elif self.mode == "locations" and self.last_changed_tile:
            last_id = self.tile_ids[self.last_changed_tile[0]][self.last_changed_tile[1]]
            id_surface = font.render(f"ID: {last_id}", True, BLACK)
            self.window.blit(id_surface, (10, 50))

        pygame.display.flip()

    @staticmethod
    def format_time(t):
        """Format a timedelta object into HH:MM format."""
        total_minutes = t.total_seconds() // 60
        hours = int(total_minutes // 60) % 24
        minutes = int(total_minutes % 60)
        return f"{hours:02}:{minutes:02}"

    def save_current_pattern(self):
        """Save the current grid as a pattern with the current time."""
        obstacles = []
        no_fly_zones = []

        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if self.grid[x][y] == "obstacle":
                    obstacles.append([x, y])
                elif self.grid[x][y] == "no-fly-zone":
                    no_fly_zones.append([x, y])

        if obstacles or no_fly_zones:
            start_time = int(self.current_time.total_seconds() // 60)
            end_time = start_time + 10
            self.patterns.append({
                "time_range": [start_time, end_time],
                "obstacles": obstacles,
                "no_fly_zones": no_fly_zones
            })

    def save_to_json(self):
        """Save configurations to a JSON file."""
        if self.mode == "event_patterns":
            # Save the current time slot before processing
            self.save_current_pattern()

            # Consolidate patterns by merging adjacent time slots with identical configurations
            consolidated_patterns = []
            for pattern in self.patterns:
                if not consolidated_patterns:
                    consolidated_patterns.append(pattern)
                else:
                    last_pattern = consolidated_patterns[-1]
                    # Check if obstacles and no-fly zones match
                    if (
                            last_pattern["obstacles"] == pattern["obstacles"]
                            and last_pattern["no_fly_zones"] == pattern["no_fly_zones"]
                    ):
                        # Extend the last pattern's time range
                        last_pattern["time_range"][1] = pattern["time_range"][1]
                    else:
                        # Add a new distinct pattern
                        consolidated_patterns.append(pattern)

            # Convert time ranges to "HH:MM" format for saving
            for pattern in consolidated_patterns:
                pattern["time_range"] = [
                    self.format_time(timedelta(minutes=t)) for t in pattern["time_range"]
                ]

            file_name = "event_patterns_custom.json"
            data = {"patterns": consolidated_patterns}

        elif self.mode == "locations":
            deliveries = []
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    if self.grid[x][y] == "pick-up":
                        deliveries.append({"pick_up": [x, y], "drop_off": None, "id": self.tile_ids[x][y]})
                    elif self.grid[x][y] == "drop-off":
                        for delivery in deliveries:
                            if delivery["id"] == self.tile_ids[x][y]:
                                delivery["drop_off"] = [x, y]
                                break

            file_name = "pick_up_drop_off_config.json"
            data = {"deliveries": deliveries}

        # Save to file
        with open(file_name, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Configuration saved to {file_name}.")

    def toggle_tile_state(self, x, y):
        """Toggle the state of a tile based on the current mode."""
        current_state = self.grid[x][y]

        if self.mode == "event_patterns":
            if current_state == "neutral":
                self.grid[x][y] = "obstacle"
            elif current_state == "obstacle":
                self.grid[x][y] = "no-fly-zone"
            elif current_state == "no-fly-zone":
                self.grid[x][y] = "neutral"

        elif self.mode == "locations":
            if current_state == "neutral":
                self.grid[x][y] = "pick-up"
                self.tile_ids[x][y] = self.next_id
                self.last_changed_tile = (x, y)
                self.next_id += 1
            elif current_state == "pick-up":
                self.grid[x][y] = "drop-off"
                self.tile_ids[x][y] = self.tile_ids[x][y]  # Keep the same ID
                self.last_changed_tile = (x, y)
            elif current_state == "drop-off":
                self.grid[x][y] = "neutral"
                self.tile_ids[x][y] = None
                self.last_changed_tile = None

    def adjust_last_tile_id(self, increment=True):
        """Adjust the ID of the last changed tile in locations mode."""
        if self.last_changed_tile:
            x, y = self.last_changed_tile
            current_id = self.tile_ids[x][y]
            if increment:
                self.tile_ids[x][y] = current_id + 1
            else:
                self.tile_ids[x][y] = max(1, current_id - 1)

    def run(self):
        """Main loop for the map editor."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.mode = "locations" if self.mode == "event_patterns" else "event_patterns"
                        self.next_id = 1
                        self.last_changed_tile = None
                    elif event.key == pygame.K_s:
                        self.save_to_json()
                    elif event.key == pygame.K_UP:
                        if self.mode == "event_patterns":
                            self.save_current_pattern()
                            self.current_time += timedelta(minutes=10)
                        elif self.mode == "locations":
                            self.adjust_last_tile_id(increment=True)
                    elif event.key == pygame.K_DOWN:
                        if self.mode == "event_patterns":
                            self.save_current_pattern()
                            self.current_time -= timedelta(minutes=10)
                        elif self.mode == "locations":
                            self.adjust_last_tile_id(increment=False)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        grid_x = mouse_x // CELL_SIZE
                        grid_y = mouse_y // CELL_SIZE
                        self.toggle_tile_state(grid_x, grid_y)

            self.draw_grid()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    editor = MapEditor()
    editor.run()
