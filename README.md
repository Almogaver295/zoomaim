Zoom Tool Crosshair
This project is a PyQt5-based zoom tool application that allows users to zoom into a specific screen region with customizable settings. The tool includes features such as global key listening, adjustable zoom levels, and a draggable selection area.

Features
Custom Zoom Levels:

Adjustable zoom levels ranging from 1x to 5x.
Configurable via a settings window.
Global Key Listener:

Toggle zoom functionality using a user-configured global key.
Compatible with various keyboard keys.
Draggable and Resizable Selection Area:

Users can select a custom screen region for zooming.
Resize or drag the area interactively.
Real-Time Zoom Preview:

Live preview of the zoomed area in a dedicated window.
Captures and scales the selected region dynamically.
Configuration Persistence:

Settings are saved to a JSON file (zoom_config.json) and loaded on startup.
Cross-Platform:

Designed for Windows but may work on other platforms with minor modifications.
Installation
Prerequisites:

Python 3.x installed.
Install the required libraries:
bash
Copiar código
pip install PyQt5 pyautogui opencv-python-headless pynput numpy
Download the Project:

Clone or download this repository to your local machine.
Run the Application:

Navigate to the project directory and run:
bash
Copiar código
python zoom_tool.py
File Structure
zoom_tool.py: Main application file containing all the functionality.
zoom_config.json: Configuration file for storing user preferences such as zoom level, selection area, and toggle key.
How to Use
Launch the Application:

Run the script to launch the Zoom Tool.
Configure Settings:

Click on the configuration window to adjust:
Zoom Level: Use the slider to set the desired zoom level.
Toggle Key: Press a key to set it as the zoom toggle shortcut.
Zoom Area: Click "Select Zoom Area" to define the screen region.
Activate Zoom:

Use the configured toggle key to enable/disable the zoom feature.
View Zoom Preview:

The zoomed view will appear in a movable and resizable preview window.
Save Settings:

Adjusted settings are automatically saved to zoom_config.json.
Configuration Details
Zoom Level: Integer value between 1 and 5, default is 2.
Rectangle Size: Default is 300x300 pixels.
Zoom Key: Default is Shift. Configurable via settings.
Key Features Explained
1. Global Key Listener
The application uses pynput to listen for global keyboard events. It maps PyQt5 keys to pynput keys for flexibility.

2. Dynamic Zoom Area
Users can define a custom rectangle on the screen that will be used for zooming. This area can be resized or dragged within the application.

3. Zoom Preview
The zoom preview is created using OpenCV for real-time screen capture and resizing. The updated zoomed region is displayed in a separate PyQt5 QLabel.

Troubleshooting
Key Listener Issues: Ensure the pynput library is installed correctly. If some keys don’t work, check the mapping in the map_qt_key_to_pynput() function.

Zoomed Area Appears Incorrectly: Verify the selected area and ensure it’s within screen boundaries.

Performance: For older systems, reduce the zoom update interval (default is 300ms) in the start_zoom() function.

Future Improvements
Add multi-monitor support.
Include more intuitive UI elements for easier configuration.
Optimize screen capturing for better performance on low-end systems.
Author
Developed using PyQt5 and Python. If you encounter issues or have feature requests, feel free to contribute or open an issue.
