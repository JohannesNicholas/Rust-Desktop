import rustplus, asyncio, time, flask, threading, atexit, os, signal
from rustplus import MovementControls, Vector

config = eval(open("config.json", "r").read())
socket = rustplus.RustSocket(config["ip"], int(config["port"]), int(config["steam_id"]), int(config["player_token"]))
asyncio.run(socket.connect())
app = flask.Flask(__name__)
quitting = []
async def entity_to_json(entity):
    toreturn = {"name": entity.name, "position": [round(entity.position.x, 6), round(entity.position.y, 6), round(entity.position.z, 6)], "rotation": [round(entity.rotation.x, 6), round(entity.rotation.y, 6), round(entity.rotation.z, 6)]}
    return [entity.entity_id, toreturn]
camera = None
@app.route("/")
async def getEntities():
    allentities = {}
    for i in (await camera.get_entities_in_frame()):
        if i.type == 2:
            temp = await entity_to_json(i)
            allentities[temp[0]] = temp[1]
    return allentities
@app.route("/ping")
async def ping():
    return "."

async def getEntity(camera: rustplus.CameraManager, name: str):
    while not camera.has_frame_data(): await asyncio.sleep(0.2)
    try: entities = await camera.get_entities_in_frame()
    except: return None
    if len(entities) == 0: return None
    for i in entities:
        if i.type != 2: continue
        if i.name == name: return i
    return None

async def xCheck(pos):
    if pos.x < -1: return -0.5
    if pos.x > 1: return 0.5
    return 0
def death():
    sig = getattr(signal, "SIGKILL", signal.SIGTERM)
    os.kill(os.getpid(), sig)

async def down(drone_cam: rustplus.CameraManager, name):
    e = await getEntity(drone_cam, name)
    while e.position.y < -0.4:
        await drone_cam.send_actions([0])
        await asyncio.sleep(0.6)
        await drone_cam.clear_movement()
        await drone_cam.send_actions([MovementControls.DUCK])
        await asyncio.sleep(0.4)
        await drone_cam.clear_movement()
        e = await getEntity(drone_cam, name)
    await socket.send_team_message("Landed drone successfully"); death()

async def follow(camera: rustplus.CameraManager, name):
    await camera.send_actions([MovementControls.SPRINT])
    await asyncio.sleep(0.35)
    await camera.send_actions([0])
    camtime = 0
    camState = 0
    while True:
        try:
            if len(quitting) == 1: raise KeyboardInterrupt()
            e = await getEntity(camera, name)
            if e != None:
                if time.time() - camera.time_since_last_subscribe > 10: await camera.resubscribe()
                t = round(time.time() * 1000)
                if t > camtime+100:
                    btns = 0
                    x = 0
                    if camState == 0 and e.position.z >= 14:
                        camState = 1
                        btns = MovementControls.FORWARD
                        if e.position.y < -8: btns = MovementControls.DUCK
                        elif e.position.y > 2: btns = MovementControls.SPRINT
                        x = await xCheck(e.position)
                    elif camState == 0 and e.position.z >= 10:
                        camState = 1
                        btns = MovementControls.FORWARD
                        if e.position.y < -5: btns = MovementControls.DUCK
                        if e.position.y > -3: btns = MovementControls.SPRINT
                        x = await xCheck(e.position)
                    elif camState == 0 and e.position.z < 6:
                        camState = -1
                        btns = MovementControls.BACKWARD
                        t -= 50
                        if e.position.y < -5: btns = MovementControls.DUCK
                        if e.position.y > -3: btns = MovementControls.SPRINT
                        x = await xCheck(e.position)
                    elif camState == 0 and e.position.z < 3:
                        camState = -1
                        btns = MovementControls.BACKWARD
                        if e.position.y < -8: btns = MovementControls.DUCK
                        if e.position.y > 2: btns = MovementControls.SPRINT
                        x = await xCheck(e.position)
                    elif camState == 0 and e.position.x > 1: camState = 2; t -= 50; x = 0.5
                    elif camState == 0 and e.position.x < -1: camState = -2; t -= 50; x = -0.5
                    elif camState == 0 and e.position.y < -8: camState = -3; btns = MovementControls.DUCK
                    elif camState == 0 and e.position.y < -5: camState = -3; t -= 50; btns = MovementControls.DUCK
                    elif camState == 0 and e.position.y > 2: camState = 3 ; btns = MovementControls.SPRINT
                    elif camState == 0 and e.position.y > -3: camState = 3; t -= 50; btns = MovementControls.SPRINT
                    elif camState != 0 and camState != 99: camState = 0
                    elif camState != 99: camState = 0
                    await camera.send_combined_movement([btns], Vector(x,0))
                    camtime = t
            await asyncio.sleep(0.15)
        except: await down(camera, name)

async def drone():
    global camera
    if config["drone"] == "": exit("No drone defined.")
    USER = (await socket.get_team_info()).members
    if len(USER) == 0: await socket.send_team_message("Player could not be found (no team error)."); death()
    else: USER = [player for player in USER if player.steam_id == int(config["steam_id"])][0].name
    try: camera = await socket.get_camera_manager(config["drone"])
    except: await socket.send_team_message("Drone could not be found."); death()
    await asyncio.sleep(0.5)
    entity = await getEntity(camera, USER)
    if not entity: await socket.send_team_message("Player could not be found (cannot be seen)."); death()
    else: await follow(camera, USER)

def run():
    try:
        app.run("127.0.0.1")
    except RuntimeError:
        pass

async def run_both():
    threading.Thread(target=app.run, args=["127.0.0.1", 80]).start()
    await drone()

if __name__ == '__main__':
    atexit.register(quitting.append, "bye")
    asyncio.run(run_both())