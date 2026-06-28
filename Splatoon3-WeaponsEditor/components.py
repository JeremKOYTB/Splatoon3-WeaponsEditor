import os
import copy
import requests
import concurrent.futures
import re

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTreeWidget, QTreeWidgetItem, QPushButton, 
                             QMessageBox, QStyledItemDelegate, QSpinBox, 
                             QComboBox, QLineEdit, QProgressBar, QMenu, 
                             QApplication, QTextEdit)
from PyQt6.QtGui import QFont, QBrush, QColor, QIcon, QImage, QPainter, QPixmap, QTextOption
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal

from utils import CACHE_DIR, log
from translations import t

class _MissingItem: pass
MISSING = _MissingItem()

class DiffDialog(QDialog):
    def __init__(self, diff_results, ref_pack, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("diff_title"))
        self.resize(1200, 700)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.ref_pack = ref_pack
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(t("diff_desc"))
        lbl.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            t("diff_col1"), 
            t("diff_col2"), 
            t("diff_col3"),
            t("diff_col4")
        ])
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 230)
        self.tree.setColumnWidth(2, 230)
        self.tree.setColumnWidth(3, 150)
        self.tree.setIconSize(QSize(44, 44)) 
        
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ecf0f1;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QTreeWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid rgba(255, 255, 255, 10);
            }
            QTreeWidget::item:selected {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 4px;
            }
        """)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        layout.addWidget(self.tree)
        
        for fname, diffs in sorted(diff_results.items()):
            if not diffs: continue
            
            basename = os.path.basename(fname)
            internal_name = basename.split('.')[0]
            
            if parent and hasattr(parent, 'data_manager'):
                _, img_filename, _, json_key = parent.data_manager.guess_image_and_name(internal_name)
                loc_name = parent.data_manager.get_exact_translation(internal_name, json_key)
                hide_filenames = parent.chk_hide_filenames.isChecked()
            else:
                img_filename = "Dummy.png"
                loc_name = None
                hide_filenames = False
                
            display_name = basename
            if loc_name:
                if hide_filenames:
                    display_name = loc_name
                else:
                    display_name = f"{basename}\n({loc_name})"
            
            file_item = QTreeWidgetItem(self.tree)
            file_item.setText(0, display_name)
            file_item.setToolTip(0, fname)
            file_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            file_item.setForeground(0, QBrush(QColor("#f39c12"))) 
            
            header_bg = QBrush(QColor(255, 255, 255, 15))
            for i in range(4):
                file_item.setBackground(i, header_bg)
            
            icon_path = os.path.join(CACHE_DIR, img_filename)
            if not os.path.exists(icon_path):
                icon_path = os.path.join(CACHE_DIR, "Dummy.png")
                
            if os.path.exists(icon_path):
                img = QImage(icon_path)
                if not img.isNull():
                    scaled = img.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    square = QImage(44, 44, QImage.Format.Format_ARGB32_Premultiplied)
                    square.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(square)
                    x = (44 - scaled.width()) // 2
                    y = (44 - scaled.height()) // 2
                    painter.drawImage(x, y, scaled)
                    painter.end()
                    
                    file_item.setIcon(0, QIcon(QPixmap.fromImage(square)))
            
            for path, cur_val, ref_val, path_tuple in diffs:
                diff_item = QTreeWidgetItem(file_item)
                diff_item.setText(0, path)
                diff_item.setText(1, str(cur_val)) 
                diff_item.setText(2, str(ref_val)) 
                diff_item.setData(0, Qt.ItemDataRole.UserRole, path_tuple)
                
                diff_item.setForeground(1, QBrush(QColor("#55efc4")))
                diff_item.setForeground(2, QBrush(QColor("#ff7675"))) 
                
                if isinstance(ref_val, (int, float)) and isinstance(cur_val, (int, float)):
                    try:
                        r_num = float(ref_val)
                        c_num = float(cur_val)
                        if r_num != 0:
                            pct = ((c_num - r_num) / abs(r_num)) * 100
                            diff_item.setText(3, f"{pct:+.6f}%")
                        else:
                            if c_num == 0:
                                diff_item.setText(3, "0.000000%")
                            else:
                                diff_item.setText(3, "+∞%" if c_num > 0 else "-∞%")
                                
                        pct_color = "#55efc4" if c_num > r_num else "#ff7675"
                        diff_item.setForeground(3, QBrush(QColor(pct_color)))
                    except (ValueError, TypeError):
                        diff_item.setText(3, "-")
                else:
                    diff_item.setText(3, "-")
                    
            file_item.setExpanded(True)
            
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_retroport = QPushButton(t("diff_btn_back"))
        btn_retroport.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #d35400; }
        """)
        btn_retroport.clicked.connect(self.on_retroport_clicked)
        btn_layout.addWidget(btn_retroport)
        
        btn_forwardport = QPushButton(t("diff_btn_forward"))
        btn_forwardport.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_forwardport.clicked.connect(self.on_forwardport_clicked)
        btn_layout.addWidget(btn_forwardport)
        
        btn_close = QPushButton(t("diff_btn_close"))
        btn_close.clicked.connect(self.accept)
        btn_close.setMinimumHeight(35)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        copy_prop = menu.addAction(t("ctx_copy_prop"))
        copy_cur = menu.addAction(t("ctx_copy_cur"))
        copy_ref = menu.addAction(t("ctx_copy_ref"))
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action == copy_prop:
            QApplication.clipboard().setText(item.text(0))
        elif action == copy_cur:
            QApplication.clipboard().setText(item.text(1))
        elif action == copy_ref:
            QApplication.clipboard().setText(item.text(2))

    def _get_nested_value(self, data, path_tuple):
        cur = data
        for k in path_tuple:
            if isinstance(cur, dict) and k not in cur: return MISSING
            if isinstance(cur, list) and k >= len(cur): return MISSING
            cur = cur[k]
        return cur

    def _set_nested_value(self, data, path_tuple, value):
        if not path_tuple: return
        cur = data
        for k in path_tuple[:-1]:
            if k not in cur:
                cur[k] = {} 
            cur = cur[k]
        
        if value is MISSING:
            if isinstance(cur, dict) and path_tuple[-1] in cur:
                del cur[path_tuple[-1]]
            elif isinstance(cur, list) and path_tuple[-1] < len(cur):
                cur.pop(path_tuple[-1])
        else:
            if isinstance(cur, list) and path_tuple[-1] == len(cur):
                cur.append(value)
            else:
                cur[path_tuple[-1]] = value

    def on_retroport_clicked(self):
        item = self.tree.currentItem()
        if not item:
            QMessageBox.warning(self, t("err_title"), t("diff_err_select"))
            return
            
        parent_win = self.parent()
        if not parent_win: return

        if item.parent() is None:
            fname = item.toolTip(0)
            if fname in self.ref_pack.byml_files:
                parent_win.pack_manager.byml_files[fname] = copy.deepcopy(self.ref_pack.byml_files[fname])
                
                item.setBackground(0, QColor("#27ae60"))
                if t("diff_restored").strip() not in item.text(0):
                    item.setText(0, item.text(0) + t("diff_restored"))
                    
                for i in range(item.childCount()):
                    child = item.child(i)
                    for col in range(4): child.setBackground(col, QColor("#27ae60"))
                    
                if parent_win.current_byml_name == fname:
                    parent_win.load_byml_to_ui(fname)
                    
        else:
            file_node = item.parent()
            fname = file_node.toolTip(0)
            path_tuple = item.data(0, Qt.ItemDataRole.UserRole)
            
            if not path_tuple: return
            
            ref_val = self._get_nested_value(self.ref_pack.byml_files.get(fname, {}), path_tuple)
            
            if fname not in parent_win.pack_manager.byml_files:
                parent_win.pack_manager.byml_files[fname] = {}
                
            self._set_nested_value(parent_win.pack_manager.byml_files[fname], path_tuple, copy.deepcopy(ref_val))
            
            for col in range(4):
                item.setBackground(col, QColor("#27ae60"))
                item.setForeground(col, QBrush(QColor("white")))
            
            val_str = t("diff_deleted") if ref_val is MISSING else str(ref_val)
            item.setText(1, val_str)
            item.setText(3, "0.000000%")
            
            if parent_win.current_byml_name == fname:
                parent_win.load_byml_to_ui(fname)

    def on_forwardport_clicked(self):
        item = self.tree.currentItem()
        if not item:
            QMessageBox.warning(self, t("err_title"), t("diff_err_select"))
            return
            
        parent_win = self.parent()
        if not parent_win: return

        if item.parent() is None:
            fname = item.toolTip(0)
            if fname in parent_win.pack_manager.byml_files:
                self.ref_pack.byml_files[fname] = copy.deepcopy(parent_win.pack_manager.byml_files[fname])
                
                item.setBackground(0, QColor("#3498db"))
                if t("diff_forwarded").strip() not in item.text(0):
                    item.setText(0, item.text(0) + t("diff_forwarded"))
                    
                for i in range(item.childCount()):
                    child = item.child(i)
                    for col in range(4): child.setBackground(col, QColor("#3498db"))
        else:
            file_node = item.parent()
            fname = file_node.toolTip(0)
            path_tuple = item.data(0, Qt.ItemDataRole.UserRole)
            
            if not path_tuple: return
            
            current_val = self._get_nested_value(parent_win.pack_manager.byml_files.get(fname, {}), path_tuple)
            
            if fname not in self.ref_pack.byml_files:
                self.ref_pack.byml_files[fname] = {}
                
            self._set_nested_value(self.ref_pack.byml_files[fname], path_tuple, copy.deepcopy(current_val))
            
            for col in range(4):
                item.setBackground(col, QColor("#3498db"))
                item.setForeground(col, QBrush(QColor("white")))
            
            val_str = t("diff_deleted") if current_val is MISSING else str(current_val)
            item.setText(2, val_str)
            item.setText(3, "0.000000%")


class TypeEnforcedDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        val_type = index.data(Qt.ItemDataRole.UserRole)
        if not val_type: return None
        
        log(f"[EDIT] Opening editor for value of type '{val_type}'.")
        if val_type == "int":
            editor = QSpinBox(parent)
            editor.setRange(-2147483648, 2147483647)
            return editor
        elif val_type == "float":
            return QLineEdit(parent)
        elif val_type == "bool":
            editor = QComboBox(parent)
            editor.addItems(["True", "False"])
            return editor
        elif val_type == "str":
            return QLineEdit(parent)
        return None

    def setEditorData(self, editor, index):
        val_type = index.data(Qt.ItemDataRole.UserRole)
        val_str = index.data(Qt.ItemDataRole.DisplayRole)
        if val_type == "int":
            editor.setValue(int(val_str))
        elif val_type == "float":
            editor.setText(val_str)
        elif val_type == "bool":
            editor.setCurrentText(val_str)
        elif val_type == "str":
            editor.setText(val_str)

    def setModelData(self, editor, model, index):
        val_type = index.data(Qt.ItemDataRole.UserRole)
        old_val = index.data(Qt.ItemDataRole.DisplayRole)
        
        if val_type == "int":
            new_val = str(editor.value())
            model.setData(index, new_val, Qt.ItemDataRole.DisplayRole)
        elif val_type == "float":
            raw_text = editor.text().replace(' ', '').replace(',', '.')
            try:
                float_val = float(raw_text)
                new_val = str(float_val)
                model.setData(index, new_val, Qt.ItemDataRole.DisplayRole)
                log(f"[EDIT] Value modified from '{old_val}' to '{new_val}' (Type: float).")
            except ValueError:
                log(f"[EDIT] Invalid input ignored: '{editor.text()}'. Value remains '{old_val}'.")
        elif val_type == "bool":
            new_val = editor.currentText()
            model.setData(index, new_val, Qt.ItemDataRole.DisplayRole)
            log(f"[EDIT] Value modified from '{old_val}' to '{new_val}' (Type: bool).")
        elif val_type == "str":
            new_val = editor.text()
            model.setData(index, new_val, Qt.ItemDataRole.DisplayRole)
            log(f"[EDIT] Value modified from '{old_val}' to '{new_val}' (Type: str).")


class CacheDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("cache_title"))
        self.setFixedSize(450, 120)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        self.lbl = QLabel(t("cache_desc"))
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

    def closeEvent(self, event):
        event.ignore()


class CacheBuilderWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(set)

    def __init__(self, missing_images):
        super().__init__()
        self.missing_images = missing_images
        self.new_dummies = set()

    def download_image(self, img_filename):
        local_path = os.path.join(CACHE_DIR, img_filename)
        urls_to_try = []
        
        if img_filename == "Dummy.png":
            urls_to_try = ["https://leanny.github.io/splat3/images/weapon/Dummy.png"]
        elif img_filename == "Wsb_SalmonBuddy00.png":
            urls_to_try = ["https://leanny.github.io/splat3/images/minigame/card/Kojake.png"]
        elif img_filename == "SakelienSmall.png":
            urls_to_try = ["https://leanny.github.io/splat3/images/coopEnemy/SakelienSmall.png"]
        elif img_filename == "Wsp_Shachihoko.png":
            urls_to_try = ["https://leanny.github.io/splat3/images/weapon/Wsp_Shachihoko.png"]
        elif img_filename.startswith("Win"):
            urls_to_try = [f"https://leanny.github.io/splat3/images/emote/{img_filename}"]
        elif img_filename.startswith("Wsp_") or img_filename.startswith("Wsb_"):
            urls_to_try = [f"https://leanny.github.io/splat3/images/subspe/{img_filename}"]
        elif img_filename.startswith("Path_"):
            urls_to_try = [f"https://leanny.github.io/splat3/images/weapon_flat/{img_filename}"]
        else:
            urls_to_try = [
                f"https://leanny.github.io/splat3/images/weapon/{img_filename}",
                f"https://leanny.github.io/splat3/images/weapon_flat/Path_{img_filename}",
                f"https://leanny.github.io/splat3/images/weapon_flat/{img_filename}"
            ]
            
        for url in urls_to_try:
            log(f"[NET] Fetching image: {url}")
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    log(f"[NET] SUCCESS (200) for {img_filename}")
                    return None
                else:
                    log(f"[NET] FAIL ({resp.status_code}) for {url}")
            except Exception as e:
                log(f"[NET] ERROR ({e}) for {url}")
                
        log(f"[NET] All URLs exhausted. Classified as Dummy: {img_filename}")
        return img_filename 

    def run(self):
        missing_list = list(self.missing_images)
        
        log(f"[CACHE] Starting download thread for {len(missing_list)} missing files.")
        
        total = len(missing_list)
        completed = 0

        if total > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.download_image, img): img for img in missing_list}
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res: 
                        self.new_dummies.add(res)
                    completed += 1
                    self.progress.emit(completed, total)

        log(f"[CACHE] Analysis complete. {len(self.new_dummies)} images not found.")
        self.finished.emit(self.new_dummies)


class ImageManager(QThread):
    finished = pyqtSignal(QImage)

    def __init__(self, img_filename):
        super().__init__()
        self.local_path = os.path.join(CACHE_DIR, img_filename)
        self.dummy_path = os.path.join(CACHE_DIR, "Dummy.png")

    def run(self):
        img = QImage()
        if os.path.exists(self.local_path) and img.load(self.local_path):
            self.finished.emit(img)
        elif os.path.exists(self.dummy_path) and img.load(self.dummy_path):
            self.finished.emit(img)
        else:
            self.finished.emit(QImage())


class UpdateCheckWorker(QThread):
    finished = pyqtSignal(int, str, str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        url = "https://api.github.com/repos/JeremKOYTB/Splatoon3-WeaponsEditor/releases/latest"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            latest_version = data.get("tag_name", "").replace("v", "")
            changelog = data.get("body", "No changelog provided.")
            
            from packaging import version
            v_latest = version.parse(latest_version)
            v_current = version.parse(self.current_version)
            
            if v_latest > v_current:
                self.finished.emit(1, latest_version, changelog)
            elif v_latest < v_current:
                self.finished.emit(2, latest_version, changelog)
            else:
                self.finished.emit(0, latest_version, "")
        except Exception as e:
            log(f"[NET] Update check failed: {e}")
            self.finished.emit(-1, "", str(e))


class UpdatePromptDialog(QDialog):
    def __init__(self, current_version, new_version, changelog, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("update_title"))
        self.resize(600, 450)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        
        lbl_info = QLabel(t("update_msg", current_version, new_version))
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("font-size: 11pt;")
        layout.addWidget(lbl_info)
        
        self.browser = QTextEdit()
        self.browser.setReadOnly(True)
        self.browser.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        text_normalized = changelog.replace("\r\n", "\n")
        html_text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text_normalized)
        self.browser.setMarkdown(html_text)
        
        self.browser.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E24;
                color: #E8E8E8;
                border: 1px solid #4A4A55;
                border-radius: 8px;
                padding: 10px;
                font-family: "Segoe UI", sans-serif;
            }
        """)
        layout.addWidget(self.browser)
        
        btn_layout = QHBoxLayout()
        
        btn_yes = QPushButton(t("btn_update_now"))
        btn_yes.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; border: none; }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_yes.clicked.connect(self.accept)
        
        btn_no = QPushButton(t("btn_update_later"))
        btn_no.setStyleSheet("""
            QPushButton { background-color: #34495e; color: white; padding: 8px 16px; border-radius: 4px; border: none; }
            QPushButton:hover { background-color: #2c3e50; }
        """)
        btn_no.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_no)
        btn_layout.addWidget(btn_yes)
        
        layout.addLayout(btn_layout)