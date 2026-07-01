import os
import copy
import requests
import concurrent.futures
import re
import darkdetect

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTreeWidget, QTreeWidgetItem, QPushButton, 
                             QMessageBox, QStyledItemDelegate, QSpinBox, 
                             QComboBox, QLineEdit, QProgressBar, QMenu, 
                             QApplication, QTextEdit, QAbstractItemView, QFileDialog)
from PyQt6.QtGui import QFont, QBrush, QColor, QIcon, QImage, QPainter, QPixmap, QTextOption
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QEvent

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
        self.diff_results = diff_results
        
        self.modifications_main = set()
        self.deletions_main = set()
        self.additions_main = set()
        
        self.modifications_ref = set()
        self.deletions_ref = set()
        self.additions_ref = set()
        
        self.backup_main = {}
        self.backup_ref = {}

        if parent and hasattr(parent, 'pack_manager'):
            for fname in diff_results.keys():
                if fname in parent.pack_manager.byml_files:
                    self.backup_main[fname] = copy.deepcopy(parent.pack_manager.byml_files[fname])
                if fname in self.ref_pack.byml_files:
                    self.backup_ref[fname] = copy.deepcopy(self.ref_pack.byml_files[fname])

        layout = QVBoxLayout(self)
        
        lbl = QLabel(t("diff_desc"))
        lbl.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        self.tree = QTreeWidget()
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setHeaderLabels([t("diff_col1"), t("diff_col2"), t("diff_col3"), t("diff_col4")])
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 230)
        self.tree.setColumnWidth(2, 230)
        self.tree.setColumnWidth(3, 150)
        self.tree.setIconSize(QSize(44, 44)) 
        
        self.tree.setStyleSheet("""
            QTreeWidget { background-color: #1e1e1e; color: #ecf0f1; border: 1px solid #444; border-radius: 6px; }
            QTreeWidget::item { padding: 6px 4px; border-bottom: 1px solid rgba(255, 255, 255, 10); }
            QTreeWidget::item:selected { background-color: rgba(255, 255, 255, 20); border-radius: 4px; }
        """)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
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
                img_filename, loc_name, hide_filenames = "Dummy.png", None, False
                
            display_name = loc_name if (loc_name and hide_filenames) else (f"{basename}\n({loc_name})" if loc_name else basename)
            
            file_item = QTreeWidgetItem(self.tree)
            file_item.setText(0, display_name)
            file_item.setToolTip(0, fname)
            file_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            file_item.setForeground(0, QBrush(QColor("#f39c12"))) 
            
            self._color_item(file_item, QColor(255, 255, 255, 15))
            
            icon_path = os.path.join(CACHE_DIR, img_filename)
            if not os.path.exists(icon_path): icon_path = os.path.join(CACHE_DIR, "Dummy.png")
                
            if os.path.exists(icon_path):
                img = QImage(icon_path)
                if not img.isNull():
                    scaled = img.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    square = QImage(44, 44, QImage.Format.Format_ARGB32_Premultiplied)
                    square.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(square)
                    painter.drawImage((44 - scaled.width()) // 2, (44 - scaled.height()) // 2, scaled)
                    painter.end()
                    file_item.setIcon(0, QIcon(QPixmap.fromImage(square)))

            is_missing_in_main = fname not in self.backup_main
            is_missing_in_ref = fname not in self.backup_ref
            
            if is_missing_in_main or is_missing_in_ref:
                file_item.setText(1, t("diff_missing") if is_missing_in_main else t("raw_data"))
                file_item.setText(2, t("diff_missing") if is_missing_in_ref else t("raw_data"))
                file_item.setForeground(1, QBrush(QColor("#ff7675") if is_missing_in_main else QColor("#55efc4")))
                file_item.setForeground(2, QBrush(QColor("#ff7675") if is_missing_in_ref else QColor("#55efc4")))
                file_item.setText(3, "-")
                file_item.setExpanded(True)
                continue
            
            for path, cur_val, ref_val, path_tuple in diffs:
                self._add_diff_node(file_item, path, cur_val, ref_val, path_tuple)
                    
            file_item.setExpanded(True)
            
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_forwardport = QPushButton(t("diff_btn_forward"))
        btn_forwardport.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 10px; border-radius: 4px; } QPushButton:hover { background-color: #2980b9; }")
        btn_forwardport.clicked.connect(self.on_forwardport_clicked)
        btn_layout.addWidget(btn_forwardport)
        
        btn_retroport = QPushButton(t("diff_btn_back"))
        btn_retroport.setStyleSheet("QPushButton { background-color: #e67e22; color: white; font-weight: bold; padding: 10px; border-radius: 4px; } QPushButton:hover { background-color: #d35400; }")
        btn_retroport.clicked.connect(self.on_retroport_clicked)
        btn_layout.addWidget(btn_retroport)

        btn_reset = QPushButton(t("diff_btn_reset"))
        btn_reset.setStyleSheet("QPushButton { background-color: #7f8c8d; color: white; font-weight: bold; padding: 10px; border-radius: 4px; } QPushButton:hover { background-color: #95a5a6; }")
        btn_reset.clicked.connect(self.on_reset_clicked)
        btn_layout.addWidget(btn_reset)
        
        btn_close = QPushButton(t("diff_btn_close"))
        btn_close.clicked.connect(self.close)
        btn_close.setMinimumHeight(35)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def _color_item(self, item, color):
        brush = QBrush(color) if isinstance(color, QColor) else QBrush(QColor(color))
        for col in range(4): item.setBackground(col, brush)

    def _add_diff_node(self, parent_item, path_str, cur_val, ref_val, path_tuple):
        is_c_dict, is_r_dict = isinstance(cur_val, dict), isinstance(ref_val, dict)
        is_c_list, is_r_list = isinstance(cur_val, list), isinstance(ref_val, list)

        if is_c_dict or is_r_dict:
            all_keys = sorted(set(cur_val.keys() if is_c_dict else []).union(set(ref_val.keys() if is_r_dict else [])))
            for k in all_keys:
                c_v = cur_val[k] if is_c_dict and k in cur_val else MISSING
                r_v = ref_val[k] if is_r_dict and k in ref_val else MISSING
                base_path = "" if not path_str or path_str in [t("raw_data"), "File"] else f"{path_str}/"
                new_path_tuple = path_tuple + (k,) if path_tuple else (k,)
                self._add_diff_node(parent_item, f"{base_path}{k}", c_v, r_v, new_path_tuple)
                
        elif is_c_list or is_r_list:
            c_len = len(cur_val) if is_c_list else 0
            r_len = len(ref_val) if is_r_list else 0
            for i in range(max(c_len, r_len)):
                c_v = cur_val[i] if is_c_list and i < c_len else MISSING
                r_v = ref_val[i] if is_r_list and i < r_len else MISSING
                base_path = "" if not path_str or path_str in [t("raw_data"), "File"] else path_str
                new_path_tuple = path_tuple + (i,) if path_tuple else (i,)
                self._add_diff_node(parent_item, f"{base_path}[{i}]", c_v, r_v, new_path_tuple)
                
        else:
            if cur_val == ref_val and cur_val is not MISSING: return 
                
            diff_item = QTreeWidgetItem(parent_item)
            diff_item.setText(0, path_str if path_str and path_str != "File" else t("raw_data"))
            diff_item.setText(1, t("diff_missing") if cur_val is MISSING else str(cur_val)) 
            diff_item.setText(2, t("diff_missing") if ref_val is MISSING else str(ref_val)) 
            diff_item.setData(0, Qt.ItemDataRole.UserRole, path_tuple)
            diff_item.setForeground(1, QBrush(QColor("#55efc4")))
            diff_item.setForeground(2, QBrush(QColor("#ff7675"))) 
            self._update_diff_percent(diff_item, cur_val, ref_val)

    def on_tree_selection_changed(self):
        self.tree.blockSignals(True)
        for item in self.tree.selectedItems():
            if item.parent() is None:
                for i in range(item.childCount()): item.child(i).setSelected(True)
        self.tree.blockSignals(False)

    def _update_diff_percent(self, item, cur_val, ref_val):
        if isinstance(ref_val, (int, float)) and isinstance(cur_val, (int, float)):
            try:
                r_num, c_num = float(ref_val), float(cur_val)
                if r_num != 0:
                    item.setText(3, f"{((c_num - r_num) / abs(r_num)) * 100:+.6f}%")
                else:
                    item.setText(3, "0.000000%" if c_num == 0 else ("+∞%" if c_num > 0 else "-∞%"))
                item.setForeground(3, QBrush(QColor("#55efc4" if c_num > r_num else "#ff7675")))
            except (ValueError, TypeError):
                item.setText(3, "-")
                item.setForeground(3, QBrush(QColor("white")))
        else:
            item.setText(3, "-")
            item.setForeground(3, QBrush(QColor("white")))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.tree.selectAll()
        else:
            super().keyPressEvent(event)

    def on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        actions = {
            menu.addAction(t("ctx_copy_prop")): 0,
            menu.addAction(t("ctx_copy_cur")): 1,
            menu.addAction(t("ctx_copy_ref")): 2
        }
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action in actions:
            QApplication.clipboard().setText(item.text(actions[action]))

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
            if k not in cur: cur[k] = {} 
            cur = cur[k]
        
        if value is MISSING:
            if isinstance(cur, dict) and path_tuple[-1] in cur: del cur[path_tuple[-1]]
            elif isinstance(cur, list) and path_tuple[-1] < len(cur): cur.pop(path_tuple[-1])
        else:
            if isinstance(cur, list) and path_tuple[-1] == len(cur): cur.append(value)
            else: cur[path_tuple[-1]] = value

    def update_item_state_text(self, item, state_text=""):
        text = item.text(0).replace(t("diff_restored"), "").replace(t("diff_forwarded"), "").replace(" (Will be deleted)", "").replace(" (Added)", "")
        item.setText(0, text + state_text)

    def _safe_reload_parent_ui(self):
        parent_win = self.parentWidget()
        while parent_win and not hasattr(parent_win, 'pack_manager'):
            parent_win = parent_win.parentWidget()
            
        if not parent_win: return
        current_name = getattr(parent_win, 'current_byml_name', None)
        if not current_name: return
        
        if hasattr(parent_win, 'pack_manager'):
            if current_name not in parent_win.pack_manager.byml_files:
                parent_win.current_byml_name = None
                if hasattr(parent_win, 'tree_props'): parent_win.tree_props.clear()
                return
                
        if hasattr(parent_win, 'load_byml_to_ui'):
            parent_win.load_byml_to_ui(current_name)

    def _delete_byml_file(self, parent_win, pack_mgr, fname):
        deleted_something = False
        
        if hasattr(pack_mgr, 'byml_files') and fname in pack_mgr.byml_files:
            del pack_mgr.byml_files[fname]
            deleted_something = True
            
        if not hasattr(pack_mgr, 'deleted_files'):
            pack_mgr.deleted_files = set()
        pack_mgr.deleted_files.add(fname)

        return deleted_something

    def on_retroport_clicked(self):
        items = self.tree.selectedItems()
        if not items: return
        for item in items: self._process_retroport(item)
        self._safe_reload_parent_ui()

    def _process_retroport(self, item):
        parent_win = self.parentWidget()
        while parent_win and not hasattr(parent_win, 'pack_manager'):
            parent_win = parent_win.parentWidget()
            
        if not parent_win: return

        if item.parent() is None:
            fname = item.toolTip(0)
            if fname in self.ref_pack.byml_files:
                parent_win.pack_manager.byml_files[fname] = copy.deepcopy(self.ref_pack.byml_files[fname])
                if fname not in self.backup_main:
                    self.additions_main.add(fname)
                    state_lbl = " (Added)"
                else:
                    self.modifications_main.add(fname)
                    state_lbl = t("diff_restored")
                    
                self.deletions_main.discard(fname)
                if hasattr(parent_win.pack_manager, 'deleted_files'):
                    parent_win.pack_manager.deleted_files.discard(fname)
                
                self.update_item_state_text(item, state_lbl)
                self._color_item(item, "#27ae60")
                item.setText(1, t("raw_data"))
                item.setForeground(1, QBrush(QColor("#55efc4")))
            else:
                self._delete_byml_file(parent_win, parent_win.pack_manager, fname)
                self.deletions_main.add(fname)
                self.modifications_main.discard(fname)
                self.additions_main.discard(fname)
                
                self.update_item_state_text(item, " (Will be deleted)")
                self._color_item(item, "#e74c3c")
                item.setText(1, t("diff_missing"))
                item.setForeground(1, QBrush(QColor("#ff7675")))
            
            for i in range(item.childCount()):
                child = item.child(i)
                if fname in self.ref_pack.byml_files:
                    child_state = " (Added)" if fname not in self.backup_main else t("diff_restored")
                else:
                    child_state = " (Will be deleted)"
                    
                self.update_item_state_text(child, child_state)
                self._color_item(child, "#27ae60" if fname in self.ref_pack.byml_files else "#e74c3c")
                
                path_tuple = child.data(0, Qt.ItemDataRole.UserRole)
                ref_val = self._get_nested_value(self.ref_pack.byml_files.get(fname, {}), path_tuple)
                
                child.setText(1, t("diff_missing") if ref_val is MISSING else str(ref_val))
                child.setText(3, "0.000000%")
                child.setForeground(3, QBrush(QColor("white")))
        else:
            file_node = item.parent()
            fname = file_node.toolTip(0)
            
            if fname not in parent_win.pack_manager.byml_files or fname not in self.ref_pack.byml_files:
                return self._process_retroport(file_node)
            
            path_tuple = item.data(0, Qt.ItemDataRole.UserRole)
            if not path_tuple: return
            
            ref_val = self._get_nested_value(self.ref_pack.byml_files.get(fname, {}), path_tuple)
            if fname not in parent_win.pack_manager.byml_files: parent_win.pack_manager.byml_files[fname] = {}
                
            self._set_nested_value(parent_win.pack_manager.byml_files[fname], path_tuple, copy.deepcopy(ref_val))
            
            if fname not in self.backup_main:
                self.additions_main.add(fname)
                state_lbl = " (Added)"
            else:
                self.modifications_main.add(fname)
                state_lbl = t("diff_restored")
            
            self.update_item_state_text(item, state_lbl)
            self._color_item(item, "#27ae60")
            
            item.setText(1, t("diff_missing") if ref_val is MISSING else str(ref_val))
            item.setText(3, "0.000000%")
            item.setForeground(3, QBrush(QColor("white")))

    def on_forwardport_clicked(self):
        items = self.tree.selectedItems()
        if not items: return
        for item in items: self._process_forward(item)
        self._safe_reload_parent_ui()

    def _process_forward(self, item):
        parent_win = self.parentWidget()
        while parent_win and not hasattr(parent_win, 'pack_manager'):
            parent_win = parent_win.parentWidget()
            
        if not parent_win: return

        if item.parent() is None:
            fname = item.toolTip(0)
            if fname in parent_win.pack_manager.byml_files:
                self.ref_pack.byml_files[fname] = copy.deepcopy(parent_win.pack_manager.byml_files[fname])
                if fname not in self.backup_ref:
                    self.additions_ref.add(fname)
                    state_lbl = " (Added)"
                else:
                    self.modifications_ref.add(fname)
                    state_lbl = t("diff_forwarded")
                    
                self.deletions_ref.discard(fname)
                if hasattr(self.ref_pack, 'deleted_files'):
                    self.ref_pack.deleted_files.discard(fname)
                    
                self.update_item_state_text(item, state_lbl)
                self._color_item(item, "#3498db")
                item.setText(2, t("raw_data"))
                item.setForeground(2, QBrush(QColor("#55efc4")))
            else:
                self._delete_byml_file(None, self.ref_pack, fname)
                self.deletions_ref.add(fname)
                self.modifications_ref.discard(fname)
                self.additions_ref.discard(fname)
                
                self.update_item_state_text(item, " (Will be deleted)")
                self._color_item(item, "#e74c3c")
                item.setText(2, t("diff_missing"))
                item.setForeground(2, QBrush(QColor("#ff7675")))
                
            for i in range(item.childCount()):
                child = item.child(i)
                if fname in parent_win.pack_manager.byml_files:
                    child_state = " (Added)" if fname not in self.backup_ref else t("diff_forwarded")
                else:
                    child_state = " (Will be deleted)"
                    
                self.update_item_state_text(child, child_state)
                self._color_item(child, "#3498db" if fname in parent_win.pack_manager.byml_files else "#e74c3c")
                
                path_tuple = child.data(0, Qt.ItemDataRole.UserRole)
                cur_val = self._get_nested_value(parent_win.pack_manager.byml_files.get(fname, {}), path_tuple)
                
                child.setText(2, t("diff_missing") if cur_val is MISSING else str(cur_val))
                child.setText(3, "0.000000%")
                child.setForeground(3, QBrush(QColor("white")))
        else:
            file_node = item.parent()
            fname = file_node.toolTip(0)
            
            if fname not in parent_win.pack_manager.byml_files or fname not in self.ref_pack.byml_files:
                return self._process_forward(file_node)
            
            path_tuple = item.data(0, Qt.ItemDataRole.UserRole)
            if not path_tuple: return
            
            cur_val = self._get_nested_value(parent_win.pack_manager.byml_files.get(fname, {}), path_tuple)
            if fname not in self.ref_pack.byml_files: self.ref_pack.byml_files[fname] = {}
                
            self._set_nested_value(self.ref_pack.byml_files[fname], path_tuple, copy.deepcopy(cur_val))
            
            if fname not in self.backup_ref:
                self.additions_ref.add(fname)
                state_lbl = " (Added)"
            else:
                self.modifications_ref.add(fname)
                state_lbl = t("diff_forwarded")
            
            self.update_item_state_text(item, state_lbl)
            self._color_item(item, "#3498db")
            
            item.setText(2, t("diff_missing") if cur_val is MISSING else str(cur_val))
            item.setText(3, "0.000000%")
            item.setForeground(3, QBrush(QColor("white")))

    def on_reset_clicked(self):
        items = self.tree.selectedItems()
        if not items: return
        for item in items: self._process_reset(item)
        self._safe_reload_parent_ui()

    def _process_reset(self, item):
        parent_win = self.parentWidget()
        while parent_win and not hasattr(parent_win, 'pack_manager'):
            parent_win = parent_win.parentWidget()
            
        if not parent_win: return

        if item.parent() is None:
            fname = item.toolTip(0)
            if fname in self.backup_main:
                parent_win.pack_manager.byml_files[fname] = copy.deepcopy(self.backup_main[fname])
                item.setText(1, t("raw_data"))
                item.setForeground(1, QBrush(QColor("#55efc4")))
            else:
                self._delete_byml_file(parent_win, parent_win.pack_manager, fname)
                item.setText(1, t("diff_missing"))
                item.setForeground(1, QBrush(QColor("#ff7675")))

            if fname in self.backup_ref:
                self.ref_pack.byml_files[fname] = copy.deepcopy(self.backup_ref[fname])
                item.setText(2, t("raw_data"))
                item.setForeground(2, QBrush(QColor("#55efc4")))
            else:
                self._delete_byml_file(None, self.ref_pack, fname)
                item.setText(2, t("diff_missing"))
                item.setForeground(2, QBrush(QColor("#ff7675")))

            self.modifications_main.discard(fname)
            self.deletions_main.discard(fname)
            self.additions_main.discard(fname)
            
            self.modifications_ref.discard(fname)
            self.deletions_ref.discard(fname)
            self.additions_ref.discard(fname)
            
            if hasattr(parent_win.pack_manager, 'deleted_files'):
                parent_win.pack_manager.deleted_files.discard(fname)
            if hasattr(self.ref_pack, 'deleted_files'):
                self.ref_pack.deleted_files.discard(fname)

            self.update_item_state_text(item, "")
            self._color_item(item, QColor(255, 255, 255, 15))

            for i in range(item.childCount()):
                child = item.child(i)
                self.update_item_state_text(child, "")
                self._color_item(child, QColor(255, 255, 255, 15))

                path_tuple = child.data(0, Qt.ItemDataRole.UserRole)
                orig_main = self._get_nested_value(self.backup_main.get(fname, {}), path_tuple) if fname in self.backup_main else MISSING
                orig_ref = self._get_nested_value(self.backup_ref.get(fname, {}), path_tuple) if fname in self.backup_ref else MISSING
                
                child.setText(1, t("diff_missing") if orig_main is MISSING else str(orig_main))
                child.setText(2, t("diff_missing") if orig_ref is MISSING else str(orig_ref))
                self._update_diff_percent(child, orig_main, orig_ref)

        else:
            file_node = item.parent()
            fname = file_node.toolTip(0)
            
            if fname not in parent_win.pack_manager.byml_files or fname not in self.ref_pack.byml_files:
                return self._process_reset(file_node)
                
            path_tuple = item.data(0, Qt.ItemDataRole.UserRole)
            if not path_tuple: return

            orig_main = self._get_nested_value(self.backup_main.get(fname, {}), path_tuple) if fname in self.backup_main else MISSING
            orig_ref = self._get_nested_value(self.backup_ref.get(fname, {}), path_tuple) if fname in self.backup_ref else MISSING
            
            self._set_nested_value(parent_win.pack_manager.byml_files.get(fname, {}), path_tuple, copy.deepcopy(orig_main))
            self._set_nested_value(self.ref_pack.byml_files.get(fname, {}), path_tuple, copy.deepcopy(orig_ref))

            self.update_item_state_text(item, "")
            self._color_item(item, QColor(255, 255, 255, 15))

            item.setText(1, t("diff_missing") if orig_main is MISSING else str(orig_main))
            item.setText(2, t("diff_missing") if orig_ref is MISSING else str(orig_ref))
            self._update_diff_percent(item, orig_main, orig_ref)

    def closeEvent(self, event):
        if not self.modifications_main and not self.modifications_ref and not self.deletions_main and not self.deletions_ref and not self.additions_main and not self.additions_ref:
            event.accept()
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(t("msg_diff_summary_title"))
        dialog.resize(550, 400)
        layout = QVBoxLayout(dialog)
        
        lbl = QLabel(t("msg_diff_summary_desc"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        desc = ""
        if self.additions_main:
            desc += "Additions in Main Pack:\n" + "\n".join([f"- {f}" for f in self.additions_main]) + "\n\n"
        if self.modifications_main:
            desc += t("msg_diff_main_pack") + "\n" + "\n".join([f"- {f}" for f in self.modifications_main]) + "\n\n"
        if self.deletions_main:
            desc += "Deletions in Main Pack:\n" + "\n".join([f"- {f}" for f in self.deletions_main]) + "\n\n"
            
        if self.additions_ref:
            desc += "Additions in Ref Pack:\n" + "\n".join([f"- {f}" for f in self.additions_ref]) + "\n\n"
        if self.modifications_ref:
            desc += t("msg_diff_ref_pack") + "\n" + "\n".join([f"- {f}" for f in self.modifications_ref]) + "\n\n"
        if self.deletions_ref:
            desc += "Deletions in Ref Pack:\n" + "\n".join([f"- {f}" for f in self.deletions_ref]) + "\n\n"
            
        text_edit.setPlainText(desc.strip())
        text_edit.setStyleSheet("""
            QTextEdit { background-color: #1E1E24; color: #E8E8E8; border: 1px solid #4A4A55; border-radius: 6px; padding: 10px; font-family: "Segoe UI", sans-serif; }
        """)
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton(t("diff_btn_close"))
        btn_cancel.setStyleSheet("QPushButton { background-color: #7f8c8d; color: white; padding: 8px 16px; border-radius: 4px; border: none; font-weight: bold; } QPushButton:hover { background-color: #95a5a6; }")
        btn_cancel.clicked.connect(lambda: dialog.done(0))
        
        btn_discard = QPushButton(t("btn_discard"))
        btn_discard.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px; border: none; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        btn_discard.clicked.connect(lambda: dialog.done(2))
        
        btn_save = QPushButton(t("btn_save"))
        btn_save.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 8px 16px; border-radius: 4px; border: none; font-weight: bold; } QPushButton:hover { background-color: #2ecc71; }")
        btn_save.clicked.connect(lambda: dialog.done(1))
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_discard)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        result = dialog.exec()
        if result == 1:
            self.save_modifications()
            event.accept()
        elif result == 2:
            self.revert_all()
            event.accept()
        else:
            event.ignore()

    def revert_all(self):
        parent_win = self.parentWidget()
        while parent_win and not hasattr(parent_win, 'pack_manager'):
            parent_win = parent_win.parentWidget()
            
        if not parent_win: return
        
        for fname in self.modifications_main.union(self.deletions_main).union(self.additions_main):
            if fname in self.backup_main: 
                parent_win.pack_manager.byml_files[fname] = copy.deepcopy(self.backup_main[fname])
                if hasattr(parent_win.pack_manager, 'deleted_files'):
                    parent_win.pack_manager.deleted_files.discard(fname)
            else: 
                self._delete_byml_file(parent_win, parent_win.pack_manager, fname)

        for fname in self.modifications_ref.union(self.deletions_ref).union(self.additions_ref):
            if fname in self.backup_ref: 
                self.ref_pack.byml_files[fname] = copy.deepcopy(self.backup_ref[fname])
                if hasattr(self.ref_pack, 'deleted_files'):
                    self.ref_pack.deleted_files.discard(fname)
            else: 
                self._delete_byml_file(None, self.ref_pack, fname)

        self._safe_reload_parent_ui()

    def _save_to_custom_path(self, pack_mgr, custom_path):
        for method_name in ['save_pack', 'save_archive', 'repack', 'save']:
            if hasattr(pack_mgr, method_name):
                method = getattr(pack_mgr, method_name)
                try:
                    method(custom_path)
                    return True
                except TypeError:
                    try:
                        old_path = getattr(pack_mgr, 'filepath', getattr(pack_mgr, 'archive_path', getattr(pack_mgr, 'file_path', None)))
                        if hasattr(pack_mgr, 'filepath'): pack_mgr.filepath = custom_path
                        elif hasattr(pack_mgr, 'archive_path'): pack_mgr.archive_path = custom_path
                        elif hasattr(pack_mgr, 'file_path'): pack_mgr.file_path = custom_path
                        
                        method()
                        
                        if old_path:
                            if hasattr(pack_mgr, 'filepath'): pack_mgr.filepath = old_path
                            elif hasattr(pack_mgr, 'archive_path'): pack_mgr.archive_path = old_path
                            elif hasattr(pack_mgr, 'file_path'): pack_mgr.file_path = old_path
                        return True
                    except Exception as e:
                        log(f"[SAVE] Erreur fallback sauvegarde: {e}")
                except Exception as e:
                    log(f"[SAVE] Erreur sauvegarde avec argument: {e}")
        return False

    def save_modifications(self):
        main_win = self.parentWidget()
        while main_win and not hasattr(main_win, 'pack_manager'):
            main_win = main_win.parentWidget()
            
        if not main_win:
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'pack_manager'):
                    main_win = widget
                    break
                    
        filter_str = "Pack ZS (*.pack.zs);;All Files (*)"
        
        saved_something = False
        main_saved_path = None
        
        if (self.modifications_main or self.deletions_main or self.additions_main) and main_win:
            default_name = "Params(Act).pack.zs"
            title = t("save_current_title")
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                title, 
                default_name, 
                filter_str,
                "Pack ZS (*.pack.zs)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            
            if file_path:
                if file_path.lower().endswith(".szs"):
                    file_path = file_path[:-4]
                if not file_path.lower().endswith(".pack.zs"):
                    if file_path.lower().endswith(".pack"):
                        file_path += ".zs"
                    else:
                        file_path += ".pack.zs"
                
                self._save_to_custom_path(main_win.pack_manager, file_path)
                saved_something = True
                main_saved_path = file_path

        if self.modifications_ref or self.deletions_ref or self.additions_ref:
            default_name_ref = "Params(Ref).pack.zs"
            title_ref = t("save_ref_title")
            
            file_path_ref, _ = QFileDialog.getSaveFileName(
                self, 
                title_ref, 
                default_name_ref, 
                filter_str,
                "Pack ZS (*.pack.zs)",
                options=QFileDialog.Option.DontUseNativeDialog
            )
            
            if file_path_ref:
                if file_path_ref.lower().endswith(".szs"):
                    file_path_ref = file_path_ref[:-4]
                if not file_path_ref.lower().endswith(".pack.zs"):
                    if file_path_ref.lower().endswith(".pack"):
                        file_path_ref += ".zs"
                    else:
                        file_path_ref += ".pack.zs"
                
                self._save_to_custom_path(self.ref_pack, file_path_ref)
                saved_something = True

        if main_win and saved_something:
            if main_saved_path and hasattr(main_win, 'load_pack'):
                main_win.load_pack(main_saved_path)
            else:
                if hasattr(main_win, 'refresh_file_list'):
                    main_win.refresh_file_list()
                self._safe_reload_parent_ui()


class TypeEnforcedDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        val_type = index.data(Qt.ItemDataRole.UserRole)
        if not val_type: return None
        
        log(f"[EDIT] Opening editor for value of type '{val_type}'.")
        is_dark = darkdetect.isDark()
        bg_popup, bg_edit, fg = ("#121212", "#3A3A3A", "#FFFFFF") if is_dark else ("#FFFFFF", "#E5E5E5", "#000000")
        
        editor = None
        if val_type == "int":
            editor = QSpinBox(parent)
            editor.setRange(-2147483648, 2147483647)
            editor.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        elif val_type in ["float", "str"]:
            editor = QLineEdit(parent)
        elif val_type == "bool":
            editor = QComboBox(parent)
            editor.addItems(["True", "False"])
            
        if editor:
            editor.setStyleSheet(f"""
                QLineEdit, QSpinBox, QComboBox {{ background-color: {bg_edit}; color: {fg}; border: none; padding: 0px; margin: 0px; selection-background-color: #0078D7; selection-color: white; }}
                QComboBox QAbstractItemView {{ background-color: {bg_popup}; color: {fg}; border: 1px solid #444; selection-background-color: #0078D7; selection-color: white; }}
            """)
            return editor
        return None

    def setEditorData(self, editor, index):
        val_type, val_str = index.data(Qt.ItemDataRole.UserRole), index.data(Qt.ItemDataRole.DisplayRole)
        if val_type == "int": editor.setValue(int(val_str))
        elif val_type == "float": editor.setText(val_str)
        elif val_type == "bool": editor.setCurrentText(val_str)
        elif val_type == "str": editor.setText(val_str)

    def setModelData(self, editor, model, index):
        val_type, old_val = index.data(Qt.ItemDataRole.UserRole), index.data(Qt.ItemDataRole.DisplayRole)
        
        if val_type == "int":
            model.setData(index, str(editor.value()), Qt.ItemDataRole.DisplayRole)
        elif val_type == "float":
            try:
                new_val = str(float(editor.text().replace(' ', '').replace(',', '.')))
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
        
        if img_filename == "Dummy.png": urls_to_try = ["https://leanny.github.io/splat3/images/weapon/Dummy.png"]
        elif img_filename == "Wsb_SalmonBuddy00.png": urls_to_try = ["https://leanny.github.io/splat3/images/minigame/card/Kojake.png"]
        elif img_filename == "SakelienSmall.png": urls_to_try = ["https://leanny.github.io/splat3/images/coopEnemy/SakelienSmall.png"]
        elif img_filename == "Wsp_Shachihoko.png": urls_to_try = ["https://leanny.github.io/splat3/images/weapon/Wsp_Shachihoko.png"]
        elif img_filename.startswith("Win"): urls_to_try = [f"https://leanny.github.io/splat3/images/emote/{img_filename}"]
        elif img_filename.startswith("Wsp_") or img_filename.startswith("Wsb_"): urls_to_try = [f"https://leanny.github.io/splat3/images/subspe/{img_filename}"]
        elif img_filename.startswith("Path_"): urls_to_try = [f"https://leanny.github.io/splat3/images/weapon_flat/{img_filename}"]
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
                    with open(local_path, "wb") as f: f.write(resp.content)
                    log(f"[NET] SUCCESS (200) for {img_filename}")
                    return None
                else: log(f"[NET] FAIL ({resp.status_code}) for {url}")
            except Exception as e: log(f"[NET] ERROR ({e}) for {url}")
                
        log(f"[NET] All URLs exhausted. Classified as Dummy: {img_filename}")
        return img_filename 

    def run(self):
        missing_list = list(self.missing_images)
        total, completed = len(missing_list), 0
        log(f"[CACHE] Starting download thread for {total} missing files.")

        if total > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.download_image, img): img for img in missing_list}
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res: self.new_dummies.add(res)
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
        if os.path.exists(self.local_path) and img.load(self.local_path): self.finished.emit(img)
        elif os.path.exists(self.dummy_path) and img.load(self.dummy_path): self.finished.emit(img)
        else: self.finished.emit(QImage())


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
            
            if v_latest > v_current: self.finished.emit(1, latest_version, changelog)
            elif v_latest < v_current: self.finished.emit(2, latest_version, changelog)
            else: self.finished.emit(0, latest_version, "")
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
        self.browser.setMarkdown(re.sub(r'(?<!\n)\n(?!\n)', '\n\n', changelog.replace("\r\n", "\n")))
        self.browser.setStyleSheet("""
            QTextEdit { background-color: #1E1E24; color: #E8E8E8; border: 1px solid #4A4A55; border-radius: 8px; padding: 10px; font-family: "Segoe UI", sans-serif; }
        """)
        layout.addWidget(self.browser)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_no = QPushButton(t("btn_update_later"))
        btn_no.setStyleSheet("QPushButton { background-color: #34495e; color: white; padding: 8px 16px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2c3e50; }")
        btn_no.clicked.connect(self.reject)
        
        btn_yes = QPushButton(t("btn_update_now"))
        btn_yes.setStyleSheet("QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2ecc71; }")
        btn_yes.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_no)
        btn_layout.addWidget(btn_yes)
        layout.addLayout(btn_layout)