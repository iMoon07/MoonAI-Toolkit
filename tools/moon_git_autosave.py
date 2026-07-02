import time
import subprocess
import threading
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEBOUNCE_TIME = 60.0
timer = None

def git_commit():
    print("\n💾 [Moon Safe Autosave] Merekam checkpoint lokal...")
    try:
        # Tambahkan semua perubahan
        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Cek apakah ada yang benar-benar berubah (menghindari empty commit)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            return
            
        # Lakukan commit
        subprocess.run([
            "git", "commit", "-m", "checkpoint: auto save Moon state"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Checkpoint lokal berhasil disimpan. (Tanpa Push)")
    except Exception as e:
        print(f"❌ Gagal melakukan commit: {e}")

class Handler(FileSystemEventHandler):
    def _is_ignored(self, path):
        # Abaikan direktori Git internal dan database memory
        if f"{os.sep}.git{os.sep}" in path or "__pycache__" in path or ".db" in path:
            return True
            
        # Gunakan Git secara native untuk mengecek apakah file ada di .gitignore
        try:
            result = subprocess.run(
                ["git", "check-ignore", path], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            # Jika return code 0, berarti file ada di .gitignore
            return result.returncode == 0
        except Exception:
            return False

    def on_modified(self, event):
        global timer
        
        if event.is_directory:
            return
            
        if self._is_ignored(event.src_path):
            return

        if timer:
            timer.cancel()

        # Mulai hitung mundur 60 detik (debounce) setiap kali ada file di-save
        timer = threading.Timer(DEBOUNCE_TIME, git_commit)
        timer.start()

if __name__ == "__main__":
    print(f"🔥 Moon Safe Autosave V2 ACTIVE (Debounce: {DEBOUNCE_TIME}s)")
    print("Memonitor perubahan kode untuk Auto-Commit Lokal...")
    print("Tekan CTRL+C untuk berhenti.\n")
    
    observer = Observer()
    # Monitor current directory (Root project)
    observer.schedule(Handler(), ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🌙 Mematikan Safe Autosave...")
        if timer:
            timer.cancel()
        observer.stop()

    observer.join()
