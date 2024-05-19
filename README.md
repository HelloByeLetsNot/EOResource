Endless Online Updater
Endless Online Updater is a Python-based GUI application designed to manage updates, provide server status, and display resources for the Endless Online game. The application is built using tkinter and ttkthemes for the GUI, and it utilizes asynchronous HTTP requests with aiohttp for fetching data.

Features
Updater Tab: Checks for updates to the Endless Online client and launches the game.
Who's Online Tab: Displays a list of players currently online.
Resources Tab: Provides quick links to various Endless Online-related resources, dynamically adjusting to window resizing.
Guilds Tab: Lists the current guilds in the game.
NPCs Tab: Shows detailed information about NPCs, including their stats.


Requirements
Python 3.7 or higher
Required Python packages:
tkinter
ttkthemes
requests
Pillow
aiohttp
Installation


Clone the repository:


git clone https://github.com/HelloByeLetsNot/EOResource.git
cd EOResource
Install the required packages:


pip install -r requirements.txt
Run the application:


python main.py


Usage
Updater Tab: Click the "Launch Endless Online" button to check for updates and launch the game.
Who's Online Tab: Automatically fetches and displays a list of players currently online.
Resources Tab: Provides links to useful resources. The layout adjusts dynamically based on window size.
Guilds Tab: Displays the list of current guilds.
NPCs Tab: Allows searching and displaying detailed NPC information, including stats and images.
Building the Executable


To package the application as an executable using pyinstaller, run:

pyinstaller --onefile --add-data "Endless.exe;." main.py
