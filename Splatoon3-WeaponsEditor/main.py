import sys
import os
import signal
import subprocess
import webbrowser

from utils import install_requirements
install_requirements()

from utils import (log, CACHE_DIR, get_last_dir, set_last_dir, get_favorites, save_favorites, 
                   get_saved_language, save_language, get_hide_dummy, save_hide_dummy, 
                   get_hide_filenames, save_hide_filenames, get_hide_warning, save_hide_warning)

import darkdetect

from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem, 
                             QMenu, QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QWidgetAction, QWidget, QSizePolicy, QMenuBar, QCheckBox)
from PyQt6.QtGui import QPixmap, QColor, QBrush, QIcon, QImage, QPainter, QAction
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QByteArray, QSize, QEvent

import translations
from translations import t, TEXTS
import ui_builder
from tree_handler import TreeHandler
from engine import SplatoonPackManager
from components import (DiffDialog, CacheDialog, CacheBuilderWorker, ImageManager, 
                        UpdateCheckWorker, UpdatePromptDialog)
from splatoon_data import SplatoonDataManager, compare_dicts, parse_node
from romfs_builder import RomFSBuilderWorker
from editor_features import EditorFeaturesMixin

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

SVG_X_DARK = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#E8E8E8" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>"""
SVG_X_LIGHT = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#1D1D1F" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>"""

SVG_GITHUB_DARK = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#E8E8E8" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.008.069-.008 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>"""
SVG_GITHUB_LIGHT = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#1D1D1F" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.008.069-.008 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>"""

SVG_DISCORD_DARK = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#E8E8E8" d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.094 13.094 0 01-1.873-.894.077.077 0 01-.008-.128c.126-.093.252-.19.372-.287a.075.075 0 01.077-.011c3.92 1.793 8.18 1.793 12.061 0a.073.073 0 01.078.009c.12.099.246.195.373.289a.075.075 0 01-.006.127 12.298 12.298 0 01-1.873.894.077.077 0 01-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03a.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.156 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.156 2.418z"/></svg>"""
SVG_DISCORD_LIGHT = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="#1D1D1F" d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.094 13.094 0 01-1.873-.894.077.077 0 01-.008-.128c.126-.093.252-.19.372-.287a.075.075 0 01.077-.011c3.92 1.793 8.18 1.793 12.061 0a.073.073 0 01.078.009c.12.099.246.195.373.289a.075.075 0 01-.006.127 12.298 12.298 0 01-1.873.894.077.077 0 01-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03a.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.156 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.156 2.418z"/></svg>"""

def get_app_icon():
    svg_data = S3WE_MAIN_LOGO
    if darkdetect.isDark():
        svg_data = svg_data.replace(b'fill="#000000"', b'fill="#FFFFFF"')
    pix = QPixmap()
    pix.loadFromData(QByteArray(svg_data))
    return QIcon(pix)

def get_stylesheet(is_dark):
    if is_dark:
        return """
        QWidget { font-family: "Segoe UI Variable", "Segoe UI", "Roboto", sans-serif; font-size: 10pt; }
        QFrame#Card { background-color: rgba(0, 0, 0, 40); border-radius: 8px; border: 1px solid rgba(0, 0, 0, 100); }
        QPushButton { border-radius: 6px; padding: 6px 14px; border: 1px solid rgba(0, 0, 0, 100); background-color: rgba(255, 255, 255, 20); outline: none; }
        QPushButton:focus { outline: none; }
        QPushButton:hover { background-color: rgba(255, 255, 255, 40); }
        QPushButton:pressed { background-color: rgba(0, 0, 0, 40); }
        QComboBox, QLineEdit { border-radius: 6px; padding: 5px; border: 1px solid rgba(0, 0, 0, 100); background-color: rgba(0, 0, 0, 40); color: white; }
        QComboBox::drop-down { border: none; }
        QTableWidget, QTreeWidget { border: none; background-color: transparent; outline: none; }
        QTableWidget::item { padding: 4px; background-color: transparent; border: none; }
        QTableWidget::item:selected, QTableWidget::item:selected:!active { background-color: #0078D7; color: white; border: none; outline: none; }
        QTableWidget::item:hover { background-color: rgba(255, 255, 255, 20); }
        QTreeWidget:focus { outline: none; }
        QMenu { background-color: #2c3e50; color: white; border: 1px solid #34495e; }
        QMenu::item:selected { background-color: #3498db; }
        #btnSocial { background-color: transparent; border: none; padding: 2px; border-radius: 4px; }
        #btnSocial:hover { background-color: rgba(255, 255, 255, 40); }
        QMenuBar { border-bottom: 1px solid rgba(0, 0, 0, 100); background-color: transparent; }
        QMenuBar::item { padding: 6px 12px; background-color: transparent; border: none; outline: none; }
        QMenuBar::item:selected { background-color: rgba(255, 255, 255, 20); border-radius: 4px; }
        QHeaderView::section { background-color: rgba(0, 0, 0, 40); color: white; padding: 4px; border: none; border-bottom: 1px solid rgba(0, 0, 0, 100); border-right: 1px solid rgba(0, 0, 0, 100); }
        #CountLabel { color: #cccccc; font-weight: bold; }
        #ProgressLabel { font-size: 11px; color: #aaaaaa; font-weight: bold; }
        """
    else:
        return """
        QWidget { font-family: "Segoe UI Variable", "Segoe UI", "Roboto", sans-serif; font-size: 10pt; color: #1D1D1F; }
        QFrame#Card { background-color: rgba(255, 255, 255, 180); border-radius: 8px; border: 1px solid rgba(0, 0, 0, 30); }
        QPushButton { border-radius: 6px; padding: 6px 14px; border: 1px solid rgba(0, 0, 0, 40); background-color: rgba(255, 255, 255, 255); outline: none; color: #1D1D1F; }
        QPushButton:focus { outline: none; }
        QPushButton:hover { background-color: rgba(0, 0, 0, 10); }
        QPushButton:pressed { background-color: rgba(0, 0, 0, 20); }
        QComboBox, QLineEdit { border-radius: 6px; padding: 5px; border: 1px solid rgba(0, 0, 0, 40); background-color: rgba(255, 255, 255, 255); color: #1D1D1F; }
        QComboBox::drop-down { border: none; }
        QTableWidget, QTreeWidget { border: none; background-color: transparent; outline: none; color: #1D1D1F; }
        QTableWidget::item { padding: 4px; background-color: transparent; border: none; }
        QTableWidget::item:selected, QTableWidget::item:selected:!active { background-color: #0078D7; color: white; border: none; outline: none; }
        QTableWidget::item:hover { background-color: rgba(0, 0, 0, 10); }
        QTreeWidget:focus { outline: none; }
        QMenu { background-color: #ffffff; color: #1D1D1F; border: 1px solid #cccccc; }
        QMenu::item:selected { background-color: #0078D7; color: white; }
        #btnSocial { background-color: transparent; border: none; padding: 2px; border-radius: 4px; }
        #btnSocial:hover { background-color: rgba(0, 0, 0, 10); }
        QMenuBar { border-bottom: 1px solid rgba(0, 0, 0, 40); background-color: transparent; }
        QMenuBar::item { padding: 6px 12px; background-color: transparent; border: none; outline: none; color: #1D1D1F; }
        QMenuBar::item:selected { background-color: rgba(0, 0, 0, 10); border-radius: 4px; }
        QHeaderView::section { background-color: rgba(240, 240, 245, 255); color: #1D1D1F; padding: 4px; border: none; border-bottom: 1px solid rgba(0, 0, 0, 40); border-right: 1px solid rgba(0, 0, 0, 40); }
        #CountLabel { color: #555555; font-weight: bold; }
        #ProgressLabel { font-size: 11px; color: #666666; font-weight: bold; }
        """

class AboutDialog(QDialog):
    def __init__(self, parent, is_dark, version):
        super().__init__(parent)
        self.setWindowTitle(t("menu_about"))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.is_dark = is_dark
        self.version = version
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        
        logo_lbl = QLabel(self)
        px_logo = QPixmap()
        px_logo.loadFromData(QByteArray(S3WE_MAIN_LOGO))
        if self.is_dark:
            px_logo = QPixmap()
            svg_data = S3WE_MAIN_LOGO.replace(b'fill="#000000"', b'fill="#FFFFFF"')
            px_logo.loadFromData(QByteArray(svg_data))
            
        logo_lbl.setPixmap(px_logo.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        top_layout.addStretch(1)
        
        social_layout = QHBoxLayout()
        social_layout.setSpacing(8)

        btn_x = QPushButton(self)
        btn_x.setObjectName("btnSocial")
        px_x = QPixmap()
        px_x.loadFromData(QByteArray(SVG_X_DARK if self.is_dark else SVG_X_LIGHT))
        btn_x.setIcon(QIcon(px_x))
        btn_x.setIconSize(QSize(24, 24))
        btn_x.clicked.connect(lambda: webbrowser.open("https://x.com/JeremKOYTB"))

        btn_git = QPushButton(self)
        btn_git.setObjectName("btnSocial")
        px_git = QPixmap()
        px_git.loadFromData(QByteArray(SVG_GITHUB_DARK if self.is_dark else SVG_GITHUB_LIGHT))
        btn_git.setIcon(QIcon(px_git))
        btn_git.setIconSize(QSize(24, 24))
        btn_git.clicked.connect(lambda: webbrowser.open("https://github.com/JeremKOYTB/Splatoon3-WeaponsEditor/"))

        btn_disc = QPushButton(self)
        btn_disc.setObjectName("btnSocial")
        px_disc = QPixmap()
        px_disc.loadFromData(QByteArray(SVG_DISCORD_DARK if self.is_dark else SVG_DISCORD_LIGHT))
        btn_disc.setIcon(QIcon(px_disc))
        btn_disc.setIconSize(QSize(24, 24))
        btn_disc.clicked.connect(self.copy_discord)

        social_layout.addWidget(btn_x)
        social_layout.addWidget(btn_git)
        social_layout.addWidget(btn_disc)
        
        top_layout.addLayout(social_layout)
        layout.addLayout(top_layout)

        info_lbl = QLabel(self)
        info_lbl.setWordWrap(True)
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_lbl.setText(t("about_desc", self.version))
        layout.addWidget(info_lbl)

        close_btn = QPushButton(t("diff_btn_close"), self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.setFixedSize(380, 260)

    def copy_discord(self):
        QApplication.clipboard().setText("jeremko")
        QMessageBox.information(self, t("msg_copied"), t("msg_discord_copied"))


class SplatoonParamEditor(QMainWindow, EditorFeaturesMixin):
    def __init__(self):
        super().__init__()
        self.APP_VERSION = "1.0.3"
        self.resize(1300, 800)

        self.last_is_dark = darkdetect.isDark()
        self.setWindowIcon(get_app_icon())

        self.pack_manager = SplatoonPackManager()
        self.data_manager = SplatoonDataManager()
        
        self.current_byml_name = None
        self.favorites = get_favorites()
        self.is_refreshing = False
        self.has_actual_dummies = False
        
        self.known_dummies = set(["Dummy.png"])
        self._thread_pool = []
        
        self.languages = {
            "English (US)": "USen",
            "Français (EU)": "EUfr",
            "English (EU)": "EUen",
            "Español (EU)": "EUes",
            "Deutsch (EU)": "EUde",
            "Italiano (EU)": "EUit",
            "Nederlands (EU)": "EUnl",
            "日本語 (JA)": "JPja"
        }
        
        ui_builder.setup_ui(self)
        self.setup_menus()
        
        self.btn_update.setIcon(QIcon())
        
        self.update_icon_overlay = QLabel(self.btn_update)
        self.update_icon_overlay.setFixedSize(24, 24)
        self.update_icon_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.update_icon_overlay.setStyleSheet("background: transparent;")
        
        self.btn_update.installEventFilter(self)

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.refresh_file_list)
        
        self.chk_hide_dummy.blockSignals(True)
        self.chk_hide_dummy.setChecked(get_hide_dummy())
        self.chk_hide_dummy.blockSignals(False)
        
        self.chk_hide_filenames.blockSignals(True)
        self.chk_hide_filenames.setChecked(get_hide_filenames())
        self.chk_hide_filenames.blockSignals(False)
        
        saved_lang = get_saved_language()
        if saved_lang in self.languages:
            self.lang_combo.setCurrentText(saved_lang)
            self.on_language_changed(saved_lang)
        else:
            self.lang_combo.setCurrentText("English (US)")
            self.on_language_changed("English (US)")

        self.update_dummy_filter_visibility()
        
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.check_system_theme)
        self.theme_timer.start(2000)

        QTimer.singleShot(100, self.show_startup_warning)
        QTimer.singleShot(1000, self.check_for_updates)

    def show_startup_warning(self):
        if not get_hide_warning():
            cb = QCheckBox(t("chk_dont_show_again"))
            msgbox = QMessageBox(self)
            msgbox.setWindowIcon(get_app_icon())
            msgbox.setIcon(QMessageBox.Icon.Warning)
            msgbox.setWindowTitle(t("warn_online_title"))
            msgbox.setText(t("warn_online_msg"))
            msgbox.setCheckBox(cb)
            msgbox.exec()
            if cb.isChecked():
                save_hide_warning(True)

    def setup_menus(self):
        self.top_bar = QWidget()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setStyleSheet("QWidget#TopBar { border-bottom: 1px solid rgba(0, 0, 0, 100); }")
        
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self._actual_menubar = QMenuBar()
        self._actual_menubar.setStyleSheet("QMenuBar { border-bottom: none; }") 
        self._actual_menubar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        file_menu = self._actual_menubar.addMenu(t("menu_file"))
        reset_action = QAction(t("menu_reset"), self)
        reset_action.triggered.connect(self.reset_config_and_restart)
        file_menu.addAction(reset_action)
        
        help_menu = self._actual_menubar.addMenu(t("menu_help"))
        about_action = QAction(t("menu_about"), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        top_layout.addWidget(self._actual_menubar)

        self.btn_rsdb = QPushButton(t("btn_rsdb")) 
        self.btn_rsdb.clicked.connect(self.show_rsdb_notice)
        self.btn_rsdb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rsdb.setFixedHeight(26) 
        
        self.btn_rsdb.setStyleSheet("""
            QPushButton { 
                background-color: #2980b9; 
                color: white; 
                font-weight: bold; 
                font-size: 10pt; 
                border-radius: 4px; 
                border: 1px solid #1c5980;
                padding: 0px 15px;
            }
            QPushButton:hover { background-color: #1c5980; }
        """)
        
        top_layout.addWidget(self.btn_rsdb, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        top_layout.addStretch()
        
        self.setMenuWidget(self.top_bar)

    def menuBar(self):
        if hasattr(self, '_actual_menubar'):
            return self._actual_menubar
        return super().menuBar()

    def show_about_dialog(self):
        dialog = AboutDialog(self, darkdetect.isDark(), self.APP_VERSION)
        dialog.exec()

    def show_rsdb_notice(self):
        QMessageBox.information(self, t("btn_rsdb"), t("msg_rsdb_soon"))

    def reset_config_and_restart(self):
        reply = QMessageBox.question(
            self, 
            t("menu_reset"), 
            t("msg_reset_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "splatoon_editor_config.json")
            
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                except Exception as e:
                    QMessageBox.critical(self, t("err_title"), f"{e}")
                    return
            
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit(0)

    def eventFilter(self, obj, event):
        if hasattr(self, 'btn_update') and obj == self.btn_update and event.type() == QEvent.Type.Resize:
            y = (self.btn_update.height() - 24) // 2
            self.update_icon_overlay.move(12, y)
        return super().eventFilter(obj, event)

    def get_text_icon(self, text):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        if text:
            painter = QPainter(pixmap)
            font = self.btn_update.font()
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()
        return pixmap

    def clear_update_icon(self):
        self.update_icon_overlay.clear()

    def check_system_theme(self):
        current_dark = darkdetect.isDark()
        if current_dark != self.last_is_dark:
            self.last_is_dark = current_dark
            new_icon = get_app_icon()
            self.setWindowIcon(new_icon)
            QApplication.instance().setWindowIcon(new_icon)
            
            QApplication.instance().setStyleSheet(get_stylesheet(current_dark))
            pal = QApplication.instance().palette()
            if current_dark:
                pal.setColor(QApplication.instance().palette().ColorRole.Window, Qt.GlobalColor.darkGray)
            else:
                pal.setColor(QApplication.instance().palette().ColorRole.Window, QColor("#F0F0F5"))
            QApplication.instance().setPalette(pal)

    def check_for_updates(self):
        self.update_spinner_idx = 0
        self.update_spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.update_spinner_timer = QTimer(self)
        self.update_spinner_timer.timeout.connect(self.tick_update_spinner)
        self.update_spinner_timer.start(100)
        
        self.update_worker = UpdateCheckWorker(self.APP_VERSION)
        self.update_worker.finished.connect(self.on_update_checked)
        self.update_worker.start()

    def tick_update_spinner(self):
        char = self.update_spinner_chars[self.update_spinner_idx]
        self.update_icon_overlay.setPixmap(self.get_text_icon(char))
        self.update_spinner_idx = (self.update_spinner_idx + 1) % len(self.update_spinner_chars)

    def on_update_checked(self, status, new_version, data_str):
        if hasattr(self, 'update_spinner_timer'):
            self.update_spinner_timer.stop()

        if status == 1:
            self.start_blinking_warning("‼️")
            
            dialog = UpdatePromptDialog(self.APP_VERSION, new_version, data_str, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.launch_updater()
                
        elif status == 0:
            self.update_icon_overlay.setPixmap(self.get_text_icon("✅"))
            QTimer.singleShot(5000, self.clear_update_icon)
            
        elif status == -1:
            self.update_icon_overlay.setPixmap(self.get_text_icon("❌"))
            QTimer.singleShot(5000, self.clear_update_icon)
            box = QMessageBox(self)
            box.setWindowIcon(get_app_icon())
            box.setWindowTitle(t("err_title"))
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(t("update_err_msg", data_str, self.APP_VERSION))
            box.exec()
            
        elif status == 2:
            self.start_blinking_warning("⚠️")
            
            box = QMessageBox(self)
            box.setWindowIcon(get_app_icon())
            box.setWindowTitle(t("dev_warn_title"))
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(t("dev_warn_msg", self.APP_VERSION, new_version))
            btn_revert = box.addButton(t("btn_revert_stable"), QMessageBox.ButtonRole.AcceptRole)
            btn_ignore = box.addButton(t("btn_ignore"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_revert)
            box.exec()
            
            if box.clickedButton() == btn_revert:
                self.launch_updater()

    def start_blinking_warning(self, symbol):
        self.blink_symbol = symbol
        self.blink_state = False
        
        if hasattr(self, 'blink_timer') and self.blink_timer.isActive():
            self.blink_timer.stop()
            
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.tick_blink)
        self.blink_timer.start(800)

    def tick_blink(self):
        if self.blink_state:
            self.update_icon_overlay.setPixmap(self.get_text_icon(self.blink_symbol))
        else:
            self.update_icon_overlay.clear()
        self.blink_state = not self.blink_state

    def launch_updater(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        updater_path = os.path.abspath(os.path.join(current_dir, "..", "updater.py"))
        
        if not os.path.exists(updater_path):
            QMessageBox.critical(self, t("err_title"), "updater.py missing.")
            return
            
        subprocess.Popen([sys.executable, updater_path, "--install-dir", os.path.abspath(os.path.join(current_dir, ".."))])
        sys.exit(0)

    def on_filter_changed(self, index):
        self.refresh_file_list()
        
    def on_search_changed(self, text):
        self.search_timer.start()

    def update_dummy_filter_visibility(self):
        is_checked = self.chk_hide_dummy.isChecked()
        self.combo_filter.blockSignals(True)
        
        for i in range(self.combo_filter.count()):
            if self.combo_filter.itemData(i) == "dummy":
                if self.combo_filter.currentIndex() == i:
                    self.combo_filter.setCurrentIndex(0) 
                self.combo_filter.removeItem(i)
                break
                
        if self.has_actual_dummies:
            self.chk_hide_dummy_container.setVisible(True)
            if not is_checked:
                self.combo_filter.addItem(t("filter_dummy"), "dummy")
        else:
            self.chk_hide_dummy_container.setVisible(False)
            
        self.combo_filter.blockSignals(False)

    def on_hide_dummy_toggled(self, state):
        is_checked = self.chk_hide_dummy.isChecked()
        save_hide_dummy(is_checked)
        self.update_dummy_filter_visibility()
        self.refresh_file_list()

    def on_hide_filenames_toggled(self, state):
        is_checked = self.chk_hide_filenames.isChecked()
        save_hide_filenames(is_checked)
        self.refresh_file_list()

    def on_auto_expand_toggled(self, state):
        if self.current_byml_name:
            byml_dict = self.pack_manager.byml_files[self.current_byml_name]
            TreeHandler.populate_tree(self.tree_w, parse_node(byml_dict), auto_expand=self.chk_auto_expand.isChecked())

    def on_language_changed(self, lang_name):
        if "Français" in lang_name:
            translations.CURRENT_LANG = "fr"
        else:
            translations.CURRENT_LANG = "en"
            
        lang_code = self.languages[lang_name]
        save_language(lang_name)
        self.data_manager.fetch_leanny_localization(lang_code)
        
        menubar = self.menuBar()
        if menubar:
            for action in menubar.actions():
                if action.menu():
                    if action.text() in [TEXTS["en"]["menu_file"], TEXTS["fr"]["menu_file"]]:
                        action.setText(t("menu_file"))
                        for sub in action.menu().actions():
                            if sub.text() in [TEXTS["en"]["menu_reset"], TEXTS["fr"]["menu_reset"]]:
                                sub.setText(t("menu_reset"))
                    elif action.text() in [TEXTS["en"]["menu_help"], TEXTS["fr"]["menu_help"]]:
                        action.setText(t("menu_help"))
                        for sub in action.menu().actions():
                            if sub.text() in [TEXTS["en"]["menu_about"], TEXTS["fr"]["menu_about"]]:
                                sub.setText(t("menu_about"))

        ui_builder.update_ui_texts(self)

    def on_table_current_changed(self, current, previous):
        if self.is_refreshing or not current: return
        if not (current.flags() & Qt.ItemFlag.ItemIsSelectable): return
        
        row = current.row()
        item = self.table_w.item(row, 1)
        if item:
            file_name = item.data(Qt.ItemDataRole.UserRole)
            self.update_count_selection(row + 1)
            self.load_byml_to_ui(file_name)

    def update_count_selection(self, current_index):
        text = self.count_lbl.text()
        if " | " in text:
            parts = text.split(" | ")
            if len(parts) >= 3:
                total_byml_str = parts[0]
                displayed_str = parts[1]
                displayed_val = displayed_str.split(": ")[1]
                total_val = total_byml_str.split(": ")[1]
                self.count_lbl.setText(t("count_info", total_val, displayed_val, current_index, displayed_val))

    def on_cell_clicked(self, row, col):
        item = self.table_w.item(row, 1)
        if not item: return
        if not (item.flags() & Qt.ItemFlag.ItemIsSelectable): return
        
        file_name = item.data(Qt.ItemDataRole.UserRole)

        if col == 0: 
            if file_name in self.favorites:
                self.favorites.remove(file_name)
            else:
                self.favorites.add(file_name)
                
            save_favorites(self.favorites)
            self.refresh_file_list()
            self.restore_selection(file_name)
            self.load_byml_to_ui(file_name)

    def on_table_context_menu(self, pos):
        item = self.table_w.itemAt(pos)
        if not item or not (item.flags() & Qt.ItemFlag.ItemIsSelectable): return
        menu = QMenu(self)
        copy_action = menu.addAction(t("ctx_copy_name"))
        action = menu.exec(self.table_w.viewport().mapToGlobal(pos))
        if action == copy_action:
            QApplication.clipboard().setText(item.text())

    def on_tree_context_menu(self, pos):
        item = self.tree_w.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        copy_prop = menu.addAction(t("ctx_copy_prop"))
        copy_val = menu.addAction(t("ctx_copy_val"))
        action = menu.exec(self.tree_w.viewport().mapToGlobal(pos))
        if action == copy_prop:
            QApplication.clipboard().setText(item.text(0))
        elif action == copy_val:
            QApplication.clipboard().setText(item.text(1))

    def restore_selection(self, file_name):
        self.is_refreshing = True
        for row in range(self.table_w.rowCount()):
            item = self.table_w.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole) == file_name:
                self.table_w.selectRow(row)
                self.update_count_selection(row + 1)
                break
        self.is_refreshing = False

    def load_byml_to_ui(self, file_name):
        if self.current_byml_name == file_name:
            return 

        if self.current_byml_name and self.current_byml_name in self.pack_manager.byml_files:
            self.pack_manager.byml_files[self.current_byml_name] = TreeHandler.build_dict(self.tree_w.invisibleRootItem())
            
        self.current_byml_name = file_name
        byml_dict = self.pack_manager.byml_files[file_name]
        
        TreeHandler.populate_tree(self.tree_w, parse_node(byml_dict), auto_expand=self.chk_auto_expand.isChecked())
        self.refresh_weapon_ui(file_name)

    def on_image_downloaded(self, image):
        if not image.isNull():
            scaled = image.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            square = QImage(128, 128, QImage.Format.Format_ARGB32_Premultiplied)
            square.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(square)
            x = (128 - scaled.width()) // 2
            y = (128 - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
            painter.end()
            
            self.img_lbl.setPixmap(QPixmap.fromImage(square))
        else:
            self.img_lbl.clear()
            self.img_lbl.setText(t("img_unavail"))

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    if os.name == 'nt':
        import ctypes
        myappid = 'jeremkoytb.splatoon3weaponseditor.1.0.3'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    is_dark = darkdetect.isDark()
    
    pal = app.palette()
    if is_dark:
        pal.setColor(app.palette().ColorRole.Window, Qt.GlobalColor.darkGray)
    else:
        pal.setColor(app.palette().ColorRole.Window, QColor("#F0F0F5"))
    app.setPalette(pal)
    
    app.setStyleSheet(get_stylesheet(is_dark))
    
    win = SplatoonParamEditor()
    win.show()
    sys.exit(app.exec())
