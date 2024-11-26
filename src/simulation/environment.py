class Environment:
    def __init__(self, grid_size, cell_size, time_step=10):
        """Initialize the environment."""
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.drone_pos = (0, 0)
        self.is_carrying_package = False
        self.package_count = 0
        self.current_delivery = None
        self.current_time = 0
        self.time_step = time_step
        self.obstacles = {}
        self.no_fly_zones = {}
        self.event_simulator = None  # Add reference for event simulator
        self.reset()

    def set_event_simulator(self, event_simulator):
        """Set the event simulator reference."""
        self.event_simulator = event_simulator

    def update_dynamic_events(self):
        """Synchronize obstacles and no-fly zones with event simulator."""
        if self.event_simulator:
            self.event_simulator.update_events(self.current_time)
            self.obstacles = {tuple(pos): "obstacle" for pos in self.event_simulator.get_obstacles()}
            self.no_fly_zones = {tuple(pos): "no-fly-zone" for pos in self.event_simulator.get_no_fly_zones()}

    def reset(self):
        """Reset the environment state."""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.drone_pos = (0, 0)
        self.is_carrying_package = False
        self.package_count = 0
        self.current_delivery = None
        self.current_time = 0
        self.obstacles = {}
        self.no_fly_zones = {}

    def advance_time(self):
        """Advance the simulation time by the time step."""
        self.current_time = (self.current_time + self.time_step) % (24 * 60)
        self.update_dynamic_events()  # Update dynamic events when time advances

    def get_formatted_time(self):
        """Return the current simulation time in HH:MM format."""
        hours = self.current_time // 60
        minutes = self.current_time % 60
        return f"{hours:02}:{minutes:02}"
