#!/usr/bin/env python3
"""
Age of Reforging: The Freelands - Complete Save Game Editor v4.0.1
====================================================================
Integrated Features:
- Terminal-style console with real-time logging
- Auto-discover save slots from AppData
- Auto-discover item IDs from saves (dynamic database)
- Full character stat editing (Attributes, Skills, Vitals, etc.)
- Item database with persistent user-renamed items
- Quick cheat buttons (max stats, gold, etc.)
- Auto-backup system before every save
- Character search/filter
- Inventory display with item names
- Raw JSON editor
- Dark theme UI

Author: Integrated Development Team
Version: 4.0.1
"""

import sys
import json
import pathlib
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTabWidget, QScrollArea, QGroupBox,
    QFormLayout, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
    QMessageBox, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QSplitter, QStatusBar, QMenuBar, QMenu, QTextEdit,
    QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QFrame, QSizePolicy, QInputDialog
)
from PySide6.QtGui import QAction, QFont, QColor
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QFileSystemWatcher

# ==============================================================================
# CONFIGURATION
# ==============================================================================

EDITOR_VERSION = "4.0.1"
EDITOR_NAME = "Age of Reforging - Complete Save Editor"

# Save file location (from user's system)
DEFAULT_SAVE_PATH = pathlib.Path(
    r"C:\Users\j\AppData\LocalLow\PersonaeGames\Age of Reforging The Freelands\Save\Sol\SaveData"
)

# Item database file (auto-created in same directory as editor)
ITEM_DATABASE_FILE = pathlib.Path(__file__).parent / "item_database.json"

# Stat categories with proper key mappings from discovered save structure
STAT_CATEGORIES = {
    "Attributes": {
        "BSstrength": ("Strength", 0, 100),
        "BSendurance": ("Endurance", 0, 100),
        "BSagility": ("Agility", 0, 100),
        "BSprecision": ("Precision", 0, 100),
        "BSintelligence": ("Intelligence", 0, 100),
        "BSwillpower": ("Willpower", 0, 100),
    },
    "Skills": {
        "BSPersuade": ("Persuasion", 0, 100),
        "BSBargain": ("Bargain", 0, 100),
        "BSIntimidate": ("Intimidation", 0, 100),
        "BSScholarly": ("Scholarly", 0, 100),
        "BSPathfind": ("Pathfind", 0, 100),
        "BSInsight": ("Insight", 0, 100),
        "BSMechanics": ("Mechanics", 0, 100),
        "BSSneak": ("Sneak", 0, 100),
        "BSTheft": ("Theft", 0, 100),
        "BSSmithing": ("Smithing", 0, 100),
        "BSAlchemy": ("Alchemy", 0, 100),
        "BSCooking": ("Cooking", 0, 100),
        "BSMedical": ("Medical", 0, 100),
        "BSTraining": ("Training", 0, 100),
        "BSTorture": ("Torture", 0, 100),
    },
    "Vitals": {
        "health": ("Health %", 0, 1000, True),
        "morale": ("Morale %", 0, 1000, True),
        "vigor": ("Vigor %", 0, 1000, True),
        "satiety": ("Satiety %", 0, 1000, True),
        "currenthp": ("Current HP", 0, 99999, True),
        "currentsp": ("Current SP", 0, 99999, True),
        "currentmp": ("Current MP", 0, 99999, True),
    },
    "Progression": {
        "exp": ("Experience", 0, 9999999),
        "potential": ("Potential Points", 0, 9999),
        "level": ("Level", 1, 100),
    },
    "Morality": {
        "goodness": ("Goodness", -100, 100),
        "lawfulness": ("Lawfulness", -100, 100),
    },
    "Career": {
        "prestige": ("Arena Prestige", 0, 999999),
        "games": ("Arena Games", 0, 99999),
        "wins": ("Arena Wins", 0, 99999),
        "losses": ("Arena Losses", 0, 99999),
        "killCount": ("Total Kills", 0, 999999),
    }
}

# ==============================================================================
# TERMINAL CONSOLE WIDGET
# ==============================================================================

class TerminalConsole(QTextEdit):
    """Terminal-style console for displaying logs and system messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #00ff00;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMaximumHeight(150)
        self.setMinimumHeight(120)
        
        # Welcome message
        self.log_system("Terminal Console initialized", "SYSTEM")
        self.log_system(f"Editor Version: {EDITOR_VERSION}", "SYSTEM")
        self.log_system("Ready for commands...", "SYSTEM")
        
    def _scroll_to_bottom(self):
        """Scroll to bottom of console"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def log_system(self, message: str, category: str = "SYSTEM"):
        """Log a system message (white text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #58a6ff;">[{category}]</span> {message}')
        self._scroll_to_bottom()
        
    def log_success(self, message: str):
        """Log a success message (green text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #3fb950;">✓ {message}</span>')
        self._scroll_to_bottom()
        
    def log_warning(self, message: str):
        """Log a warning message (yellow text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #d29922;">⚠ {message}</span>')
        self._scroll_to_bottom()
        
    def log_error(self, message: str):
        """Log an error message (red text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #f85149;">✗ {message}</span>')
        self._scroll_to_bottom()
        
    def log_info(self, message: str):
        """Log an info message (cyan text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #58a6ff;">ℹ {message}</span>')
        self._scroll_to_bottom()
        
    def log_change(self, message: str):
        """Log a change message (magenta text)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #8b949e;">[{timestamp}]</span> <span style="color: #bc8cff;">→ {message}</span>')
        self._scroll_to_bottom()
        
    def clear_console(self):
        """Clear the console"""
        self.clear()
        self.log_system("Console cleared", "SYSTEM")

# ==============================================================================
# INTEGRATED ITEM DATABASE WITH AUTO-DISCOVERY
# ==============================================================================

class IntegratedItemDatabase:
    """
    Integrated item database that auto-discovers items from save files
    and persists user-renamed items across sessions.
    """
    
    def __init__(self):
        self.items: Dict[int, dict] = {}
        self.discovered_ids: Set[int] = set()
        self.database_file = ITEM_DATABASE_FILE
        self.load_database()
        
    def load_database(self):
        """Load item database from JSON file"""
        try:
            if self.database_file.exists():
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # Convert string keys to int for consistent lookup
                for item_id_str, data in raw_data.items():
                    try:
                        item_id = int(item_id_str)
                        if isinstance(data, dict):
                            self.items[item_id] = data
                        else:
                            self.items[item_id] = {"name": str(data), "type": "unknown"}
                    except (ValueError, TypeError):
                        continue
                        
                print(f"[+] Loaded {len(self.items)} item definitions from database")
            else:
                print("[!] No existing item database found. Will create new one on first save scan.")
        except Exception as e:
            print(f"[!] Error loading item database: {e}")
            self.items = {}
            
    def save_database(self):
        """Save item database to JSON file"""
        try:
            # Convert int keys to string for JSON
            save_data = {}
            for item_id, data in self.items.items():
                save_data[str(item_id)] = data
            
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print(f"[+] Saved {len(self.items)} items to database")
        except Exception as e:
            print(f"[!] Error saving database: {e}")
            
    def discover_items_from_save(self, save_data: dict) -> Set[int]:
        """
        Extract all item IDs from a save file and add to database.
        Returns set of newly discovered item IDs.
        """
        newly_discovered = set()
        
        try:
            # Extract from all NPCs
            for npc in save_data.get('npcs', []):
                # Inventory items
                for item in npc.get('items', []):
                    if item and isinstance(item, dict):
                        item_id = item.get('id')
                        if item_id is not None:
                            self._add_discovered_item(item_id, newly_discovered)
                
                # Equipment
                for equip in npc.get('equips', []):
                    if equip and isinstance(equip, dict):
                        item_id = equip.get('id')
                        if item_id is not None:
                            self._add_discovered_item(item_id, newly_discovered)
            
            # Extract from caravan, shops, etc.
            caravan = save_data.get('caravan', {})
            if caravan:
                for item in caravan.get('items', []):
                    if isinstance(item, dict):
                        item_id = item.get('id')
                        if item_id is not None:
                            self._add_discovered_item(item_id, newly_discovered)
                            
        except Exception as e:
            print(f"[!] Error discovering items: {e}")
            
        return newly_discovered
        
    def _add_discovered_item(self, item_id: int, newly_discovered: set):
        """Add a discovered item to the database"""
        if item_id not in self.items:
            # New item - add template
            self.items[item_id] = {
                "name": f"Unknown Item {item_id}",
                "type": "unknown",
                "category": "uncategorized",
                "description": "",
                "discovered_date": datetime.now().isoformat(),
                "auto_discovered": True
            }
            newly_discovered.add(item_id)
            self.discovered_ids.add(item_id)
        else:
            # Existing item - mark as discovered
            self.discovered_ids.add(item_id)
            # Update discovery date if it was manually named
            if not self.items[item_id].get('auto_discovered', True):
                self.items[item_id]['last_seen'] = datetime.now().isoformat()
                
    def get_item_name(self, item_id: int) -> str:
        """Get item name from ID"""
        item_data = self.items.get(item_id, {})
        if isinstance(item_data, dict):
            return item_data.get('name', f'Unknown Item {item_id}')
        return str(item_data)
        
    def get_item_data(self, item_id: int) -> dict:
        """Get full item data"""
        item_data = self.items.get(item_id, {})
        if isinstance(item_data, dict):
            return item_data
        return {"name": f"Unknown Item {item_id}", "type": "unknown"}
        
    def set_item_name(self, item_id: int, name: str, item_type: str = "unknown", 
                     category: str = "uncategorized", description: str = ""):
        """Set item name and metadata in database"""
        if item_id not in self.items:
            self.items[item_id] = {}
            
        self.items[item_id].update({
            "name": name,
            "type": item_type,
            "category": category,
            "description": description,
            "auto_discovered": False,
            "manually_named": True,
            "last_modified": datetime.now().isoformat()
        })
        self.save_database()
        
    def search_items(self, query: str) -> List[Tuple[int, str, str]]:
        """Search items by name or ID"""
        results = []
        query_lower = query.lower()
        
        for item_id, item_data in self.items.items():
            if isinstance(item_data, dict):
                item_name = item_data.get('name', '')
                item_category = item_data.get('category', '')
            else:
                item_name = str(item_data)
                item_category = ''
                
            if (query_lower in item_name.lower() or 
                query in str(item_id) or
                query_lower in item_category.lower()):
                results.append((item_id, item_name, item_category))
                
        return sorted(results, key=lambda x: x[0])[:200]
        
    def get_statistics(self) -> dict:
        """Get database statistics"""
        total = len(self.items)
        named = sum(1 for item in self.items.values() 
                   if isinstance(item, dict) and not item.get('auto_discovered', True))
        unknown = total - named
        
        return {
            "total_items": total,
            "named_items": named,
            "unknown_items": unknown,
            "discovered_ids": len(self.discovered_ids)
        }

# ==============================================================================
# MAIN EDITOR WINDOW
# ==============================================================================

class SaveGameEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_save_path: Optional[pathlib.Path] = None
        self.save_data: Optional[dict] = None
        self.original_data: Optional[dict] = None
        self.current_character_index: Optional[int] = None
        self.current_character_data: Optional[dict] = None
        self.widget_map: Dict[str, Dict[str, Any]] = {}
        self.item_db = IntegratedItemDatabase()
        self.file_watcher = QFileSystemWatcher()
        self.modified = False
        self.selected_item_id: Optional[int] = None
        
        self.init_ui()
        self.update_item_db_stats()
        self.discover_saves()
        self.setup_file_watcher()
        
    def init_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle(f"{EDITOR_NAME} v{EDITOR_VERSION}")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # TOP: Terminal Console (fills available space)
        self.terminal = TerminalConsole()
        main_layout.addWidget(self.terminal)
        
        # Terminal info label
        terminal_info = QLabel("📋 Terminal Console - Real-time change logging enabled")
        terminal_info.setStyleSheet("color: #8b949e; font-size: 10px; padding: 2px;")
        main_layout.addWidget(terminal_info)
        
        # MIDDLE: Save selection and controls
        middle_frame = QFrame()
        middle_frame.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 4px; padding: 8px;")
        middle_layout = QHBoxLayout(middle_frame)
        
        middle_layout.addWidget(QLabel("💾 Save Slot:"))
        self.save_combo = QComboBox()
        self.save_combo.setMinimumWidth(300)
        self.save_combo.currentIndexChanged.connect(self.on_save_selected)
        middle_layout.addWidget(self.save_combo, 1)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.discover_saves)
        middle_layout.addWidget(self.refresh_btn)
        
        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.open_folder_btn.clicked.connect(self.open_save_folder)
        middle_layout.addWidget(self.open_folder_btn)
        
        middle_layout.addSpacing(20)
        middle_layout.addWidget(QLabel("💰 Global Gold:"))
        self.gold_display = QSpinBox()
        self.gold_display.setRange(0, 999999999)
        self.gold_display.setMinimumWidth(120)
        self.gold_display.valueChanged.connect(self.on_value_changed)
        middle_layout.addWidget(self.gold_display)
        
        middle_layout.addSpacing(20)
        self.item_db_stats_label = QLabel("📦 Items: 0")
        self.item_db_stats_label.setStyleSheet("color: #3fb950; font-weight: bold;")
        middle_layout.addWidget(self.item_db_stats_label)
        
        main_layout.addWidget(middle_frame)
        
        # BOTTOM: Splitter for character tree and editor
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Character tree with search
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right: Stat editor tabs
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)
        
        # Bottom: Action buttons
        bottom_bar = self.create_bottom_bar()
        main_layout.addLayout(bottom_bar)
        
        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        
        # Menu bar
        self.create_menu_bar()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Log startup
        self.terminal.log_system("=" * 60)
        self.terminal.log_system(f"{EDITOR_NAME} v{EDITOR_VERSION} started")
        self.terminal.log_system("=" * 60)
        self.terminal.log_info(f"Save path: {DEFAULT_SAVE_PATH}")
        self.terminal.log_info(f"Item database: {ITEM_DATABASE_FILE}")
        
    def create_left_panel(self) -> QWidget:
        """Create left panel with character tree"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search box
        layout.addWidget(QLabel("🔍 Search Characters:"))
        self.char_search = QLineEdit()
        self.char_search.setPlaceholderText("Type to filter...")
        self.char_search.textChanged.connect(self.filter_characters)
        layout.addWidget(self.char_search)
        
        # Character tree
        layout.addWidget(QLabel("Characters:"))
        self.char_tree = QTreeWidget()
        self.char_tree.setHeaderLabels(["Name", "Level", "Type"])
        self.char_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.char_tree.currentItemChanged.connect(self.on_character_selected)
        layout.addWidget(self.char_tree)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(self.char_count_label)
        
        return widget
        
    def create_right_panel(self) -> QWidget:
        """Create right panel with stat tabs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_attributes_tab(), "⚔️ Attributes")
        self.tabs.addTab(self.create_skills_tab(), "📚 Skills")
        self.tabs.addTab(self.create_vitals_tab(), "❤️ Vitals")
        self.tabs.addTab(self.create_progression_tab(), "📈 Progression")
        self.tabs.addTab(self.create_morality_tab(), "⚖️ Morality")
        self.tabs.addTab(self.create_career_tab(), "🏆 Career")
        self.tabs.addTab(self.create_inventory_tab(), "🎒 Inventory")
        self.tabs.addTab(self.create_item_database_tab(), "🗄️ Item Database")
        self.tabs.addTab(self.create_cheats_tab(), "⚡ Quick Cheats")
        self.tabs.addTab(self.create_raw_json_tab(), "📄 Raw JSON")
        
        layout.addWidget(self.tabs)
        
        return widget
        
    def create_bottom_bar(self) -> QHBoxLayout:
        """Create bottom action bar"""
        layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                padding: 12px 24px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        layout.addWidget(self.save_btn)
        
        self.backup_btn = QPushButton("📋 Create Backup")
        self.backup_btn.clicked.connect(self.create_backup)
        layout.addWidget(self.backup_btn)
        
        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.clicked.connect(self.reload_save)
        layout.addWidget(self.reload_btn)
        
        layout.addSpacing(20)
        
        # Item database tools
        self.scan_items_btn = QPushButton("🔍 Scan Save for Items")
        self.scan_items_btn.clicked.connect(self.scan_save_for_items)
        layout.addWidget(self.scan_items_btn)
        
        self.export_db_btn = QPushButton("📤 Export Item DB")
        self.export_db_btn.clicked.connect(self.export_item_database)
        layout.addWidget(self.export_db_btn)
        
        layout.addStretch()
        
        # Clear console button
        self.clear_console_btn = QPushButton(" Clear Console")
        self.clear_console_btn.clicked.connect(self.terminal.clear_console)
        layout.addWidget(self.clear_console_btn)
        
        return layout
        
    def create_attributes_tab(self) -> QWidget:
        return self.create_stat_tab("Attributes", STAT_CATEGORIES["Attributes"])
        
    def create_skills_tab(self) -> QWidget:
        return self.create_stat_tab("Skills", STAT_CATEGORIES["Skills"])
        
    def create_vitals_tab(self) -> QWidget:
        return self.create_stat_tab("Vitals", STAT_CATEGORIES["Vitals"], float_widgets=True)
        
    def create_progression_tab(self) -> QWidget:
        return self.create_stat_tab("Progression", STAT_CATEGORIES["Progression"])
        
    def create_morality_tab(self) -> QWidget:
        return self.create_stat_tab("Morality", STAT_CATEGORIES["Morality"])
        
    def create_career_tab(self) -> QWidget:
        return self.create_stat_tab("Career", STAT_CATEGORIES["Career"])
        
    def create_stat_tab(self, tab_name: str, categories: Dict, float_widgets: bool = False) -> QWidget:
        """Create a generic stat tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(8)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.widget_map[tab_name] = {}
        
        for key, config in categories.items():
            label = config[0]
            min_val = config[1]
            max_val = config[2]
            is_float = config[3] if len(config) > 3 else float_widgets
            
            if is_float:
                spin = QDoubleSpinBox()
                spin.setDecimals(1)
            else:
                spin = QSpinBox()
                
            spin.setRange(min_val, max_val)
            spin.valueChanged.connect(self.on_value_changed)
            layout.addRow(label, spin)
            self.widget_map[tab_name][key] = spin
            
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll
        
    def create_inventory_tab(self) -> QWidget:
        """Create Inventory tab with full item management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Item database info
        db_info = QLabel(f"📦 Item Database: {len(self.item_db.items)} items loaded")
        db_info.setStyleSheet("color: #3fb950; font-weight: bold;")
        layout.addWidget(db_info)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search:"))
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Search by name or ID...")
        self.item_search.textChanged.connect(self.search_items)
        search_layout.addWidget(self.item_search, 1)
        layout.addLayout(search_layout)
        
        # Item search results table
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(["Item ID", "Name", "Category"])
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.item_table.setMaximumHeight(200)
        self.item_table.cellClicked.connect(self.on_item_selected)
        layout.addWidget(self.item_table)
        
        # Equipment display
        layout.addWidget(QLabel("\n📦 Current Equipment:"))
        self.inventory_text = QTextEdit()
        self.inventory_text.setReadOnly(True)
        self.inventory_text.setMaximumHeight(300)
        layout.addWidget(self.inventory_text)
        
        # Edit equipment buttons
        btn_layout = QHBoxLayout()
        
        self.edit_item_btn = QPushButton("✏️ Rename Item in DB")
        self.edit_item_btn.clicked.connect(self.rename_item_in_database)
        btn_layout.addWidget(self.edit_item_btn)
        
        self.add_item_btn = QPushButton("➕ Add Item")
        self.add_item_btn.clicked.connect(self.add_inventory_item)
        btn_layout.addWidget(self.add_item_btn)
        
        self.remove_item_btn = QPushButton("🗑️ Remove Item")
        self.remove_item_btn.clicked.connect(self.remove_inventory_item)
        btn_layout.addWidget(self.remove_item_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Info label
        info_label = QLabel("💡 Tip: Items auto-discovered from saves. Rename as you encounter them!")
        info_label.setStyleSheet("color: #8b949e; font-style: italic;")
        layout.addWidget(info_label)
        
        return widget
        
    def create_item_database_tab(self) -> QWidget:
        """Create dedicated Item Database management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistics
        stats_group = QGroupBox("📊 Database Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.db_total_label = QLabel("0")
        self.db_named_label = QLabel("0")
        self.db_unknown_label = QLabel("0")
        
        stats_layout.addRow("Total Items:", self.db_total_label)
        stats_layout.addRow("Named Items:", self.db_named_label)
        stats_layout.addRow("Unknown Items:", self.db_unknown_label)
        
        layout.addWidget(stats_group)
        
        # Filter options
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_unknown_only = QCheckBox("Show Unknown Only")
        self.filter_unknown_only.stateChanged.connect(self.refresh_item_table)
        filter_layout.addWidget(self.filter_unknown_only)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Full item list
        layout.addWidget(QLabel("\n🗄️ All Items:"))
        self.full_item_table = QTableWidget()
        self.full_item_table.setColumnCount(4)
        self.full_item_table.setHorizontalHeaderLabels(["Item ID", "Name", "Category", "Type"])
        self.full_item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.full_item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.full_item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.full_item_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.full_item_table.cellClicked.connect(self.on_full_item_selected)
        layout.addWidget(self.full_item_table)
        
        # Edit buttons
        btn_layout = QHBoxLayout()
        
        self.bulk_rename_btn = QPushButton("✏️ Rename Selected")
        self.bulk_rename_btn.clicked.connect(self.bulk_rename_items)
        btn_layout.addWidget(self.bulk_rename_btn)
        
        self.export_csv_btn = QPushButton("📤 Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_item_database_csv)
        btn_layout.addWidget(self.export_csv_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Refresh button
        self.refresh_db_btn = QPushButton("🔄 Refresh Database View")
        self.refresh_db_btn.clicked.connect(self.refresh_item_database_tab)
        layout.addWidget(self.refresh_db_btn)
        
        # Update stats
        self.update_item_db_stats()
        self.refresh_item_table()
        
        return widget
        
    def create_cheats_tab(self) -> QWidget:
        """Create Quick Cheats tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Resource cheats
        resource_group = QGroupBox("💰 Resource Cheats")
        resource_layout = QFormLayout(resource_group)
        
        self.cheat_gold_btn = QPushButton("Set Gold to 999,999")
        self.cheat_gold_btn.clicked.connect(lambda: self.apply_cheat("wealth", 999999))
        resource_layout.addRow(self.cheat_gold_btn)
        
        self.cheat_potential_btn = QPushButton("Set Potential to 1000")
        self.cheat_potential_btn.clicked.connect(lambda: self.apply_cheat("potential", 1000))
        resource_layout.addRow(self.cheat_potential_btn)
        
        self.cheat_exp_btn = QPushButton("Set EXP to 999,999")
        self.cheat_exp_btn.clicked.connect(lambda: self.apply_cheat("exp", 999999))
        resource_layout.addRow(self.cheat_exp_btn)
        
        layout.addWidget(resource_group)
        
        # Stat cheats
        stat_group = QGroupBox("💪 Stat Cheats")
        stat_layout = QFormLayout(stat_group)
        
        self.cheat_max_attrs_btn = QPushButton("Max All Attributes (100)")
        self.cheat_max_attrs_btn.clicked.connect(self.max_all_attributes)
        stat_layout.addRow(self.cheat_max_attrs_btn)
        
        self.cheat_max_skills_btn = QPushButton("Max All Skills (100)")
        self.cheat_max_skills_btn.clicked.connect(self.max_all_skills)
        stat_layout.addRow(self.cheat_max_skills_btn)
        
        self.cheat_max_vitals_btn = QPushButton("Max All Vitals (1000)")
        self.cheat_max_vitals_btn.clicked.connect(self.max_all_vitals)
        stat_layout.addRow(self.cheat_max_vitals_btn)
        
        layout.addWidget(stat_group)
        
        # Career cheats
        career_group = QGroupBox("🏆 Career Cheats")
        career_layout = QFormLayout(career_group)
        
        self.cheat_max_prestige_btn = QPushButton("Max Arena Prestige (999999)")
        self.cheat_max_prestige_btn.clicked.connect(lambda: self.apply_cheat("prestige", 999999))
        career_layout.addRow(self.cheat_max_prestige_btn)
        
        self.cheat_max_wins_btn = QPushButton("Set Arena Wins to 1000")
        self.cheat_max_wins_btn.clicked.connect(lambda: self.apply_cheat("wins", 1000))
        career_layout.addRow(self.cheat_max_wins_btn)
        
        layout.addWidget(career_group)
        
        layout.addStretch()
        
        return widget
        
    def create_raw_json_tab(self) -> QWidget:
        """Create Raw JSON editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.raw_json_text = QTextEdit()
        self.raw_json_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.raw_json_text)
        
        btn_layout = QHBoxLayout()
        
        format_btn = QPushButton("📐 Format JSON")
        format_btn.clicked.connect(self.format_json)
        btn_layout.addWidget(format_btn)
        
        validate_btn = QPushButton("✓ Validate")
        validate_btn.clicked.connect(self.validate_json)
        btn_layout.addWidget(validate_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
        
    def discover_saves(self):
        """Auto-discover save slots"""
        self.terminal.log_info("Scanning for save slots...")
        self.save_combo.clear()
        
        if not DEFAULT_SAVE_PATH.exists():
            self.terminal.log_error(f"Save path not found: {DEFAULT_SAVE_PATH}")
            self.status.showMessage(f"❌ Save path not found: {DEFAULT_SAVE_PATH}")
            QMessageBox.warning(self, "Error", 
                f"Save directory not found:\n{DEFAULT_SAVE_PATH}\n\n"
                "Please ensure the game has been played and saved at least once.")
            return
        
        save_folders = [f for f in DEFAULT_SAVE_PATH.iterdir() if f.is_dir()]
        
        for folder in sorted(save_folders, key=lambda x: x.name):
            sav_file = folder / "sav.dat"
            if sav_file.exists():
                # Try to get save name from info.dat or folder name
                save_name = folder.name
                try:
                    info_file = folder / "info.dat"
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            save_name = info.get('saveName', folder.name)
                except:
                    pass
                    
                self.save_combo.addItem(f"{save_name} ({folder.name})", str(folder))
                self.terminal.log_success(f"Found save: {save_name}")
        
        self.status.showMessage(f"Found {self.save_combo.count()} save slot(s)")
        self.terminal.log_info(f"Total save slots found: {self.save_combo.count()}")
        
        if self.save_combo.count() > 0:
            self.save_combo.setCurrentIndex(0)
            
    def on_save_selected(self, index: int):
        """Load selected save file"""
        if index < 0:
            return
            
        save_folder = pathlib.Path(self.save_combo.currentData())
        self.current_save_path = save_folder / "sav.dat"
        
        self.terminal.log_info(f"Loading save: {self.current_save_path.name}")
        
        try:
            with open(self.current_save_path, 'r', encoding='utf-8') as f:
                self.save_data = json.load(f)
                self.original_data = json.loads(json.dumps(self.save_data))
                
            self.terminal.log_success(f"Save loaded successfully")
            
            # Auto-discover items from this save
            newly_discovered = self.item_db.discover_items_from_save(self.save_data)
            if newly_discovered:
                self.terminal.log_change(f"Discovered {len(newly_discovered)} new item IDs")
                self.update_item_db_stats()
                self.refresh_item_table()
            else:
                self.terminal.log_info("No new items discovered")
            
            # Update gold display
            self.gold_display.blockSignals(True)
            self.gold_display.setValue(self.save_data.get('wealth', 0))
            self.gold_display.blockSignals(False)
            
            self.populate_character_tree()
            self.populate_raw_json()
            self.modified = False
            self.update_save_button()
            
            # Add to file watcher
            if str(self.current_save_path) not in self.file_watcher.files():
                self.file_watcher.addPath(str(self.current_save_path))
                self.terminal.log_info("File watcher enabled for auto-save detection")
            
            self.terminal.log_system("=" * 40)
            
        except Exception as e:
            self.terminal.log_error(f"Failed to load save: {e}")
            self.status.showMessage(f"❌ Error loading save: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load save file:\n{e}")
            
    def populate_character_tree(self):
        """Populate character selection tree"""
        self.char_tree.clear()
        
        npcs = self.save_data.get("npcs", [])
        self.terminal.log_info(f"Loading {len(npcs)} characters from save")
        
        for i, npc in enumerate(npcs):
            name = npc.get("unitname", f"NPC {i}")
            level = npc.get("level", 0)
            char_type = npc.get("characterType", 0)
            
            type_labels = {0: "Player", 1: "Companion", 2: "Mercenary", 3: "Other"}
            type_label = type_labels.get(char_type, "Unknown")
            
            item = QTreeWidgetItem([name, str(level), type_label])
            item.setData(0, Qt.UserRole, i)
            
            # Highlight player characters
            if char_type == 0 or npc.get("heroCareer", {}).get("isInParty", False):
                item.setForeground(0, QColor("#3fb950"))
                item.setFont(0, QFont("", -1, QFont.Bold))
                
            self.char_tree.addTopLevelItem(item)
            
        self.char_count_label.setText(f"{len(npcs)} characters")
        
        if self.char_tree.topLevelItemCount() > 0:
            self.char_tree.setCurrentItem(self.char_tree.topLevelItem(0))
            
    def filter_characters(self, text: str):
        """Filter character tree by search text"""
        text_lower = text.lower()
        
        for i in range(self.char_tree.topLevelItemCount()):
            item = self.char_tree.topLevelItem(i)
            name = item.text(0).lower()
            
            if text_lower in name or not text:
                item.setHidden(False)
            else:
                item.setHidden(True)
                
    def on_character_selected(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Load selected character's stats"""
        if not current:
            return
            
        npc_index = current.data(0, Qt.UserRole)
        if npc_index is None:
            return
            
        npcs = self.save_data.get("npcs", [])
        if npc_index >= len(npcs):
            return
            
        npc = npcs[npc_index]
        self.current_character_index = npc_index
        self.current_character_data = npc
        
        self.terminal.log_change(f"Selected character: {npc.get('unitname', 'Unknown')} (Level {npc.get('level', 0)})")
        
        # Populate all tabs
        self.populate_attributes(npc)
        self.populate_skills(npc)
        self.populate_vitals(npc)
        self.populate_progression(npc)
        self.populate_morality(npc)
        self.populate_career(npc)
        self.populate_inventory(npc)
        
        self.status.showMessage(f"Editing: {npc.get('unitname', 'Unknown')}")
        
    def populate_attributes(self, npc: Dict):
        human_attr = npc.get("humanAttribute", {})
        for key, widget in self.widget_map.get("Attributes", {}).items():
            value = human_attr.get(key, 0)
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)
            
    def populate_skills(self, npc: Dict):
        human_talent = npc.get("humanTalent", {})
        for key, widget in self.widget_map.get("Skills", {}).items():
            value = human_talent.get(key, 0)
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)
            
    def populate_vitals(self, npc: Dict):
        for key, widget in self.widget_map.get("Vitals", {}).items():
            value = npc.get(key, 100.0)
            widget.blockSignals(True)
            widget.setValue(float(value))
            widget.blockSignals(False)
            
    def populate_progression(self, npc: Dict):
        for key, widget in self.widget_map.get("Progression", {}).items():
            value = npc.get(key, 0)
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)
            
    def populate_morality(self, npc: Dict):
        for key, widget in self.widget_map.get("Morality", {}).items():
            value = npc.get(key, 0)
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)
            
    def populate_career(self, npc: Dict):
        hero_career = npc.get("heroCareer", {})
        for key, widget in self.widget_map.get("Career", {}).items():
            value = hero_career.get(key, 0)
            widget.blockSignals(True)
            widget.setValue(int(value))
            widget.blockSignals(False)
            
    def populate_inventory(self, npc: Dict):
        """Display inventory with item names"""
        equips = npc.get("equips", [])
        items = npc.get("items", [])
        
        text = "=== EQUIPMENT ===\n\n"
        for i, item in enumerate(equips):
            if item:
                item_id = item.get('id', 0)
                item_name = self.item_db.get_item_name(item_id)
                durability = item.get('durability', 0)
                quality = item.get('quality', 0)
                text += f"Slot {i}: [{item_id}] {item_name}\n"
                text += f"  Durability: {durability} | Quality: {quality}\n\n"
            else:
                text += f"Slot {i}: [Empty]\n\n"
        
        text += "\n=== INVENTORY ===\n\n"
        for i, item in enumerate(items):
            if item:
                item_id = item.get('id', 0)
                item_name = self.item_db.get_item_name(item_id)
                stack = item.get('stackNum', 1)
                durability = item.get('durability', 0)
                quality = item.get('quality', 0)
                text += f"Slot {i}: [{item_id}] {item_name} (x{stack})\n"
                text += f"  Durability: {durability} | Quality: {quality}\n\n"
            else:
                text += f"Slot {i}: [Empty]\n\n"
                
        self.inventory_text.setText(text)
        
    def populate_raw_json(self):
        if self.save_data:
            self.raw_json_text.setText(json.dumps(self.save_data, indent=2))
            
    def on_value_changed(self):
        self.modified = True
        self.update_save_button()
        
    def update_save_button(self):
        if self.modified:
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d29922;
                    color: white;
                    padding: 12px 24px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e3b341;
                }
            """)
            self.save_btn.setText("💾 Save Changes *")
        else:
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #238636;
                    color: white;
                    padding: 12px 24px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2ea043;
                }
            """)
            self.save_btn.setText("💾 Save Changes")
            
    def save_changes(self):
        """Save modified data"""
        if not self.current_save_path or not self.save_data:
            self.terminal.log_error("No save file loaded!")
            QMessageBox.warning(self, "Error", "No save file loaded!")
            return
            
        reply = QMessageBox.question(
            self, "Confirm Save",
            "This will overwrite the save file. Make sure you have a backup!\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            self.terminal.log_warning("Save cancelled by user")
            return
        
        self.terminal.log_info("Saving changes...")
        
        try:
            # Auto-backup before saving
            self.create_backup(silent=True)
            
            # Update data from widgets
            self.update_character_from_widgets()
            
            # Update global gold
            old_gold = self.save_data.get("wealth", 0)
            new_gold = self.gold_display.value()
            if old_gold != new_gold:
                self.terminal.log_change(f"Gold: {old_gold} → {new_gold}")
            self.save_data["wealth"] = new_gold
            
            # Write to file
            with open(self.current_save_path, 'w', encoding='utf-8') as f:
                json.dump(self.save_data, f, indent=2)
                
            self.modified = False
            self.update_save_button()
            
            self.terminal.log_success("Save file updated successfully!")
            self.terminal.log_system("=" * 40)
            self.status.showMessage("✅ Save successful!")
            QMessageBox.information(self, "Success", "Save file updated successfully!")
            
        except Exception as e:
            self.terminal.log_error(f"Save failed: {e}")
            self.status.showMessage(f"❌ Save failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
            
    def update_character_from_widgets(self):
        """Update save data from widget values"""
        if self.current_character_index is None:
            return
            
        npcs = self.save_data.get("npcs", [])
        if self.current_character_index >= len(npcs):
            return
            
        npc = npcs[self.current_character_index]
        char_name = npc.get('unitname', 'Unknown')
        
        # Track changes for logging
        changes = []
        
        # Update attributes
        if "humanAttribute" not in npc:
            npc["humanAttribute"] = {}
        for key, widget in self.widget_map.get("Attributes", {}).items():
            old_val = npc["humanAttribute"].get(key, 0)
            new_val = widget.value()
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc["humanAttribute"][key] = new_val
            
        # Update skills
        if "humanTalent" not in npc:
            npc["humanTalent"] = {}
        for key, widget in self.widget_map.get("Skills", {}).items():
            old_val = npc["humanTalent"].get(key, 0)
            new_val = widget.value()
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc["humanTalent"][key] = new_val
            
        # Update vitals
        for key, widget in self.widget_map.get("Vitals", {}).items():
            old_val = npc.get(key, 100.0)
            new_val = widget.value()
            if abs(old_val - new_val) > 0.1:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc[key] = new_val
            
        # Update progression
        for key, widget in self.widget_map.get("Progression", {}).items():
            old_val = npc.get(key, 0)
            new_val = widget.value()
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc[key] = new_val
            
        # Update morality
        for key, widget in self.widget_map.get("Morality", {}).items():
            old_val = npc.get(key, 0)
            new_val = widget.value()
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc[key] = new_val
            
        # Update career
        if "heroCareer" not in npc:
            npc["heroCareer"] = {}
        for key, widget in self.widget_map.get("Career", {}).items():
            old_val = npc["heroCareer"].get(key, 0)
            new_val = widget.value()
            if old_val != new_val:
                changes.append(f"{key}: {old_val} → {new_val}")
            npc["heroCareer"][key] = new_val
            
        # Log changes
        if changes:
            self.terminal.log_change(f"Character '{char_name}' changes:")
            for change in changes[:10]:  # Limit to 10 changes
                self.terminal.log_info(f"  {change}")
            if len(changes) > 10:
                self.terminal.log_info(f"  ... and {len(changes) - 10} more changes")
            
    def create_backup(self, silent: bool = False):
        """Create backup of save file"""
        if not self.current_save_path:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.current_save_path.parent / f"sav.dat.backup_{timestamp}"
        
        try:
            shutil.copy2(self.current_save_path, backup_path)
            if not silent:
                self.terminal.log_success(f"Backup created: {backup_path.name}")
                self.status.showMessage(f"✅ Backup: {backup_path.name}")
                QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{backup_path}")
            else:
                self.terminal.log_info(f"Auto-backup: {backup_path.name}")
        except Exception as e:
            self.terminal.log_error(f"Backup failed: {e}")
            if not silent:
                QMessageBox.critical(self, "Error", f"Failed to create backup:\n{e}")
                
    def reload_save(self):
        """Reload save from disk"""
        if not self.current_save_path:
            return
            
        self.terminal.log_info("Reloading save from disk...")
        index = self.save_combo.currentIndex()
        self.save_combo.setCurrentIndex(-1)
        self.save_combo.setCurrentIndex(index)
        
    def apply_cheat(self, key: str, value: int):
        """Apply a quick cheat"""
        if key == "wealth":
            old_val = self.gold_display.value()
            self.gold_display.setValue(value)
            self.terminal.log_change(f"Cheat applied - Gold: {old_val} → {value}")
        elif self.current_character_data:
            if key in self.widget_map.get("Progression", {}):
                widget = self.widget_map["Progression"][key]
                old_val = widget.value()
                widget.setValue(value)
                self.terminal.log_change(f"Cheat applied - {key}: {old_val} → {value}")
            elif key in self.widget_map.get("Career", {}):
                hero_career = self.current_character_data.get("heroCareer", {})
                old_val = hero_career.get(key, 0)
                hero_career[key] = value
                self.current_character_data["heroCareer"] = hero_career
                self.populate_career(self.current_character_data)
                self.terminal.log_change(f"Cheat applied - {key}: {old_val} → {value}")
                
        self.on_value_changed()
        self.status.showMessage(f"⚡ Applied: {key} = {value}")
        
    def max_all_attributes(self):
        for key, widget in self.widget_map.get("Attributes", {}).items():
            widget.setValue(100)
        self.terminal.log_change("Cheat applied - All attributes set to 100")
        self.on_value_changed()
        
    def max_all_skills(self):
        for key, widget in self.widget_map.get("Skills", {}).items():
            widget.setValue(100)
        self.terminal.log_change("Cheat applied - All skills set to 100")
        self.on_value_changed()
        
    def max_all_vitals(self):
        for key, widget in self.widget_map.get("Vitals", {}).items():
            widget.setValue(1000.0)
        self.terminal.log_change("Cheat applied - All vitals set to 1000")
        self.on_value_changed()
        
    def scan_save_for_items(self):
        """Manually trigger item scan from current save"""
        if not self.save_data:
            self.terminal.log_warning("No save loaded")
            QMessageBox.warning(self, "No Save", "Please load a save file first!")
            return
            
        self.terminal.log_info("Scanning save for new items...")
        newly_discovered = self.item_db.discover_items_from_save(self.save_data)
        
        if newly_discovered:
            self.update_item_db_stats()
            self.refresh_item_table()
            self.terminal.log_success(f"Discovered {len(newly_discovered)} new item IDs")
            QMessageBox.information(
                self, 
                "Items Discovered", 
                f"Found {len(newly_discovered)} new item IDs!\n\n"
                f"Total items in database: {len(self.item_db.items)}\n\n"
                f"Unknown items: {sum(1 for item in self.item_db.items.values() if isinstance(item, dict) and item.get('auto_discovered', True))}"
            )
        else:
            self.terminal.log_info("No new items discovered")
            QMessageBox.information(
                self, 
                "Scan Complete", 
                f"No new items discovered.\n\n"
                f"Total items in database: {len(self.item_db.items)}"
            )
            
    def search_items(self, text: str):
        """Search item database"""
        if len(text) < 2:
            self.item_table.setRowCount(0)
            return
            
        results = self.item_db.search_items(text)
        
        self.item_table.setRowCount(len(results))
        for i, (item_id, item_name, item_category) in enumerate(results):
            self.item_table.setItem(i, 0, QTableWidgetItem(str(item_id)))
            self.item_table.setItem(i, 1, QTableWidgetItem(item_name))
            self.item_table.setItem(i, 2, QTableWidgetItem(item_category))
            
    def on_item_selected(self, row: int, column: int):
        """Handle item selection from table"""
        item_id = self.item_table.item(row, 0).text()
        item_name = self.item_table.item(row, 1).text()
        self.selected_item_id = int(item_id)
        self.terminal.log_info(f"Selected item: [{item_id}] {item_name}")
        
    def on_full_item_selected(self, row: int, column: int):
        """Handle item selection from full database table"""
        item_id = self.full_item_table.item(row, 0).text()
        self.selected_item_id = int(item_id)
        
    def rename_item_in_database(self):
        """Open dialog to rename an item in the database"""
        if not hasattr(self, 'selected_item_id') or self.selected_item_id is None:
            self.terminal.log_warning("No item selected")
            QMessageBox.warning(self, "No Item Selected", "Please select an item from the table first.")
            return
        
        current_data = self.item_db.get_item_data(self.selected_item_id)
        current_name = current_data.get('name', f'Unknown Item {self.selected_item_id}')
        current_type = current_data.get('type', 'unknown')
        current_category = current_data.get('category', 'uncategorized')
        current_desc = current_data.get('description', '')
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Rename Item {self.selected_item_id}")
        dialog.setMinimumWidth(500)
        
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit(current_name)
        type_edit = QLineEdit(current_type)
        category_edit = QLineEdit(current_category)
        desc_edit = QTextEdit(current_desc)
        desc_edit.setMaximumHeight(80)
        
        layout.addRow("Item Name:", name_edit)
        layout.addRow("Item Type:", type_edit)
        layout.addRow("Category:", category_edit)
        layout.addRow("Description:", desc_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            old_name = current_name
            new_name = name_edit.text()
            self.item_db.set_item_name(
                self.selected_item_id,
                new_name,
                type_edit.text(),
                category_edit.text(),
                desc_edit.toPlainText()
            )
            self.update_item_db_stats()
            self.refresh_item_table()
            self.populate_inventory(self.current_character_data)
            self.terminal.log_change(f"Item renamed: [{self.selected_item_id}] '{old_name}' → '{new_name}'")
            QMessageBox.information(
                self, 
                "Success", 
                f"Item {self.selected_item_id} renamed to '{new_name}'"
            )
            
    def add_inventory_item(self):
        """Add item to character inventory"""
        if not self.current_character_data:
            self.terminal.log_warning("No character selected")
            QMessageBox.warning(self, "No Character", "Please select a character first.")
            return
        
        item_id_str, ok = QInputDialog.getText(
            self,
            "Add Item",
            "Enter Item ID (from database):",
            placeholderText="e.g., 1969"
        )
        
        if ok and item_id_str:
            try:
                item_id = int(item_id_str)
                
                new_item = {
                    "id": item_id,
                    "slotIndex": -1,
                    "subSlotIndex": 0,
                    "stackNum": 1,
                    "isNew": True,
                    "isStolen": 0,
                    "durability": 100.0,
                    "quality": 1,
                    "addAttrs": []
                }
                
                if "items" not in self.current_character_data:
                    self.current_character_data["items"] = []
                
                self.current_character_data["items"].append(new_item)
                
                self.on_value_changed()
                self.populate_inventory(self.current_character_data)
                
                item_name = self.item_db.get_item_name(item_id)
                self.terminal.log_change(f"Item added: [{item_id}] {item_name}")
                QMessageBox.information(self, "Success", f"Added [{item_id}] {item_name} to inventory")
                
            except ValueError:
                self.terminal.log_error("Invalid item ID")
                QMessageBox.warning(self, "Invalid ID", "Please enter a valid number.")
                
    def remove_inventory_item(self):
        """Remove selected item from inventory"""
        if not self.current_character_data:
            self.terminal.log_warning("No character selected")
            QMessageBox.warning(self, "No Character", "Please select a character first.")
            return
        
        self.terminal.log_info("Item removal - use Raw JSON tab for precise removal")
        QMessageBox.information(self, "Remove Item", 
            "Select the item slot in Raw JSON tab for precise removal.\n\n"
            "Full inventory editor coming in next update!")
            
    def refresh_item_table(self):
        """Refresh the item search table"""
        self.search_items(self.item_search.text())
        
    def refresh_item_database_tab(self):
        """Refresh the full item database table"""
        self.update_item_db_stats()
        
        items = sorted(self.item_db.items.items(), key=lambda x: x[0])
        
        if self.filter_unknown_only.isChecked():
            items = [(id, data) for id, data in items 
                    if isinstance(data, dict) and data.get('auto_discovered', True)]
        
        self.full_item_table.setRowCount(len(items))
        for i, (item_id, item_data) in enumerate(items):
            if isinstance(item_data, dict):
                name = item_data.get('name', f'Unknown Item {item_id}')
                category = item_data.get('category', 'uncategorized')
                item_type = item_data.get('type', 'unknown')
            else:
                name = str(item_data)
                category = 'unknown'
                item_type = 'unknown'
            
            self.full_item_table.setItem(i, 0, QTableWidgetItem(str(item_id)))
            self.full_item_table.setItem(i, 1, QTableWidgetItem(name))
            self.full_item_table.setItem(i, 2, QTableWidgetItem(category))
            self.full_item_table.setItem(i, 3, QTableWidgetItem(item_type))
            
    def update_item_db_stats(self):
        """Update item database statistics display"""
        stats = self.item_db.get_statistics()
        
        self.item_db_stats_label.setText(f"📦 Items: {stats['total_items']}")
        self.db_total_label.setText(str(stats['total_items']))
        self.db_named_label.setText(str(stats['named_items']))
        self.db_unknown_label.setText(str(stats['unknown_items']))
        
    def export_item_database(self):
        """Export item database to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Item Database",
            "item_database_export.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.item_db.save_database()
                shutil.copy2(ITEM_DATABASE_FILE, file_path)
                self.terminal.log_success(f"Database exported to: {file_path}")
                QMessageBox.information(self, "Export Complete", f"Database exported to:\n{file_path}")
            except Exception as e:
                self.terminal.log_error(f"Export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Failed to export:\n{e}")
                
    def export_item_database_csv(self):
        """Export item database to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Item Database to CSV",
            "item_database.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Item ID', 'Name', 'Type', 'Category', 'Description'])
                    
                    for item_id, item_data in sorted(self.item_db.items.items()):
                        if isinstance(item_data, dict):
                            writer.writerow([
                                item_id,
                                item_data.get('name', ''),
                                item_data.get('type', ''),
                                item_data.get('category', ''),
                                item_data.get('description', '')
                            ])
                        else:
                            writer.writerow([item_id, str(item_data), '', '', ''])
                            
                self.terminal.log_success(f"Database exported to CSV: {file_path}")
                QMessageBox.information(self, "Export Complete", f"Database exported to:\n{file_path}")
            except Exception as e:
                self.terminal.log_error(f"CSV export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Failed to export:\n{e}")
                
    def bulk_rename_items(self):
        """Bulk rename selected items"""
        self.terminal.log_info("Bulk rename - export to CSV for bulk operations")
        QMessageBox.information(self, "Bulk Rename", 
            "Select items in the table and use 'Rename Selected' for individual editing.\n\n"
            "For bulk operations, export to CSV, edit, and re-import.")
            
    def format_json(self):
        """Format JSON in raw editor"""
        try:
            data = json.loads(self.raw_json_text.toPlainText())
            self.raw_json_text.setText(json.dumps(data, indent=2))
            self.terminal.log_success("JSON formatted")
        except Exception as e:
            self.terminal.log_error(f"JSON format failed: {e}")
            QMessageBox.warning(self, "Invalid JSON", f"Cannot format:\n{e}")
            
    def validate_json(self):
        """Validate JSON"""
        try:
            json.loads(self.raw_json_text.toPlainText())
            self.terminal.log_success("JSON validation passed")
            QMessageBox.information(self, "Valid JSON", "JSON structure is valid!")
        except Exception as e:
            self.terminal.log_error(f"JSON validation failed: {e}")
            QMessageBox.critical(self, "Invalid JSON", f"JSON error:\n{e}")
            
    def open_save_folder(self):
        """Open save folder in explorer"""
        if self.current_save_path:
            import subprocess
            subprocess.run(['explorer', str(self.current_save_path.parent)])
            self.terminal.log_info(f"Opened save folder: {self.current_save_path.parent}")
            
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Save Folder...", self)
        open_action.triggered.connect(self.open_save_folder)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        tools_menu = menubar.addMenu("&Tools")
        
        scan_action = QAction("&Scan Save for Items", self)
        scan_action.triggered.connect(self.scan_save_for_items)
        tools_menu.addAction(scan_action)
        
        export_db_action = QAction("&Export Item Database", self)
        export_db_action.triggered.connect(self.export_item_database)
        tools_menu.addAction(export_db_action)
        
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def show_about(self):
        """Show about dialog"""
        stats = self.item_db.get_statistics()
        
        QMessageBox.about(self, "About Save Editor",
            f"<h3>Age of Reforging: The Freelands</h3>"
            f"<p>Complete Save Game Editor v{EDITOR_VERSION}</p>"
            f"<p><b>Features:</b></p>"
            f"<ul>"
            f"<li>✅ Terminal console with real-time logging</li>"
            f"<li>✅ Save file editing</li>"
            f"<li>✅ Integrated item database ({stats['total_items']} items)</li>"
            f"<li>✅ Auto-discovery of new items from saves</li>"
            f"<li>✅ Inventory management</li>"
            f"<li>✅ Quick cheats</li>"
            f"<li>✅ Auto-backup system</li>"
            f"<li>✅ Character search</li>"
            f"<li>✅ CSV export for item database</li>"
            f"</ul>"
            f"<p><b>Item Database:</b></p>"
            f"<ul>"
            f"<li>Named: {stats['named_items']}</li>"
            f"<li>Unknown: {stats['unknown_items']}</li>"
            f"</ul>"
            f"<p>⚠️ Always backup saves before editing!</p>"
            f"<p>🎮 Items auto-discover as you play and load saves!</p>")
            
    def setup_file_watcher(self):
        """Setup file system watcher for auto-save detection"""
        self.file_watcher.fileChanged.connect(self.on_save_file_changed)
        
    def on_save_file_changed(self, path: str):
        """Handle save file change detection"""
        self.terminal.log_warning(f"Game save detected - Reload recommended")
        self.status.showMessage("⚠️ Game save detected - Reload recommended")
            
    def apply_dark_theme(self):
        """Apply dark theme to application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QGroupBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #c9d1d9;
                padding: 6px;
                border-radius: 3px;
            }
            QSpinBox::hover, QDoubleSpinBox::hover, QLineEdit::hover {
                border: 1px solid #58a6ff;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                padding: 8px 16px;
                border-radius: 4px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #161b22;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #21262d;
                color: #c9d1d9;
                padding: 10px 20px;
                border: 1px solid #30363d;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #161b22;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #30363d;
            }
            QTreeWidget, QTableWidget {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #c9d1d9;
                gridline-color: #30363d;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: #1f6feb;
            }
            QTreeWidget::item:hover, QTableWidget::item:hover {
                background-color: #21262d;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #c9d1d9;
                padding: 8px;
                border: 1px solid #30363d;
            }
            QStatusBar {
                background-color: #161b22;
                color: #8b949e;
                border-top: 1px solid #30363d;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                font-family: Consolas;
                border-radius: 4px;
            }
            QCheckBox {
                color: #c9d1d9;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #30363d;
                border-radius: 3px;
                background-color: #0d1117;
            }
            QCheckBox::indicator:checked {
                background-color: #238636;
                border-color: #238636;
            }
            QScrollBar:vertical {
                background-color: #0d1117;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #30363d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #484f58;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QLabel {
                color: #c9d1d9;
            }
            QMenuBar {
                background-color: #161b22;
                color: #c9d1d9;
                border-bottom: 1px solid #30363d;
            }
            QMenuBar::item:selected {
                background-color: #21262d;
            }
            QMenu {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QMenu::item:selected {
                background-color: #21262d;
            }
        """)
        
    def closeEvent(self, event):
        """Handle window close"""
        # Save item database on exit
        self.item_db.save_database()
        self.terminal.log_system("Editor closing...")
        self.terminal.log_system("Item database saved")
        self.terminal.log_system("=" * 60)
        
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Exit anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.terminal.log_warning("Exiting with unsaved changes")
                event.accept()
            else:
                event.ignore()
        else:
            self.terminal.log_success("Editor closed successfully")
            event.accept()

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(EDITOR_NAME)
    app.setApplicationVersion(EDITOR_VERSION)
    
    window = SaveGameEditor()
    window.show()
    
    sys.exit(app.exec())