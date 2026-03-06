import cv2
import numpy as np
import mss
import time
import threading
import pydirectinput
import customtkinter as ctk
import os
import uuid
import requests
import json
import hashlib
import sys
from tkinter import messagebox

running = False
last_press = 0

SERVER_URL = "https://synoicous-poetically-ludivina.ngrok-free.dev/verify"

# ซ่อน license file
CACHE_FILE = os.path.join(os.getenv("APPDATA"), "syscache.dat")

monitor = {
    "top": 872,
    "left": 860,
    "width": 200,
    "height": 200
}

button_templates = {}
keys_to_load = ["W","A","S","D","Q","E"]

# =========================
# FIX PATH FOR EXE
# =========================

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# =========================
# LICENSE SYSTEM
# =========================

def get_hwid():
    return str(uuid.getnode())


def create_hash(key,hwid):
    raw = key + hwid + "SECRET_SALT"
    return hashlib.sha256(raw.encode()).hexdigest()


def save_local_license(key):

    hwid = get_hwid()

    data = {
        "key": key,
        "hwid": hwid,
        "hash": create_hash(key,hwid)
    }

    with open(CACHE_FILE,"w") as f:
        json.dump(data,f)


def check_local_license():

    if not os.path.exists(CACHE_FILE):
        return False

    try:

        with open(CACHE_FILE,"r") as f:
            data = json.load(f)

        key = data["key"]
        hwid = data["hwid"]
        saved_hash = data["hash"]

        if hwid != get_hwid():
            return False

        if saved_hash != create_hash(key,hwid):
            return False

        return True

    except:
        return False


def verify_license(key):

    hwid = get_hwid()

    data = {
        "key": key,
        "hwid": hwid
    }

    try:

        r = requests.post(SERVER_URL,json=data,timeout=5)
        result = r.json()

        if result["status"] == "VALID":
            return True

        if result["status"] == "HWID_MISMATCH":
            messagebox.showerror("Error","Key already used on another PC")

        if result["status"] == "INVALID":
            messagebox.showerror("Error","Invalid License Key")

        return False

    except:
        messagebox.showerror("Error","Cannot connect to License Server")
        return False


# =========================
# BOT SYSTEM
# =========================

def load_templates():

    for k in keys_to_load:

        file = resource_path(f"{k}.png")

        if os.path.exists(file):
            img = cv2.imread(file,0)
            button_templates[k] = img


def detect_key(gray):

    best_key = None
    max_val = 0

    for k,temp in button_templates.items():

        res = cv2.matchTemplate(gray,temp,cv2.TM_CCOEFF_NORMED)
        _,val,_,_ = cv2.minMaxLoc(res)

        if val > 0.65 and val > max_val:
            max_val = val
            best_key = k.lower()

    return best_key,max_val


def detect_red(frame):

    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    lower1 = np.array([0,150,120])
    upper1 = np.array([10,255,255])

    lower2 = np.array([170,150,120])
    upper2 = np.array([180,255,255])

    mask = cv2.inRange(hsv,lower1,upper1) + cv2.inRange(hsv,lower2,upper2)

    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    if contours:

        c = max(contours,key=cv2.contourArea)

        if cv2.contourArea(c) > 20:

            M = cv2.moments(c)

            if M["m00"] != 0:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                return (cx,cy)

    return None


def detect_fish_bar(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array([0,0,150])
    upper = np.array([180,80,255])

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0

    for c in contours:

        area = cv2.contourArea(c)

        if area < 80:
            continue

        x,y,w,h = cv2.boundingRect(c)

        ratio = w / float(h)

        if 1.2 < ratio < 4.5:

            if area > best_area:

                cx = x + w//2
                cy = y + h//2

                best = (cx,cy)
                best_area = area

    return best


def press_key(k):

    global last_press

    now = time.time()

    if now - last_press < 0.18:
        return

    pydirectinput.keyDown(k)
    time.sleep(0.03)
    pydirectinput.keyUp(k)

    last_press = now


def bot_loop():

    global running

    load_templates()

    sct = mss.mss()

    while running:

        img = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(img,cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        key,score = detect_key(gray)
        red = detect_red(frame)
        fish = detect_fish_bar(frame)

        if red and fish and key:

            dist = np.sqrt((red[0]-fish[0])**2 + (red[1]-fish[1])**2)

            if dist < 28:
                press_key(key)

        time.sleep(0.002)


def start_bot():

    global running

    if not running:
        running = True
        status_label.configure(text="STATUS : RUNNING", text_color="green")
        threading.Thread(target=bot_loop,daemon=True).start()


def stop_bot():

    global running
    running = False
    status_label.configure(text="STATUS : STOPPED", text_color="red")


# =========================
# BOT UI
# =========================

def main_bot():

    global status_label

    app = ctk.CTk()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app.title("Fishing Bot")
    app.geometry("420x260")

    title = ctk.CTkLabel(app,text="Private",font=("Arial",24,"bold"))
    title.pack(pady=15)

    status_label = ctk.CTkLabel(app,text="STATUS : STOPPED",font=("Arial",16))
    status_label.pack(pady=10)

    frame = ctk.CTkFrame(app)
    frame.pack(pady=10)

    btn_start = ctk.CTkButton(frame,text="START BOT",width=150,height=40,
    fg_color="#2ecc71",command=start_bot)
    btn_start.grid(row=0,column=0,padx=10)

    btn_stop = ctk.CTkButton(frame,text="STOP BOT",width=150,height=40,
    fg_color="#e74c3c",command=stop_bot)
    btn_stop.grid(row=0,column=1,padx=10)

    hwid_label = ctk.CTkLabel(app,text=f"HWID : {get_hwid()}")
    hwid_label.pack(pady=10)

    app.mainloop()


# =========================
# LICENSE UI
# =========================

def license_window():

    win = ctk.CTk()

    ctk.set_appearance_mode("dark")

    win.title("License Login")
    win.geometry("360x220")

    label = ctk.CTkLabel(win,text="ENTER LICENSE KEY",font=("Arial",18))
    label.pack(pady=20)

    key_entry = ctk.CTkEntry(win,width=220)
    key_entry.pack(pady=10)

    def submit():

        key = key_entry.get()

        if verify_license(key):

            save_local_license(key)

            messagebox.showinfo("Success","License Activated")
            win.destroy()
            main_bot()

    btn = ctk.CTkButton(win,text="ACTIVATE",command=submit)
    btn.pack(pady=20)

    win.mainloop()


# =========================
# START PROGRAM
# =========================

if check_local_license():
    main_bot()
else:
    license_window()