# Age of Reforging: The Freelands - Save Game Editor
![Version](https://img.shields.io/badge/version-4.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**A comprehensive save game editor for Age of Reforging: The Freelands**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing)


---

##  About

This is a **community-driven save game editor** for *Age of Reforging: The Freelands*. It allows players to view, edit, and manage their save files with an intuitive graphical interface. Built with Python and PySide6, it features automatic item discovery, character stat editing, inventory management, and real-time change logging.

###  Why This Exists

Save editing for this game was previously done through manual JSON editing. This tool makes it **accessible to all players** with:
- ✅ No manual JSON editing required
- ✅ Automatic item ID discovery and naming
- ✅ Real-time change logging (terminal-style console)
- ✅ Safe backup system before every save
- ✅ Open source for community contributions

---
<div align="center">
<img width="1756" height="1164" alt="image" src="https://github.com/user-attachments/assets/2ed28339-93ae-43b0-a8b4-6c88242001b4" />
</div>
   ##  Features

| Feature | Description |
|---------|-------------|
|  **Auto Save Detection** | Automatically finds all save slots from AppData |
|  **Character Editor** | Edit all character stats, skills, vitals, and more |
|  *Inventory Management** | View and edit items with ID-to-name lookup |
|  **Item Database** | Auto-discovers items from saves, community-expandable |
|  **Terminal Console** | Real-time logging of all changes made |
|  **Auto Backup** | Creates timestamped backups before every save |
|  **Quick Cheats** | One-click buttons for common modifications |
|  **Raw JSON Editor** | Advanced users can edit raw save data |
|  **Export/Import** | Export item database to CSV for sharing |
|  **Dark Theme** | Easy on the eyes for long editing sessions |

---


## 📦 Installation

### Requirements

- **Python 3.8 or higher**
- **Windows 10/11** (save path is Windows-specific)
- **Age of Reforging: The Freelands** (installed via Steam)

### Quick Install

```bash
# 1. Clone the repository
git clone https://github.com/Vilonauzd/reforge-save-editor.git
cd reforge-save-editor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the editor
python reforge_gameEditor.py
```

### Dependencies

```txt
PySide6>=6.5.0
```

---

##  Usage

### First Launch

1. **Run the editor**: `python reforge_gameEditor.py`
2. **Select a save slot** from the dropdown (auto-detected)
3. **Select a character** from the left panel tree
4. **Edit stats** in the tabs on the right
5. **Click "Save Changes"** when done

### Terminal Console

The top section shows a **live log** of all actions:
- 🟢 **Green** = Success operations
- 🟡 **Yellow** = Warnings
- 🔴 **Red** = Errors
- 🔵 **Cyan** = Info messages
- 🟣 **Magenta** = Value changes

### Item Database

Items are **auto-discovered** from your saves. To name unknown items:

1. Go to **Item Database** tab
2. Find an "Unknown Item XXXX"
3. Click **"Rename Selected"**
4. Enter the actual item name from in-game
5. **Saved permanently** for all future sessions

### Quick Cheats

Navigate to the **Quick Cheats** tab for one-click modifications:
- Set Gold to 999,999
- Max All Attributes (100)
- Max All Skills (100)
- Max Arena Prestige

---

## 📁 File Structure

```
reforge-save-editor/
├── reforge_gameEditor.py      # Main editor application
├── requirements.txt            # Python dependencies
├── item_database.json          # Auto-created item name database
├── README.md                   # This file
├── LICENSE                     # MIT License
├── backups/                    # Auto-created save backups
│   └── sav.dat.backup_TIMESTAMP
└── screenshots/                # Screenshots for documentation
```

### Save File Location

```
C:\Users\<USERNAME>\AppData\LocalLow\PersonaeGames\Age of Reforging The Freelands\Save\Sol\SaveData\
```

---

##  Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

| Contribution Type | How to Help |
|------------------|-------------|
|  **Item Names** | Play the game, note item IDs, submit to database |
|  **Bug Reports** | Open issues with steps to reproduce |
|  **Feature Requests** | Suggest new features via GitHub Issues |
|  **Code Contributions** | Submit pull requests with improvements |
|  **Documentation** | Improve README, add tutorials, fix typos |
|  **Translations** | Help translate the editor to other languages |

### Item Database Contribution

The item database (`item_database.json`) is community-maintained. To contribute:

1. **Find an item ID** in-game (use the editor to view your inventory)
2. **Note the actual name** from the game tooltip
3. **Submit via GitHub Issue** with format:
   ```
   Item ID: 1969
   Name: Iron Sword
   Type: weapon
   Category: one-handed
   Description: A basic iron sword
   ```
4. **Or submit a PR** with the updated `item_database.json`

### Development Setup

```bash
# Fork the repository
git fork https://github.com/YOUR_USERNAME/reforge-save-editor.git

# Clone your fork
git clone https://github.com/YOUR_USERNAME/reforge-save-editor.git
cd reforge-save-editor

# Create a branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Commit and push
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

# Open a Pull Request
```

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** for function parameters
- Add **docstrings** for classes and methods
- Keep functions **focused and testable**

---

##  Known Limitations

| Limitation | Workaround |
|-----------|------------|
| Item names require manual entry | Use in-game tooltips to identify items |
| No live memory editing (yet) | Edit saves, reload game |
| Windows-only save path | Mac/Linux users: manual path config needed |
| No multiplayer support | Single-player saves only |

---

##  Safety & Warnings

>  **IMPORTANT: Always backup your saves before editing!**

- The editor creates **automatic backups** before every save
- Backups are stored in the `backups/` folder
- **Test edits** on a copy of your save first
- **Some edits may cause game instability** - use responsibly
- **Online features may be affected** - use offline mode when editing

---

##  Credits

### Original Development
- **Lead Developer**: [Your Name/GitHub Username]
- **Contributors**: See [CONTRIBUTORS.md](CONTRIBUTORS.md)

### Special Thanks
- **Age of Reforging Community** - For testing and feedback
- **PersonaeGames** - For creating an amazing game
- **PySide6 Team** - For the excellent Qt bindings

### Tools & Libraries
- [PySide6](https://pypi.org/project/PySide6/) - Qt for Python
- [Python](https://www.python.org/) - Programming language

---

##  License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Age of Reforging Save Editor Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

##  Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/YOUR_USERNAME/reforge-save-editor/issues)
- **Discussions**: [Community discussions](https://github.com/YOUR_USERNAME/reforge-save-editor/discussions)
- **Steam Community**: [Age of Reforging Steam Forum](https://steamcommunity.com/app/YOUR_GAME_ID/discussions/)

---

##  Roadmap

### v4.1.0 (Planned)
- [ ] Full inventory add/remove/edit UI
- [ ] Item stat editing (durability, quality, attributes)
- [ ] Bulk item operations
- [ ] Save comparison tool

### v4.2.0 (Planned)
- [ ] Live memory editing (WeMod-style)
- [ ] Cheat table import/export
- [ ] Character build presets
- [ ] Save file validation

### Future Considerations
- [ ] Mac/Linux support
- [ ] Multiple language support
- [ ] Plugin system for community extensions
- [ ] Auto-updater

---

<div align="center">

**Made with ❤️ by the Age of Reforging Community**

[⬆ Back to Top](#age-of-reforging-the-freelands---save-game-editor)

</div>
