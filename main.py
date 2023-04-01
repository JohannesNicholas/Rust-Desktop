import os, threading, rustplus, asyncio
import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk, ImageFont, ImageDraw, Image
DEBUG = False

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
        
        if DEBUG == True: socket = rustplus.RustSocket("rplustestserver.ollieee.xyz", None, 76561198181939243, -718287530, use_test_server=True) 
        else: socket = rustplus.RustSocket(ip, port, int(steam_id), int(player_token))
        await socket.connect()
        self.window.destroy()

        init_window = InitWindow()
        await init_window.start(socket, int(steam_id))

class InitWindow:
    async def start(self, socket, steam_id):
        self.socket: rustplus.RustSocket = socket
        self.steam_id: int = steam_id
        self.init_window = ctk.CTk()
        self.init_window.title("Rust+Desktop")
        self.init_window.geometry("400x400")
        self.time_label = ctk.CTkLabel(self.init_window, text="Initialising, please wait. This window may freeze, just wait.")
        self.time_label.pack()

        self.init_window.update()
        await asyncio.sleep(0.5)
        if DEBUG == False: await asyncio.get_event_loop().create_task(self.map_update_loop())
        await asyncio.sleep(0.5)
        self.init_window.destroy()

        main_window = MainWindow()
        await main_window.start(socket, int(steam_id))
    
    async def map_update_loop(self):
        print("INIT | Running Map Update")
        map = await self.socket.get_map(False, True, True)
        monuments = (await self.socket.get_raw_map_data()).monuments
        mapsize = await self.socket.get_info()
        map = map.resize((mapsize.size,mapsize.size), Image.LANCZOS)
        rustfont = ImageFont.truetype(font="assets/RustMarker.ttf", size=64)
        monument_list = {
                "lighthouse_display_name": "Lighthouse",
                "large_oil_rig": "Large Oil Rig",
                "oil_rig_small": "Small Oil Rig",
                "underwater_lab": "Underwater Labs",
                "mining_outpost_display_name": "Mining Outpost",
                "supermarket": "Supermarket",
                "gas_station": "Gas Station",
                "dome_monument_name": "Dome",
                "swamp": "Swamp",
                "satellite_dish_display_name": "Satellite Dish",
                "mining_quarry_hqm_display_name": "HQM Quarry",
                "mining_quarry_stone_display_name": "Stone Quarry",
                "stables": "Stables",
                "mining_quarry_sulfur_display_name": "Sulfur Quarry",
                "sewer_display_name": "Sewers",
                "military_tunnels_display_name": "Military Tunnels",
                "water_treatment_plant_display_name": "Water Treatment Plant",
                "power_plant_display_name": "Power Plant",
                "airfield_display_name": "Airfield",
                "junkyard_display_name": "Junkyard",
                "excavator": "Excavator",
                "outpost": "Outpost",
                "bandit_camp": "Bandit Camp",
                "launchsite": "Launchsite",
                "arctic_base": "Arctic Base",
                "abandonedmilitarybase": "Abandoned Military Base",
                "large_fishing_village_display_name": "Large Fishing Village",
                "fishing_village_display_name": "Fishing Village",
                "harbor": "Harbor",
                "train_yard_display_name": "Trainyard"
            }
        for monument in monuments:
            if "dungeonbase" in monument.token.lower(): continue
            if "train_tunnel" in monument.token.lower(): continue
            draw = ImageDraw.Draw(map)
            name = monument.token.lower()
            if "stables" in name: name="stables"
            elif "swamp" in name: name="swamp"
            elif "arctic_base" in name: name="arctic_base"
            elif "harbor" in name: name="harbor"
            if name in monument_list: name=monument_list[name]
            remx = 0; remy = 0 # just for overriding some positions, allows to manually re-adjust
            if "excavator" in name.lower(): remy = 60
            elif "water treatment plant" in name.lower(): remy=40
            draw.text(xy=(rustplus.format_coord(int(monument.x-int(len(name)*11)-remx), int(monument.y-remy), mapsize.size)), text=name, font=rustfont, fill="black")
        map = map.resize((2000,2000), Image.LANCZOS)
        map.save("map.png")
        return

class MapCanvas(ctk.CTkCanvas):
    def __init__(self,parent,**kwargs):
        ctk.CTkCanvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
    
    def on_resize(self, event):
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        self.config(width=self.width, height=self.height)
        self.scale("all",0,0,wscale,hscale)
class TeamCanvas(ctk.CTkCanvas):
    def __init__(self,parent,**kwargs):
        ctk.CTkCanvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
    
    def on_resize(self, event):
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        self.config(width=self.width, height=self.height)
        self.scale("all",0,0,wscale,hscale)
class ServerCanvas(ctk.CTkCanvas):
    def __init__(self,parent,**kwargs):
        ctk.CTkCanvas.__init__(self,parent,**kwargs)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
class MenuCanvas(ctk.CTkCanvas):
    def __init__(self,parent,**kwargs):
        ctk.CTkCanvas.__init__(self,parent,**kwargs)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()
class TimeLabel(ctk.CTkLabel):
    def __init__(self,parent,**kwargs):
        ctk.CTkLabel.__init__(self,parent,**kwargs)

class MainWindow:
    def topage(self, typee: str):
        types = { #define the class and self names
            "Map": [MapCanvas, self.map_canvas],
            "Team": [TeamCanvas, self.team_canvas],
            "Server": [ServerCanvas, self.server_canvas],
        }

        for i in self.main_window.winfo_children():
            if type(i) not in [TimeLabel, MenuCanvas, types[typee][0]]:
                i.destroy() #kill everything but time, menu and the menu its trying to create (double click accidents etc)

        for i in types: # save resources using if != checks
            if i != typee:
                if i == "Map":
                    if self.map_canvas != None: self.map_canvas.destroy(); self.map_canvas = None
                if i == "Team":
                    if self.team_canvas != None: self.team_canvas.destroy(); self.team_canvas = None; self.widgets = []; self.team_info = None
                if i == "Server":
                    if self.server_canvas != None: self.server_canvas.destroy(); self.server_canvas = None; self.server_info = None

        if types[typee][1] not in self.main_window.winfo_children(): #make the menu if it doesnt exist
            if types[typee][0] == MapCanvas:
                self.map_canvas = MapCanvas(self.main_window, width=525, height=650, bg="gray14", highlightthickness=0)
                self.map_canvas.pack()
            elif types[typee][0] == TeamCanvas:
                self.team_canvas = TeamCanvas(self.main_window, width=525, height=650, bg="gray14", highlightthickness=0)
                self.team_canvas.pack()
            elif types[typee][0] == ServerCanvas:
                self.server_canvas = ServerCanvas(self.main_window, width=525, height=650, bg="gray14", highlightthickness=0)
                self.server_canvas.pack()

        for i in self.menu.winfo_children(): #make the selected button green and the others the default colour
            if type(i) == ctk.CTkButton:
                if i._text == typee: i.configure(fg_color="#0d610c", hover_color="#063b05")
                else: i.configure(fg_color="#3a7ebf", hover_color="#325882")

    async def start(self, socket, steam_id):
        self.socket: rustplus.RustSocket = socket
        self.steam_id: int = steam_id
        self.team = await self.socket.get_team_info()
        player = [player for player in self.team.members if player.steam_id == self.steam_id][0]
        self.name = player.name
        self.mapsize = (await self.socket.get_info()).size

        self.map_canvas = None
        self.team_canvas = None
        self.server_canvas = None

        self.team_info = None
        self.server_info = None
        self.server = None
        self.widgets = []
        
        self.main_window = ctk.CTk()
        self.main_window.title("Rust+Desktop")
        self.main_window.geometry("650x650")

        #Canvas Menu
        self.menu = MenuCanvas(self.main_window, width=125, height=650, bg="darkolivegreen4")
        self.menu.pack_propagate(0)
        self.menu.pack(side="left", fill="y")
        img = ImageTk.PhotoImage(Image.open("assets/User.png"))
        self.menu.create_image(62.5,5,anchor=tk.N, image=img)
        self.menu.create_text(62.5, 100, text=str(self.name), fill="white", font=("Verdana", 12))
        self.menu.create_text(62.5, 115, text=f"Online: {player.is_online}", fill="light gray", font=("Verdana", 10))
        self.menu.create_text(62.5, 130, text=f"Alive: {player.is_alive}", fill="light gray", font=("Verdana", 10))
        self.time_label = TimeLabel(self.menu, text="Loading time...", text_color="white") # Time
        self.time_label.pack(pady=(135,0))
        self.menu.create_line(0,165,130,165,fill="black", width=3)
        ctk.CTkButton(self.menu, 110, 30, text="Map", fg_color="#0d610c", hover_color="#063b05", command=lambda:self.topage("Map")).pack(pady=(15,0))
        ctk.CTkButton(self.menu, 110, 30, text="Team", command=lambda:self.topage("Team")).pack(pady=(5,0))
        ctk.CTkButton(self.menu, 110, 30, text="Server", command=lambda:self.topage("Server")).pack(pady=(5,0))

        #Canvas for the map
        self.map_canvas = MapCanvas(self.main_window, width=525, height=650)
        self.map_canvas.pack()

        asyncio.create_task(self.time_loop()) #update time
        asyncio.create_task(self.location_update_loop()) #update minimap
        asyncio.create_task(self.update_team()) #self.team and teamcanvas updater
        asyncio.create_task(self.update_server()) #self.server and servercanvas updater

        while True:
            try: self.main_window.update()
            except: pass

            # If the window is closed, disconnect from the server
            try:
                if not self.main_window.winfo_exists():
                    await self.socket.disconnect()
                    exit()
            except:
                await self.socket.disconnect()
                exit()
                
            await asyncio.sleep(0.1)

    async def update_server(self):
        print("LOOPS | Update Server Started")
        while True:
            s = await self.socket.get_info()
            self.server = s
            if self.server_canvas != None:
                if self.server_info == None:
                    self.server_info = ctk.CTkFrame(self.server_canvas, height=500, width=1920, corner_radius=10, fg_color="gray10", bg_color="gray10")
                    self.server_info.pack()
                    ctk.CTkLabel(self.server_info, anchor="w", width=self.server_canvas.width/2, height=50, bg_color="gray10", fg_color="gray10", corner_radius=15, text=f"Name: {s.name}", font=("Verdana", 16)).grid(row=1, column=1)
                    ctk.CTkLabel(self.server_info, anchor="w", width=self.server_canvas.width/2, height=50, bg_color="gray10", fg_color="gray10", corner_radius=15, text=f"URL: {s.url}", font=("Verdana", 16)).grid(row=2, column=1)
                    ctk.CTkLabel(self.server_info, anchor="w", width=self.server_canvas.width/2, height=50, bg_color="gray10", fg_color="gray10", corner_radius=15, text=f"Map Size: {s.size}", font=("Verdana", 16)).grid(row=1, column=2)
                    ctk.CTkLabel(self.server_info, anchor="w", width=self.server_canvas.width/2, height=50, bg_color="gray10", fg_color="gray10", corner_radius=15, text=f"Players: {s.players}", font=("Verdana", 16)).grid(row=2, column=2)
                else:
                    for i in self.server_info.winfo_children():
                        if "Name: " in i._text: i.configure(text=f"Name: {s.name}")
                        elif "URL: " in i._text: i.configure(text=f"URL: {s.url}")
                        elif "Map Size: " in i._text: i.configure(text=f"Map Size: {s.size}")
                        elif "Players: " in i._text: i.configure(text=f"Players: {s.players}")
                await asyncio.sleep(5)

    async def update_team(self):
        print("LOOPS | Update Team Started")
        while True:
            t = await self.socket.get_team_info()
            self.team = t
            if self.team_canvas != None:
                if str(t.leader_steam_id)[0] != "7":
                    if not self.team_info:
                        self.team_info = ctk.CTkLabel(self.team_canvas, height=50, bg_color="gray14", fg_color="gray14", corner_radius=3, text="You are not in a team.", font=("Verdana", 24)).pack()
                else:
                    if self.team_info: self.team_info.destroy(); self.team_info = None
                    height_per = self.team_canvas.height/len(t.members)-10
                    if self.widgets == []:
                        for i in t.members:
                            frame = ctk.CTkFrame(self.team_canvas, height=height_per, width=1920, corner_radius=10)
                            self.widgets.append(frame)
                            frame.pack(pady=(10), padx=(10,10))
                            if self.team.leader_steam_id == i.steam_id: extra = "👑 | "
                            else: extra = "👤 | "
                            if i.is_online == True: coloron = "green"
                            else: coloron="red"
                            if i.is_alive == True: coloral = "green"
                            else: coloral="red"
                            ctk.CTkLabel(frame, width=self.team_canvas.width/2, bg_color="#114f80", fg_color="#114f80", text=f"{extra}{i.name}", font=("Noto Sans", 17), anchor="nw").grid(row=1, column=1)
                            ctk.CTkLabel(frame, width=self.team_canvas.width/2, bg_color="#114f80", fg_color="#114f80", text=f"{i.steam_id}", font=("Noto Sans", 17), anchor="nw").grid(row=2, column=1)
                            ctk.CTkLabel(frame, width=self.team_canvas.width/2, bg_color="#114f80", fg_color="#114f80", text_color=coloron, text="Online", font=("Noto Sans", 17), anchor="nw").grid(row=1, column=2)
                            ctk.CTkLabel(frame, width=self.team_canvas.width/2, bg_color="#114f80", fg_color="#114f80", text_color=coloral, text=f"Alive", font=("Noto Sans", 17), anchor="nw").grid(row=2, column=2) 
            await asyncio.sleep(0.5)

    async def time_loop(self):
        print("LOOPS | Time Loop Started")
        while True:
            self.time_label.configure(text=f"Time: {(await self.socket.get_time()).time}")
            await asyncio.sleep(1)

    async def location_update_loop(self):
        print("LOOPS | Minimap Loop Started")
        while True:
            if self.map_canvas != None:
                team = self.team #get team info
                player = [player for player in team.members if player.steam_id == self.steam_id][0] #get the player with the same steam id as the one used to connect to the server
                mapsize = self.mapsize
                
                #location to draw the map (by the player)
                x = 0 - (player.x/mapsize) * 2000
                y = -2000 + (player.y/mapsize) * 2000
                # Draw the map on the canvas
                if os.path.isfile("map.png"):
                    img = ImageTk.PhotoImage(file="map.png")
                else:
                    while not os.path.isfile("map.png"):
                        await asyncio.sleep(0.1)
                    img = ImageTk.PhotoImage(file="map.png")
                
                try:
                    if self.map_canvas != None:
                        self.map_canvas.create_image(x + self.map_canvas.width/2, y + self.map_canvas.height/2, anchor=tk.NW, image=img)
                        
                        # Draw own player
                        self.map_canvas.create_oval(self.map_canvas.width/2 - 5, self.map_canvas.height/2 - 5, self.map_canvas.width/2 + 5, self.map_canvas.height/2 + 5, fill="lime")
                        self.map_canvas.create_text(self.map_canvas.width/2, self.map_canvas.height/2 - 15, text=str(player.name), fill="black", font=("Verdana", 10))

                        self.map_canvas.update()
                except: print("error"); pass # if window changes
            await asyncio.sleep(0.5)

SignInPage()