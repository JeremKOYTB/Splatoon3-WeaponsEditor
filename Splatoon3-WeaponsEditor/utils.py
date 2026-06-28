import sys
import os
import subprocess
import traceback
import json
import importlib
from datetime import datetime
from translations import t

def exception_hook(exctype, value, tb):
    if issubclass(exctype, KeyboardInterrupt):
        print("\n💬 [INFO] Program cleanly stopped by user (Ctrl+C). Goodbye!")
        sys.exit(0)

    print("\n" + "="*60)
    print("🚨 [FATAL CRITICAL CRASH] The program crashed! 🚨")
    print("="*60)
    traceback.print_exception(exctype, value, tb)
    print("="*60 + "\n")
    
    try:
        with open("crash_report.log", "w", encoding="utf-8") as f:
            f.write(f"Crash Time: {datetime.now()}\n\n")
            traceback.print_exception(exctype, value, tb, file=f)
        print("💾 A crash report has been saved to: crash_report.log\n")
    except:
        pass

    sys.stderr.flush()
    sys.stdout.flush()
    sys.exit(1)

sys.excepthook = exception_hook

def log(msg):
    time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{time_str}] 💬 {msg}")

log(t("log_init"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CONFIG_FILE = os.path.join(BASE_DIR, "splatoon_editor_config.json")

if not os.path.exists(CACHE_DIR):
    log(t("log_cache_dir", CACHE_DIR))
    os.makedirs(CACHE_DIR)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e: 
            log(f"❌ [ERROR] Cannot read config file: {e}")
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e: 
        log(f"❌ [ERROR] Cannot save configuration: {e}")

def get_last_dir():
    return load_config().get("last_dir", "")

def set_last_dir(file_path):
    config = load_config()
    config["last_dir"] = os.path.dirname(file_path)
    save_config(config)

def get_favorites():
    return set(load_config().get("favorites", []))

def save_favorites(fav_set):
    config = load_config()
    config["favorites"] = list(fav_set)
    save_config(config)
    log(t("log_fav_update", len(fav_set)))

def get_saved_language():
    return load_config().get("language", "English (US)")

def save_language(lang_name):
    config = load_config()
    config["language"] = lang_name
    save_config(config)

def get_hide_dummy():
    return load_config().get("hide_dummy", False)

def save_hide_dummy(state):
    config = load_config()
    config["hide_dummy"] = state
    save_config(config)

def get_hide_filenames():
    return load_config().get("hide_filenames", True)

def save_hide_filenames(state):
    config = load_config()
    config["hide_filenames"] = state
    save_config(config)

def get_hide_warning():
    return load_config().get("hide_warning", False)

def save_hide_warning(state):
    config = load_config()
    config["hide_warning"] = state
    save_config(config)

def install_requirements():
    log(t("log_dep_check"))
    required_packages = {
        "requests": "requests",
        "zstandard": "zstandard",
        "oead": "oead",
        "PyQt6": "PyQt6",
        "byml": "byml",
        "darkdetect": "darkdetect",
        "packaging": "packaging"
    }
    
    needs_restart = False
    for module_name, package_name in required_packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            log(f"[SYSTEM] -> Missing installation detected: '{package_name}'. Installing via pip...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                needs_restart = True
            except subprocess.CalledProcessError:
                print("\n" + "="*70)
                print(f"❌ [CRITICAL ERROR] The installation of library '{package_name}' failed.")
                if package_name == "oead":
                    print("⚠️  DIAGNOSTIC: 'oead' (Nintendo archive library) fails to compile.")
                    print(f"⚠️  You are using Python {sys.version_info.major}.{sys.version_info.minor}.")
                    print("⚠️  SOLUTION: Uninstall this recent Python version and install Python 3.11 or 3.12.")
                print("="*70 + "\n")
                sys.exit(1)

    if needs_restart:
        log(t("log_restart"))
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)