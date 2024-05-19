import re
import os
import aiohttp
import shutil
import tkinter as tk
from tkinter import ttk
from typing import NamedTuple
import asyncio
from bs4 import BeautifulSoup
import webbrowser
import json
import threading
import subprocess
from ttkthemes import ThemedTk
import requests
from PIL import Image, ImageTk
from io import BytesIO
import sys
import subprocess
import os
class FileVersion(NamedTuple):
    major: int
    minor: int
    build: int
    patch: int


class ClientVersionFetcher:
    ENDLESS_ONLINE_ZIP_REGEX = re.compile(r'href="(.*EndlessOnline(\d+)[a-zA-Z]*)(\d*)(\.zip)"')

    async def get_remote_async(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
            async with session.get('https://www.endless-online.com/client/download.html') as resp:
                endless_home_page = await resp.text()

        regex_version_matches = self.ENDLESS_ONLINE_ZIP_REGEX.search(endless_home_page)
        if regex_version_matches:
            download_link = regex_version_matches.group(1) + regex_version_matches.group(4)
            major = int(regex_version_matches.group(2)[0])
            minor = int(regex_version_matches.group(2)[1])
            build = int(regex_version_matches.group(2)[2:])
            patch = int(regex_version_matches.group(3)) if regex_version_matches.group(3) else 0

            return download_link, FileVersion(major, minor, build, patch)
        else:
            return None, None

    def get_local(self):
        exe_path = os.path.join(os.path.dirname(__file__), 'Endless.exe')
        if not os.path.exists(exe_path):
            return FileVersion(0, 0, 0, 0)

        
        version_info = '0.0.0.0'

        return FileVersion._make([int(x) for x in version_info.split('.')])

    async def update_local(self, update_progress):
        script_dir = os.path.dirname(__file__)
        remote_download_link, remote_version = await self.get_remote_async()
        local_version = self.get_local()

        if remote_version and remote_version > local_version:
            update_progress("Downloading...")
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                    async with session.get(remote_download_link) as resp:
                        total_size = int(resp.headers.get('content-length', 0))
                        zip_path = os.path.join(script_dir, 'EndlessOnline.zip')
                        with open(zip_path, 'wb') as f:
                            downloaded_size = 0
                            async for chunk in resp.content.iter_chunked(1024):
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                progress_percent = (downloaded_size / total_size) * 100
                                update_progress(f"Downloading... {progress_percent:.2f}%")
            except Exception as e:
                update_progress(f"Error during download: {e}")
                return

            update_progress("Extracting...")
            try:
                shutil.unpack_archive(zip_path, script_dir)
                os.remove(zip_path)
            except Exception as e:
                update_progress(f"Error during extraction: {e}")
                return

            update_progress("Cleaning up...")
            await asyncio.sleep(1)
            update_progress("Done")
            self.launch_client()
        else:
            update_progress("Up to date")
            self.launch_client()

    def launch_client(self):
        exe_path = os.path.join(os.path.dirname(__file__), 'Endless.exe')
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])





async def fetch_server_status():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://game.endless-online.com/server.html') as resp:
            return await resp.text()


def updater_tab(parent):
    frame = ttk.Frame(parent)

    progress_label = ttk.Label(frame, text="")
    progress_label.pack(pady=5)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    progress_bar.pack(fill=tk.X, padx=20, pady=5)

    def update_progress(stage):
        progress_label.config(text=stage)
        if "Downloading" in stage and "%" in stage:
            progress_bar.config(mode="determinate", maximum=100)
            progress_percent = float(stage.split()[-1][:-1])
            progress_bar['value'] = progress_percent
        elif stage in ["Extracting...", "Cleaning up...", "Up to date"]:
            progress_bar.config(mode="indeterminate")
            progress_bar.start()
        elif stage == "Done":
            progress_bar.stop()
            progress_bar.config(value=100)

    fetcher = ClientVersionFetcher()

    async def update_local_with_progress():
        await fetcher.update_local(update_progress)

    def start_update():
        threading.Thread(target=asyncio.run, args=(update_local_with_progress(),)).start()

    def launch_game():
        
        if hasattr(sys, '_MEIPASS'):
           
            script_dir = sys._MEIPASS
        else:
        
            script_dir = os.path.dirname(os.path.abspath(__file__))

        exe_path = os.path.join(script_dir, 'Endless.exe')
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
        else:
            print("Endless.exe not found")

    async def update_server_status():
        page_content = await fetch_server_status()
        soup = BeautifulSoup(page_content, 'html.parser')

        try:
            version_element = soup.find(string=re.compile(r'server core version', re.IGNORECASE))
            server_core_version = version_element.find_next().text.strip() if version_element else "N/A"
        except AttributeError:
            server_core_version = "N/A"

        try:
            status_text = soup.get_text()
            server_status = "Online" if "Online!" in status_text else "Offline"
        except AttributeError:
            server_status = "Offline"

        version_label.config(text=f"Server Core Version: {server_core_version}")
        status_label.config(text=f"Server Status: {server_status}")

    update_button = ttk.Button(frame, text="Update Client", command=start_update)
    update_button.pack(pady=10, padx=20)

    launch_button = ttk.Button(frame, text="Launch Game", command=launch_game)
    launch_button.pack(pady=10, padx=20)

    version_label = ttk.Label(frame, text="Server Core Version: ")
    status_label = ttk.Label(frame, text="Server Status: ")

    version_label.pack(pady=5)
    status_label.pack(pady=5)

    threading.Thread(target=asyncio.run, args=(update_server_status(),)).start()

    return frame




async def fetch_whos_online():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://game.endless-online.com/playerlist.html') as resp:
            return await resp.text()


def whos_online_tab(parent):
    frame = ttk.Frame(parent)
    search_var = tk.StringVar()

    def search():
        query = search_var.get().lower()
        for item in tree.get_children():
            tree.delete(item)
        for player in players:
            if query in player['name'].lower() or query in player['class'].lower():
                tree.insert("", "end", values=(player['name'], player['class'], player['level'], player['experience'], player['gender']))

    def sort_by_column(col, reverse):
        try:
            players.sort(key=lambda x: int(x[col]) if x[col].isdigit() else x[col].lower(), reverse=reverse)
        except ValueError:
            players.sort(key=lambda x: x[col].lower(), reverse=reverse)
        for item in tree.get_children():
            tree.delete(item)
        for player in players:
            tree.insert("", "end", values=(player['name'], player['class'], player['level'], player['experience'], player['gender']))
        tree.heading(col, command=lambda: sort_by_column(col, not reverse))

    async def update_online_list():
        global players
        page_content = await fetch_whos_online()
        soup = BeautifulSoup(page_content, 'html.parser')
        players = []
        table = soup.find('table')
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) == 5 and columns[0].text.strip() != "Player name":
                player_data = {
                    'name': columns[0].text.strip(),
                    'class': columns[1].text.strip(),
                    'level': columns[2].text.strip(),
                    'experience': columns[3].text.strip(),
                    'gender': columns[4].text.strip(),
                }
                players.append(player_data)
        search_var.set('')  
        search()  

    def refresh():
        threading.Thread(target=asyncio.run, args=(update_online_list(),)).start()

    search_entry = ttk.Entry(frame, textvariable=search_var)
    search_entry.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
    search_button = ttk.Button(frame, text="Search", command=search)
    search_button.pack(side=tk.TOP, pady=5)
    refresh_button = ttk.Button(frame, text="Refresh", command=refresh)
    refresh_button.pack(side=tk.TOP, pady=5)

    columns = ("name", "class", "level", "experience", "gender")
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col.capitalize(), command=lambda c=col: sort_by_column(c, False))
        tree.column(col, width=100, anchor="center")

    
    scrollbar_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscroll=scrollbar_y.set)
    scrollbar_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.configure(xscroll=scrollbar_x.set)

    tree.pack(expand=True, fill='both')

    threading.Thread(target=asyncio.run, args=(update_online_list(),)).start()

    return frame





async def fetch_resources():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://raw.githubusercontent.com/HelloByeLetsNot/linklist/main/links.json') as resp:
            links_json = await resp.text()
            return json.loads(links_json)


def resources_tab(parent):
    frame = ttk.Frame(parent)

    resources = {
        "EOBud": "https://eobud.boards.net",
        "EODash": "https://www.eodash.com/guides",
        "EOMix": "https://www.eomix.com",
        "SinTV": "https://www.youtube.com/user/SiinTV",
        "Eoserv": "https://eoserv.net/",
        "EORadio": "https://www.eoradio.co.uk/",
        "Endless Reddit": "https://www.reddit.com/r/EndlessOnline/?rdt=61294",
        "Endless Discord": "https://discord.com/invite/mRFXs2w",
        "404 Discord": "https://discord.com/invite/MCk65uP",
        "SLN": "https://www.apollo-games.com/SLN/sln.php/",
        "EO Patcher": "https://github.com/DanDecrypted/EndlessOnlinePatcher/releases/",
        "EOData Base": "http://apollo-games.com/eodatabase/",
        "Arvid DiscordBot": "https://github.com/HelloByeLetsNot/ArvidBot"
    }

    def open_url(url):
        webbrowser.open_new(url)

    buttons = []
    for name, url in resources.items():
        button = ttk.Button(frame, text=name, command=lambda url=url: open_url(url), style="RoundedButton.TButton")
        buttons.append(button)

    def update_grid(event=None):
        for widget in frame.winfo_children():
            widget.grid_forget()

        width = frame.winfo_width()
        max_cols = max(1, width // 150)  
        col = 0
        row = 0

        for button in buttons:
            button.grid(row=row, column=col + (max_cols - len(resources) % max_cols) // 2, padx=10, pady=10, sticky='ew')
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    frame.bind("<Configure>", update_grid)

    return frame


async def fetch_guilds():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://game.endless-online.com/guilds.html') as resp:
            return await resp.text()


def guilds_tab(parent):
    frame = ttk.Frame(parent)
    search_var = tk.StringVar()

    def search():
        query = search_var.get().lower()
        for item in tree.get_children():
            tree.delete(item)
        for guild in guilds:
            if query in guild['name'].lower() or query in guild['tag'].lower():
                tree.insert("", "end", values=(guild['name'], guild['tag'], guild['members'], guild['experience']))

    def sort_by_column(col, reverse):
        try:
            guilds.sort(key=lambda x: int(x[col]) if x[col].isdigit() else x[col].lower(), reverse=reverse)
        except ValueError:
            guilds.sort(key=lambda x: x[col].lower(), reverse=reverse)
        for item in tree.get_children():
            tree.delete(item)
        for guild in guilds:
            tree.insert("", "end", values=(guild['name'], guild['tag'], guild['members'], guild['experience']))
        tree.heading(col, command=lambda: sort_by_column(col, not reverse))

    async def update_guilds_list():
        global guilds
        page_content = await fetch_guilds()
        soup = BeautifulSoup(page_content, 'html.parser')
        guilds = []
        table = soup.find('table')
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) == 4 and columns[0].text.strip().lower() != "guild name" and columns[2].text.strip().isdigit() and columns[3].text.strip().isdigit():
                guild_data = {
                    'name': columns[0].text.strip(),
                    'tag': columns[1].text.strip(),
                    'members': columns[2].text.strip(),
                    'experience': columns[3].text.strip(),
                }
                guilds.append(guild_data)
        search_var.set('')  
        search()  

    def refresh():
        threading.Thread(target=asyncio.run, args=(update_guilds_list(),)).start()

    search_entry = ttk.Entry(frame, textvariable=search_var)
    search_entry.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
    search_button = ttk.Button(frame, text="Search", command=search)
    search_button.pack(side=tk.TOP, pady=5)
    refresh_button = ttk.Button(frame, text="Refresh", command=refresh)
    refresh_button.pack(side=tk.TOP, pady=5)

    columns = ("name", "tag", "members", "experience")
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col.capitalize(), command=lambda c=col: sort_by_column(c, False))
        tree.column(col, width=100, anchor="center")

    
    scrollbar_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscroll=scrollbar_y.set)
    scrollbar_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.configure(xscroll=scrollbar_x.set)

    tree.pack(expand=True, fill='both')

    threading.Thread(target=asyncio.run, args=(update_guilds_list(),)).start()

    return frame

async def fetch_npcs():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://eor-api.exile-studios.com/api/npcs/dump') as resp:
            return await resp.json()

def npcs_tab(parent):
    frame = ttk.Frame(parent)
    search_var = tk.StringVar()

    
    image_refs = {}

    def search():
        query = search_var.get().lower()
        for item in tree.get_children():
            tree.delete(item)
        for npc in npcs:
            if query in npc['name'].lower():
                try:
                    image_url = f"https://eor-api.exile-studios.com/api/npcs/{npc['id']}/graphic"
                    image_data = requests.get(image_url).content
                    image = Image.open(BytesIO(image_data))
                    photo = ImageTk.PhotoImage(image.resize((50, 50))) 
                    image_refs[npc['name']] = photo  
                    tree.insert("", "end", values=(
                        npc['name'],
                        npc['hp'],
                        f"{npc['min_damage']}-{npc['max_damage']}",
                        npc['accuracy'],
                        npc['evasion'],
                        npc['armor'],
                        npc['level'],
                        npc['experience']
                    ), image=photo)
                except Exception as e:
                    print(f"Error loading image for {npc['name']}: {e}")
                    tree.insert("", "end", values=(
                        npc['name'],
                        npc['hp'],
                        f"{npc['min_damage']}-{npc['max_damage']}",
                        npc['accuracy'],
                        npc['evasion'],
                        npc['armor'],
                        npc['level'],
                        npc['experience']
                    ))

    async def update_npc_list():
        global npcs
        npcs = await fetch_npcs()
        search_var.set('')  
        search() 

    def refresh():
        threading.Thread(target=asyncio.run, args=(update_npc_list(),)).start()

    search_entry = ttk.Entry(frame, textvariable=search_var)
    search_entry.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
    search_button = ttk.Button(frame, text="Search", command=search)
    search_button.pack(side=tk.TOP, pady=5)
    refresh_button = ttk.Button(frame, text="Refresh", command=refresh)
    refresh_button.pack(side=tk.TOP, pady=5)

    columns = ("name", "hp", "damage", "accuracy", "evasion", "armor", "level", "experience")
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=100, anchor="center")

    
    scrollbar_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscroll=scrollbar_y.set)
    scrollbar_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.configure(xscroll=scrollbar_x.set)

    tree.pack(expand=True, fill='both')

    threading.Thread(target=asyncio.run, args=(update_npc_list(),)).start()

    return frame



class App(ThemedTk):
    def __init__(self):
        super().__init__(theme="adapta")
        self.title("Endless Online Updater")
        self.geometry("600x400")

        #rounded buttons
        style = ttk.Style()
        style.configure("RoundedButton.TButton", padding=6, relief="flat", background="#ffffff", borderwidth=2)
        style.map("RoundedButton.TButton", background=[('active', '#cceeff')], relief=[('pressed', 'sunken')])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill="both")

        self.tabs = {
            "Updater": updater_tab,
            "Who's Online": whos_online_tab,
            "Guilds": guilds_tab,
            "Resources": resources_tab,
            "NPCs": npcs_tab
        }

        self.frames = {}
        for tab_name in self.tabs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self.frames[tab_name] = frame

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_selected)

        # Load the content 
        self.after(100, lambda: self.on_tab_selected(None))

        # Themes
        self.theme_var = tk.StringVar(value="radiance")
        theme_label = ttk.Label(self, text="Select Theme:")
        theme_label.pack(side=tk.LEFT, padx=10, pady=5)
        theme_menu = ttk.OptionMenu(self, self.theme_var, "radiance", "radiance", "equilux", "clearlooks", "breeze", command=self.change_theme)
        theme_menu.pack(side=tk.LEFT, padx=10, pady=5)

    def change_theme(self, theme_name):
        self.set_theme(theme_name)

    def on_tab_selected(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab in self.tabs:
            frame = self.frames[selected_tab]
            if not frame.winfo_children():
                tab_content = self.tabs[selected_tab](frame)
                tab_content.pack(expand=True, fill="both")

if __name__ == "__main__":
    app = App()
    app.mainloop()
