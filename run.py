import os
import sys
import subprocess
import time

def run_command(command, description):
    """Utility to run a command and print its status."""
    print(f"[INFO] {description}...")
    try:
        # Show output for pip install so user sees progress
        if "pip" in str(command):
            subprocess.check_call(command, shell=False)
        else:
            subprocess.check_call(command, shell=False, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        return False

def check_packages_installed(venv_pip, req_file):
    """Check if all requirements are already installed to save time."""
    try:
        result = subprocess.run(
            [venv_pip, "list", "--format=freeze"],
            capture_output=True, text=True, check=True
        )
        installed = set(pkg.lower().split("==")[0] for pkg in result.stdout.splitlines())
        
        with open(req_file, 'r') as f:
            required = {line.strip().lower().split("==")[0] for line in f if line.strip() and not line.startswith("#")}
        
        return required.issubset(installed)
    except Exception:
        return False

def main():
    print("=" * 50)
    print("  Heisenberg - Auto Setup")
    print("=" * 50)

    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_root, "venv")
    
    # 1. Check/Create Virtual Environment
    print("[1/3] Checking virtual environment...")
    if not os.path.exists(venv_dir):
        if not run_command([sys.executable, "-m", "venv", "venv"], "Creating virtual environment"):
            return
    else:
        print("[OK] Virtual environment found")

    # Determine paths for pip and python in venv
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")

    # 2. Auto Install Requirements
    print("[2/3] Checking requirements...")
    req_file = os.path.join(project_root, "requirements.txt")
    if os.path.exists(req_file):
        if check_packages_installed(venv_pip, req_file):
            print("[OK] All requirements already installed")
        else:
            if not run_command([venv_pip, "install", "-r", "requirements.txt"], "Installing missing requirements"):
                return
            print("[OK] Installation complete")
    else:
        print("[WARN] requirements.txt not found, skipping installation")

    # 3. Run Launcher
    print("[3/3] Running launcher...")
    print("=" * 50)
    
    launcher_script = os.path.join(project_root, "launcher_no_gui.py")
    if os.path.exists(launcher_script):
        # We use subprocess.run here so start.py stays alive until the launcher exits
        try:
            subprocess.run([venv_python, "launcher_no_gui.py"])
        except KeyboardInterrupt:
            pass
    else:
        print(f"[ERROR] Launcher not found at {launcher_script}")

if __name__ == "__main__":
    main()
