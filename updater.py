import os
import sys
import json
import re
import zipfile
import urllib.request
import urllib.error
import subprocess
import importlib.util
import signal
import colorsys
import shutil
import time
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if "--install-dir" in sys.argv:
    try:
        idx = sys.argv.index("--install-dir")
        install_dir_path = sys.argv[idx + 1]
        sys.path.insert(0, os.path.abspath(install_dir_path))
    except IndexError:
        pass

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QMessageBox, QComboBox, QCheckBox, QSizePolicy,
                             QGraphicsOpacityEffect, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray, QPropertyAnimation, QAbstractAnimation, QDir
from PyQt6.QtGui import QIcon, QPixmap, QTextOption

def ensure_dependencies():
    if importlib.util.find_spec("darkdetect") is None:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "darkdetect"], 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            sys.exit(1)

ensure_dependencies()
import darkdetect

def get_current_app_version():
    base_dirs = [os.getcwd()]
    if "--install-dir" in sys.argv:
        try:
            idx = sys.argv.index("--install-dir")
            base_dirs.insert(0, sys.argv[idx + 1])
        except IndexError:
            pass

    for base_dir in base_dirs:
        for sub_path in ["main.py", os.path.join("Splatoon3-WeaponsEditor", "main.py")]:
            main_py_path = os.path.join(base_dir, sub_path)
            if os.path.exists(main_py_path):
                try:
                    with open(main_py_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        match = re.search(r'self\.APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            return match.group(1)
                except Exception:
                    pass
    return "1.0.0"

APP_VERSION = get_current_app_version()

BASE_FONT = "\"Segoe UI Variable\", \"Segoe UI\", \"Roboto\", sans-serif"

S3WE_MAIN_LOGO = b"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="1000.000000pt" height="1077.000000pt" viewBox="0 0 1000.000000 1077.000000"
 preserveAspectRatio="xMidYMid meet">
<g transform="translate(0.000000,1077.000000) scale(0.100000,-0.100000)" fill="#000000" stroke="none">
<path d="M4861 10735 c-494 -108 -1268 -693 -2291 -1731 -770 -783 -1286 -1399 -1750 -2094 -415 -621 -704 -1232 -775 -1634 -34 -200 -27 -460 17 -590 75 -222 236 -397 460 -500 261 -121 667 -182 1282 -195 l319 -6 23 -80 c32 -108 70 -289 86 -410 8 -65 13 -210 13 -415 l0 -315 -44 -90 c-171 -355 -241 -613 -241 -891 0 -268 54 -455 195 -683 177 -286 521 -611 864 -816 l63 -38 57 28 c130 63 270 186 345 303 51 79 108 191 126 247 7 22 17 48 22 58 15 30 34 4 64 -86 61 -188 161 -344 314 -491 102 -98 211 -175 327 -233 l72 -36 43 17 c124 50 305 197 393 321 60 85 91 150 123 262 15 53 33 98 39 100 6 2 20 -32 33 -79 66 -247 222 -442 450 -567 116 -63 147 -58 320 59 124 84 228 177 304 272 104 129 155 224 219 407 12 36 27 66 33 68 6 2 24 -31 39 -74 86 -240 238 -423 447 -537 35 -20 71 -36 80 -36 17 0 245 153 352 236 200 155 386 345 513 522 119 166 218 388 243 542 16 102 12 392 -6 501 -21 120 -86 319 -168 513 -97 227 -101 247 -100 531 0 243 9 361 44 560 16 93 72 311 82 320 2 2 147 8 323 14 584 21 876 57 1137 141 350 112 577 355 628 672 18 112 8 385 -19 511 -55 254 -147 496 -311 822 -202 402 -470 826 -804 1270 -654 873 -1773 2039 -2561 2671 -654 525 -1097 729 -1424 659z m296 -351 c469 -176 1654 -1277 2655 -2466 899 -1067 1462 -1953 1624 -2556 22 -82 27 -118 27 -237 0 -161 -10 -207 -68 -284 -104 -142 -393 -283 -768 -376 -188 -46 -381 -79 -645 -110 -299 -35 -278 -30 -309 -82 -60 -104 -209 -519 -283 -795 -64 -236 -57 -222 -116 -229 -79 -10 -124 -28 -170 -71 -58 -54 -85 -121 -85 -213 0 -91 17 -131 78 -185 41 -36 133 -80 167 -80 19 0 32 -19 41 -58 3 -17 22 -71 41 -118 19 -48 34 -88 32 -89 -2 -2 -39 -20 -83 -40 -199 -94 -346 -337 -332 -550 7 -104 28 -169 78 -244 77 -116 182 -170 347 -179 65 -3 102 -9 102 -16 0 -17 -68 -125 -120 -191 -105 -131 -363 -355 -429 -372 -26 -6 -49 4 -65 30 -8 12 1 26 46 70 69 65 93 133 86 232 -7 76 -36 134 -102 200 -127 127 -320 162 -442 79 -20 -14 -42 -23 -49 -20 -16 6 -63 126 -103 260 l-29 99 -12 -109 c-33 -299 -110 -546 -227 -726 -83 -129 -231 -266 -353 -328 -66 -33 -120 -25 -207 32 -174 112 -295 288 -384 557 -40 118 -79 293 -81 353 -1 85 -16 64 -32 -46 -59 -389 -212 -697 -416 -835 -121 -82 -168 -95 -239 -66 -56 24 -164 97 -155 105 4 4 33 15 63 25 138 44 238 124 291 232 34 68 34 204 -1 283 -57 134 -159 239 -296 305 -126 62 -277 63 -401 5 -36 -17 -68 -28 -70 -26 -3 2 -10 52 -16 110 -6 58 -14 106 -18 106 -4 0 -13 -24 -19 -52 -51 -215 -159 -416 -335 -626 -80 -95 -243 -246 -278 -258 -33 -10 -253 161 -386 302 -115 121 -199 266 -241 415 -11 41 -20 77 -20 81 0 3 26 14 57 23 84 24 124 48 171 99 60 65 82 122 82 209 0 133 -41 230 -129 309 l-50 45 36 84 c19 46 49 120 65 164 46 123 49 128 112 161 73 37 112 83 132 152 30 101 -1 197 -93 291 -42 43 -70 62 -100 70 -48 13 -41 -4 -118 280 -46 169 -124 396 -213 621 l-69 175 -49 7 c-27 4 -146 19 -264 33 -368 45 -647 104 -900 190 -317 109 -503 241 -551 393 -55 173 -10 437 128 761 306 717 1056 1754 2077 2871 220 240 866 886 1071 1070 536 481 901 734 1115 774 44 8 133 -5 197 -30z"/>
<path d="M3669 6820 c-171 -20 -362 -78 -499 -152 -275 -147 -538 -442 -657 -735 -188 -465 -197 -966 -26 -1428 46 -125 152 -319 233 -427 149 -198 332 -348 555 -454 211 -100 363 -130 620 -121 281 10 434 49 723 186 212 101 260 115 387 115 128 0 170 -13 410 -124 316 -146 432 -173 750 -174 156 -1 218 3 282 17 443 95 803 392 1017 837 59 122 123 306 151 430 23 102 32 485 15 646 -20 199 -84 412 -180 603 -140 279 -371 513 -636 645 -237 117 -557 168 -869 137 -231 -23 -368 -62 -646 -188 l-174 -78 -120 0 -120 0 -167 77 c-255 119 -331 144 -523 174 -112 18 -424 26 -526 14z m346 -160 c306 -36 592 -192 804 -441 58 -69 91 -118 179 -268 6 -10 25 13 69 85 155 249 319 401 558 516 458 218 1003 120 1371 -248 255 -256 395 -605 395 -989 0 -229 -42 -416 -136 -613 -219 -458 -639 -732 -1121 -733 -67 0 -150 5 -185 10 -221 36 -442 144 -625 306 -78 68 -214 236 -265 325 -58 103 -51 102 -97 16 -177 -327 -512 -575 -869 -642 -133 -25 -374 -15 -506 19 -270 71 -526 246 -695 472 -111 150 -207 374 -249 580 -26 134 -24 405 5 542 135 632 621 1058 1222 1072 30 0 95 -4 145 -9z"/>
<path d="M3844 6420 c-151 -22 -325 -125 -437 -258 -57 -67 -121 -194 -137 -272 -14 -69 -14 -211 -1 -272 49 -218 222 -409 451 -501 260 -103 569 -36 775 168 79 78 130 157 171 267 25 65 28 86 28 198 1 111 -2 133 -26 198 -73 201 -222 352 -428 435 -110 43 -257 57 -396 37z"/>
<path d="M5883 6416 c-251 -48 -484 -266 -548 -511 -19 -75 -19 -221 0 -304 36 -151 152 -308 298 -404 233 -154 480 -169 734 -47 84 41 116 64 181 127 136 134 201 273 210 448 5 123 -11 195 -70 313 -80 161 -234 292 -415 354 -71 25 -106 31 -202 34 -73 2 -143 -2 -188 -10z"/>
<path d="M5212 2997 c-48 -15 -117 -80 -143 -135 -32 -64 -33 -170 -2 -227 58 -109 195 -166 315 -131 141 41 199 195 129 341 -64 133 -178 191 -299 152z"/>
<path d="M3655 2747 c-63 -21 -97 -42 -142 -89 -84 -86 -104 -187 -58 -286 55 -118 109 -162 202 -162 156 0 279 88 320 229 13 46 14 65 4 121 -17 91 -46 138 -103 168 -58 30 -163 38 -223 19z"/>
<path d="M6179 2655 c-104 -38 -205 -126 -229 -201 -17 -51 -7 -168 18 -226 29 -65 94 -133 148 -154 136 -52 366 73 410 223 34 118 5 256 -66 316 -61 51 -200 72 -281 42z"/>
<path d="M4660 2321 c-84 -27 -162 -100 -211 -199 -32 -63 -34 -73 -34 -172 0 -90 3 -111 23 -147 77 -145 204 -191 376 -133 91 30 144 73 181 145 28 54 30 66 29 159 0 79 -5 113 -22 156 -47 117 -144 192 -257 197 -33 1 -71 -1 -85 -6z"/>
<path d="M3032 1579 c-45 -9 -102 -56 -131 -108 -34 -62 -34 -181 1 -249 45 -89 143 -132 253 -111 66 12 94 34 128 99 34 68 38 169 8 229 -47 91 -172 159 -259 140z"/>
<path d="M5460 1423 c-29 -10 -72 -58 -98 -108 -52 -99 -30 -209 56 -287 47 -43 93 -52 176 -38 71 11 108 42 131 108 17 51 20 148 6 185 -36 94 -185 171 -271 140z"/>
</g>
</svg>"""

def get_app_icon():
    svg_data = S3WE_MAIN_LOGO
    if darkdetect.isDark():
        svg_data = svg_data.replace(b'fill="#000000"', b'fill="#FFFFFF"')
    pix = QPixmap()
    pix.loadFromData(QByteArray(svg_data))
    return QIcon(pix)

THEMES = {
    "dark": {
        "bg": "#3C3C44", "bg_input": "#32323A", "text": "#E8E8E8", "text_title": "#FFFFFF", 
        "text_dim": "#B0B0B8", "card": "#4A4A54", "border": "#555560", "border_hover": "#626270",
        "btn_text": "#2B2B30", "warn": "#EF5350"
    },
    "light": {
        "bg": "#F0F0F5", "bg_input": "#F9F9FB", "text": "#1D1D1F", "text_title": "#000000", 
        "text_dim": "#8E8E93", "card": "#FFFFFF", "border": "#D1D1D6", "border_hover": "#E5E5EA",
        "btn_text": "#1D1D1F", "warn": "#EF5350"
    },
    "oled": {
        "bg": "#000000", "bg_input": "#121212", "text": "#E8E8E8", "text_title": "#FFFFFF", 
        "text_dim": "#888888", "card": "#0A0A0A", "border": "#333333", "border_hover": "#555555",
        "btn_text": "#000000", "warn": "#EF5350"
    }
}

def load_editor_config():
    base_dirs = [os.getcwd()]
    if "--install-dir" in sys.argv:
        try:
            idx = sys.argv.index("--install-dir")
            base_dirs.insert(0, sys.argv[idx + 1])
        except IndexError:
            pass

    cfg = {
        "theme": "dark",
        "accent_color": "#E6FF00", 
        "rainbow_mode": False,
        "rainbow_speed": 2
    }
    
    for base_dir in base_dirs:
        for sub_path in ["splatoon_editor_config.json", os.path.join("Splatoon3-WeaponsEditor", "splatoon_editor_config.json")]:
            config_path = os.path.join(base_dir, sub_path)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for k in cfg:
                            if k in data:
                                cfg[k] = data[k]
                    return cfg
                except Exception:
                    pass
    return cfg

def get_stylesheet(theme_name, accent_color):
    c = THEMES.get(theme_name, THEMES["dark"])
    return f"""
    QMainWindow, QDialog, QMessageBox {{ background-color: {c['bg']}; color: {c['text']}; }}
    QWidget {{ font-family: {BASE_FONT}; font-size: 10pt; }}
    QLabel {{ color: {c['text']}; }}
    QFrame#Card {{ background-color: {c['card']}; border-radius: 8px; border: 1px solid {c['border']}; }}
    QLabel#CardTitle {{ color: {c['text_title']}; font-size: 13pt; font-weight: 700; }}
    QLabel#CardVersion {{ color: {c['text_dim']}; font-size: 9pt; font-weight: 500; }}
    QComboBox {{ background-color: {c['bg_input']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 6px; color: {c['text']}; min-height: 28px; outline: none; }}
    QCheckBox {{ color: {c['text']}; outline: none; }}
    QPushButton {{ background-color: {c['border']}; color: {c['text']}; border-radius: 6px; padding: 6px 14px; font-weight: 600; border: 1px solid {c['border_hover']}; min-height: 20px; outline: none; }}
    QPushButton:hover {{ background-color: {c['border_hover']}; }}
    QPushButton:pressed {{ background-color: {accent_color}; color: {c['btn_text']}; border: 1px solid {accent_color}; }}
    #btnExecute {{ background-color: {accent_color}; color: {c['btn_text']}; font-size: 11pt; font-weight: bold; padding: 10px 24px; border-radius: 6px; border: none; min-width: 200px; }}
    #btnExecute:hover {{ opacity: 0.8; color: {c['btn_text']}; }}
    """

class ReleasesFetchThread(QThread):
    finished = pyqtSignal(list, str)

    def run(self):
        url = f"https://api.github.com/repos/JeremKOYTB/Splatoon3-WeaponsEditor/releases?t={int(time.time())}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Splatoon3Editor-Updater'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            self.finished.emit(data, "")
        except Exception as e:
            self.finished.emit([], str(e))

class DownloadWorkerThread(QThread):
    progress = pyqtSignal(str)
    completed = pyqtSignal(bool, str)

    def __init__(self, download_url, install_dir, target_version):
        super().__init__()
        self.download_url = download_url
        self.install_dir = os.path.abspath(install_dir)
        self.target_version = target_version
        self.is_7z = download_url.lower().endswith(".7z")

    def run(self):
        temp_archive_path = os.path.join(self.install_dir, "S3E_Update_Temp." + ("7z" if self.is_7z else "zip"))
        temp_extract_dir = os.path.join(self.install_dir, "S3E_Extract_Temp")
        
        try:
            if self.is_7z:
                self.progress.emit("Loading 7z extraction modules...")
                if importlib.util.find_spec("py7zr") is None:
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "py7zr"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except subprocess.CalledProcessError:
                        raise Exception("Failed to install py7zr required for 7z extraction.")
            
            self.progress.emit("Downloading archive...")
            req = urllib.request.Request(self.download_url, headers={'User-Agent': 'Splatoon3Editor-Updater'})
            with urllib.request.urlopen(req, timeout=30) as response, open(temp_archive_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            self.progress.emit("Extracting files...")
            os.makedirs(temp_extract_dir, exist_ok=True)
            
            if self.is_7z:
                import py7zr
                with py7zr.SevenZipFile(temp_archive_path, mode='r') as z:
                    z.extractall(path=temp_extract_dir)
            else:
                with zipfile.ZipFile(temp_archive_path, 'r') as z:
                    z.extractall(temp_extract_dir)

            self.progress.emit("Analyzing architecture...")
            base_target = temp_extract_dir
            contents = os.listdir(temp_extract_dir)
            if len(contents) == 1:
                possible_dir = os.path.join(temp_extract_dir, contents[0])
                if os.path.isdir(possible_dir):
                    base_target = possible_dir

            main_script_target = os.path.join(base_target, "Splatoon3-WeaponsEditor", "main.py")
            if not os.path.exists(main_script_target):
                raise Exception("Security: The vital file 'Splatoon3-WeaponsEditor/main.py' is missing from the downloaded archive.")

            self.progress.emit("Cleaning up old files...")
            extracted_files = set()
            for root, _, files in os.walk(base_target):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), base_target)
                    extracted_files.add(os.path.normcase(os.path.abspath(os.path.join(self.install_dir, rel_path))))

            protected_paths = [
                os.path.normcase(os.path.abspath(os.path.join(self.install_dir, "Splatoon3-WeaponsEditor", "cache"))),
                os.path.normcase(os.path.abspath(os.path.join(self.install_dir, "Splatoon3-WeaponsEditor", "splatoon_editor_config.json"))),
                os.path.normcase(os.path.abspath(os.path.join(self.install_dir, "cache"))),
                os.path.normcase(os.path.abspath(os.path.join(self.install_dir, "splatoon_editor_config.json")))
            ]

            for root_dir, dirs, files in os.walk(self.install_dir, topdown=False):
                rel_root = os.path.relpath(root_dir, self.install_dir)
                if rel_root == "." or rel_root.startswith("Splatoon3-WeaponsEditor"):
                    
                    is_dir_protected = False
                    for p in protected_paths:
                        if os.path.normcase(os.path.abspath(root_dir)).startswith(p):
                            is_dir_protected = True
                            break
                    if is_dir_protected:
                        continue

                    for f in files:
                        file_path = os.path.abspath(os.path.join(root_dir, f))
                        file_norm = os.path.normcase(file_path)
                        
                        is_file_protected = False
                        for p in protected_paths:
                            if file_norm == p or file_norm.startswith(p):
                                is_file_protected = True
                                break
                        if is_file_protected:
                            continue
                            
                        if rel_root == ".":
                            if f.lower() not in ["start.bat", "updater.py"]:
                                continue
                        
                        if file_norm not in extracted_files:
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                    try:
                        if not os.listdir(root_dir) and rel_root != ".":
                            os.rmdir(root_dir)
                    except Exception:
                        pass

            self.progress.emit("Installing new files...")
            for root, _, files in os.walk(base_target):
                for f in files:
                    src_file = os.path.join(root, f)
                    rel_path = os.path.relpath(src_file, base_target)
                    dst_file = os.path.abspath(os.path.join(self.install_dir, rel_path))
                    dst_norm = os.path.normcase(dst_file)
                    
                    is_protected = False
                    for p in protected_paths:
                        if dst_norm == p or dst_norm.startswith(p):
                            if os.path.exists(dst_file):
                                is_protected = True
                            break
                            
                    if is_protected:
                        continue
                        
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)

            self.completed.emit(True, "Update installed successfully.")
        except Exception as e:
            self.completed.emit(False, str(e))
        finally:
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            if os.path.exists(temp_archive_path):
                try:
                    os.remove(temp_archive_path)
                except Exception:
                    pass

class UpdaterWindow(QMainWindow):
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.is_dev_version = False
        self.first_stable_idx = -1
        
        self.install_dir = os.getcwd()
        if "--install-dir" in sys.argv:
            try:
                idx = sys.argv.index("--install-dir")
                self.install_dir = sys.argv[idx + 1]
            except IndexError:
                pass
                
        self.setWindowTitle("Splatoon 3 Weapons Editor (Updater)")
        
        self.last_is_dark = darkdetect.isDark()
        self.setWindowIcon(get_app_icon())
        
        self.releases_data = []
        self.cached_releases = []
        
        self.force_reinstall_mode = "--reinstall" in sys.argv
        self.force_prerelease_mode = "--prerelease" in sys.argv
        self.force_view_all_mode = "--view-all" in sys.argv

        self.app_cfg = load_editor_config()
        self.theme_name = self.app_cfg["theme"].lower()
        if self.theme_name not in THEMES:
            self.theme_name = "dark" if self.last_is_dark else "light"
            
        self.accent_color = self.app_cfg.get("accent_color", "#E6FF00")
        self.rainbow_mode = self.app_cfg.get("rainbow_mode", False)
        self.rainbow_speed = self.app_cfg.get("rainbow_speed", 2)
        self.current_hue = 0.0
        
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update_spinner_ui)
        
        self.init_ui()
        self.apply_style()
        
        if self.rainbow_mode:
            self.rainbow_timer = QTimer(self)
            self.rainbow_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.rainbow_timer.timeout.connect(self.update_rainbow_tick)
            self.rainbow_timer.start(33)
            
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.check_system_theme)
        self.theme_timer.start(2000)
        
        self.fetch_all_releases()

    def relaunch_app(self):
        start_bat = os.path.join(self.install_dir, "Start.bat")
        main_script_1 = os.path.join(self.install_dir, "main.py")
        main_script_2 = os.path.join(self.install_dir, "Splatoon3-WeaponsEditor", "main.py")
        
        try:
            if os.path.exists(start_bat):
                kwargs = {'cwd': self.install_dir}
                if os.name == 'nt':
                    kwargs['creationflags'] = 0x00000010
                subprocess.Popen([start_bat], **kwargs)
            elif os.path.exists(main_script_1):
                kwargs = {'cwd': self.install_dir}
                if os.name == 'nt':
                    kwargs['creationflags'] = 0x00000008 | 0x00000200
                else:
                    kwargs['stdin'] = subprocess.DEVNULL
                    kwargs['stdout'] = subprocess.DEVNULL
                    kwargs['stderr'] = subprocess.DEVNULL
                subprocess.Popen([sys.executable, main_script_1], **kwargs)
            elif os.path.exists(main_script_2):
                kwargs = {'cwd': os.path.join(self.install_dir, "Splatoon3-WeaponsEditor")}
                if os.name == 'nt':
                    kwargs['creationflags'] = 0x00000008 | 0x00000200
                else:
                    kwargs['stdin'] = subprocess.DEVNULL
                    kwargs['stdout'] = subprocess.DEVNULL
                    kwargs['stderr'] = subprocess.DEVNULL
                subprocess.Popen([sys.executable, main_script_2], **kwargs)
        except Exception:
            pass
        sys.exit(0)

    def check_system_theme(self):
        current_dark = darkdetect.isDark()
        if current_dark != self.last_is_dark:
            self.last_is_dark = current_dark
            new_icon = get_app_icon()
            self.setWindowIcon(new_icon)
            QApplication.instance().setWindowIcon(new_icon)
            
            if self.app_cfg["theme"].lower() not in THEMES:
                self.theme_name = "dark" if current_dark else "light"
                self.apply_style()

    def _convert_markdown_to_html(self, text):
        if not text:
            return ""
        text_normalized = text.replace("\r\n", "\n")
        return re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text_normalized)

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        card_frame = QFrame(self)
        card_frame.setObjectName("Card")
        card_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(12)
        
        title_lbl = QLabel("Splatoon 3 Weapons Editor (Updater)", card_frame)
        title_lbl.setObjectName("CardTitle")
        card_layout.addWidget(title_lbl)
        
        self.version_lbl = QLabel(f"Current version installed: {self.current_version}", card_frame)
        self.version_lbl.setObjectName("CardVersion")
        card_layout.addWidget(self.version_lbl)
        
        self.beta_checkbox = QCheckBox("Include main branch [not recommended]", card_frame)
        self.beta_checkbox.stateChanged.connect(self.toggle_beta_mode)
        card_layout.addWidget(self.beta_checkbox)
        
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_lbl = QLabel("Checking available Editor versions...", card_frame)
        status_layout.addWidget(self.status_lbl)
        
        self.status_icon_lbl = QLabel("", card_frame)
        self.status_icon_lbl.setFixedWidth(20)
        status_layout.addWidget(self.status_icon_lbl)
        
        status_layout.addStretch()
        
        card_layout.addLayout(status_layout)
        
        combo_layout = QHBoxLayout()
        combo_layout.setContentsMargins(0, 0, 0, 0)
        
        self.version_combo = QComboBox(card_frame)
        self.version_combo.setEnabled(False)
        self.version_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo_layout.addWidget(self.version_combo)
        
        self.btn_refresh = QPushButton("🔄", card_frame)
        self.btn_refresh.clicked.connect(self.refresh_data)
        combo_layout.addWidget(self.btn_refresh)
        
        card_layout.addLayout(combo_layout)
        
        self.browser = QTextEdit(card_frame)
        self.browser.setReadOnly(True)
        self.browser.setMinimumHeight(150)
        self.browser.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        card_layout.addWidget(self.browser)
        
        self.version_combo.currentIndexChanged.connect(self.on_version_changed_index)
        
        main_layout.addWidget(card_frame)
        
        btn_layout = QHBoxLayout()
        
        btn_text = "Install"
        if self.force_reinstall_mode:
            btn_text = "Reinstall Current Version"
        elif self.force_prerelease_mode:
            btn_text = "Install Beta Build"
        
        self.btn_execute = QPushButton(btn_text, self)
        self.btn_execute.setObjectName("btnExecute")
        self.btn_execute.setEnabled(False)
        self.btn_execute.clicked.connect(self.start_installation)
        
        self.lbl_warning_symbol = QLabel("", self)
        self.lbl_warning_symbol.setMinimumWidth(15)
        self.lbl_warning_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.lbl_warning_symbol)
        self.lbl_warning_symbol.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setKeyValueAt(0.5, 0.3)
        self.pulse_anim.setEndValue(1.0)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.setDuration(2000)
        
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.handle_cancel)
        
        btn_layout.addWidget(self.btn_execute)
        btn_layout.addWidget(self.lbl_warning_symbol)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_cancel)
        
        main_layout.addLayout(btn_layout)
        
        self.setFixedWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        QTimer.singleShot(10, self.adjustSize)

    def apply_style(self):
        self.setStyleSheet(get_stylesheet(self.theme_name, self.accent_color))
        self.update_scrollbar_stylesheet()

    def update_rainbow_tick(self):
        increment = self.rainbow_speed * 0.8
        self.current_hue = (self.current_hue + increment) % 360.0
        is_dark = self.theme_name in ["dark", "oled"]
        sat_f = 200.0 / 255.0 if is_dark else 240.0 / 255.0
        val_f = 255.0 / 255.0 if is_dark else 180.0 / 255.0
        r, g, b = colorsys.hsv_to_rgb(self.current_hue / 360.0, sat_f, val_f)
        self.accent_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        self.apply_style()

    def update_spinner_ui(self):
        self.status_icon_lbl.setText(self.spinner_chars[self.spinner_idx])
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)

    def update_scrollbar_stylesheet(self):
        tmp_dir = QDir.tempPath() + "/SplatoonEditor_SVGs"
        QDir().mkpath(tmp_dir)
        
        def create_svg_file(name, color, is_up):
            path = tmp_dir + "/" + name
            pts = "18 15 12 9 6 15" if is_up else "6 9 12 15 18 9"
            content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="{pts}"/></svg>"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path

        up_idle = create_svg_file("up_idle.svg", "#8A8A95", True)
        up_hover = create_svg_file("up_hover.svg", "#FFFFFF", True)
        down_idle = create_svg_file("down_idle.svg", "#8A8A95", False)
        down_hover = create_svg_file("down_hover.svg", "#FFFFFF", False)

        self.browser.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1E1E24;
                color: #E8E8E8;
                border: 1px solid #4A4A55;
                border-radius: 8px;
                padding: 8px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #2D2D36;
                width: 20px;
                margin: 0px 0 0px 0;
                padding-top: 20px;
                padding-bottom: 20px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.accent_color};
                width: 20px;
                min-height: 40px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical {{
                border: none;
                background: #3A3A45;
                width: 20px;
                height: 20px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                border-radius: 6px;
            }}
            QScrollBar::sub-line:vertical {{
                border: none;
                background: #3A3A45;
                width: 20px;
                height: 20px;
                subcontrol-position: top;
                subcontrol-origin: margin;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover,
            QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed {{
                background: {self.accent_color};
            }}
            QScrollBar::up-arrow:vertical {{
                image: url("{up_idle}");
                width: 14px;
                height: 14px;
            }}
            QScrollBar::down-arrow:vertical {{
                image: url("{down_idle}");
                width: 14px;
                height: 14px;
            }}
            QScrollBar::up-arrow:vertical:hover, QScrollBar::up-arrow:vertical:pressed {{
                image: url("{up_hover}");
            }}
            QScrollBar::down-arrow:vertical:hover, QScrollBar::down-arrow:vertical:pressed {{
                image: url("{down_hover}");
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
                border: none;
            }}
        """)

    def set_warning(self, warn_state):
        if warn_state:
            self.lbl_warning_symbol.setText("⚠️")
            if self.pulse_anim.state() != QAbstractAnimation.State.Running:
                self.pulse_anim.start()
        else:
            self.pulse_anim.stop()
            self.opacity_effect.setOpacity(1.0)
            self.lbl_warning_symbol.setText("")
        QTimer.singleShot(10, self.adjustSize)

    def refresh_data(self):
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setEnabled(False)
        self.status_icon_lbl.setText("")
        self.status_lbl.setText("Refreshing data from GitHub...")
        self.version_combo.clear()
        self.version_combo.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.fetch_all_releases()

    def toggle_beta_mode(self, state):
        self.version_combo.clear()
        self.set_warning(False)
        self.browser.clear()
        
        for text, data in self.cached_releases:
            self.version_combo.addItem(text, data)
            
        if state == 2:
            self.btn_execute.setEnabled(False)
            QTimer.singleShot(100, self.fetch_beta_source)
        else:
            self.btn_execute.setEnabled(self.version_combo.count() > 0)
            self.check_version_warnings(self.version_combo.currentIndex())
        self.adjustSize()

    def merge_dicts(self, dict1, dict2):
        return {**dict1, **dict2}

    def fetch_all_releases(self):
        self.fetch_thread = ReleasesFetchThread()
        self.fetch_thread.finished.connect(self.process_releases)
        self.fetch_thread.start()

    def process_releases(self, data, error_str):
        if error_str:
            self.status_icon_lbl.setText("❌")
            self.status_lbl.setText(f"API Connection Error: {error_str}")
            if hasattr(self, 'btn_refresh'):
                self.btn_refresh.setEnabled(True)
            return
            
        self.releases_data = data
        self.cached_releases = []
        self.version_combo.clear()
        self.browser.clear()
        self.status_icon_lbl.setText("")
        
        first_stable_idx = -1
        prerelease_idx = -1
        latest_stable_tag = ""
        
        for idx, release in enumerate(data):
            tag = release.get("tag_name", "").strip().lstrip('v')
            if tag:
                if release.get("prerelease", False):
                    display_name = f"{tag} [!Pre-release!]"
                    if prerelease_idx == -1:
                        prerelease_idx = idx
                else:
                    display_name = tag
                    if first_stable_idx == -1:
                        first_stable_idx = idx
                        latest_stable_tag = tag
                        
                self.cached_releases.append((display_name, release))
                self.version_combo.addItem(display_name, release)

        self.first_stable_idx = first_stable_idx
        self.is_dev_version = False
        
        if latest_stable_tag:
            try:
                import packaging.version
                v_curr = packaging.version.parse(self.current_version.lstrip('v'))
                v_stab = packaging.version.parse(latest_stable_tag)
                if v_curr > v_stab:
                    self.is_dev_version = True
            except Exception:
                pass
                
        if self.version_combo.count() > 0:
            self.status_lbl.setText("Select a release:")
            self.version_combo.setEnabled(True)
            self.btn_execute.setEnabled(True)
            
            if self.is_dev_version and not self.force_reinstall_mode and not self.force_prerelease_mode and not self.force_view_all_mode:
                self.version_lbl.setText(f"Current version installed: {self.current_version} ⚠️ [DEV]")
                self.version_lbl.setStyleSheet("color: #e67e22; font-weight: bold;")
                
                if first_stable_idx != -1:
                    self.version_combo.setCurrentIndex(first_stable_idx)
                else:
                    self.version_combo.setCurrentIndex(0)
            else:
                if self.force_reinstall_mode:
                    self.status_lbl.setText("Automatic reinstallation triggered...")
                    QTimer.singleShot(300, self.start_installation)
                elif self.force_prerelease_mode and prerelease_idx != -1:
                    self.version_combo.setCurrentIndex(prerelease_idx)
                    self.status_lbl.setText("Automatic reinstallation (beta) triggered...")
                    QTimer.singleShot(300, self.start_installation)
                elif self.force_view_all_mode:
                    self.version_combo.setCurrentIndex(0)
                else:
                    if data[0].get("prerelease", False) and first_stable_idx != -1:
                        self.version_combo.setCurrentIndex(first_stable_idx)
                    else:
                        self.version_combo.setCurrentIndex(0)
            
            self.check_version_warnings(self.version_combo.currentIndex())
                        
            if self.beta_checkbox.isChecked():
                self.toggle_beta_mode(2)
        else:
            self.status_lbl.setText("No public release distributions found?")
            
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setEnabled(True)
        self.adjustSize()

    def fetch_beta_source(self):
        url = f"https://raw.githubusercontent.com/JeremKOYTB/Splatoon3-WeaponsEditor/refs/heads/main/Splatoon3-WeaponsEditor/main.py?t={int(time.time())}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Splatoon3Editor-Updater'})
                
            with urllib.request.urlopen(req, timeout=5) as response:
                code = response.read().decode('utf-8', errors='ignore')
            
            match = re.search(r'self\.APP_VERSION\s*=\s*["\']([^"\']+)["\']', code)
            beta_version = match.group(1) if match else "Unknown"
            display_version = beta_version if beta_version.startswith("v") else f"v{beta_version}"
            
            target_zip = "https://api.github.com/repos/JeremKOYTB/Splatoon3-WeaponsEditor/zipball/main"
            
            dummy_release = {
                "tag_name": f"main branch ({display_version})", 
                "zipball_url": target_zip, 
                "assets": [],
                "is_main_branch_node": True
            }
            
            self.version_combo.insertItem(0, f"main branch ({display_version})", dummy_release)
            self.version_combo.setCurrentIndex(0)
            self.check_version_warnings(self.version_combo.currentIndex())
            self.btn_execute.setEnabled(True)
        except Exception as e:
            self.browser.setHtml(f"<div style='color: #EF5350;'>Failed to fetch main branch metadata: {e}</div>")
            self.set_warning(False)
            self.btn_execute.setEnabled(False)
            
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setEnabled(True)
        self.adjustSize()

    def on_version_changed_index(self, index):
        if index < 0:
            return
        current_data = self.version_combo.currentData()
        self.browser.clear()
        
        self.check_version_warnings(index)
        
        if isinstance(current_data, dict) and current_data.get("is_main_branch_node", False):
            self.browser.setHtml("<div style='color: #8A8A95; font-style: italic;'>Fetching latest commit data from GitHub...</div>")
            self.commit_thread = MainBranchCommitFetchThread()
            self.commit_thread.finished.connect(self.on_main_branch_commit_loaded)
            self.commit_thread.start()
        else:
            changelog_text = current_data.get("body", "No changelog provided.") if isinstance(current_data, dict) else ""
            self.browser.setMarkdown(self._convert_markdown_to_html(changelog_text))

    def on_main_branch_commit_loaded(self, commit_text):
        self.browser.setHtml(commit_text)

    def check_version_warnings(self, index):
        if index < 0: return
        current_text = self.version_combo.currentText()
        current_data = self.version_combo.currentData()
        
        is_dangerous = False
        is_stable = False
        
        if "main branch" in current_text:
            is_dangerous = True
        elif isinstance(current_data, dict):
            if current_data.get("prerelease", False):
                is_dangerous = True
            elif not current_data.get("is_main_branch_node", False):
                is_stable = True
                
        self.set_warning(is_dangerous)
        
        if not self.force_reinstall_mode and not self.force_prerelease_mode:
            if is_dangerous:
                self.btn_execute.setText("Install (Not recommended)")
            elif self.is_dev_version and is_stable:
                self.btn_execute.setText("Revert to Stable")
            else:
                self.btn_execute.setText("Install")

    def start_installation(self, *args):
        current_data = self.version_combo.currentData()
        if not current_data: return
        
        current_text = self.version_combo.currentText()
        base_version = current_text.split(" ")[0]
        
        download_url = None
        is_main_branch = current_data.get("is_main_branch_node", False)
        
        if is_main_branch:
            download_url = current_data.get("zipball_url")
        else:
            assets = current_data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".zip") or name.endswith(".7z"):
                    download_url = asset.get("browser_download_url")
                    break
                    
        if not download_url:
            self.status_icon_lbl.setText("❌")
            self.status_lbl.setText("Select a release:")
            err_box = QMessageBox(self)
            err_box.setWindowIcon(get_app_icon())
            err_box.setIcon(QMessageBox.Icon.Critical)
            err_box.setWindowTitle("Asset Missing")
            err_box.setText("Security: No valid compiled asset (.zip or .7z) was found in this release. Source code download is explicitly forbidden for official releases.")
            err_box.exec()
            return
            
        self.version_combo.setEnabled(False)
        self.btn_execute.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.beta_checkbox.setEnabled(False)
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setEnabled(False)
            
        self.spinner_timer.start(100)
        
        self.worker = DownloadWorkerThread(download_url, self.install_dir, base_version)
        self.worker.progress.connect(self.status_lbl.setText)
        self.worker.completed.connect(self.installation_finished)
        self.worker.start()

    def installation_finished(self, success, message):
        self.spinner_timer.stop()
        if success:
            self.status_icon_lbl.setText("✅")
            self.status_lbl.setText("Complete.")
            success_box = QMessageBox(self)
            success_box.setWindowIcon(get_app_icon())
            success_box.setIcon(QMessageBox.Icon.Information)
            success_box.setWindowTitle("Success:")
            success_box.setText("Splatoon 3 Editor has been updated successfully.\n\nPress OK to reload the Editor.")
            success_box.exec()
            self.relaunch_app()
        else:
            self.status_icon_lbl.setText("❌")
            self.status_lbl.setText("Select a release:")
            fail_box = QMessageBox(self)
            fail_box.setWindowIcon(get_app_icon())
            fail_box.setIcon(QMessageBox.Icon.Critical)
            fail_box.setWindowTitle("Installation Failed...")
            fail_box.setText(f"Critical execution error:\n{message}")
            fail_box.exec()
            
            self.version_combo.setEnabled(True)
            self.btn_execute.setEnabled(True)
            self.btn_cancel.setEnabled(True)
            self.beta_checkbox.setEnabled(True)
            if hasattr(self, 'btn_refresh'):
                self.btn_refresh.setEnabled(True)

    def handle_cancel(self, *args):
        box = QMessageBox(self)
        box.setWindowIcon(get_app_icon())
        box.setWindowTitle("Cancel Update")
        box.setText(f"Do you want to return to Splatoon 3 Editor ({self.current_version}) or exit completely?")
        box.setIcon(QMessageBox.Icon.Question)
        
        btn_return = box.addButton("Return to Editor", QMessageBox.ButtonRole.YesRole)
        btn_exit = box.addButton("Exit", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Stay here", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(btn_return)
        box.exec()
        
        if box.clickedButton() == btn_return:
            self.relaunch_app()
        elif box.clickedButton() == btn_exit:
            sys.exit(0)
        else:
            self.status_icon_lbl.setText("❌")
            self.status_lbl.setText("Select a release:")

class MainBranchCommitFetchThread(QThread):
    finished = pyqtSignal(str)

    def run(self):
        url = f"https://api.github.com/repos/JeremKOYTB/Splatoon3-WeaponsEditor/commits/main?t={int(time.time())}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Splatoon3Editor-Updater'})
                
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            sha = data.get("sha", "")[:7]
            commit_info = data.get("commit", {})
            message = commit_info.get("message", "No description provided.")
            author_info = commit_info.get("author", {})
            date_str = author_info.get("date", "").replace("T", " ").replace("Z", "")
            
            html_output = (
                f"<div style='margin-bottom: 4px;'><b style='color: #C4A1FF;'>Latest Main Commit:</b> <code style='background-color: #2D2D36; padding: 2px 4px; border-radius: 4px; color: #FFFFFF;'>{sha}</code></div>"
                f"<div style='margin-bottom: 4px;'><b style='color: #8A8A95;'>Date:</b> <span style='color: #E8E8E8;'>{date_str}</span></div>"
                f"<hr style='border: none; border-top: 1px solid #4A4A55; margin: 6px 0;'>"
                f"<div><b style='color: #FFFFFF;'>Modification Notes:</b></div>"
                f"<div style='color: #E8E8E8; white-space: pre-wrap; margin-top: 4px;'>{message}</div>"
            )
            self.finished.emit(html_output)
        except Exception as e:
            self.finished.emit(f"<div style='color: #EF5350;'>Failed to reach main branch commit API endpoint: {e}</div>")

def handle_interrupt(window_instance):
    box = QMessageBox(window_instance)
    box.setWindowIcon(window_instance.get_app_icon())
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle("Exit?")
    box.setText("Ctrl+C was detected in the terminal.\n\nDo you want to close the updater?")
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    if box.exec() == QMessageBox.StandardButton.Yes:
        QApplication.quit()
        sys.exit(0)

if __name__ == "__main__":
    if os.name == 'nt':
        import ctypes
        myappid = 'jeremkoytb.splatoon3weaponseditor.updater'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    current_script = os.path.abspath(__file__)
    appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "Splatoon3Editor")
    temp_updater = os.path.join(appdata_dir, "TempUpdater.py")

    if os.path.normcase(current_script) != os.path.normcase(temp_updater):
        relocated_successfully = False
        try:
            os.makedirs(appdata_dir, exist_ok=True)
            shutil.copy2(current_script, temp_updater)
            
            for _ in range(10):
                if os.path.exists(temp_updater) and os.path.getsize(temp_updater) > 0:
                    break
                time.sleep(0.05)
                
            args = [sys.executable, temp_updater]
            passed_args = sys.argv[1:]
            if "--install-dir" not in passed_args:
                args.extend(["--install-dir", os.path.dirname(current_script)])
            args.extend(passed_args)
            
            log_file_path = os.path.join(appdata_dir, "updater_debug.log")
            debug_log = open(log_file_path, "w", encoding="utf-8")
            kwargs = {
                "stdin": subprocess.DEVNULL,
                "stdout": debug_log,
                "stderr": subprocess.STDOUT
            }
            if os.name == 'nt':
                kwargs['creationflags'] = 0x00000008 | 0x00000200
                
            proc = subprocess.Popen(args, **kwargs)
            time.sleep(0.4)
            if proc.poll() is None:
                relocated_successfully = True
        except Exception:
            pass 
            
        if relocated_successfully:
            sys.exit(0)

    app = QApplication(sys.argv)
    window = UpdaterWindow(APP_VERSION)
    window.show()
    
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    signal.signal(signal.SIGINT, lambda sig, frame: handle_interrupt(window))
    
    sys.exit(app.exec())