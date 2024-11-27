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
        self.future_obstacles = {}
        self.future_no_fly_zones = {}
        self.event_simulator = None
        self.locations_manager = None
        self.reset()

    def set_event_simulator(self, event_simulator):
        """Set the event simulator reference."""
        self.event_simulator = event_simulator

    def set_locations_manager(self, locations_manager):
        """Set the locations manager reference."""
        self.locations_manager = locations_manager

    def update_dynamic_events(self):
        """Synchronize current and future event zones with the event simulator."""
        if self.event_simulator:
            self.event_simulator.update_events(self.current_time)

            # Get pickup and dropoff points
            pick_up_points = self.grid_with_priority("pickup")
            drop_off_points = self.grid_with_priority("dropoff")

            # Merge event zones while giving priority to pickup/dropoff
            self.obstacles = {
                tuple(pos): "obstacle"
                for pos in self.event_simulator.get_obstacles()
                if tuple(pos) not in pick_up_points and tuple(pos) not in drop_off_points
            }

            self.no_fly_zones = {
                tuple(pos): "no-fly-zone"
                for pos in self.event_simulator.get_no_fly_zones()
                if tuple(pos) not in pick_up_points and tuple(pos) not in drop_off_points
            }

            self.future_obstacles = {
                tuple(pos): "future-obstacle"
                for pos in self.event_simulator.get_future_obstacles()
                if tuple(pos) not in pick_up_points and tuple(pos) not in drop_off_points
            }

            self.future_no_fly_zones = {
                tuple(pos): "future-no-fly-zone"
                for pos in self.event_simulator.get_future_no_fly_zones()
                if tuple(pos) not in pick_up_points and tuple(pos) not in drop_off_points
            }

    def grid_with_priority(self, point_type):
        """Retrieve grid points based on priority."""
        if not self.locations_manager:
            return {}

        if point_type == "pickup":
            return set(self.locations_manager.get_pick_up_points().keys())
        elif point_type == "dropoff":
            return set(self.locations_manager.get_drop_off_points().keys())
        return {}

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
