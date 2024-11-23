# CS4260_FinalProject

To test the environment:
* pip install all libraries in requirements.txt
* Run environment.py
* Use arrow keys to move drone

To use map editor:
* Run map_editor.py
* Default mode is event_patterns, use 'm' to switch to location mode
* event_patterns mode: 
  * Click on tiles to toggle them between default tile, obstacle tile, no-fly zone tile
  * Use up and down arrow keys to switch time
  * Make a configuration and move to other time, all those times in between will use that configuration, from new time make new configuration in the map and switch to other next time. 
  * Use 's' to save the map. The map will be saved with the configurations for each specific time interval it had in a new .json file. 
  * Move the file to configs/ and modify the event_simulator.py to use that pattern.
* location mode:
  * Click on tiles to toggle them between default tile, pick-up tile, and drop-off tile.
  * Use up and down arrow keys to switch the id of last modified tile.
  * Make sure each pick-up tile has a corresponding drop-off tile with the same id number.
  * Use 's' to save the map. The map will be saved with the configurations for those pick-up and drop-off tiles.
  * Move the file to configs/ and modify the environment.py to use that pattern.
* Make sure that the map is blank before switching modes.