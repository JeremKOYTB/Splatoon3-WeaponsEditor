import os
import json
import requests
import re
from datetime import datetime
import byml

from utils import log, CACHE_DIR
from translations import t

class SplatoonDataManager:
    def __init__(self):
        self.localization_data = {}

    def is_file_outdated(self, url, local_path):
        try:
            response = requests.head(url, timeout=5)
            remote_last_modified = response.headers.get("Last-Modified")
            if not remote_last_modified: return True
            remote_time = datetime.strptime(remote_last_modified, "%a, %d %b %Y %H:%M:%S %Z").timestamp()
            return remote_time > os.path.getmtime(local_path)
        except Exception as e:
            log(f"[NET] Cannot check headers for '{url}': {e}")
            return False

    def fetch_leanny_localization(self, lang_code):
        log(f"[DB] Fetching language file: {lang_code}.json")
        url = f"https://leanny.github.io/splat3/data/language/{lang_code}.json"
        local_path = os.path.join(CACHE_DIR, f"{lang_code}.json")
        
        needs_dl = True
        if os.path.exists(local_path):
            if not self.is_file_outdated(url, local_path):
                needs_dl = False
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        self.localization_data = json.load(f)
                    log(f"[DB] DB {lang_code} loaded from local cache.")
                except Exception as e:
                    log(f"[DB] Cache read error ({e}), forcing redownload.")
                    needs_dl = True

        if needs_dl:
            log(f"[DB] Downloading {lang_code}.json from Github Pages...")
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                self.localization_data = resp.json()
                log(f"[DB] DB {lang_code} downloaded and secured in cache.")
            except Exception as e:
                log(f"[DB] Network failure downloading language: {e}")

    def _find_json_value(self, key, default):
        for category, items in self.localization_data.items():
            if isinstance(items, dict) and key in items:
                return items[key]
        return default

    def guess_image_and_name(self, internal_name, verbose=False):
        if verbose: log(f"[DATA] Step 1: Processing raw internal name: '{internal_name}'")
        
        if internal_name == "SplPlayer":
            if verbose: log("[DATA] Custom override: SplPlayer detected, deploying Win13.png.")
            return f"{t('raw_data')} (SplPlayer)", "Win13.png", True, "SplPlayer"

        if internal_name == "WeaponFree":
            if verbose: log("[DATA] Custom override: WeaponFree detected, deploying Win_Tricol.png.")
            return f"{t('raw_data')} (WeaponFree)", "Win_Tricol.png", True, "WeaponFree"

        if internal_name == "WeaponSpIkuraShoot":
            if verbose: log("[DATA] Custom override: WeaponSpIkuraShoot detected, deploying SakelienSmall.png.")
            return f"{t('raw_data')} (WeaponSpIkuraShoot)", "SakelienSmall.png", True, "WeaponSpIkuraShoot"

        is_exact = internal_name.startswith("Weapon")
        
        clean_name = internal_name.replace("Weapon", "").replace("Bullet", "").replace("SplPlayer", "")
        raw_name = f"{t('raw_data')} ({internal_name})"
        
        if verbose and clean_name != internal_name:
            log(f"[DATA] Stripped base architecture prefixes. Clean name base: '{clean_name}'")

        if "SalmonBuddy" in internal_name:
            if verbose: log("[DATA] Custom override: SalmonBuddy detected, deploying Wsb_SalmonBuddy00.png.")
            return raw_name, "Wsb_SalmonBuddy00.png", True, "SalmonBuddy"

        modifiers = ["_Coop", "Coop", "BigCoop", "_Mission", "Mission", "_Rival", "Rival", "Hero", "_Msn", "Enemy", "General"]
        
        lv_match = re.search(r'(_Lv\d+)', clean_name)
        if lv_match:
            if verbose: log(f"[DATA] Story Mode level modifier detected and stripped: '{lv_match.group(1)}'")
            clean_name = clean_name.replace(lv_match.group(1), "")
        
        for mod in modifiers:
            if mod in clean_name:
                clean_name = clean_name.replace(mod, "")
                if verbose: log(f"[DATA] Stripped mode modifier: '{mod}'")
            
        if not is_exact:
            if clean_name.startswith("Splash") and not clean_name.startswith("SplashWall"):
                clean_name = clean_name[6:]
                if verbose: log("[DATA] Stripped 'Splash' component prefix.")
            if clean_name.startswith("Blast") and not clean_name.startswith("Blaster"):
                clean_name = clean_name[5:]
                if verbose: log("[DATA] Stripped 'Blast' component prefix.")
        
        for art in ["Hit", "Drop", "Area", "Nearest", "Scatter", "Spiral", "Explosion"]:
            if clean_name.endswith(art):
                clean_name = clean_name[:-len(art)]
                if verbose: log(f"[DATA] Stripped projectile interaction suffix: '{art}'")

        img_filename = "Dummy.png"
        json_key = clean_name
        
        sp_list = [
            "SpBlower", "SpCastle", "SpChariot", "SpChimney", "SpEnergyStand", 
            "SpFirework", "SpGachihoko", "SpGreatBarrier", "SpHyperPresser", 
            "SpIkuraShoot", "SpInkStorm", "SpJetpack", "SpMicroLaser", "SpMultiMissile", 
            "SpNiceBall", "SpPogo", "SpShockSonar", "SpSkewer", "SpSuperHook", 
            "SpSuperLanding", "SpTripleTornado", "SpUltraShot", "SpUltraStamp"
        ]
        
        is_sp = False
        for sp in sp_list:
            if clean_name.startswith(sp):
                if verbose: log(f"[DATA] Classified as Special Attack. Match found: '{sp}'")
                if sp == "SpGachihoko":
                    img_filename = "Wsp_Shachihoko.png"
                else:
                    img_filename = f"Wsp_{sp}00.png"
                json_key = sp
                if clean_name != sp: is_exact = False 
                is_sp = True
                break
                
        if is_sp:
            if verbose and not is_exact: log("[DATA] Target marked as Component/Projectile (is_exact=False).")
            if verbose: log(f"[DATA] Final designated icon: '{img_filename}'")
            return raw_name, img_filename, is_exact, json_key

        subs_list = [
            "BombCurling", "BombFizzy", "BombQuick", "BombRobot", "BombSplash", 
            "BombSuction", "BombTorpedo", "LineMarker", "PointSensor", "PoisonMist", 
            "Sprinkler", "Shield", "Trap", "Beacon", "SplashWall", "TimerTrap"
        ]
        
        is_sub = False
        for sub in subs_list:
            if clean_name.startswith(sub):
                if verbose: log(f"[DATA] Classified as Sub Weapon. Match found: '{sub}'")
                if sub.startswith("Bomb") and sub != "Bomb":
                    sub_formatted = sub.replace("Bomb", "Bomb_")
                else:
                    sub_formatted = sub
                    
                img_filename = f"Wsb_{sub_formatted}00.png"
                json_key = sub_formatted
                if clean_name != sub: is_exact = False
                is_sub = True
                break
                
        if is_sub:
            if verbose and not is_exact: log("[DATA] Target marked as Component/Projectile (is_exact=False).")
            if verbose: log(f"[DATA] Final designated icon: '{img_filename}'")
            return raw_name, img_filename, is_exact, json_key

        classes = ["Blaster", "Brush", "Charger", "Maneuver", "Roller", "Saber", "Shelter", "Shooter", "Slosher", "Spinner", "Stringer"]
        
        for c in classes:
            if clean_name.startswith(c):
                if verbose: log(f"[DATA] Classified as Main Weapon Class. Match found: '{c}'")
                suffix = clean_name[len(c):]
                
                components = ["Ink", "Body", "Canopy", "Shot", "Parent", "Matoi", "Tenjin", "Spawner", "Tcl"]
                for proj in components:
                    if proj in suffix:
                        if verbose: log(f"[DATA] Sub-component architecture detected: '{proj}'. Marking is_exact=False.")
                        suffix = suffix.replace(proj, "")
                        is_exact = False
                        
                if suffix == "Bear":
                    img_filename = f"Path_Wst_{c}_Bear.png"
                    json_key = f"{c}_Bear_Coop" if "Coop" in internal_name else f"{c}_Bear"
                else:
                    if not suffix or suffix == "Base":
                        suffix = "Normal"
                        is_exact = False 
                    img_filename = f"Wst_{c}_{suffix}_00.png"
                    json_key = f"{c}_{suffix}_00"
                break
                
        if verbose and not is_exact and not (is_sp or is_sub): 
            log("[DATA] Target marked as Component/Projectile (is_exact=False).")
        if verbose: 
            log(f"[DATA] Final designated icon: '{img_filename}'")
            
        return raw_name, img_filename, is_exact, json_key

    def get_exact_translation(self, internal_name, json_key, verbose=False):
        if internal_name == "SplPlayer":
            if verbose: log("[DATA] Hardcoded translation override for SplPlayer.")
            return "Player"

        if internal_name == "WeaponFree":
            if verbose: log("[DATA] Hardcoded translation override for WeaponFree.")
            return t("name_unarmed")

        if internal_name == "WeaponSpIkuraShoot":
            if verbose: log("[DATA] Hardcoded translation override for WeaponSpIkuraShoot.")
            return t("name_ikurashoot")

        if verbose: log(f"[DATA] Step 2: Searching translation dictionaries for root key: '{json_key}'")
        clean_name = internal_name.replace("Weapon_", "")
        
        base_keys = [
            json_key.rstrip("0123456789_"), 
            internal_name,
            clean_name
        ]
        if "Bomb_" in json_key:
            base_keys.append(json_key.replace("Bomb_", "Bomb").rstrip("0123456789_"))
            
        categories = [
            "CommonMsg/Weapon/WeaponName_Main",
            "CommonMsg/Weapon/WeaponName_Sub",
            "CommonMsg/Weapon/WeaponName_Special"
        ]
        
        is_special_mode = any(m in internal_name for m in ["Coop", "Mission", "Rival", "Hero", "_Msn", "Lv"])
        if verbose and is_special_mode:
            log(f"[DATA] Story/Coop Mode detected. Translation engine will restrict sub-variant scanning.")
        
        found_names = []
        for cat in categories:
            if cat in self.localization_data:
                dict_cat = self.localization_data[cat]
                for bk in base_keys:
                    pattern = re.compile(rf"^{re.escape(bk)}(_\d{{2}})?$")
                    for key, val in dict_cat.items():
                        if pattern.match(key):
                            if is_special_mode:
                                if key == f"{bk}_00" or key == bk:
                                    if val not in found_names:
                                        if verbose: log(f"[DATA] Locked base translation found: '{val}' (Key: {key})")
                                        found_names.append(val)
                            else:
                                if val not in found_names:
                                    if verbose: log(f"[DATA] Variant translation appended: '{val}' (Key: {key})")
                                    found_names.append(val)
            if found_names:
                break
                
        if not found_names:
            if verbose: log(f"[DATA] Warning: No translation matches found in JSON database for {json_key}.")
            return None

        final_name = " / ".join(found_names)

        suffix_tag = ""
        if "Coop" in internal_name:
            tag = self._find_json_value("Coop", t("tag_coop"))
            suffix_tag = f" ({tag})"
            if verbose: log(f"[DATA] Coop tag generated: '{tag}'")
        elif any(m in internal_name for m in ["Mission", "Rival", "Hero", "_Msn", "Lv"]) or "SalmonBuddy" in internal_name:
            tag = self._find_json_value("ModeMission", t("tag_hero"))
            
            lv_match = re.search(r'Lv(\d+)', internal_name)
            if lv_match:
                tag += f" Lv{lv_match.group(1)}"
                if verbose: log(f"[DATA] Story Mode Level appended: Lv{lv_match.group(1)}")
                
            suffix_tag = f" ({tag})"
            if verbose: log(f"[DATA] Story Mode tag generated: '{tag}'")
            
        return final_name + suffix_tag

def truncate_str(val):
    s = str(val)
    return s if len(s) < 100 else s[:97] + "..."

def get_python_value(node):
    return node.value if hasattr(node, 'value') else node

def compare_dicts(dict_old, dict_new, path="", path_tuple=()):
    diffs = []
    if isinstance(dict_old, dict) and isinstance(dict_new, dict):
        all_keys = set(dict_old.keys()).union(set(dict_new.keys()))
        for k in all_keys:
            new_path = f"{path}/{k}" if path else str(k)
            new_tuple = path_tuple + (k,)
            if k not in dict_old:
                diffs.append((new_path, truncate_str(get_python_value(dict_new[k])), t("diff_missing"), new_tuple))
            elif k not in dict_new:
                diffs.append((new_path, t("diff_deleted"), truncate_str(get_python_value(dict_old[k])), new_tuple))
            else:
                diffs.extend(compare_dicts(dict_old[k], dict_new[k], new_path, new_tuple))
                
    elif isinstance(dict_old, list) and isinstance(dict_new, list):
        if len(dict_old) != len(dict_new):
            diffs.append((path, f"Size: {len(dict_new)}", f"Size: {len(dict_old)}", path_tuple))
        else:
            for i in range(len(dict_old)):
                new_path = f"{path}[{i}]"
                new_tuple = path_tuple + (i,)
                diffs.extend(compare_dicts(dict_old[i], dict_new[i], new_path, new_tuple))
    else:
        v_old = get_python_value(dict_old)
        v_new = get_python_value(dict_new)
        
        if v_old != v_new:
            diffs.append((path, v_new, v_old, path_tuple))
            
    return diffs

def parse_node(node):
    if isinstance(node, dict):
        return {k: parse_node(v) for k, v in node.items()}
    elif isinstance(node, list):
        return [parse_node(v) for v in node]
    else:
        return node