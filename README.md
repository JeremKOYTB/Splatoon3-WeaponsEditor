# Splatoon 3 Weapons Editor

A simple tool to edit, compare, and balance Splatoon 3 weapons for fun! It lets you change current game parameters (BGYML) and will soon support "RSDB" Editing.

---

## ⚠️ Critical Warning: Online Safety & Bannable Risks

**READ THIS CAREFULLY BEFORE USING:**

> [!CAUTION]
> * **Offline Use Only:** This tool, and all the files it generates, is strictly for offline use. Any modification to the game files is immediately detected by Nintendo's security systems if the console is connected to servers.
> * **Ban Risk:** Modifying game files will result in a permanent console and/or account ban from Nintendo services.
> * **User Responsibility:** By using this tool, you acknowledge that any resulting ban is entirely your own responsibility. Ensure your console remains offline when using modded files.

## About the Project

The **Splatoon 3 Weapons Editor** is a comprehensive GUI tool designed to manipulate the game's `Params.pack.zs` files.
It simplifies editing weapon parameters, comparing them against reference archives, and extracting assets from a local RomFS dump.

> **Note:** This project is intended for Windows 10 22H2/11. If there are any problems under Linux/macOS, I'm not aware of them.

> **Note 2:** Basic knowledge of Splatoon 3 data structures is recommended.

---

## Key Features

* **BGYML Editor:** View and modify weapon parameters via an intuitive tree-view interface.
* **Archive Comparator:** Compare modified files against a reference archive (Vanilla or modded) to identify changes (Backport/Forward functionality).
* **RomFS Manager** *(optional)*: Extract and automatically convert game textures (BNTX) and files from a local RomFS dump.
* **Caching:** Automatically manages local image caches.
* **Updater:** Integrated system to keep the editor updated.
* **RSDB Editor:** Support coming in future updates.

---

## Prerequisites

1. **Python 3.11 or 3.12:** (required for `oead` library compatibility).
2. **Game Data Files:** Valid `Params.pack.zs` files.
3. **Optional:** ARM ASTC Encoder (automatically downloaded by the script for texture to png).

---

## Installation

1. Download the latest release from the **Releases** page.
2. Extract the contents to your preferred directory.
3. Execute **`Start.bat`**.
4. The script will automatically create a virtual environment (`.venv`) and install all necessary dependencies.

---

## Usage

### Launching

Run `Start.bat` to launch the editor. This script verifies updates and ensures the environment is correctly configured.

### Editing

1. Click **"Open Params.pack.zs"** to load the archive.
2. Select weapons or components in the left panel.
3. Edit values in the properties tree on the right.
4. Click **"Save Repack"** to generate a new ZSTD-compressed Params.pack.zs.

### Comparison

Click **"Compare Params"** and select a reference archive. The tool displays differences line-by-line, allowing for the restoration of specific values or the transfer of modifications between files.

---

## Transparency & Contributions

* **AI Assistance:** This project was developed with the assistance of **Gemini** to translate concepts into functional Python code (but ideas/features come from me).
* **Open Source:** This project is collaborative. Contributions are encouraged to improve robustness and maintainability.
* Use the **Issue** tab [HERE](https://github.com/JeremKOYTB/Splatoon3-WeaponsEditor/issues) to report bugs.
* Submit a **Pull Request** for fixes or feature enhancements.



---

## Credits

* Thanks to [Leanny](https://www.google.com/search?q=https://leanny.github.io/splat3/) for the localization data and file structure research.
* Thanks to the Splatoon modding community/[Switch-Toolbox](https://github.com/KillzXGaming/Switch-Toolbox) for their ongoing research into Nintendo file formats.

---

*Developed by JérémKO.*

*Licensed under the MIT License.*
