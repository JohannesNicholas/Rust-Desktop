import os
import rustplus
import asyncio
import tkinter as tk
from PIL import ImageTk
import customtkinter as ctk




class SignInPage:
    def __init__(self):

        ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
        ctk.set_default_color_theme("blue")


        # Start a window
        self.window = ctk.CTk()
        self.window.title("Rust+Desktop")
        self.window.geometry("400x400")

        # Input fields for the server ip and port, steam id and player token
        ctk.CTkLabel(self.window, text="Server IP:").pack()
        ip = ctk.CTkEntry(self.window)
        ip.pack()
        ctk.CTkLabel(self.window, text="Server Port:").pack()
        port = ctk.CTkEntry(self.window)
        port.pack()
        ctk.CTkLabel(self.window, text="Steam ID:").pack()
        steam_id = ctk.CTkEntry(self.window)
        steam_id.pack()
        ctk.CTkLabel(self.window, text="Player Token:").pack()
        player_token = ctk.CTkEntry(self.window)
        player_token.pack()
        ctk.CTkButton(self.window, text="Connect", command=lambda: asyncio.run(self.connect(ip.get(), port.get(), steam_id.get(), player_token.get()))).pack()

        # Read the config file if it exists
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = eval(f.read())
                ip.insert(0, config["ip"])
                port.insert(0, config["port"])
                steam_id.insert(0, config["steam_id"])
                player_token.insert(0, config["player_token"])


        self.window.mainloop()


    # Connect to the server
    async def connect(self, ip, port, steam_id, player_token):

        # Save the input fields
        with open("config.json", "w") as f:
            f.write(f'{{"ip": "{ip}", "port": "{port}", "steam_id": "{steam_id}", "player_token": "{player_token}"}}')

        socket = rustplus.RustSocket(ip, port, int(steam_id), int(player_token))
        await socket.connect()
        self.window.destroy()

        main_window = MainWindow()
        await main_window.start(socket, int(steam_id))

        



class MainWindow:
    async def start(self, socket, steam_id):
        self.socket = socket
        self.steam_id = steam_id
        self.main_window = ctk.CTk()
        self.main_window.title("Rust+Desktop")
        self.main_window.geometry("400x400")

        # Time
        self.time_label = ctk.CTkLabel(self.main_window, text="Loading time...")
        self.time_label.pack()

        #Canvas for the map
        self.map_canvas = ctk.CTkCanvas(self.main_window, width=400, height=400)
        self.map_canvas.pack()

        asyncio.create_task(self.time_loop())
        asyncio.create_task(self.map_update_loop())
        asyncio.create_task(self.location_update_loop())

        while True:
            self.main_window.update()

            # If the window is closed, disconnect from the server
            if not self.main_window.winfo_exists():
                await self.socket.disconnect()
                exit()
                
            await asyncio.sleep(0.1)

    async def time_loop(self):
        print("Time loop started")
        while True:
            self.time_label.configure(text=f"{(await self.socket.get_time()).time}")
            await asyncio.sleep(1)


    async def map_update_loop(self):
        print("Map update loop started")
        while True:
            map = await self.socket.get_map(False, True, True)
            map.save("map.png")

            
            await asyncio.sleep(15)

    async def location_update_loop(self):
        print("Minimap player location update loop started")
        while True:
            # Get the players position
            team = await self.socket.get_team_info()
            # get the player with the same steam id as the one used to connect to the server
            player = [player for player in team.members if player.steam_id == self.steam_id][0]


            mapsize = 4500

            #location to draw the map
            x = 0 - (player.x/mapsize) * 2000
            y = -2000 + (player.y/mapsize) * 2000

            # Draw the map on the canvas
            img = ImageTk.PhotoImage(file="map.png")
            self.map_canvas.create_image(x + 200, y + 200, anchor=tk.NW, image=img)
            
            # Draw a circle in the middle of the canvas
            self.map_canvas.create_oval(200 - 5, 200 - 5, 200 + 5, 200 + 5, fill="lime")

            self.map_canvas.update()
            await asyncio.sleep(0.5)

            






SignInPage()



