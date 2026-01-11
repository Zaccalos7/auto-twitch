#!/usr/bin/env python3
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Scrollbar, Toplevel

STATUS_PATH = "/home/mario/streamer/STATUS.txt"
GAME_PATH = "/home/mario/streamer/GAME.txt"
NEXTVIDEO_PATH = "/home/mario/streamer/NEXTVIDEO.txt"
RESTART_PATH = "/home/mario/streamer/RESTART.txt"
USB_REPLICHE = "/mnt/usb/repliche"

def leggi_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None

def scrivi_file(path, contenuto):
    with open(path, "w") as f:
        f.write(contenuto)

def touch(path):
    open(path, "a").close()

def esegui(cmd):
    try:
        risultato = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        stderr = risultato.stderr.lower()

        if "sudo" in cmd and ("command not found" in stderr or "is not recognized" in stderr):
            messagebox.showerror("Errore", "Sudo non è disponibile su questo sistema.")
            return False

        if "sudo" in cmd and ("permission denied" in stderr or "password" in stderr):
            messagebox.showerror("Errore", "Permessi insufficienti per usare sudo.")
            return False

        if "systemctl" in cmd and ("command not found" in stderr or "is not recognized" in stderr):
            messagebox.showerror("Errore", "systemctl non è disponibile su questo sistema.")
            return False

        if risultato.returncode != 0:
            messagebox.showerror("Errore comando", risultato.stderr)
            return False

        return True

    except Exception as e:
        messagebox.showerror("Errore", str(e))
        return False

def avvia_stream():
    if esegui("sudo systemctl start streamer"):
        messagebox.showinfo("Streamer", "Diretta avviata.")

def ferma_stream():
    if esegui("sudo systemctl stop streamer"):
        messagebox.showinfo("Streamer", "Diretta fermata.")

def riavvia_stream():
    if esegui("sudo systemctl restart streamer"):
        messagebox.showinfo("Streamer", "Diretta riavviata.")

def cambia_categoria():
    nuova = simpledialog.askstring("Categoria", "Inserisci la nuova categoria:")
    if nuova:
        scrivi_file(GAME_PATH, nuova)
        messagebox.showinfo("Categoria", f"Categoria aggiornata a: {nuova}")

def stato_servizio():
    try:
        output = subprocess.getoutput("systemctl status streamer")
        mostra_output("Stato servizio", output)
    except:
        messagebox.showerror("Errore", "Impossibile eseguire systemctl.")

def log_realtime():
    try:
        os.system("x-terminal-emulator -e 'journalctl -u streamer -f'")
    except:
        messagebox.showerror("Errore", "Impossibile aprire il terminale.")

def video_attuale():
    video = leggi_file(STATUS_PATH)
    if not video:
        video = "Nessuna informazione disponibile."
    messagebox.showinfo("Video attuale", video)

def cambia_video_casuale():
    touch(RESTART_PATH)
    messagebox.showinfo("Cambio video", "Il video verrà cambiato automaticamente.")

def scegli_video():
    try:
        files = sorted(os.listdir(USB_REPLICHE))
    except:
        messagebox.showerror("Errore", f"La cartella {USB_REPLICHE} non esiste.")
        return

    win = Toplevel()
    win.title("Seleziona video")

    scrollbar = Scrollbar(win)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    lista = Listbox(win, width=60, height=20, yscrollcommand=scrollbar.set)
    for f in files:
        lista.insert(tk.END, f)
    lista.pack(side=tk.LEFT, fill=tk.BOTH)

    scrollbar.config(command=lista.yview)

    def conferma():
        selezione = lista.curselection()
        if not selezione:
            messagebox.showerror("Errore", "Seleziona un video.")
            return
        video = lista.get(selezione[0])
        scrivi_file(NEXTVIDEO_PATH, video)
        touch(RESTART_PATH)
        messagebox.showinfo("Video selezionato", f"Hai scelto: {video}")
        win.destroy()

    tk.Button(win, text="Conferma", command=conferma).pack(pady=10)

def mostra_output(titolo, testo):
    win = Toplevel()
    win.title(titolo)
    text = tk.Text(win, wrap="word", width=100, height=30)
    text.insert("1.0", testo)
    text.config(state="disabled")
    text.pack()

root = tk.Tk()
root.title("Gestione Diretta Twitch")
root.geometry("640x720")
root.aspect(3, 4, 3, 4)

BG = "#1e1e1e"
BTN_BG = "#2d2d2d"
BTN_FG = "#ffffff"
BTN_ACTIVE = "#3c3c3c"
BTN_BORDER = "#5a5a5a"

root.configure(bg=BG)

def crea_pulsante(testo, comando):
    return tk.Button(
        frame,
        text=testo,
        command=comando,
        font=("Segoe UI", 14),
        bg=BTN_BG,
        fg=BTN_FG,
        activebackground=BTN_ACTIVE,
        activeforeground=BTN_FG,
        relief="flat",
        bd=2,
        highlightthickness=2,
        highlightbackground=BTN_BORDER,
        highlightcolor=BTN_BORDER,
        padx=10,
        pady=10,
        width=18
    )

frame = tk.Frame(root, bg=BG)
frame.pack(pady=20)

btns = [
    ("Avvia diretta", avvia_stream),
    ("Ferma diretta", ferma_stream),
    ("Riavvia diretta", riavvia_stream),
    ("Cambia categoria", cambia_categoria),
    ("Stato servizio", stato_servizio),
    ("Log in tempo reale", log_realtime),
    ("Video attuale", video_attuale),
    ("Cambia video (casuale)", cambia_video_casuale),
    ("Scegli video manualmente", scegli_video),
]

riga = 0
col = 0

for testo, funzione in btns:
    crea_pulsante(testo, funzione).grid(row=riga, column=col, padx=10, pady=10)
    col += 1
    if col > 1:
        col = 0
        riga += 1

tk.Button(
    root,
    text="Esci",
    command=root.quit,
    font=("Segoe UI", 14, "bold"),
    bg="#8b0000",
    fg="white",
    activebackground="#a00000",
    relief="flat",
    padx=10,
    pady=10,
    width=25
).pack(pady=20)

root.mainloop()
