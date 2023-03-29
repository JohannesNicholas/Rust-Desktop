import os
import rustplus
import asyncio
import tkinter as tk




class SignInPage:
    def __init__(self):
        # Start a window
        self.window = tk.Tk()
        self.window.title("Rust+Desktop")
        self.window.geometry("400x400")

        # Input fields for the server ip and port, steam id and player token
        tk.Label(self.window, text="Server IP:").pack()
        ip = tk.Entry(self.window)
        ip.pack()
        tk.Label(self.window, text="Server Port:").pack()
        port = tk.Entry(self.window)
        port.pack()
        tk.Label(self.window, text="Steam ID:").pack()
        steam_id = tk.Entry(self.window)
        steam_id.pack()
        tk.Label(self.window, text="Player Token:").pack()
        player_token = tk.Entry(self.window)
        player_token.pack()
        tk.Button(self.window, text="Connect", command=lambda: asyncio.run(self.connect(ip.get(), port.get(), steam_id.get(), player_token.get()))).pack()

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
        await main_window.start(socket)

        



class MainWindow:
    async def start(self, socket):
        self.socket = socket
        self.main_window = tk.Tk()
        self.main_window.title("Rust+Desktop")
        self.main_window.geometry("400x400")

        self.time_label = tk.Label(self.main_window, text="Loading time...")
        self.time_label.pack()

        asyncio.create_task(self.time_loop())

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
            self.time_label.config(text=f"{(await self.socket.get_time()).time}")
            await asyncio.sleep(1)

            






SignInPage()



