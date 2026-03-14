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

# Lock for thread-safe output
output_lock = threading.Lock()

def log_output(name, stream, prefix):
    """Read from subprocess stream and print all output with proper synchronization"""
    try:
        for line in stream:
            if line:
                with output_lock:
                    print(f"[{prefix}] {line.rstrip()}")
                    sys.stdout.flush()
    except Exception as e:
        with output_lock:
            print(f"[{prefix}] Error reading output: {e}")
            sys.stdout.flush()
    finally:
        try:
            stream.close()
        except:
            pass

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
        with output_lock:
            print(f"[LAUNCHER] Starting {name}...")
            sys.stdout.flush()
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUNBUFFERED", "1")
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            self.processes[name] = proc
            
            # Create threads for stdout and stderr separately for complete output capture
            stdout_thread = threading.Thread(
                target=log_output, 
                args=(name, proc.stdout, f"{name.upper()}-OUT"), 
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=log_output, 
                args=(name, proc.stderr, f"{name.upper()}-ERR"), 
                daemon=True
            )
            stdout_thread.start()
            stderr_thread.start()
            
            with output_lock:
                print(f"[LAUNCHER] {name} started (PID: {proc.pid})")
                sys.stdout.flush()
            return proc
        except Exception as e:
            with output_lock:
                print(f"[LAUNCHER] Failed to start {name}: {e}")
                sys.stdout.flush()
            return None
    
    def stop_process(self, name):
        if name in self.processes:
            proc = self.processes[name]
            if proc and proc.poll() is None:
                with output_lock:
                    print(f"[LAUNCHER] Stopping {name}...")
                    sys.stdout.flush()
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                with output_lock:
                    print(f"[LAUNCHER] {name} stopped")
                    sys.stdout.flush()
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
                with output_lock:
                    print("\n[LAUNCHER] Settings changed! Restarting mouse and voice...")
                    sys.stdout.flush()
                self.last_modified = self.get_settings_mtime()
                self.restart_process("mouse", [sys.executable, "mouse_control.py"], cwd=PROJECT_ROOT)
                self.restart_process("voice", [sys.executable, "heisenberg.py"], cwd=PROJECT_ROOT)
                with output_lock:
                    print("[LAUNCHER] Restart complete")
                    sys.stdout.flush()
    
    def check_processes(self):
        for name, proc in list(self.processes.items()):
            if proc.poll() is not None:
                with output_lock:
                    print(f"[LAUNCHER] {name} crashed, restarting...")
                    sys.stdout.flush()
                if name == "webserver":
                    self.start_process(name, [sys.executable, "heisenberg_gui/main_web.py"], cwd=PROJECT_ROOT)
                elif name == "mouse":
                    self.start_process(name, [sys.executable, "mouse_control.py"], cwd=PROJECT_ROOT)
                elif name == "voice":
                    self.start_process(name, [sys.executable, "heisenberg.py"], cwd=PROJECT_ROOT)
    
    def run(self):
        with output_lock:
            print("=" * 50)
            print("  HEISENBERG LAUNCHER")
            print("=" * 50)
            print("\nStarting all services...")
            sys.stdout.flush()
        
        self.start_all()
        
        with output_lock:
            print("\n[LAUNCHER] All services started!")
            print("  - Web Server: http://127.0.0.1:8000")
            print("  - Mouse Control: Running")
            print("  - Voice Control: Running")
            print("\nPress Ctrl+C to stop all services\n")
            sys.stdout.flush()
        
        watch_thread = threading.Thread(target=self.watch_settings, daemon=True)
        watch_thread.start()
        
        try:
            while self.running:
                self.check_processes()
                time.sleep(3)
        except KeyboardInterrupt:
            with output_lock:
                print("\n[LAUNCHER] Interrupt received")
                sys.stdout.flush()
        finally:
            self.running = False
            self.stop_all()
            with output_lock:
                print("[LAUNCHER] Done")
                sys.stdout.flush()

if __name__ == "__main__":
    launcher = HeisenbergLauncher()
    launcher.run()
