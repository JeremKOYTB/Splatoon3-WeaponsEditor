import os
import zstandard as zstd
import oead
import subprocess
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QThread, pyqtSignal

from utils import log, CACHE_DIR
from translations import t

try:
    from bntx_decoder import process_bntx
except ImportError:
    log("⚠️ [SYSTEM] Le module bntx_decoder.py est introuvable. Assurez-vous qu'il est present.")

class RomFSBuilderWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, romfs_path, data_manager=None):
        super().__init__()
        self.romfs_path = romfs_path
        self.data_manager = data_manager
        self.extracted_count = 0
        self.converter_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astcenc.exe")
        
        self.exclusions = {
            "manual", "zakkapreview", "catalog", "mngcard", "badge", 
            "npl", "news", "stagebanner", "bgmimage", "gear", "stagel", 
            "mngsleevel", "npc"
        }

    def run(self):
        log(f"[ROMFS] Analyse dynamique et sans restriction de l'arborescence : {self.romfs_path}")
        
        required_icons = set()
        pack_path = None
        
        if self.data_manager:
            for root, dirs, files in os.walk(self.romfs_path):
                if "Params.pack.zs" in files:
                    pack_path = os.path.join(root, "Params.pack.zs")
                    break
                    
            if pack_path:
                log(f"[ROMFS] Params.pack.zs detecte ({pack_path}). Generation de la liste stricte...")
                try:
                    with open(pack_path, "rb") as f:
                        compressed_data = f.read()
                    dctx = zstd.ZstdDecompressor()
                    decompressed_sarc_data = dctx.decompress(compressed_data)
                    sarc = oead.Sarc(decompressed_sarc_data)
                    
                    for file in sarc.get_files():
                        if file.name.endswith(".bgyml"):
                            internal_name = file.name.split('/')[-1].split('.')[0]
                            _, img_filename, _, _ = self.data_manager.guess_image_and_name(internal_name)
                            required_icons.add(img_filename.replace(".png", "").lower())
                                
                    log(f"[ROMFS] {len(required_icons)} icones identifiees par le Params.pack.")
                    required_icons.add("dummy")
                except Exception as e:
                    log(f"[ROMFS] Erreur analyse Params.pack : {e}")

        files_to_process = []

        for root, dirs, files in os.walk(self.romfs_path):
            dirs[:] = [d for d in dirs if d.lower() not in self.exclusions]
            
            root_lower = root.lower().replace("\\", "/")
            
            for f in files:
                f_lower = f.lower()
                
                if f_lower.endswith(".szs") and "mals" in root_lower:
                    files_to_process.append((os.path.join(root, f), "szs"))
                    
                elif (f_lower.endswith(".bntx") or f_lower.endswith(".bntx.zs")) and "ui" in root_lower and "icon" in root_lower:
                    base_bntx = f_lower.replace(".bntx.zs", "").replace(".bntx", "")
                    
                    leanny_name = base_bntx
                    if leanny_name.startswith("wst_") and "_bear" in leanny_name:
                        leanny_name = f"path_{leanny_name.replace('_00', '')}"
                    elif leanny_name == "splplayer":
                        leanny_name = "win13"
                        
                    if required_icons and leanny_name not in required_icons and base_bntx not in required_icons:
                        continue
                        
                    files_to_process.append((os.path.join(root, f), "bntx"))

        total_files = len(files_to_process)
        if total_files == 0:
            log("[ROMFS] Aucun fichier cible n'a ete trouve apres le filtrage.")
            self.finished.emit(False, t("msg_romfs_empty"))
            return

        log(f"[ROMFS] {total_files} fichiers cibles valides retenus. Initialisation du traitement multithread (8 instances)...")

        completed = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for file_path, f_type in files_to_process:
                if f_type == "szs":
                    futures.append(executor.submit(self._extract_szs, file_path))
                else:
                    futures.append(executor.submit(self._process_bntx, file_path))
                    
            for future in futures:
                try:
                    filename = future.result()
                    completed += 1
                    if filename:
                        self.progress.emit(completed, total_files, filename)
                except Exception as e:
                    completed += 1
                    log(f"[ROMFS] Erreur dans le pipeline parallele : {e}")

        self.progress.emit(total_files, total_files, t("cache_done"))
        self.finished.emit(True, t("msg_romfs_success", self.extracted_count))

    def _extract_szs(self, file_path):
        filename = os.path.basename(file_path)
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            decompressed_data = oead.yaz0.decompress(data) if data.startswith(b"Yaz0") else data
            sarc = oead.Sarc(decompressed_data)
            for file in sarc.get_files():
                if file.name.endswith(".msbt"):
                    out_path = os.path.join(CACHE_DIR, os.path.basename(file.name))
                    with open(out_path, "wb") as out_f:
                        out_f.write(bytes(file.data))
                    self.extracted_count += 1
            return filename
        except Exception as e:
            log(f"[ROMFS] Erreur archive SZS {filename} : {e}")
            return filename

    def _process_bntx(self, file_path):
        filename = os.path.basename(file_path)
        target_texture_name = filename.replace(".bntx.zs", "").replace(".bntx", "").replace(".BNTX", "")
        
        if target_texture_name.startswith("Wst_") and "_Bear" in target_texture_name:
            target_texture_name = f"Path_{target_texture_name.replace('_00', '')}"
        elif target_texture_name == "SplPlayer":
            target_texture_name = "Win13"
            
        if target_texture_name.startswith("Wsp_") or target_texture_name.startswith("Wsb_"):
            return filename

        png_path = os.path.join(CACHE_DIR, f"{target_texture_name}.png")
        if os.path.exists(png_path) and target_texture_name.lower() != "dummy":
            return filename

        try:
            with open(file_path, "rb") as f:
                data = f.read()
                
            if file_path.lower().endswith(".zs"):
                dctx = zstd.ZstdDecompressor()
                bntx_data = dctx.decompress(data)
            else:
                bntx_data = data
                
            result = process_bntx(bntx_data, "*")
            
            if result:
                out_data, ext = result
                temp_extracted_path = os.path.join(CACHE_DIR, f"{target_texture_name}.{ext}")
                
                with open(temp_extracted_path, "wb") as f:
                    f.write(out_data)
                
                if ext == "astc" and os.path.exists(self.converter_exe):
                    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        
                    process = subprocess.run(
                        [self.converter_exe, "-dl", temp_extracted_path, png_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        creationflags=creationflags
                    )
                    
                    if process.returncode == 0 and os.path.exists(png_path):
                        self.extracted_count += 1
                        os.remove(temp_extracted_path)
                    else:
                        error_msg = process.stderr.decode('utf-8', 'ignore') if process.stderr else "Inconnue"
                        log(f"[ROMFS] Echec astcenc pour {target_texture_name}: {error_msg}")
                        self.extracted_count += 1
                else:
                    self.extracted_count += 1
            else:
                out_path = os.path.join(CACHE_DIR, filename.replace(".zs", ""))
                with open(out_path, "wb") as f:
                    f.write(bntx_data)
                self.extracted_count += 1
            return filename
        except Exception as e:
            log(f"[ROMFS] Erreur decodeur BNTX {filename} : {e}")
            return filename