import json

with open("settingdata.json", "r") as file:
    settings = json.load(file)

PID_KP = settings["servo_control"]["pid"]["kp"]
CAMERA_FPS = settings["camera"]["fps"]
MODEL_PATH = settings["tensorflow"]["model_path"]
