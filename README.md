# CS4260 Final Project: Drone Delivery System

### Install Dependencies
To install the required dependencies, run the following command
```
pip install all libraries in requirements.txt
```

### Creating custom maps
New maps can be created using ```map_editor.py```. To create a new map, follow the procedure described below
1. Run map_editor.py using ```python map_editor.py```
2. Default mode is event_patterns, press 'm' to switch to location mode
3. event_patterns mode: 
   * Click on tiles to toggle them between default tile, obstacle tile, no-fly zone tile
   * Use up and down arrow keys to switch time
   * Make a configuration and move to other time, all those times in between will use that configuration, from new time make new configuration in the map and switch to other next time. 
   * Use 's' to save the map. The map will be saved with the configurations for each specific time interval it had in a new .json file. 
   * Move the file to configs/ and modify the event_simulator.py to use that pattern.
4. location mode:
   * Click on tiles to toggle them between the default tile, pick-up tile, and drop-off tile.
   * Use up and down arrow keys to switch the id of last modified tile.
   * Make sure each pick-up tile has a corresponding drop-off tile with the same id number.
   * Use 's' to save the map. The map will be saved with the configurations for those pick-up and drop-off tiles.
   * Move the file to configs/ and modify the environment.py to use that pattern.

**Note: Make sure that the map is blank before switching modes.**

### Testing Environment
To test the environment or to play the game manually, run the following code:
```
python manual_play.py
```

Once the environment appears, use the arrow keys to move the drone. 

### Running Agents for Automatic Solving 
To test agents, use the following command on the desired agent in the `src/agent/` folder. 
**Note: To Avoid the src module not found error, run the following command from the base directory**
```
python -m src.agent.bad_agent
```
