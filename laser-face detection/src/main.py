# python/main.py
import socket
import time
import threading
import math
import argparse
from pathlib import Path
import subprocess
import json

HOST = '127.0.0.1'
PORT = 9000

class ControllerClient:
    def __init__(self, host=HOST, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.lock = threading.Lock()
        self.telemetry = {'pan':0.0, 'tilt':0.0, 'laser':0}

        # start receiver thread
        self._running = True
        self.thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.thread.start()

    def _recv_loop(self):
        buff = b''
        while self._running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    self._running = False
                    break
                buff += data
                while b'\n' in buff:
                    line, buff = buff.split(b'\n',1)
                    s = line.decode().strip()
                    if s.startswith("POS"):
                        parts = s.split()
                        if len(parts) >= 4:
                            _, p, t, l = parts[:4]
                            with self.lock:
                                self.telemetry['pan'] = float(p)
                                self.telemetry['tilt'] = float(t)
                                self.telemetry['laser'] = int(float(l))
            except Exception as e:
                print("recv error:", e)
                self._running = False

    def set(self, pan, tilt, laser=0):
        cmd = f"SET {pan:.3f} {tilt:.3f} {1 if laser else 0}\n"
        with self.lock:
            self.sock.send(cmd.encode())

    def get_telemetry(self):
        with self.lock:
            return dict(self.telemetry)

    def close(self):
        self._running = False
        try:
            self.sock.close()
        except:
            pass

# helper scan patterns
def raster_scan(client, pan_min=-60, pan_max=60, tilt_min=-30, tilt_max=30, steps=6, dwell=0.6):
    pans = [pan_min + i*(pan_max-pan_min)/(steps-1) for i in range(steps)]
    tilts = [tilt_min + i*(tilt_max-tilt_min)/(steps-1) for i in range(steps)]
    for j, t in enumerate(tilts):
        for i, p in enumerate(pans if j%2==0 else reversed(pans)):
            client.set(p, t, laser=0)
            time.sleep(dwell)
            yield p,t

def search_and_lock(client, detect_func, max_cycles=3):
    # run raster scans until detect returns a position
    for cycle in range(max_cycles):
        print("Search cycle", cycle+1)
        for p,t in raster_scan(client):
            # ask detector for a frame and detection
            det = detect_func()  # should return (x_px, y_px, w, h) or None
            if det:
                print("Target detected:", det)
                x,y,w,h = det
                # simple mapping from image center offset to pan/tilt correction
                img_w, img_h = 320, 240
                cx = img_w/2; cy = img_h/2
                dx = (x - cx) / cx  # -1 to 1
                dy = (y - cy) / cy
                # convert to degrees: assume FOV ~ 60 deg horizontally and 45 deg vertically
                pan_corr = dx * 30
                tilt_corr = -dy * 22.5
                # aim and enable laser
                client.set(p + pan_corr, t + tilt_corr, laser=1)
                # hold for a second
                time.sleep(1.0)
                client.set(p + pan_corr, t + tilt_corr, laser=0)
                return True
    return False

# stub detection function
def make_detector(script_path=None):
    # returns a callable that runs detect_tf.py and returns center x,y,w,h or None
    def detect():
        if script_path:
            try:
                p = subprocess.run(['python3', script_path, '--single'], capture_output=True, text=True, timeout=2.5)
                out = p.stdout.strip()
                # expect JSON line or "NONE"
                if out.startswith("{"):
                    j = json.loads(out)
                    return (j['x'], j['y'], j['w'], j['h'])
            except Exception as e:
                # print("detector error", e)
                return None
        return None
    return detect

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--detector', default="../python/detect_tf.py", help="path to detection script")
    args = parser.parse_args()

    client = ControllerClient()
    detector = make_detector(script_path=args.detector)

    try:
        locked = search_and_lock(client, detector, max_cycles=6)
        if locked:
            print("Target lock sequence complete.")
        else:
            print("Target not found.")
    finally:
        client.close()

if __name__ == '__main__':
    main()
