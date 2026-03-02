import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
MOUSE_SETTINGS = PROJECT_ROOT / "mouse_settings.json"
VOICE_SETTINGS = PROJECT_ROOT / "voice_settings.json"

class HeisenbergLauncher:
    def __init__(self):
        self.processes = {}
        self.last_modified = {}
        self.running = True
        self.watch_interval = 2
        
    def get_settings_mtime(self):
        mtimes = {}
        if MOUSE_SETTINGS.exists():
            mtimes[str(MOUSE_SETTINGS)] = MOUSE_SETTINGS.stat().st_mtime
        if VOICE_SETTINGS.exists():
            mtimes[str(VOICE_SETTINGS)] = VOICE_SETTINGS.stat().st_mtime
        return mtimes
    
    def check_settings_changed(self):
        current_mtimes = self.get_settings_mtime()
        for path, mtime in current_mtimes.items():
            if path not in self.last_modified:
                return True
            if mtime != self.last_modified[path]:
                return True
        return False
    
    def start_process(self, name, command, cwd=None):
        print(f"[LAUNCHER] Starting {name}...")
        try:
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            self.processes[name] = proc
            print(f"[LAUNCHER] {name} started (PID: {proc.pid})")
            return proc
        except Exception as e:
            print(f"[LAUNCHER] Failed to start {name}: {e}")
            return None
    
    def stop_process(self, name):
        if name in self.processes:
            proc = self.processes[name]
            if proc and proc.poll() is None:
                print(f"[LAUNCHER] Stopping {name}...")
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                print(f"[LAUNCHER] {name} stopped")
            del self.processes[name]
    
    def restart_process(self, name, command, cwd=None):
        self.stop_process(name)
        time.sleep(1)
        self.start_process(name, command, cwd)
    
    def start_all(self):
        self.last_modified = self.get_settings_mtime()
        
        self.start_process("webserver", [sys.executable, "heisenberg_gui/main_web.py"], cwd=PROJECT_ROOT)
        
        self.start_process("mouse", [sys.executable, "mouse_control.py"], cwd=PROJECT_ROOT)
        
        self.start_process("voice", [sys.executable, "heisenberg.py"], cwd=PROJECT_ROOT)
    
    def stop_all(self):
        print("\n[LAUNCHER] Shutting down...")
        for name in list(self.processes.keys()):
            self.stop_process(name)
    
    def watch_settings(self):
        while self.running:
            time.sleep(self.watch_interval)
            if self.check_settings_changed():
                print("\n[LAUNCHER] Settings changed! Restarting mouse and voice...")
                self.last_modified = self.get_settings_mtime()
                self.restart_process("mouse", [sys.executable, "mouse_control.py"], cwd=PROJECT_ROOT)
                self.restart_process("voice", [sys.executable, "heisenberg.py"], cwd=PROJECT_ROOT)
                print("[LAUNCHER] Restart complete")
    
    def check_processes(self):
        for name, proc in list(self.processes.items()):
            if proc.poll() is not None:
                print(f"[LAUNCHER] {name} crashed, restarting...")
                if name == "webserver":
                    self.start_process(name, [sys.executable, "heisenberg_gui/main_web.py"], cwd=PROJECT_ROOT)
                elif name == "mouse":
                    self.start_process(name, [sys.executable, "mouse_control.py"], cwd=PROJECT_ROOT)
                elif name == "voice":
                    self.start_process(name, [sys.executable, "heisenberg.py"], cwd=PROJECT_ROOT)
    
    def run(self):
        print("=" * 50)
        print("  HEISENBERG LAUNCHER")
        print("=" * 50)
        print("\nStarting all services...")
        
        self.start_all()
        
        print("\n[LAUNCHER] All services started!")
        print("  - Web Server: http://127.0.0.1:8000")
        print("  - Mouse Control: Running")
        print("  - Voice Control: Running")
        print("\nPress Ctrl+C to stop all services\n")
        
        watch_thread = threading.Thread(target=self.watch_settings, daemon=True)
        watch_thread.start()
        
        try:
            while self.running:
                self.check_processes()
                time.sleep(3)
        except KeyboardInterrupt:
            print("\n[LAUNCHER] Interrupt received")
        finally:
            self.running = False
            self.stop_all()
            print("[LAUNCHER] Done")

if __name__ == "__main__":
    launcher = HeisenbergLauncher()
    launcher.run()
