import os
import sys
import subprocess
import requests
import zipfile
import io

from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog, QTableWidgetItem
from PyQt6.QtGui import QPixmap, QColor, QBrush, QIcon, QImage, QPainter
from PyQt6.QtCore import Qt, QTimer

from utils import log, CACHE_DIR, get_last_dir, set_last_dir, save_favorites
from translations import t
from tree_handler import TreeHandler
from engine import SplatoonPackManager
from components import DiffDialog, CacheDialog, CacheBuilderWorker, ImageManager
from splatoon_data import compare_dicts, parse_node
from romfs_builder import RomFSBuilderWorker

class EditorFeaturesMixin:

    def perform_comparison(self):
        if not self.pack_manager.pack_path:
            QMessageBox.warning(self, t("warn_title"), t("msg_err_main_first"))
            return
            
        start_dir = get_last_dir()
        path, _ = QFileDialog.getOpenFileName(self, t("msg_open_ref"), start_dir, "Archives (*.pack.zs *.zs)")
        if not path: return

        if self.current_byml_name:
            self.pack_manager.byml_files[self.current_byml_name] = TreeHandler.build_dict(self.tree_w.invisibleRootItem())

        ref_pack = SplatoonPackManager()
        self.name_lbl.setText(t("msg_analyzing"))
        QApplication.processEvents()

        success, msg = ref_pack.load_pack(path)
        if not success:
            QMessageBox.critical(self, t("err_title"), f"{msg}")
            if self.current_byml_name: self.refresh_weapon_ui(self.current_byml_name)
            return

        diff_results = {}
        all_files = set(self.pack_manager.byml_files.keys()).union(set(ref_pack.byml_files.keys()))
        
        for fname in all_files:
            if fname not in ref_pack.byml_files:
                diff_results[fname] = [("File", "N/A", "Added", ())]
            elif fname not in self.pack_manager.byml_files:
                diff_results[fname] = [("File", "Existed", "Deleted", ())]
            else:
                dict_current = parse_node(self.pack_manager.byml_files[fname])
                dict_ref = parse_node(ref_pack.byml_files[fname])
                
                diffs = compare_dicts(dict_ref, dict_current)
                if diffs:
                    diff_results[fname] = diffs

        if self.current_byml_name: 
            self.refresh_weapon_ui(self.current_byml_name) 
        else: 
            self.name_lbl.setText(t("msg_compare_done"))
        
        if not any(diff_results.values()):
            QMessageBox.information(self, t("compare_title"), t("msg_identical"))
        else:
            dialog = DiffDialog(diff_results, ref_pack, self)
            if self.chk_auto_expand.isChecked():
                dialog.tree.expandAll()
            dialog.exec()

    def refresh_file_list(self):
        if not self.pack_manager.sarc: return
        self.is_refreshing = True
        self.table_w.clearContents()
        self.table_w.clearSpans()

        total_byml = len(self.pack_manager.byml_files)
        all_files = list(self.pack_manager.byml_files.keys())
        
        f_data = self.combo_filter.currentData()
        hide_dummies = self.chk_hide_dummy.isChecked()
        hide_filenames = self.chk_hide_filenames.isChecked()
        search_text = self.search_bar.text().lower()
        
        filtered_files = []
        hidden_by_dummy_count = 0
        
        for path in all_files:
            internal_name = path.split('/')[-1].split('.')[0]
            _, img_filename, _, json_key = self.data_manager.guess_image_and_name(internal_name)
            loc_name = self.data_manager.get_exact_translation(internal_name, json_key)
            
            if search_text:
                search_target = internal_name.lower()
                if loc_name:
                    search_target += " " + loc_name.lower()
                if search_text not in search_target:
                    continue

            if f_data == "all": 
                pass
            elif f_data == "dummy": 
                is_dummy = img_filename in self.known_dummies
                if not is_dummy: continue
            elif internal_name in ["SplPlayer", "WeaponFree"]:
                pass
            elif f_data == "Hero":
                if not (any(m in path for m in ["Mission", "Rival", "Hero", "_Msn", "Lv"]) or "SalmonBuddy" in path or "SpIkuraShoot" in path):
                    continue
            elif f_data == "Coop":
                if "Coop" not in path:
                    continue
            elif f_data == "WeaponSp":
                if not (("WeaponSp" in path and "WeaponSpinner" not in path) or "IkuraShoot" in path):
                    continue
            elif f_data and f_data not in path: 
                continue

            is_dummy = img_filename in self.known_dummies
            if hide_dummies and is_dummy:
                hidden_by_dummy_count += 1
                continue
                
            filtered_files.append(path)

        if len(filtered_files) == 0:
            self.table_w.setRowCount(1)
            item = QTableWidgetItem()
            if hidden_by_dummy_count > 0:
                item.setText(t("msg_hidden_by_dummy"))
            else:
                item.setText(t("msg_no_results"))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            
            self.table_w.setSpan(0, 0, 1, 2)
            self.table_w.setItem(0, 0, item)
            
            self.count_lbl.setText(t("count_info", total_byml, 0, 0, 0))
            self.is_refreshing = False
            return

        filtered_files.sort(key=lambda x: os.path.basename(x).lower())
        filtered_files.sort(key=lambda x: x not in self.favorites)

        displayed_count = len(filtered_files)
        self.table_w.setRowCount(displayed_count)
        
        for row, path in enumerate(filtered_files):
            basename = os.path.basename(path)
            internal_name = basename.split('.')[0]
            
            _, img_filename, _, json_key = self.data_manager.guess_image_and_name(internal_name)
            loc_name = self.data_manager.get_exact_translation(internal_name, json_key)
            
            display_name = basename
            if loc_name:
                if hide_filenames:
                    display_name = loc_name
                else:
                    display_name = f"{basename} ({loc_name})"

            star_item = QTableWidgetItem("★" if path in self.favorites else "☆")
            star_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            star_color = QColor("#f1c40f") if path in self.favorites else QColor("#cccccc")
            star_item.setForeground(QBrush(star_color))

            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.ItemDataRole.UserRole, path)
            name_item.setToolTip(path)
            
            icon_path = os.path.join(CACHE_DIR, img_filename)
            if not os.path.exists(icon_path):
                icon_path = os.path.join(CACHE_DIR, "Dummy.png")
                
            if os.path.exists(icon_path):
                img = QImage(icon_path)
                if not img.isNull():
                    scaled = img.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    square = QImage(28, 28, QImage.Format.Format_ARGB32_Premultiplied)
                    square.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(square)
                    x = (28 - scaled.width()) // 2
                    y = (28 - scaled.height()) // 2
                    painter.drawImage(x, y, scaled)
                    painter.end()
                    
                    name_item.setIcon(QIcon(QPixmap.fromImage(square)))

            self.table_w.setItem(row, 0, star_item)
            self.table_w.setItem(row, 1, name_item)

        self.count_lbl.setText(t("count_info", total_byml, displayed_count, 0, displayed_count))
        self.is_refreshing = False

    def load_pack(self, path=None):
        if not path:
            start_dir = get_last_dir()
            path, _ = QFileDialog.getOpenFileName(self, t("btn_open"), start_dir, "Archives (*.pack.zs *.zs)")
            if not path: 
                return

        set_last_dir(path)
        self.name_lbl.setText(t("lbl_extracting"))
        QApplication.processEvents()

        success, msg = self.pack_manager.load_pack(path)
        if success:
            self.name_lbl.setText(t("lbl_archive_loaded"))
            self.start_global_cache()
        else:
            QMessageBox.critical(self, t("err_title"), msg)

    def import_local_romfs(self):
        converter_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astcenc.exe")
        
        if not os.path.exists(converter_exe) and os.name == 'nt':
            reply = QMessageBox.question(
                self, 
                t("warn_title"), 
                t("msg_ask_download_astc"), 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.prog_container.setVisible(True)
                self.progress_bar.setMaximum(0)
                self.progress_lbl.setText("Téléchargement de astc-encoder depuis GitHub...")
                QApplication.processEvents()
                
                success = self.download_astc_encoder(converter_exe)
                
                self.progress_bar.setMaximum(100)
                if not success:
                    QMessageBox.warning(self, t("err_title"), "Le téléchargement a échoué. Les images BNTX ne seront pas converties en PNG.")
                    self.prog_container.setVisible(False)
            else:
                QMessageBox.information(self, t("warn_title"), "L'outil n'a pas été téléchargé. Les fichiers BNTX bruts seront copiés au lieu d'être convertis en PNG.")

        start_dir = get_last_dir()
        romfs_folder = QFileDialog.getExistingDirectory(self, t("msg_select_romfs"), start_dir)
        
        if not romfs_folder:
            self.prog_container.setVisible(False)
            return

        set_last_dir(romfs_folder)
        
        self.prog_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_lbl.setText(t("lbl_extracting"))
        
        self.romfs_worker = RomFSBuilderWorker(romfs_folder, self.data_manager)
        self.romfs_worker.progress.connect(self.update_romfs_progress)
        self.romfs_worker.finished.connect(self.on_romfs_finished)
        self.romfs_worker.start()

    def download_astc_encoder(self, exe_path):
        api_url = "https://api.github.com/repos/ARM-software/astc-encoder/releases/latest"
        try:
            api_response = requests.get(api_url, timeout=10)
            api_response.raise_for_status()
            release_data = api_response.json()
            
            download_url = None
            for asset in release_data.get("assets", []):
                name = asset.get("name", "").lower()
                if "windows" in name and "x64" in name and name.endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break
                    
            if not download_url:
                return False
                
            zip_response = requests.get(download_url, timeout=15)
            zip_response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
                target_filename = None
                for file_info in z.infolist():
                    if file_info.filename.endswith("avx2.exe"):
                        target_filename = file_info.filename
                        break
                
                if not target_filename:
                    for file_info in z.infolist():
                        if file_info.filename.endswith("sse4.1.exe"):
                            target_filename = file_info.filename
                            break
                            
                if target_filename:
                    with z.open(target_filename) as source, open(exe_path, "wb") as target:
                        target.write(source.read())
                    return True
                else:
                    return False
        except Exception as e:
            log(f"[NET] Erreur de téléchargement ASTC : {e}")
            return False

    def update_romfs_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_lbl.setText(f"Extraction : {filename}")

    def on_romfs_finished(self, success, message):
        if success:
            QMessageBox.information(self, t("success_title"), message)
            self.progress_lbl.setText(t("cache_done"))
            
            auto_pack_path = None
            for root, dirs, files in os.walk(self.romfs_worker.romfs_path):
                if "Params.pack.zs" in files:
                    auto_pack_path = os.path.join(root, "Params.pack.zs")
                    break
                    
            if auto_pack_path:
                log(f"[ROMFS] Target identifiée : {auto_pack_path}. Lancement de l'ouverture...")
                self.load_pack(auto_pack_path)
        else:
            QMessageBox.warning(self, t("warn_title"), message)
            self.progress_lbl.setText("Erreur d'extraction")
            
        QTimer.singleShot(4000, self.hide_progress_ui)

    def start_global_cache(self):
        log("[CACHE] Initiating deep image cache check. Identifying missing or corrupted icons.")
        expected_images = set()
        for file_name in self.pack_manager.byml_files.keys():
            internal_name = file_name.split('/')[-1].split('.')[0]
            _, img_filename, _, _ = self.data_manager.guess_image_and_name(internal_name)
            expected_images.add(img_filename)

        missing_images = set()
        for img in expected_images:
            path = os.path.join(CACHE_DIR, img)
            if not os.path.exists(path):
                missing_images.add(img)
            else:
                if os.path.getsize(path) == 0:
                    log(f"[CACHE] Corrupted file detected (0 bytes): {img}")
                    missing_images.add(img)

        if missing_images:
            existing_pngs = [f for f in os.listdir(CACHE_DIR) if f.endswith('.png') and f != "Dummy.png"]
            is_first_run = len(existing_pngs) == 0

            self.cache_worker = CacheBuilderWorker(missing_images)
            self.cache_worker.progress.connect(self.update_cache_progress)
            self.cache_worker.finished.connect(self.on_cache_finished)

            if is_first_run:
                self.cache_dialog = CacheDialog(self)
                self.cache_dialog.progress.setMaximum(len(missing_images))
                self.cache_dialog.show()
            else:
                self.prog_container.setVisible(True)
                self.progress_bar.setMaximum(len(missing_images))
                self.progress_bar.setValue(0)
                self.progress_lbl.setText(t("cache_bg"))
                self.refresh_file_list()

            self.cache_worker.start()
        else:
            log("[CACHE] All required images are fully present and healthy in the local cache directory.")
            self.refresh_file_list()

    def update_cache_progress(self, completed, total):
        if hasattr(self, 'cache_dialog') and self.cache_dialog.isVisible():
            self.cache_dialog.progress.setValue(completed)
        else:
            self.progress_bar.setValue(completed)

    def on_cache_finished(self, new_dummies):
        self.known_dummies.update(new_dummies)
        
        self.has_actual_dummies = False
        for file_name in self.pack_manager.byml_files.keys():
            internal_name = file_name.split('/')[-1].split('.')[0]
            _, img_filename, _, _ = self.data_manager.guess_image_and_name(internal_name)
            if img_filename in self.known_dummies:
                self.has_actual_dummies = True
                break
                
        self.update_dummy_filter_visibility()
        
        if hasattr(self, 'cache_dialog') and self.cache_dialog.isVisible():
            self.cache_dialog.setWindowFlags(Qt.WindowType.Dialog)
            self.cache_dialog.accept()
        else:
            self.progress_lbl.setText(t("cache_done"))
            QTimer.singleShot(1500, self.hide_progress_ui)
            
        self.refresh_file_list()

    def hide_progress_ui(self):
        self.prog_container.setVisible(False)

    def refresh_weapon_ui(self, file_name):
        internal_name = file_name.split('/')[-1].split('.')[0]
        log(f"\n========================================")
        log(f"[UI] Object selected. Beginning deep analysis for: {internal_name}")
        
        raw_name, img_filename, is_exact, json_key = self.data_manager.guess_image_and_name(internal_name, verbose=True)
        loc_name = self.data_manager.get_exact_translation(internal_name, json_key, verbose=True)
        
        html_text = f"<b><span style='font-size: 14pt;'>{t('raw_data')}<br>({internal_name})</span></b><br>"
        
        if loc_name:
            html_text += f"<span style='font-size: 12pt; color: #2ecc71; font-weight: bold;'>{loc_name}</span><br>"
        else:
            html_text += "<span style='font-size: 12pt;'>&nbsp;</span><br>"
            
        if not is_exact:
            html_text += f"<span style='font-size: 10pt; color: #ff9f43;'>{t('warn_projectile')}</span>"
        else:
            html_text += "<span style='font-size: 10pt;'>&nbsp;</span>"
            
        self.name_lbl.setText(html_text)

        self._thread_pool = [t for t in self._thread_pool if t.isRunning()]
        
        if hasattr(self, 'image_manager') and self.image_manager.isRunning():
            try:
                self.image_manager.finished.disconnect()
            except TypeError:
                pass
            self._thread_pool.append(self.image_manager)

        icon_path = os.path.join(CACHE_DIR, img_filename)
        if not os.path.exists(icon_path):
            icon_path = os.path.join(CACHE_DIR, "Dummy.png")
            
        if os.path.exists(icon_path):
            log(f"[UI] Valid icon mapping established with local cache file: {os.path.basename(icon_path)}")
        else:
            log(f"[UI] CRITICAL: Computed icon '{img_filename}' AND fallback 'Dummy.png' are missing from local cache directory.")

        self.image_manager = ImageManager(os.path.basename(icon_path))
        self.image_manager.finished.connect(self.on_image_downloaded)
        self.image_manager.start()

    def save_pack(self):
        if not self.pack_manager.pack_path: 
            return

        if self.current_byml_name:
            new_dict = TreeHandler.build_dict(self.tree_w.invisibleRootItem())
            self.pack_manager.byml_files[self.current_byml_name] = new_dict

        if hasattr(self.pack_manager, 'deleted_files'):
            try:
                if hasattr(self.pack_manager, 'sarc') and hasattr(self.pack_manager.sarc, 'files'):
                    if isinstance(self.pack_manager.sarc.files, dict):
                        for df in self.pack_manager.deleted_files:
                            if df in self.pack_manager.sarc.files:
                                del self.pack_manager.sarc.files[df]
            except Exception: pass

        base_dir = os.path.dirname(self.pack_manager.pack_path)

        suggested_path = os.path.join(base_dir, "Params.pack.zs")

        path, _ = QFileDialog.getSaveFileName(
            self, 
            t("msg_save_title"), 
            suggested_path, 
            "ZSTD (*.zs)" 
        )
        
        if path:
            selected_dir = os.path.dirname(path)
            final_path = os.path.join(selected_dir, "Params.pack.zs")
            set_last_dir(final_path)
            QApplication.processEvents()
            s, msg = self.pack_manager.save_pack(final_path)
            if s:
                self.pack_manager.pack_path = final_path
                QMessageBox.information(self, t("success_title"), t("msg_save_success"))
            else:
                QMessageBox.critical(self, t("err_title"), msg)