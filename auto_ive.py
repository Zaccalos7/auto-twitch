import os
import time
import random
import subprocess
import glob
import signal

VIDEO_DIR = "/mnt/usb/repliche"
LOG_FILE = "/home/mario/streamer/logs/stream.log"
STOP_FILE = "/home/mario/streamer/STOP.txt"
START_FILE = "/home/mario/streamer/START.txt"
RESTART_FILE = "/home/mario/streamer/RESTART.txt"
GAME_FILE = "/home/mario/streamer/GAME.txt"
GAME_LAST = "/home/mario/streamer/.game_last"
NEXTVIDEO = "/home/mario/streamer/NEXTVIDEO.txt"
STATUS_FILE = "/home/mario/streamer/STATUS.txt"

TWITCH_KEY = "live_1421368812_Sz6gdF4iRgqdIFhWsmYbHj8qxmSAik"
TWITCH_URL = f"rtmp://live.twitch.tv/app/{TWITCH_KEY}"

if not os.path.exists(GAME_LAST):
    with open(GAME_LAST, "w") as f:
        f.write("none")

def log_message(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()} {message}\n")

def get_video_info(path):
    try:
        cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
        duration = float(subprocess.check_output(cmd_dur).strip())
        
        cmd_fps = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", path]
        fps_str = subprocess.check_output(cmd_fps).decode().strip()
        num, den = map(int, fps_str.split('/')) if '/' in fps_str else (float(fps_str), 1)
        fps = num / den
        
        return duration, fps
    except:
        return 0, 30

while True:
    if os.path.exists(STOP_FILE):
        log_message("STOP richiesto. In attesa di START...")
        os.remove(STOP_FILE)
        while not os.path.exists(START_FILE):
            time.sleep(2)
        log_message("START ricevuto. Riprendo...")
        os.remove(START_FILE)

    current_game = "Just Chatting"
    if os.path.exists(GAME_FILE):
        with open(GAME_FILE, "r") as f:
            current_game = f.read().strip()
    with open(GAME_LAST, "w") as f:
        f.write(current_game)

    video_path = ""
    if os.path.exists(NEXTVIDEO):
        with open(NEXTVIDEO, "r") as f:
            requested = f.read().strip()
        full_path = os.path.join(VIDEO_DIR, requested)
        if os.path.exists(full_path):
            video_path = full_path
        os.remove(NEXTVIDEO)

    if not video_path:
        files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4")) + glob.glob(os.path.join(VIDEO_DIR, "*.mkv"))
        if files:
            video_path = random.choice(files)
    
    if not video_path:
        time.sleep(5)
        continue

    display_name = os.path.splitext(os.path.basename(video_path))[0]
    with open(STATUS_FILE, "w") as f:
        f.write(video_path)

    duration, fps = get_video_info(video_path)
    gop = int(fps * 2)
    
    log_message(f"Inizio streaming: {display_name} (Durata: {int(duration)} sec)")

    countdown_text = f"%{{eif\\:({duration}-t)/3600\\:d\\:2}}\\:%{{eif\\:mod(({duration}-t),3600)/60\\:d\\:2}}\\:%{{eif\\:mod(({duration}-t),60)\\:d\\:2}}"

    filters = (
        f"drawtext=text='{display_name}':fontcolor=white:fontsize=26:box=1:boxcolor=black@0.5:boxborderw=6:x=20:y=20,"
        f"drawtext=text='REPLAY & PECORIZIA ✦ LIVE 24/7':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.4:boxborderw=6:x='mod(-t*120,w)':y=h-th-20,"
        f"drawtext=text='-{countdown_text}':fontcolor=yellow:fontsize=26:box=1:boxcolor=black@0.5:boxborderw=6:x=w-tw-20:y=20"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-re", "-i", video_path,
        "-vf", filters,
        "-c:v", "h264_v4l2m2m", "-b:v", "2500k", "-pix_fmt", "yuv420p",
        "-g", str(gop),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", TWITCH_URL
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    while process.poll() is None:
        if os.path.exists(GAME_FILE):
            with open(GAME_FILE, "r") as f:
                check_game = f.read().strip()
            if check_game != current_game:
                process.terminate()
                break
        
        if os.path.exists(NEXTVIDEO) or os.path.exists(STOP_FILE) or os.path.exists(RESTART_FILE):
            if os.path.exists(RESTART_FILE):
                os.remove(RESTART_FILE)
            process.terminate()
            break
        
        time.sleep(2)

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    time.sleep(1)