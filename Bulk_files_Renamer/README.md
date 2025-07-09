
# 🗂️ Bulk File Renamer (CustomTkinter GUI)

A powerful and user-friendly bulk file renaming tool built with Python and `customtkinter`. Rename hundreds of files in seconds using prefixes, suffixes, find/replace (with optional regex), extension filtering, preview before rename, undo feature, and support for saving/loading presets.

---

## 🚀 Features

* ✅ **GUI Interface** with `customtkinter` (Dark Mode)
* 📝 Add **prefix** and **suffix** to filenames
* 🔁 **Find & Replace** (supports Regex)
* 🎯 **Filter by Extension** (e.g. `.jpg`, `.png`, `.txt`)
* 🔍 **Preview Changes** before renaming
* ⛔ **Collision Detection** (duplicate names, existing files, permission errors)
* ↩️ **Undo Last Rename**
* 💾 **Save & Load Presets** (as `.json`)
* ⚡ Multithreaded for non-blocking operations

---

## 📸 GUI Overview

![Demo GIF](assets/demo.gif)

---

## 🛠️ Installation

1. Install dependencies:

   ```bash
   pip install customtkinter
   ```

2. Run the program:

   ```bash
   python bulk_renamer.py
   ```

---

## 🧠 How It Works

1. Select a folder with files.
2. Apply any combination of:

   * Prefix
   * Suffix
   * Find/Replace (regex optional)
   * Extension filters
3. Click **Preview Changes** to simulate renaming.
4. If all looks good, click **Apply Renames**.
5. Click **Undo Last Rename** if needed.

---

## 💾 Presets

* **Save Preset**: Save current rename config (prefix, suffix, filters, etc.)
* **Load Preset**: Quickly reuse saved configurations.

Presets are stored as JSON files.

---

## 🧱 Example Preset JSON

```json
{
  "prefix": "IMG_",
  "suffix": "_edited",
  "find_text": "screenshot",
  "replace_text": "image",
  "extensions": "jpg,png",
  "use_regex": false
}
```

---

## ⚠️ Safety & Warnings

* Preview changes before applying them.
* Undo works only for the **last operation**.
* The app does **not rename folders**, only files.

---

## 📂 Supported Platforms

* ✅ Windows
* ✅ Linux
* ✅ macOS

> *(Tested with Python 3.10+)*

---

## 📜 License

MIT License. Use, modify, and share freely.

---

## ✨ Credits

Built with ❤️ by \[MubarakSec] using `customtkinter` and Python.

