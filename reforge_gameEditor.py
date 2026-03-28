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
Version: 4.0.8
"""

import sys
import os
import re
import difflib
import json
import pathlib
import shutil
import subprocess
import time
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

EDITOR_VERSION = "4.0.9"
EDITOR_NAME = "Age of Reforging - Complete Save Editor"

# Save file location hint (runtime discovery handles user / character specific paths)
DEFAULT_SAVE_PATH = pathlib.Path.home() / "AppData/LocalLow/PersonaeGames/Age of Reforging The Freelands/Save"

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
# PATCHED RUNTIME DISCOVERY / SAVE BUNDLE SUPPORT
# ==============================================================================

GAME_NAME = "Age of Reforging The Freelands"
GAME_SAVE_VENDOR = "PersonaeGames"
GAME_SAVE_ROOT_RELATIVE = pathlib.Path("AppData/LocalLow") / GAME_SAVE_VENDOR / GAME_NAME / "Save"
KNOWN_INSTALL_HINT = pathlib.Path(r"H:\SteamLibrary\steamapps\common") / GAME_NAME
PRIMARY_SAVE_FILE = "sav.dat"
SECONDARY_SAVE_FILES = ["story.dat", "info.dat", "000-AWayToBrea.dat"]
BUNDLE_FILE_NAMES = [PRIMARY_SAVE_FILE] + SECONDARY_SAVE_FILES
REFLECTION_REPORT_FILE = pathlib.Path(__file__).parent / "reforge_reflection_report.json"
GAME_EXE_PREFERRED_NAMES = [
    f"{GAME_NAME}.exe",
    "Age of Reforging The Freelands.exe",
]

def _dedupe_paths(paths: List[pathlib.Path]) -> List[pathlib.Path]:
    seen = set()
    result: List[pathlib.Path] = []
    for path in paths:
        try:
            key = str(path.resolve(strict=False)).lower()
        except Exception:
            key = str(path).lower()
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _build_env_user_candidates() -> List[pathlib.Path]:
    candidates: List[pathlib.Path] = []
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(pathlib.Path(userprofile))
    home_drive = os.environ.get("HOMEDRIVE")
    home_path = os.environ.get("HOMEPATH")
    if home_drive and home_path:
        candidates.append(pathlib.Path(home_drive + home_path))
    try:
        candidates.append(pathlib.Path.home())
    except Exception:
        pass
    return _dedupe_paths(candidates)


def _candidate_save_roots() -> List[pathlib.Path]:
    roots: List[pathlib.Path] = []
    for user_root in _build_env_user_candidates():
        roots.append(user_root / GAME_SAVE_ROOT_RELATIVE)
    return _dedupe_paths(roots)


def _parse_libraryfolders_vdf(library_file: pathlib.Path) -> List[pathlib.Path]:
    libraries: List[pathlib.Path] = []
    try:
        raw = library_file.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'"path"\s+"([^"]+)"', raw):
            libraries.append(pathlib.Path(match.group(1).replace("\\\\", "\\")))
    except Exception:
        pass
    return _dedupe_paths(libraries)


def _candidate_game_installs() -> List[pathlib.Path]:
    installs: List[pathlib.Path] = [KNOWN_INSTALL_HINT]
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    program_files = os.environ.get("ProgramFiles")
    steam_roots: List[pathlib.Path] = []
    for base in [program_files_x86, program_files]:
        if base:
            steam_roots.append(pathlib.Path(base) / "Steam")
    steam_roots.append(pathlib.Path(r"H:\SteamLibrary"))
    for steam_root in _dedupe_paths(steam_roots):
        installs.append(steam_root / "steamapps" / "common" / GAME_NAME)
        library_file = steam_root / "steamapps" / "libraryfolders.vdf"
        if library_file.exists():
            for library in _parse_libraryfolders_vdf(library_file):
                installs.append(library / "steamapps" / "common" / GAME_NAME)
    for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = pathlib.Path(f"{drive_letter}:/")
        installs.append(drive / "SteamLibrary" / "steamapps" / "common" / GAME_NAME)
        installs.append(drive / "Games" / "SteamLibrary" / "steamapps" / "common" / GAME_NAME)
    return _dedupe_paths(installs)


def _safe_json_load(path: pathlib.Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _find_best_game_executable(game_root: pathlib.Path) -> Optional[pathlib.Path]:
    for name in GAME_EXE_PREFERRED_NAMES:
        candidate = game_root / name
        if candidate.exists():
            return candidate
    exes = sorted(
        [path for path in game_root.glob("*.exe") if path.is_file()],
        key=lambda p: (p.name.lower().startswith("unitycrashhandler"), p.name.lower())
    )
    return exes[0] if exes else None


def _summarize_type(value: Any) -> str:
    if isinstance(value, dict):
        return f"dict[{len(value)}]"
    if isinstance(value, list):
        return f"list[{len(value)}]"
    return type(value).__name__


class PatchedSaveGameEditor(SaveGameEditor):
    def __init__(self):
        QMainWindow.__init__(self)
        self.current_save_path: Optional[pathlib.Path] = None
        self.current_save_folder: Optional[pathlib.Path] = None
        self.current_save_root: Optional[pathlib.Path] = None
        self.current_save_bundle_paths: Dict[str, pathlib.Path] = {}
        self.save_bundle_data: Dict[str, Any] = {}
        self.save_data: Optional[dict] = None
        self.original_data: Optional[dict] = None
        self.current_character_index: Optional[int] = None
        self.current_character_data: Optional[dict] = None
        self.widget_map: Dict[str, Dict[str, Any]] = {}
        self.item_db = IntegratedItemDatabase()
        self.file_watcher = QFileSystemWatcher()
        self.modified = False
        self.selected_item_id: Optional[int] = None
        self.detected_save_roots: List[pathlib.Path] = []
        self.detected_game_paths: List[pathlib.Path] = []
        self.game_install_path: Optional[pathlib.Path] = None
        self.game_executable_path: Optional[pathlib.Path] = None
        self.last_reflection_report: Dict[str, Any] = {}

        self.init_ui()
        self.update_item_db_stats()
        self.refresh_detected_paths()
        self.discover_saves()
        self.refresh_reflection_view()
        self.setup_file_watcher()

    def init_ui(self):
        self.setWindowTitle(f"{EDITOR_NAME} v{EDITOR_VERSION}")
        self.setMinimumSize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.terminal = TerminalConsole()
        main_layout.addWidget(self.terminal)

        terminal_info = QLabel("📋 Terminal Console - bundle-aware save editing + discovery")
        terminal_info.setStyleSheet("color: #8b949e; font-size: 10px; padding: 2px;")
        main_layout.addWidget(terminal_info)

        middle_frame = QFrame()
        middle_frame.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 4px; padding: 8px;")
        middle_layout = QHBoxLayout(middle_frame)

        middle_layout.addWidget(QLabel("💾 Save Slot:"))
        self.save_combo = QComboBox()
        self.save_combo.setMinimumWidth(360)
        self.save_combo.currentIndexChanged.connect(self.on_save_selected)
        middle_layout.addWidget(self.save_combo, 1)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.discover_saves)
        middle_layout.addWidget(self.refresh_btn)

        self.open_folder_btn = QPushButton("📂 Open Save Folder")
        self.open_folder_btn.clicked.connect(self.open_save_folder)
        middle_layout.addWidget(self.open_folder_btn)

        self.open_game_folder_btn = QPushButton("🎮 Open Game Folder")
        self.open_game_folder_btn.clicked.connect(self.open_game_folder)
        middle_layout.addWidget(self.open_game_folder_btn)

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

        splitter = QSplitter(Qt.Horizontal)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([350, 1050])
        main_layout.addWidget(splitter)

        bottom_bar = self.create_bottom_bar()
        main_layout.addLayout(bottom_bar)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        self.create_menu_bar()
        self.apply_dark_theme()

        self.terminal.log_system("=" * 60)
        self.terminal.log_system(f"{EDITOR_NAME} v{EDITOR_VERSION} started")
        self.terminal.log_system("=" * 60)
        self.terminal.log_info(f"Primary save root hint: {_candidate_save_roots()[0] if _candidate_save_roots() else 'Unavailable'}")
        self.terminal.log_info(f"Preferred install hint: {KNOWN_INSTALL_HINT}")
        self.terminal.log_info(f"Item database: {ITEM_DATABASE_FILE}")

    def create_right_panel(self) -> QWidget:
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
        self.tabs.addTab(self.create_reflection_tab(), "🧭 Reflection")
        layout.addWidget(self.tabs)
        return widget

    def create_bottom_bar(self) -> QHBoxLayout:
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

        self.launch_game_btn = QPushButton("🎮 Launch Game")
        self.launch_game_btn.clicked.connect(self.launch_game)
        layout.addWidget(self.launch_game_btn)

        self.reflect_btn = QPushButton("🧭 Reflect Game Data")
        self.reflect_btn.clicked.connect(self.refresh_reflection_view)
        layout.addWidget(self.reflect_btn)

        self.scan_items_btn = QPushButton("🔍 Scan Save for Items")
        self.scan_items_btn.clicked.connect(self.scan_save_for_items)
        layout.addWidget(self.scan_items_btn)

        self.export_db_btn = QPushButton("📤 Export Item DB")
        self.export_db_btn.clicked.connect(self.export_item_database)
        layout.addWidget(self.export_db_btn)

        layout.addStretch()

        self.clear_console_btn = QPushButton(" Clear Console")
        self.clear_console_btn.clicked.connect(self.terminal.clear_console)
        layout.addWidget(self.clear_console_btn)

        return layout

    def create_raw_json_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.raw_json_text = QTextEdit()
        self.raw_json_text.setFont(QFont("Consolas", 10))
        self.raw_json_text.textChanged.connect(self.on_value_changed)
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

    def create_reflection_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QLabel("🧭 Install + save bundle reflection")
        header.setStyleSheet("font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)

        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh Reflection")
        refresh_btn.clicked.connect(self.refresh_reflection_view)
        btn_layout.addWidget(refresh_btn)

        export_btn = QPushButton("📤 Export Reflection Report")
        export_btn.clicked.connect(self.export_reflection_report)
        btn_layout.addWidget(export_btn)

        open_game_btn = QPushButton("📂 Open Game Folder")
        open_game_btn.clicked.connect(self.open_game_folder)
        btn_layout.addWidget(open_game_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.reflection_summary_label = QLabel("No reflection report yet.")
        self.reflection_summary_label.setWordWrap(True)
        layout.addWidget(self.reflection_summary_label)

        self.reflection_text = QTextEdit()
        self.reflection_text.setReadOnly(True)
        self.reflection_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.reflection_text)
        return widget

    def refresh_detected_paths(self):
        self.detected_save_roots = [path for path in _candidate_save_roots() if path.exists()]
        self.detected_game_paths = [path for path in _candidate_game_installs() if path.exists()]
        self.game_install_path = self.detected_game_paths[0] if self.detected_game_paths else None
        self.game_executable_path = _find_best_game_executable(self.game_install_path) if self.game_install_path else None

    def get_bundle_file_paths(self, save_folder: pathlib.Path) -> Dict[str, pathlib.Path]:
        return {name: save_folder / name for name in BUNDLE_FILE_NAMES}

    def load_bundle_file(self, path: pathlib.Path) -> Any:
        if not path.exists():
            return None
        return _safe_json_load(path)

    def discover_items_from_bundle(self, bundle_data: Dict[str, Any]) -> Set[int]:
        newly_discovered: Set[int] = set()
        for _, data in bundle_data.items():
            if isinstance(data, dict):
                newly_discovered.update(self.item_db.discover_items_from_save(data))
        return newly_discovered

    def discover_saves(self):
        self.refresh_detected_paths()
        self.terminal.log_info("Scanning for save slots across detected save roots...")
        self.save_combo.clear()

        if not self.detected_save_roots:
            attempted = "\n".join(str(path) for path in _candidate_save_roots())
            self.terminal.log_error("No save roots detected")
            self.status.showMessage("❌ No save roots detected")
            QMessageBox.warning(
                self,
                "Save Roots Not Found",
                f"No save roots were found. Checked:\n{attempted}\n\n"
                "Please ensure the game has been launched and at least one save exists."
            )
            return

        found_count = 0
        for save_root in self.detected_save_roots:
            try:
                character_dirs = [p for p in save_root.iterdir() if p.is_dir()]
            except Exception as e:
                self.terminal.log_warning(f"Skipping save root {save_root}: {e}")
                continue

            for character_dir in sorted(character_dirs, key=lambda p: p.name.lower()):
                save_data_dir = character_dir / "SaveData"
                if not save_data_dir.exists():
                    continue
                save_folders = [p for p in save_data_dir.iterdir() if p.is_dir()]
                for folder in sorted(save_folders, key=lambda p: p.name.lower()):
                    bundle_paths = self.get_bundle_file_paths(folder)
                    primary_path = bundle_paths[PRIMARY_SAVE_FILE]
                    if not primary_path.exists():
                        continue

                    save_name = folder.name
                    info_data = self.load_bundle_file(bundle_paths["info.dat"])
                    if isinstance(info_data, dict):
                        save_name = info_data.get("saveName") or info_data.get("name") or info_data.get("slotName") or save_name

                    label = f"{character_dir.name} | {save_name} ({folder.name})"
                    metadata = {
                        "save_root": str(save_root),
                        "character_dir": str(character_dir),
                        "save_folder": str(folder),
                    }
                    self.save_combo.addItem(label, metadata)
                    found_count += 1
                    self.terminal.log_success(f"Found save: {label}")

        self.status.showMessage(f"Found {found_count} save slot(s)")
        self.terminal.log_info(f"Total save slots found: {found_count}")

        if found_count > 0:
            self.save_combo.setCurrentIndex(0)

    def on_save_selected(self, index: int):
        if index < 0:
            return
        metadata = self.save_combo.currentData()
        if not metadata:
            return

        self.current_save_root = pathlib.Path(metadata["save_root"])
        self.current_save_folder = pathlib.Path(metadata["save_folder"])
        self.current_save_bundle_paths = self.get_bundle_file_paths(self.current_save_folder)
        self.current_save_path = self.current_save_bundle_paths[PRIMARY_SAVE_FILE]

        self.terminal.log_info(f"Loading save bundle: {self.current_save_folder}")
        try:
            self.save_bundle_data = {}
            for bundle_name, path in self.current_save_bundle_paths.items():
                bundle_data = self.load_bundle_file(path)
                if bundle_data is not None:
                    self.save_bundle_data[bundle_name] = bundle_data
                    self.terminal.log_info(f"Loaded {bundle_name}")

            self.save_data = self.save_bundle_data.get(PRIMARY_SAVE_FILE)
            if not isinstance(self.save_data, dict):
                raise ValueError(f"{PRIMARY_SAVE_FILE} did not contain valid JSON object data")

            self.original_data = json.loads(json.dumps(self.save_data))
            self.terminal.log_success("Save bundle loaded successfully")

            newly_discovered = self.discover_items_from_bundle(self.save_bundle_data)
            if newly_discovered:
                self.terminal.log_change(f"Discovered {len(newly_discovered)} new item IDs across save bundle")
                self.update_item_db_stats()
                self.refresh_item_table()
            else:
                self.terminal.log_info("No new items discovered")

            self.gold_display.blockSignals(True)
            self.gold_display.setValue(int(self.save_data.get("wealth", 0)))
            self.gold_display.blockSignals(False)

            self.populate_character_tree()
            self.populate_raw_json()
            self.modified = False
            self.update_save_button()

            existing = set(self.file_watcher.files())
            new_paths = [str(path) for path in self.current_save_bundle_paths.values() if path.exists() and str(path) not in existing]
            if new_paths:
                self.file_watcher.addPaths(new_paths)
                self.terminal.log_info("File watcher enabled for bundle files")

            self.refresh_reflection_view()
            self.terminal.log_system("=" * 40)

        except Exception as e:
            self.terminal.log_error(f"Failed to load save bundle: {e}")
            self.status.showMessage(f"❌ Error loading save bundle: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load save bundle:\n{e}")

    def populate_raw_json(self):
        if self.save_data:
            self.raw_json_text.blockSignals(True)
            self.raw_json_text.setText(json.dumps(self.save_data, indent=2))
            self.raw_json_text.blockSignals(False)

    def sync_raw_json_to_save_data(self):
        raw_text = self.raw_json_text.toPlainText().strip()
        if not raw_text:
            return
        parsed = json.loads(raw_text)
        if not isinstance(parsed, dict):
            raise ValueError("Raw JSON must be a JSON object at the root.")
        self.save_data = parsed
        self.save_bundle_data[PRIMARY_SAVE_FILE] = parsed

    def build_character_payload(self, npc: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "unitname": npc.get("unitname"),
            "humanAttribute": json.loads(json.dumps(npc.get("humanAttribute", {}))),
            "humanTalent": json.loads(json.dumps(npc.get("humanTalent", {}))),
            "heroCareer": json.loads(json.dumps(npc.get("heroCareer", {}))),
            "items": json.loads(json.dumps(npc.get("items", []))),
            "equips": json.loads(json.dumps(npc.get("equips", []))),
        }
        for category in ("Vitals", "Progression", "Morality"):
            for key in self.widget_map.get(category, {}):
                if key in npc:
                    payload[key] = npc.get(key)
        return payload

    def apply_character_payload(self, target: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        changed = False
        for key in ("humanAttribute", "humanTalent", "heroCareer", "items", "equips"):
            if key in payload:
                target[key] = json.loads(json.dumps(payload[key]))
                changed = True
        for category in ("Vitals", "Progression", "Morality"):
            for key in self.widget_map.get(category, {}):
                if key in payload:
                    target[key] = payload[key]
                    changed = True
        return changed

    def _recursive_update_key(self, node: Any, key: str, value: Any) -> int:
        count = 0
        if isinstance(node, dict):
            if key in node:
                node[key] = value
                count += 1
            for child in node.values():
                count += self._recursive_update_key(child, key, value)
        elif isinstance(node, list):
            for child in node:
                count += self._recursive_update_key(child, key, value)
        return count

    def _recursive_sync_character(self, node: Any, payload: Dict[str, Any], character_name: str) -> int:
        hits = 0
        if isinstance(node, dict):
            if node.get("unitname") == character_name:
                if self.apply_character_payload(node, payload):
                    hits += 1
            for child in node.values():
                hits += self._recursive_sync_character(child, payload, character_name)
        elif isinstance(node, list):
            for child in node:
                hits += self._recursive_sync_character(child, payload, character_name)
        return hits

    def propagate_changes_to_bundle(self):
        if not isinstance(self.save_data, dict):
            return

        self.save_bundle_data[PRIMARY_SAVE_FILE] = self.save_data
        wealth = self.save_data.get("wealth", self.gold_display.value())
        character_payload = None
        character_name = None
        if self.current_character_index is not None:
            npcs = self.save_data.get("npcs", [])
            if 0 <= self.current_character_index < len(npcs):
                source_npc = npcs[self.current_character_index]
                character_name = source_npc.get("unitname")
                character_payload = self.build_character_payload(source_npc)

        for bundle_name, bundle_data in self.save_bundle_data.items():
            if bundle_name == PRIMARY_SAVE_FILE or not isinstance(bundle_data, (dict, list)):
                continue
            wealth_hits = self._recursive_update_key(bundle_data, "wealth", wealth)
            char_hits = 0
            if character_payload and character_name:
                char_hits = self._recursive_sync_character(bundle_data, character_payload, character_name)
            self.terminal.log_info(
                f"Propagated to {bundle_name}: wealth matches updated={wealth_hits}, "
                f"character mirrors updated={char_hits}"
            )

    def write_bundle_files(self):
        for bundle_name, path in self.current_save_bundle_paths.items():
            data = self.save_bundle_data.get(bundle_name)
            if data is None:
                continue
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def backup_bundle_files(self, silent: bool = False):
        if not self.current_save_folder:
            return []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backups = []
        for bundle_name, path in self.current_save_bundle_paths.items():
            if not path.exists():
                continue
            backup_path = self.current_save_folder / f"{bundle_name}.backup_{timestamp}"
            shutil.copy2(path, backup_path)
            backups.append(backup_path)
        if backups:
            msg = f"Created {len(backups)} backup(s)"
            if silent:
                self.terminal.log_info(msg)
            else:
                self.terminal.log_success(msg)
        return backups

    def save_changes(self):
        if not self.current_save_path or not isinstance(self.save_data, dict):
            self.terminal.log_error("No save file loaded!")
            QMessageBox.warning(self, "Error", "No save file loaded!")
            return

        reply = QMessageBox.question(
            self, "Confirm Save",
            "This will overwrite the entire save bundle. A backup will be created first.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            self.terminal.log_warning("Save cancelled by user")
            return

        self.terminal.log_info("Saving changes across save bundle...")
        try:
            self.backup_bundle_files(silent=True)
            self.sync_raw_json_to_save_data()
            self.update_character_from_widgets()

            self.save_data["wealth"] = self.gold_display.value()
            self.save_bundle_data[PRIMARY_SAVE_FILE] = self.save_data

            self.propagate_changes_to_bundle()
            self.write_bundle_files()

            self.modified = False
            self.update_save_button()
            self.populate_raw_json()
            self.refresh_reflection_view()

            self.terminal.log_success("Save bundle updated successfully!")
            self.terminal.log_system("=" * 40)
            self.status.showMessage("✅ Save successful!")
            QMessageBox.information(self, "Success", "Save bundle updated successfully!")

        except Exception as e:
            self.terminal.log_error(f"Save failed: {e}")
            self.status.showMessage(f"❌ Save failed: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def create_backup(self, silent: bool = False):
        try:
            backups = self.backup_bundle_files(silent=silent)
            if not backups and not silent:
                QMessageBox.warning(self, "Backup", "No bundle files were available to back up.")
            elif backups and not silent:
                paths_preview = "\n".join(str(path) for path in backups[:8])
                QMessageBox.information(
                    self,
                    "Backup Created",
                    f"Created {len(backups)} backup file(s):\n{paths_preview}"
                )
        except Exception as e:
            self.terminal.log_error(f"Backup failed: {e}")
            if not silent:
                QMessageBox.critical(self, "Error", f"Failed to create backup:\n{e}")

    def scan_save_for_items(self):
        if not self.save_bundle_data:
            self.terminal.log_warning("No save bundle loaded")
            QMessageBox.warning(self, "No Save", "Please load a save bundle first!")
            return

        self.terminal.log_info("Scanning save bundle for new items...")
        newly_discovered = self.discover_items_from_bundle(self.save_bundle_data)

        if newly_discovered:
            self.update_item_db_stats()
            self.refresh_item_table()
            self.terminal.log_success(f"Discovered {len(newly_discovered)} new item IDs")
            QMessageBox.information(
                self,
                "Items Discovered",
                f"Found {len(newly_discovered)} new item IDs across {len(self.save_bundle_data)} loaded file(s)!\n\n"
                f"Total items in database: {len(self.item_db.items)}"
            )
        else:
            self.terminal.log_info("No new items discovered")
            QMessageBox.information(
                self,
                "Scan Complete",
                f"No new items discovered.\n\nTotal items in database: {len(self.item_db.items)}"
            )

    def open_save_folder(self):
        if self.current_save_folder:
            subprocess.run(["explorer", str(self.current_save_folder)])
            self.terminal.log_info(f"Opened save folder: {self.current_save_folder}")

    def open_game_folder(self):
        self.refresh_detected_paths()
        if self.game_install_path and self.game_install_path.exists():
            subprocess.run(["explorer", str(self.game_install_path)])
            self.terminal.log_info(f"Opened game folder: {self.game_install_path}")
        else:
            self.terminal.log_warning("Game folder not detected")
            QMessageBox.warning(self, "Game Folder Not Found", "No game install folder was detected.")

    def launch_game(self):
        self.refresh_detected_paths()
        if not self.game_executable_path or not self.game_executable_path.exists():
            self.terminal.log_error("Game executable not found")
            QMessageBox.warning(
                self,
                "Game Not Found",
                "Could not locate the game executable automatically.\n\n"
                "Use the Reflection tab to verify the detected install path."
            )
            return
        try:
            subprocess.Popen([str(self.game_executable_path)], cwd=str(self.game_executable_path.parent))
            self.terminal.log_success(f"Launched game: {self.game_executable_path.name}")
            self.status.showMessage("✅ Game launch requested")
        except Exception as e:
            self.terminal.log_error(f"Launch failed: {e}")
            QMessageBox.critical(self, "Launch Failed", f"Could not launch game:\n{e}")

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Save Folder...", self)
        open_action.triggered.connect(self.open_save_folder)
        file_menu.addAction(open_action)

        open_game_action = QAction("Open &Game Folder...", self)
        open_game_action.triggered.connect(self.open_game_folder)
        file_menu.addAction(open_game_action)

        launch_action = QAction("&Launch Game", self)
        launch_action.triggered.connect(self.launch_game)
        file_menu.addAction(launch_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("&Tools")

        refresh_paths_action = QAction("&Refresh Discovery", self)
        refresh_paths_action.triggered.connect(self.refresh_reflection_view)
        tools_menu.addAction(refresh_paths_action)

        reflect_action = QAction("&Export Reflection Report", self)
        reflect_action.triggered.connect(self.export_reflection_report)
        tools_menu.addAction(reflect_action)

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
        stats = self.item_db.get_statistics()
        QMessageBox.about(self, "About Save Editor",
            f"<h3>Age of Reforging: The Freelands</h3>"
            f"<p>Complete Save Game Editor v{EDITOR_VERSION}</p>"
            f"<p><b>Features:</b></p>"
            f"<ul>"
            f"<li>✅ Save bundle editing (sav.dat / story.dat / info.dat / 000-AWayToBrea.dat)</li>"
            f"<li>✅ Dynamic save-root discovery by current Windows user / character folders</li>"
            f"<li>✅ Dynamic Steam install discovery with reflection report</li>"
            f"<li>✅ Launch game button</li>"
            f"<li>✅ Integrated item database ({stats['total_items']} items)</li>"
            f"<li>✅ Auto-discovery of new items from entire save bundle</li>"
            f"</ul>"
            f"<p><b>Item Database:</b></p>"
            f"<ul>"
            f"<li>Named: {stats['named_items']}</li>"
            f"<li>Unknown: {stats['unknown_items']}</li>"
            f"</ul>"
            f"<p>⚠️ Always backup saves before editing!</p>")

    def setup_file_watcher(self):
        self.file_watcher.fileChanged.connect(self.on_save_file_changed)

    def on_save_file_changed(self, path: str):
        self.terminal.log_warning(f"Bundle file changed on disk: {path}")
        self.status.showMessage("⚠️ Save bundle changed on disk - Reload recommended")

    def generate_reflection_report(self) -> Dict[str, Any]:
        self.refresh_detected_paths()
        report: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "game_name": GAME_NAME,
            "detected_save_roots": [str(path) for path in self.detected_save_roots],
            "detected_game_paths": [str(path) for path in self.detected_game_paths],
            "selected_save_folder": str(self.current_save_folder) if self.current_save_folder else None,
            "selected_game_install": str(self.game_install_path) if self.game_install_path else None,
            "install_scan": {},
            "save_scan": {},
        }

        if self.game_install_path and self.game_install_path.exists():
            extension_counts: Dict[str, int] = defaultdict(int)
            candidate_files: List[str] = []
            file_count = 0
            dir_count = 0
            total_bytes = 0
            for root, dirs, files in os.walk(self.game_install_path):
                dir_count += len(dirs)
                for filename in files:
                    file_count += 1
                    path = pathlib.Path(root) / filename
                    ext = path.suffix.lower() or "<noext>"
                    extension_counts[ext] += 1
                    try:
                        total_bytes += path.stat().st_size
                    except Exception:
                        pass
                    lower_name = filename.lower()
                    if (
                        ext in {".dat", ".json", ".txt", ".ini", ".xml", ".bundle", ".asset", ".bytes"}
                        or any(token in lower_name for token in ("item", "master", "weapon", "skill", "save", "stat", "equip"))
                    ):
                        if len(candidate_files) < 300:
                            candidate_files.append(str(path))
            report["install_scan"] = {
                "root": str(self.game_install_path),
                "file_count": file_count,
                "dir_count": dir_count,
                "total_bytes": total_bytes,
                "extension_counts": dict(sorted(extension_counts.items(), key=lambda x: (-x[1], x[0]))),
                "candidate_editor_relevant_files": candidate_files,
                "game_executable": str(self.game_executable_path) if self.game_executable_path else None,
            }

        for save_root in self.detected_save_roots:
            save_root_entry: Dict[str, Any] = {"characters": []}
            try:
                character_dirs = [p for p in save_root.iterdir() if p.is_dir()]
            except Exception:
                character_dirs = []
            for character_dir in sorted(character_dirs, key=lambda p: p.name.lower()):
                save_data_dir = character_dir / "SaveData"
                if not save_data_dir.exists():
                    continue
                char_entry: Dict[str, Any] = {"character": character_dir.name, "slots": []}
                for slot_dir in sorted([p for p in save_data_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
                    files = []
                    for bundle_name in BUNDLE_FILE_NAMES:
                        path = slot_dir / bundle_name
                        if path.exists():
                            data = _safe_json_load(path)
                            files.append({
                                "file": bundle_name,
                                "path": str(path),
                                "exists": True,
                                "root_type": _summarize_type(data),
                                "keys": sorted(list(data.keys()))[:40] if isinstance(data, dict) else [],
                            })
                    if files:
                        char_entry["slots"].append({"slot": slot_dir.name, "files": files})
                if char_entry["slots"]:
                    save_root_entry["characters"].append(char_entry)
            report["save_scan"][str(save_root)] = save_root_entry

        return report

    def refresh_reflection_view(self):
        report = self.generate_reflection_report()
        self.last_reflection_report = report
        summary_bits = [
            f"Save roots: {len(report.get('detected_save_roots', []))}",
            f"Install paths: {len(report.get('detected_game_paths', []))}",
        ]
        install_scan = report.get("install_scan", {})
        if install_scan:
            summary_bits.append(f"Install files: {install_scan.get('file_count', 0)}")
        if self.current_save_folder:
            summary_bits.append(f"Active save: {self.current_save_folder.name}")
        summary = " | ".join(summary_bits)
        if hasattr(self, "reflection_summary_label"):
            self.reflection_summary_label.setText(summary)
        if hasattr(self, "reflection_text"):
            self.reflection_text.setText(json.dumps(report, indent=2))
        self.terminal.log_info("Reflection report refreshed")

    def export_reflection_report(self):
        if not self.last_reflection_report:
            self.refresh_reflection_view()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Reflection Report",
            str(REFLECTION_REPORT_FILE),
            "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.last_reflection_report, f, indent=2)
            self.terminal.log_success(f"Reflection report exported to: {file_path}")
            QMessageBox.information(self, "Export Complete", f"Reflection report exported to:\n{file_path}")


class PatchedSaveGameEditorV42(PatchedSaveGameEditor):
    DYNAMIC_ATTR_SKIP_BRANCHES = {"items", "equips", "npcs", "caravan", "shops", "inventory", "stash", "addattrs"}
    WEAPON_MASTERY_TOKENS = {
        "unarmed", "onehanded", "onehand", "twohanded", "twohand", "shield",
        "ranged", "dual", "polearm", "polearms"
    }
    CARRY_TOKENS = {
        "encumbrance", "encumberance", "carry", "carryweight", "maxcarry", "weight",
        "maxweight", "load", "burden"
    }

    def __init__(self):
        self.dynamic_attr_widget_map = {}
        self.dynamic_attr_original_types = {}
        self.special_attr_form_widget = None
        self.special_attr_host_layout = None
        self.special_attr_info_label = None
        self.equipment_editor_row_map = {}
        self._populating_equipment_table = False
        super().__init__()

    def _normalize_token(self, value: Any) -> str:
        return re.sub(r'[^a-z0-9]+', '', str(value).strip().lower())

    def _split_words(self, value: Any) -> str:
        text = str(value).replace('_', ' ').replace('-', ' ')
        text = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text.title() if text else str(value)

    def _friendly_path_label(self, path_parts: Tuple[Any, ...]) -> str:
        pieces = [self._split_words(part) for part in path_parts]
        label = ' / '.join(pieces)
        replacements = {
            'One Handed': 'One-handed',
            'Two Handed': 'Two-handed',
            'Carryweight': 'Carry Weight',
            'Maxweight': 'Max Weight',
            'Encumberance': 'Encumbrance',
        }
        for old, new in replacements.items():
            label = label.replace(old, new)
        return label

    def _iter_numeric_leaf_paths(self, node: Any, path_parts: Tuple[Any, ...] = ()):
        if isinstance(node, dict):
            for key, value in node.items():
                norm_key = self._normalize_token(key)
                if norm_key in self.DYNAMIC_ATTR_SKIP_BRANCHES:
                    continue
                yield from self._iter_numeric_leaf_paths(value, path_parts + (key,))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                if isinstance(value, (dict, list)):
                    yield from self._iter_numeric_leaf_paths(value, path_parts + (index,))
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            yield path_parts, node

    def _is_dynamic_combat_or_carry_path(self, path_parts: Tuple[Any, ...]) -> bool:
        normalized = [self._normalize_token(part) for part in path_parts if not isinstance(part, int)]
        path_join = '.'.join(normalized)
        if not normalized:
            return False
        if any(token in self.WEAPON_MASTERY_TOKENS for token in normalized):
            return True
        if 'mastery' in path_join and any(token in path_join for token in self.WEAPON_MASTERY_TOKENS):
            return True
        if any(token in self.CARRY_TOKENS for token in normalized):
            return True
        if 'carry' in path_join or 'encumbr' in path_join or 'weight' in path_join:
            return True
        return False

    def _dynamic_attr_sort_key(self, candidate: Dict[str, Any]):
        label_norm = self._normalize_token(candidate['label'])
        order = [
            'unarmed', 'onehanded', 'twohanded', 'shield', 'ranged', 'dual', 'polearm',
            'encumbrance', 'carry', 'weight', 'load', 'burden'
        ]
        for idx, token in enumerate(order):
            if token in label_norm:
                return (idx, candidate['label'].lower())
        return (len(order), candidate['label'].lower())

    def _extract_dynamic_combat_carry_candidates(self, npc: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        seen = set()
        for path_parts, value in self._iter_numeric_leaf_paths(npc):
            if not path_parts:
                continue
            leaf_key = path_parts[-1]
            if isinstance(leaf_key, str) and leaf_key in STAT_CATEGORIES['Attributes']:
                continue
            if not self._is_dynamic_combat_or_carry_path(path_parts):
                continue
            key = tuple(path_parts)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({
                'path': key,
                'label': self._friendly_path_label(key),
                'value': value,
                'is_float': isinstance(value, float) and not float(value).is_integer(),
                'original_type': float if isinstance(value, float) else int,
            })
        return sorted(candidates, key=self._dynamic_attr_sort_key)

    def _get_nested_value(self, node: Any, path_parts: Tuple[Any, ...], default: Any = None) -> Any:
        current = node
        for part in path_parts:
            if isinstance(part, int):
                if not isinstance(current, list) or part >= len(current):
                    return default
                current = current[part]
            else:
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
        return current

    def _set_nested_value(self, node: Any, path_parts: Tuple[Any, ...], value: Any) -> bool:
        if not path_parts:
            return False
        current = node
        for part in path_parts[:-1]:
            if isinstance(part, int):
                if not isinstance(current, list) or part >= len(current):
                    return False
                current = current[part]
            else:
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]
        leaf = path_parts[-1]
        if isinstance(leaf, int):
            if not isinstance(current, list) or leaf >= len(current):
                return False
            current[leaf] = value
            return True
        if not isinstance(current, dict):
            return False
        current[leaf] = value
        return True

    def _cast_dynamic_value(self, path_parts: Tuple[Any, ...], value: Any) -> Any:
        original_type = self.dynamic_attr_original_types.get(path_parts, float if isinstance(value, float) else int)
        try:
            if original_type is float:
                return float(value)
            return int(round(float(value)))
        except Exception:
            return value

    def on_dynamic_attr_changed(self, path_parts: Tuple[Any, ...], _value: Any):
        if self.current_character_index is None or not isinstance(self.save_data, dict):
            self.on_value_changed()
            return
        npcs = self.save_data.get('npcs', [])
        if not (0 <= self.current_character_index < len(npcs)):
            self.on_value_changed()
            return
        widget = self.dynamic_attr_widget_map.get(path_parts)
        if widget is None:
            self.on_value_changed()
            return
        value = widget.value()
        cast_value = self._cast_dynamic_value(path_parts, value)
        npc = npcs[self.current_character_index]
        self._set_nested_value(npc, path_parts, cast_value)
        self.current_character_data = npc
        self.on_value_changed()

    def create_attributes_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        base_group = QGroupBox('Primary Attributes')
        base_layout = QFormLayout(base_group)
        base_layout.setSpacing(8)
        base_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.widget_map['Attributes'] = {}
        for key, config in STAT_CATEGORIES['Attributes'].items():
            label = config[0]
            min_val = config[1]
            max_val = config[2]
            spin = QSpinBox()
            spin.setRange(min_val, max_val)
            spin.valueChanged.connect(self.on_value_changed)
            base_layout.addRow(label, spin)
            self.widget_map['Attributes'][key] = spin
        layout.addWidget(base_group)

        self.special_attr_group = QGroupBox('Weapon Masteries / Encumbrance (auto-discovered)')
        group_layout = QVBoxLayout(self.special_attr_group)
        self.special_attr_info_label = QLabel('Load a character to detect mastery and carry-weight fields in the save data.')
        self.special_attr_info_label.setWordWrap(True)
        self.special_attr_info_label.setStyleSheet('color: #8b949e;')
        group_layout.addWidget(self.special_attr_info_label)
        self.special_attr_host_layout = QVBoxLayout()
        group_layout.addLayout(self.special_attr_host_layout)
        layout.addWidget(self.special_attr_group)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll

    def rebuild_dynamic_attribute_widgets(self, npc: Dict[str, Any]):
        candidates = self._extract_dynamic_combat_carry_candidates(npc)
        self.dynamic_attr_widget_map = {}
        self.dynamic_attr_original_types = {}

        if self.special_attr_form_widget is not None and self.special_attr_host_layout is not None:
            self.special_attr_host_layout.removeWidget(self.special_attr_form_widget)
            self.special_attr_form_widget.deleteLater()
            self.special_attr_form_widget = None

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        if not candidates:
            self.special_attr_info_label.setText('No obvious weapon mastery or encumbrance keys were discovered for this character yet.')
        else:
            self.special_attr_info_label.setText(
                'These fields were discovered directly from the selected character payload and will save back into the bundle.'
            )

        for candidate in candidates:
            path_parts = candidate['path']
            value = candidate['value']
            label = candidate['label']
            is_float = candidate['is_float']
            if is_float:
                editor = QDoubleSpinBox()
                editor.setDecimals(3)
                editor.setRange(-999999.0, 999999.0)
                editor.setSingleStep(0.5)
                editor.setValue(float(value))
                editor.valueChanged.connect(lambda _v, p=path_parts: self.on_dynamic_attr_changed(p, _v))
            else:
                editor = QSpinBox()
                editor.setRange(-999999, 999999)
                editor.setValue(int(value))
                editor.valueChanged.connect(lambda _v, p=path_parts: self.on_dynamic_attr_changed(p, _v))
            form_layout.addRow(label, editor)
            self.dynamic_attr_widget_map[path_parts] = editor
            self.dynamic_attr_original_types[path_parts] = candidate['original_type']

        self.special_attr_form_widget = form_widget
        if self.special_attr_host_layout is not None:
            self.special_attr_host_layout.addWidget(form_widget)

    def populate_attributes(self, npc: Dict):
        super().populate_attributes(npc)
        self.rebuild_dynamic_attribute_widgets(npc)

    def _render_inventory_preview_text(self, npc: Dict[str, Any]) -> str:
        equips = npc.get('equips', [])
        items = npc.get('items', [])
        text = '=== EQUIPMENT ===\n\n'
        for i, item in enumerate(equips):
            if item:
                item_id = item.get('id', 0)
                item_name = self.item_db.get_item_name(item_id)
                durability = item.get('durability', 0)
                quality = item.get('quality', 0)
                text += f"Slot {i}: [{item_id}] {item_name}\n"
                text += f"  Durability: {durability} | Quality: {quality}\n\n"
            else:
                text += f'Slot {i}: [Empty]\n\n'
        text += '\n=== INVENTORY ===\n\n'
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
                text += f'Slot {i}: [Empty]\n\n'
        return text

    def create_inventory_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        db_info = QLabel(f"📦 Item Database: {len(self.item_db.items)} items loaded")
        db_info.setStyleSheet('color: #3fb950; font-weight: bold;')
        layout.addWidget(db_info)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('🔍 Search:'))
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText('Search by name or ID...')
        self.item_search.textChanged.connect(self.search_items)
        search_layout.addWidget(self.item_search, 1)
        layout.addLayout(search_layout)

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(['Item ID', 'Name', 'Category'])
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.item_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.item_table.setMaximumHeight(180)
        self.item_table.cellClicked.connect(self.on_item_selected)
        layout.addWidget(self.item_table)

        layout.addWidget(QLabel('\n🛡️ Current Equipment (editable):'))
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(7)
        self.equipment_table.setHorizontalHeaderLabels(['Slot', 'Item ID', 'Name', 'Durability', 'Quality', 'New', 'Stolen'])
        self.equipment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.equipment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.equipment_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.equipment_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.equipment_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.equipment_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.equipment_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.equipment_table.setMinimumHeight(220)
        layout.addWidget(self.equipment_table)

        equipment_tip = QLabel('Edit durability/quality and save. Changes are written back into the active equipment payload and then propagated across the save bundle.')
        equipment_tip.setWordWrap(True)
        equipment_tip.setStyleSheet('color: #8b949e; font-style: italic;')
        layout.addWidget(equipment_tip)

        layout.addWidget(QLabel('\n📦 Inventory Preview:'))
        self.inventory_text = QTextEdit()
        self.inventory_text.setReadOnly(True)
        self.inventory_text.setMaximumHeight(220)
        layout.addWidget(self.inventory_text)

        btn_layout = QHBoxLayout()
        self.edit_item_btn = QPushButton('✏️ Rename Item in DB')
        self.edit_item_btn.clicked.connect(self.rename_item_in_database)
        btn_layout.addWidget(self.edit_item_btn)
        self.add_item_btn = QPushButton('➕ Add Item')
        self.add_item_btn.clicked.connect(self.add_inventory_item)
        btn_layout.addWidget(self.add_item_btn)
        self.remove_item_btn = QPushButton('🗑️ Remove Item')
        self.remove_item_btn.clicked.connect(self.remove_inventory_item)
        btn_layout.addWidget(self.remove_item_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        info_label = QLabel('💡 Tip: item IDs auto-discover from saves, and equipment values here are directly editable.')
        info_label.setStyleSheet('color: #8b949e; font-style: italic;')
        layout.addWidget(info_label)

        return widget

    def on_equipment_editor_changed(self, *_args):
        if self._populating_equipment_table:
            return
        if self.current_character_index is None or not isinstance(self.save_data, dict):
            self.on_value_changed()
            return
        npcs = self.save_data.get('npcs', [])
        if not (0 <= self.current_character_index < len(npcs)):
            self.on_value_changed()
            return
        npc = npcs[self.current_character_index]
        self.sync_equipment_table_to_npc(npc)
        self.current_character_data = npc
        self.inventory_text.setText(self._render_inventory_preview_text(npc))
        self.on_value_changed()

    def sync_equipment_table_to_npc(self, npc: Dict[str, Any]) -> List[str]:
        changes = []
        equips = npc.get('equips', [])
        if not isinstance(equips, list):
            return changes

        for row, slot_index in self.equipment_editor_row_map.items():
            if slot_index >= len(equips):
                continue
            item = equips[slot_index]
            if not isinstance(item, dict):
                continue
            durability_widget = self.equipment_table.cellWidget(row, 3)
            quality_widget = self.equipment_table.cellWidget(row, 4)
            new_widget = self.equipment_table.cellWidget(row, 5)
            stolen_widget = self.equipment_table.cellWidget(row, 6)
            if durability_widget is None or quality_widget is None or new_widget is None or stolen_widget is None:
                continue

            new_durability = float(durability_widget.value())
            new_quality = int(quality_widget.value())
            new_is_new = bool(new_widget.isChecked())
            new_is_stolen = int(stolen_widget.value())

            old_durability = float(item.get('durability', 0))
            old_quality = int(item.get('quality', 0))
            old_is_new = bool(item.get('isNew', False))
            old_is_stolen = int(item.get('isStolen', 0))

            if abs(old_durability - new_durability) > 0.0001:
                changes.append(f"equipment[{slot_index}].durability: {old_durability} → {new_durability}")
                item['durability'] = new_durability
            if old_quality != new_quality:
                changes.append(f"equipment[{slot_index}].quality: {old_quality} → {new_quality}")
                item['quality'] = new_quality
            if old_is_new != new_is_new:
                changes.append(f"equipment[{slot_index}].isNew: {old_is_new} → {new_is_new}")
                item['isNew'] = new_is_new
            if old_is_stolen != new_is_stolen:
                changes.append(f"equipment[{slot_index}].isStolen: {old_is_stolen} → {new_is_stolen}")
                item['isStolen'] = new_is_stolen
        return changes

    def populate_inventory(self, npc: Dict):
        self.inventory_text.setText(self._render_inventory_preview_text(npc))

        equips = npc.get('equips', [])
        self._populating_equipment_table = True
        self.equipment_editor_row_map = {}
        self.equipment_table.setRowCount(len(equips))

        for row, item in enumerate(equips):
            self.equipment_editor_row_map[row] = row
            slot_item = QTableWidgetItem(str(row))
            slot_item.setFlags(slot_item.flags() & ~Qt.ItemIsEditable)
            self.equipment_table.setItem(row, 0, slot_item)

            if item and isinstance(item, dict):
                item_id = int(item.get('id', 0))
                item_name = self.item_db.get_item_name(item_id)
                id_item = QTableWidgetItem(str(item_id))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                name_item = QTableWidgetItem(item_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.equipment_table.setItem(row, 1, id_item)
                self.equipment_table.setItem(row, 2, name_item)

                durability = QDoubleSpinBox()
                durability.setDecimals(3)
                durability.setRange(0.0, 999999.0)
                durability.setSingleStep(1.0)
                durability.setValue(float(item.get('durability', 0)))
                durability.valueChanged.connect(self.on_equipment_editor_changed)
                self.equipment_table.setCellWidget(row, 3, durability)

                quality = QSpinBox()
                quality.setRange(0, 999999)
                quality.setValue(int(item.get('quality', 0)))
                quality.valueChanged.connect(self.on_equipment_editor_changed)
                self.equipment_table.setCellWidget(row, 4, quality)

                is_new = QCheckBox()
                is_new.setChecked(bool(item.get('isNew', False)))
                is_new.stateChanged.connect(self.on_equipment_editor_changed)
                new_holder = QWidget()
                new_holder_layout = QHBoxLayout(new_holder)
                new_holder_layout.setContentsMargins(6, 0, 6, 0)
                new_holder_layout.addWidget(is_new)
                new_holder_layout.addStretch()
                self.equipment_table.setCellWidget(row, 5, new_holder)

                stolen = QSpinBox()
                stolen.setRange(0, 999999)
                stolen.setValue(int(item.get('isStolen', 0)))
                stolen.valueChanged.connect(self.on_equipment_editor_changed)
                self.equipment_table.setCellWidget(row, 6, stolen)
            else:
                for col, value in [(1, ''), (2, '[Empty]')]:
                    cell = QTableWidgetItem(value)
                    cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                    self.equipment_table.setItem(row, col, cell)
                for col in (3, 4, 5, 6):
                    empty_cell = QTableWidgetItem('')
                    empty_cell.setFlags(empty_cell.flags() & ~Qt.ItemIsEditable)
                    self.equipment_table.setItem(row, col, empty_cell)
        self._populating_equipment_table = False

    def _read_checkbox_from_holder(self, holder: QWidget) -> bool:
        if holder is None:
            return False
        checkbox = holder.findChild(QCheckBox)
        return checkbox.isChecked() if checkbox else False

    def sync_equipment_table_to_npc(self, npc: Dict[str, Any]) -> List[str]:
        changes = []
        equips = npc.get('equips', [])
        if not isinstance(equips, list):
            return changes
        for row, slot_index in self.equipment_editor_row_map.items():
            if slot_index >= len(equips):
                continue
            item = equips[slot_index]
            if not isinstance(item, dict):
                continue
            durability_widget = self.equipment_table.cellWidget(row, 3)
            quality_widget = self.equipment_table.cellWidget(row, 4)
            new_holder = self.equipment_table.cellWidget(row, 5)
            stolen_widget = self.equipment_table.cellWidget(row, 6)
            if durability_widget is None or quality_widget is None or stolen_widget is None:
                continue
            new_durability = float(durability_widget.value())
            new_quality = int(quality_widget.value())
            new_is_new = self._read_checkbox_from_holder(new_holder)
            new_is_stolen = int(stolen_widget.value())
            old_durability = float(item.get('durability', 0))
            old_quality = int(item.get('quality', 0))
            old_is_new = bool(item.get('isNew', False))
            old_is_stolen = int(item.get('isStolen', 0))
            if abs(old_durability - new_durability) > 0.0001:
                changes.append(f"equipment[{slot_index}].durability: {old_durability} → {new_durability}")
                item['durability'] = new_durability
            if old_quality != new_quality:
                changes.append(f"equipment[{slot_index}].quality: {old_quality} → {new_quality}")
                item['quality'] = new_quality
            if old_is_new != new_is_new:
                changes.append(f"equipment[{slot_index}].isNew: {old_is_new} → {new_is_new}")
                item['isNew'] = new_is_new
            if old_is_stolen != new_is_stolen:
                changes.append(f"equipment[{slot_index}].isStolen: {old_is_stolen} → {new_is_stolen}")
                item['isStolen'] = new_is_stolen
        return changes

    def update_character_from_widgets(self):
        super().update_character_from_widgets()
        if self.current_character_index is None or not isinstance(self.save_data, dict):
            return
        npcs = self.save_data.get('npcs', [])
        if not (0 <= self.current_character_index < len(npcs)):
            return
        npc = npcs[self.current_character_index]
        self.current_character_data = npc
        char_name = npc.get('unitname', 'Unknown')
        extra_changes = []
        for path_parts, widget in self.dynamic_attr_widget_map.items():
            new_value = self._cast_dynamic_value(path_parts, widget.value())
            old_value = self._get_nested_value(npc, path_parts, None)
            if old_value != new_value:
                extra_changes.append(f"{self._friendly_path_label(path_parts)}: {old_value} → {new_value}")
            self._set_nested_value(npc, path_parts, new_value)
        extra_changes.extend(self.sync_equipment_table_to_npc(npc))
        if extra_changes:
            self.terminal.log_change(f"Character '{char_name}' extended changes:")
            for change in extra_changes[:12]:
                self.terminal.log_info(f"  {change}")
            if len(extra_changes) > 12:
                self.terminal.log_info(f"  ... and {len(extra_changes) - 12} more changes")
        self.inventory_text.setText(self._render_inventory_preview_text(npc))

    def build_character_payload(self, npc: Dict[str, Any]) -> Dict[str, Any]:
        payload = super().build_character_payload(npc)
        payload['__dynamic_numeric_paths__'] = [
            {
                'path': list(candidate['path']),
                'value': self._get_nested_value(npc, candidate['path'])
            }
            for candidate in self._extract_dynamic_combat_carry_candidates(npc)
        ]
        return payload

    def apply_character_payload(self, target: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        changed = super().apply_character_payload(target, payload)
        for entry in payload.get('__dynamic_numeric_paths__', []):
            path_parts = tuple(entry.get('path', []))
            if not path_parts:
                continue
            if self._set_nested_value(target, path_parts, entry.get('value')):
                changed = True
        return changed



class PatchedSaveGameEditorV43(PatchedSaveGameEditorV42):
    FUZZY_STAT_ALIASES = {
        'Unarmed': ['unarmed'],
        'One-handed': ['one handed', 'one-handed', 'onehanded', 'one hand'],
        'Two-handed': ['two handed', 'two-handed', 'twohanded', 'two hand'],
        'Shield': ['shield'],
        'Ranged': ['ranged'],
        'Dual': ['dual'],
        'Polearms': ['polearms', 'polearm'],
        'Encumbrance': ['encumbrance', 'encumberance', 'carry weight', 'carryweight', 'current weight', 'load', 'burden'],
        'Carry Capacity': ['carry capacity', 'max carry', 'maximum carry', 'max weight', 'weight capacity', 'capacity'],
    }
    FUZZY_STAT_ORDER = [
        'Unarmed', 'One-handed', 'Two-handed', 'Shield', 'Ranged', 'Dual', 'Polearms', 'Encumbrance', 'Carry Capacity'
    ]
    DESCRIPTOR_HINT_KEYS = {
        'name', 'label', 'title', 'type', 'stat', 'key', 'kind', 'skill', 'mastery', 'masteryname', 'skillname'
    }
    NUMERIC_VALUE_HINT_KEYS = {
        'value', 'level', 'amount', 'current', 'currentvalue', 'points', 'score', 'rank', 'num', 'weight', 'max', 'maximum'
    }

    def __init__(self):
        self.dynamic_attr_bindings = {}
        super().__init__()

    def _tokenize_for_fuzzy(self, value: Any) -> List[str]:
        tokens = re.findall(r'[a-z0-9]+', str(value).replace('_', ' ').replace('-', ' ').lower())
        return [token for token in tokens if token]

    def _fuzzy_match_score(self, text: str, alias: str) -> float:
        text_norm = self._normalize_token(text)
        alias_norm = self._normalize_token(alias)
        if not text_norm or not alias_norm:
            return 0.0
        if text_norm == alias_norm:
            return 1.0

        text_tokens = set(self._tokenize_for_fuzzy(text))
        alias_tokens = set(self._tokenize_for_fuzzy(alias))
        overlap = (len(text_tokens & alias_tokens) / len(alias_tokens)) if alias_tokens else 0.0
        seq_ratio = difflib.SequenceMatcher(None, alias_norm, text_norm).ratio()

        score = max(overlap * 0.9, seq_ratio * 0.78)
        if alias_norm in text_norm:
            score = max(score, 0.97)
        elif text_norm in alias_norm and len(text_norm) >= 5:
            score = max(score, 0.84)
        if alias_tokens and alias_tokens.issubset(text_tokens):
            score = max(score, 0.95)
        return min(score, 1.0)

    def _best_fuzzy_stat_label(self, text: str) -> Tuple[Optional[str], float]:
        best_label = None
        best_score = 0.0
        for label, aliases in self.FUZZY_STAT_ALIASES.items():
            for alias in aliases:
                score = self._fuzzy_match_score(text, alias)
                if score > best_score:
                    best_label = label
                    best_score = score
        threshold = 0.72
        if best_label == 'Carry Capacity':
            threshold = 0.68
        return (best_label, best_score) if best_score >= threshold else (None, best_score)

    def _iter_fuzzy_numeric_candidates(self, node: Any, path_parts: Tuple[Any, ...] = (), context_character: Optional[str] = None):
        if isinstance(node, dict):
            current_character = context_character
            if isinstance(node.get('unitname'), str):
                current_character = node.get('unitname')

            descriptor_values: List[str] = []
            numeric_items: List[Tuple[Any, Any]] = []

            for key, value in node.items():
                key_norm = self._normalize_token(key)
                if isinstance(value, str) and key_norm in self.DESCRIPTOR_HINT_KEYS:
                    descriptor_values.append(value)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_items.append((key, value))

            if descriptor_values and numeric_items:
                descriptor_text = ' '.join(descriptor_values)
                for num_key, num_value in numeric_items:
                    num_key_norm = self._normalize_token(num_key)
                    if num_key_norm and num_key_norm not in self.NUMERIC_VALUE_HINT_KEYS and len(numeric_items) > 1:
                        continue
                    yield {
                        'path': path_parts + (num_key,),
                        'value': num_value,
                        'context_character': current_character,
                        'match_text': f"{self._friendly_path_label(path_parts)} {descriptor_text} {self._split_words(num_key)}".strip(),
                        'source': 'descriptor',
                    }

            for key, value in node.items():
                key_norm = self._normalize_token(key)
                if key_norm in self.DYNAMIC_ATTR_SKIP_BRANCHES:
                    continue
                yield from self._iter_fuzzy_numeric_candidates(value, path_parts + (key,), current_character)

        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from self._iter_fuzzy_numeric_candidates(value, path_parts + (index,), context_character)

        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            yield {
                'path': path_parts,
                'value': node,
                'context_character': context_character,
                'match_text': self._friendly_path_label(path_parts),
                'source': 'path',
            }

    def _rank_fuzzy_hit(self, hit: Dict[str, Any], current_character_name: Optional[str]) -> Tuple[float, int, int, int]:
        score = float(hit.get('score', 0.0))
        char_match = 1 if current_character_name and hit.get('context_character') == current_character_name else 0
        primary = 1 if hit.get('bundle_name') == PRIMARY_SAVE_FILE else 0
        depth = len(hit.get('path', ()))
        return (score, char_match, primary, -depth)

    def _dedupe_fuzzy_hits(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped = {}
        for hit in hits:
            key = (hit.get('bundle_name'), tuple(hit.get('path', ())), hit.get('label'))
            if key not in deduped or self._rank_fuzzy_hit(hit, hit.get('selected_character')) > self._rank_fuzzy_hit(deduped[key], deduped[key].get('selected_character')):
                deduped[key] = hit
        return list(deduped.values())

    def _discover_fuzzy_stat_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        current_character_name = npc.get('unitname') if isinstance(npc, dict) else None
        hits: List[Dict[str, Any]] = []

        for bundle_name, bundle_data in self.save_bundle_data.items():
            if not isinstance(bundle_data, (dict, list)):
                continue
            for candidate in self._iter_fuzzy_numeric_candidates(bundle_data):
                match_text = f"{bundle_name} {candidate['match_text']}"
                label, score = self._best_fuzzy_stat_label(match_text)
                if not label:
                    continue
                hit = dict(candidate)
                hit['bundle_name'] = bundle_name
                hit['label'] = label
                hit['score'] = score
                hit['selected_character'] = current_character_name
                hit['is_float'] = isinstance(candidate.get('value'), float) and not float(candidate.get('value')).is_integer()
                hits.append(hit)

        hits = self._dedupe_fuzzy_hits(hits)
        bindings: Dict[str, Dict[str, Any]] = {}

        for label in self.FUZZY_STAT_ORDER:
            label_hits = [hit for hit in hits if hit['label'] == label]
            if not label_hits:
                continue

            char_hits = [hit for hit in label_hits if current_character_name and hit.get('context_character') == current_character_name]
            preferred_hits = char_hits if char_hits else label_hits
            preferred_hits = sorted(preferred_hits, key=lambda hit: self._rank_fuzzy_hit(hit, current_character_name), reverse=True)
            best_hit = preferred_hits[0]

            if char_hits:
                floor = max(0.72, float(best_hit['score']) - 0.08)
                selected_targets = [hit for hit in preferred_hits if float(hit['score']) >= floor]
            else:
                selected_targets = [best_hit]

            targets = []
            seen_targets = set()
            for hit in selected_targets:
                target_key = (hit['bundle_name'], tuple(hit['path']))
                if target_key in seen_targets:
                    continue
                seen_targets.add(target_key)
                targets.append({
                    'bundle_name': hit['bundle_name'],
                    'path': tuple(hit['path']),
                    'display_path': self._friendly_path_label(hit['path']),
                    'source': hit.get('source', 'path'),
                })

            bindings[label] = {
                'label': label,
                'value': best_hit['value'],
                'is_float': bool(best_hit['is_float']),
                'original_type': float if isinstance(best_hit['value'], float) else int,
                'targets': targets,
                'context_character': best_hit.get('context_character'),
                'score': best_hit['score'],
                'bundle_sources': sorted({target['bundle_name'] for target in targets}),
            }

        return bindings

    def rebuild_dynamic_attribute_widgets(self, npc: Dict[str, Any]):
        self.dynamic_attr_bindings = self._discover_fuzzy_stat_bindings(npc)
        self.dynamic_attr_widget_map = {}
        self.dynamic_attr_original_types = {}

        if self.special_attr_form_widget is not None and self.special_attr_host_layout is not None:
            self.special_attr_host_layout.removeWidget(self.special_attr_form_widget)
            self.special_attr_form_widget.deleteLater()
            self.special_attr_form_widget = None

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        if not self.dynamic_attr_bindings:
            self.special_attr_info_label.setText(
                'No fuzzy matches were found yet for Unarmed / One-handed / Two-handed / Shield / Ranged / Dual / Polearms / Encumbrance across the loaded save .dat files.'
            )
        else:
            discovered = ', '.join([label for label in self.FUZZY_STAT_ORDER if label in self.dynamic_attr_bindings])
            self.special_attr_info_label.setText(
                f'Fuzzy-matched across loaded save .dat files for the selected character where possible: {discovered}'
            )

        for label in self.FUZZY_STAT_ORDER:
            binding = self.dynamic_attr_bindings.get(label)
            if not binding:
                continue

            value = binding['value']
            if binding['is_float']:
                editor = QDoubleSpinBox()
                editor.setDecimals(3)
                editor.setRange(-999999.0, 999999.0)
                editor.setSingleStep(0.5)
                editor.setValue(float(value))
                editor.valueChanged.connect(lambda _v, b=label: self.on_dynamic_attr_changed(b, _v))
            else:
                editor = QDoubleSpinBox()
                editor.setDecimals(0)
                editor.setRange(-999999.0, 999999.0)
                editor.setSingleStep(1.0)
                editor.setValue(float(value))
                editor.valueChanged.connect(lambda _v, b=label: self.on_dynamic_attr_changed(b, _v))

            source_hint = ', '.join(binding.get('bundle_sources', []))
            row_label = label if not source_hint else f"{label} [{source_hint}]"
            form_layout.addRow(row_label, editor)
            self.dynamic_attr_widget_map[label] = editor
            self.dynamic_attr_original_types[label] = binding['original_type']

        self.special_attr_form_widget = form_widget
        if self.special_attr_host_layout is not None:
            self.special_attr_host_layout.addWidget(form_widget)

    def _set_bundle_target_value(self, bundle_name: str, path_parts: Tuple[Any, ...], value: Any) -> bool:
        bundle_data = self.save_bundle_data.get(bundle_name)
        if bundle_data is None:
            return False
        return self._set_nested_value(bundle_data, path_parts, value)

    def on_dynamic_attr_changed(self, binding_key: str, _value: Any):
        binding = self.dynamic_attr_bindings.get(binding_key)
        widget = self.dynamic_attr_widget_map.get(binding_key)
        if not binding or widget is None:
            self.on_value_changed()
            return
        cast_value = self._cast_dynamic_value(binding_key, widget.value())
        binding['value'] = cast_value
        for target in binding.get('targets', []):
            self._set_bundle_target_value(target['bundle_name'], target['path'], cast_value)
        self.on_value_changed()

    def _primary_binding_relative_paths(self) -> List[Tuple[Tuple[Any, ...], Any]]:
        relative_entries: List[Tuple[Tuple[Any, ...], Any]] = []
        if self.current_character_index is None:
            return relative_entries
        for binding_key, binding in self.dynamic_attr_bindings.items():
            widget = self.dynamic_attr_widget_map.get(binding_key)
            if widget is None:
                continue
            value = self._cast_dynamic_value(binding_key, widget.value())
            for target in binding.get('targets', []):
                if target['bundle_name'] != PRIMARY_SAVE_FILE:
                    continue
                path_parts = tuple(target['path'])
                if len(path_parts) >= 2 and path_parts[0] == 'npcs' and path_parts[1] == self.current_character_index:
                    relative_entries.append((path_parts[2:], value))
        return relative_entries

    def update_character_from_widgets(self):
        SaveGameEditor.update_character_from_widgets(self)
        if self.current_character_index is None or not isinstance(self.save_data, dict):
            return
        npcs = self.save_data.get('npcs', [])
        if not (0 <= self.current_character_index < len(npcs)):
            return
        npc = npcs[self.current_character_index]
        self.current_character_data = npc
        char_name = npc.get('unitname', 'Unknown')
        extra_changes = []

        for binding_key, binding in self.dynamic_attr_bindings.items():
            widget = self.dynamic_attr_widget_map.get(binding_key)
            if widget is None:
                continue
            new_value = self._cast_dynamic_value(binding_key, widget.value())
            old_value = binding.get('value')
            if old_value != new_value:
                extra_changes.append(f"{binding_key}: {old_value} → {new_value}")
            binding['value'] = new_value
            for target in binding.get('targets', []):
                bundle_name = target['bundle_name']
                path_parts = target['path']
                bundle_data = self.save_bundle_data.get(bundle_name)
                old_target_value = self._get_nested_value(bundle_data, path_parts, None)
                if old_target_value != new_value:
                    extra_changes.append(f"{binding_key} [{bundle_name}]: {old_target_value} → {new_value}")
                self._set_bundle_target_value(bundle_name, path_parts, new_value)

        extra_changes.extend(self.sync_equipment_table_to_npc(npc))
        if extra_changes:
            self.terminal.log_change(f"Character '{char_name}' extended changes:")
            for change in extra_changes[:16]:
                self.terminal.log_info(f"  {change}")
            if len(extra_changes) > 16:
                self.terminal.log_info(f"  ... and {len(extra_changes) - 16} more changes")
        self.inventory_text.setText(self._render_inventory_preview_text(npc))

    def build_character_payload(self, npc: Dict[str, Any]) -> Dict[str, Any]:
        payload = PatchedSaveGameEditor.build_character_payload(self, npc)
        dynamic_entries = []
        seen = set()
        for relative_path, value in self._primary_binding_relative_paths():
            if not relative_path or relative_path in seen:
                continue
            seen.add(relative_path)
            dynamic_entries.append({'path': list(relative_path), 'value': value})
        if dynamic_entries:
            payload['__dynamic_numeric_paths__'] = dynamic_entries
        return payload


class PatchedSaveGameEditorV44(PatchedSaveGameEditorV43):
    EXACT_WEAPON_MASTERY_LABELS = [
        'Unarmed', 'One-handed', 'Two-handed', 'Shield', 'Ranged', 'Dual', 'Polearms'
    ]
    WEAPON_MASTERY_ARRAY_KEY = 'weaponMasteryEXP'

    def _iter_dict_nodes(self, node: Any, path_parts: Tuple[Any, ...] = (), context_character: Optional[str] = None):
        if isinstance(node, dict):
            current_character = context_character
            if isinstance(node.get('unitname'), str):
                current_character = node.get('unitname')
            yield path_parts, node, current_character
            for key, value in node.items():
                yield from self._iter_dict_nodes(value, path_parts + (key,), current_character)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from self._iter_dict_nodes(value, path_parts + (index,), context_character)

    def _rank_exact_mastery_hit(self, hit: Dict[str, Any], current_character_name: Optional[str]) -> Tuple[int, int, int, int]:
        char_match = 1 if current_character_name and hit.get('context_character') == current_character_name else 0
        primary = 1 if hit.get('bundle_name') == PRIMARY_SAVE_FILE else 0
        depth = len(hit.get('path', ()))
        return (char_match, primary, -depth, -int(hit.get('index', 0)))

    def _discover_exact_weapon_mastery_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        current_character_name = npc.get('unitname') if isinstance(npc, dict) else None
        mastery_hits: Dict[str, List[Dict[str, Any]]] = {label: [] for label in self.EXACT_WEAPON_MASTERY_LABELS}

        for bundle_name, bundle_data in self.save_bundle_data.items():
            if not isinstance(bundle_data, (dict, list)):
                continue
            for node_path, node_dict, context_character in self._iter_dict_nodes(bundle_data):
                mastery_values = node_dict.get(self.WEAPON_MASTERY_ARRAY_KEY)
                if not isinstance(mastery_values, list):
                    continue
                if len(mastery_values) < len(self.EXACT_WEAPON_MASTERY_LABELS):
                    continue
                for index, label in enumerate(self.EXACT_WEAPON_MASTERY_LABELS):
                    value = mastery_values[index]
                    if not isinstance(value, (int, float)) or isinstance(value, bool):
                        continue
                    mastery_hits[label].append({
                        'label': label,
                        'bundle_name': bundle_name,
                        'path': tuple(node_path + (self.WEAPON_MASTERY_ARRAY_KEY, index)),
                        'display_path': self._friendly_path_label(node_path + (self.WEAPON_MASTERY_ARRAY_KEY, index)),
                        'context_character': context_character,
                        'value': value,
                        'is_float': isinstance(value, float) and not float(value).is_integer(),
                        'original_type': float if isinstance(value, float) else int,
                        'index': index,
                        'source': 'weaponMasteryEXP-array',
                    })

        bindings: Dict[str, Dict[str, Any]] = {}
        for label in self.EXACT_WEAPON_MASTERY_LABELS:
            label_hits = mastery_hits.get(label, [])
            if not label_hits:
                continue
            char_hits = [hit for hit in label_hits if current_character_name and hit.get('context_character') == current_character_name]
            preferred_hits = char_hits if char_hits else label_hits
            preferred_hits = sorted(preferred_hits, key=lambda hit: self._rank_exact_mastery_hit(hit, current_character_name), reverse=True)
            best_hit = preferred_hits[0]

            if char_hits:
                selected_hits = char_hits
            else:
                selected_hits = [best_hit]

            targets = []
            seen_targets = set()
            for hit in selected_hits:
                target_key = (hit['bundle_name'], tuple(hit['path']))
                if target_key in seen_targets:
                    continue
                seen_targets.add(target_key)
                targets.append({
                    'bundle_name': hit['bundle_name'],
                    'path': tuple(hit['path']),
                    'display_path': hit['display_path'],
                    'source': hit.get('source', 'weaponMasteryEXP-array'),
                })

            bindings[label] = {
                'label': label,
                'value': best_hit['value'],
                'is_float': bool(best_hit['is_float']),
                'original_type': best_hit['original_type'],
                'targets': targets,
                'context_character': best_hit.get('context_character'),
                'score': 1.0,
                'bundle_sources': sorted({target['bundle_name'] for target in targets}),
                'source': 'weaponMasteryEXP-array',
            }

        return bindings

    def _discover_fuzzy_stat_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        bindings = super()._discover_fuzzy_stat_bindings(npc)
        exact_masteries = self._discover_exact_weapon_mastery_bindings(npc)
        for label, binding in exact_masteries.items():
            bindings[label] = binding
        return bindings

    def rebuild_dynamic_attribute_widgets(self, npc: Dict[str, Any]):
        super().rebuild_dynamic_attribute_widgets(npc)
        if self.special_attr_info_label is None:
            return
        exact_found = [label for label in self.EXACT_WEAPON_MASTERY_LABELS if label in self.dynamic_attr_bindings]
        extra_found = [label for label in ('Encumbrance', 'Carry Capacity') if label in self.dynamic_attr_bindings]
        if exact_found:
            msg = (
                'Weapon masteries are bound directly from weaponMasteryEXP[0..6] '
                '(Unarmed, One-handed, Two-handed, Shield, Ranged, Dual, Polearms).'
            )
            if extra_found:
                msg += ' Additional fuzzy matches: ' + ', '.join(extra_found) + '.'
            self.special_attr_info_label.setText(msg)



class PatchedSaveGameEditorV45(PatchedSaveGameEditorV44):
    SAVE_SLOT_IGNORE_TOKENS = {"cache", "caches", "cached", "temp", "tmp"}
    EXTRA_ENCUMBRANCE_ALIASES = [
        'encumbrance', 'encumberance', 'carry weight', 'carryweight', 'current weight',
        'weight current', 'load', 'burden', 'bag weight', 'inventory weight', 'total weight',
        'weight now', 'current load', 'load current', 'bagweight'
    ]
    EXTRA_CAPACITY_ALIASES = [
        'carry capacity', 'max carry', 'maximum carry', 'max weight', 'weight capacity',
        'capacity', 'load limit', 'weight limit', 'carry limit', 'burden limit',
        'maximum load', 'max load', 'max burden'
    ]

    def __init__(self):
        self.raw_json_dirty = False
        self.raw_json_programmatic = False
        self._is_reloading = False
        self._is_saving = False
        super().__init__()

    def create_raw_json_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.raw_json_text = QTextEdit()
        self.raw_json_text.setFont(QFont("Consolas", 10))
        self.raw_json_text.textChanged.connect(self.on_raw_json_text_changed)
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

    def on_raw_json_text_changed(self):
        if not getattr(self, 'raw_json_programmatic', False):
            self.raw_json_dirty = True
        self.on_value_changed()

    def populate_raw_json(self):
        if self.save_data:
            self.raw_json_programmatic = True
            try:
                self.raw_json_text.blockSignals(True)
                self.raw_json_text.setText(json.dumps(self.save_data, indent=2))
            finally:
                self.raw_json_text.blockSignals(False)
                self.raw_json_programmatic = False
            self.raw_json_dirty = False

    def _normalize_slot_name(self, value: Any) -> str:
        return re.sub(r'[^a-z0-9]+', '', str(value).strip().lower())

    def _is_cache_like_name(self, value: Any) -> bool:
        normalized = self._normalize_slot_name(value)
        if not normalized:
            return False
        return any(token in normalized for token in self.SAVE_SLOT_IGNORE_TOKENS)

    def _build_slot_entry(self, save_root: pathlib.Path, character_dir: pathlib.Path, folder: pathlib.Path) -> Optional[Dict[str, Any]]:
        bundle_paths = self.get_bundle_file_paths(folder)
        primary_path = bundle_paths[PRIMARY_SAVE_FILE]
        if not primary_path.exists():
            return None
        primary_data = self.load_bundle_file(primary_path)
        if not isinstance(primary_data, dict):
            return None
        info_data = self.load_bundle_file(bundle_paths['info.dat'])
        save_name = folder.name
        if isinstance(info_data, dict):
            save_name = info_data.get('saveName') or info_data.get('name') or info_data.get('slotName') or save_name

        npc_count = len(primary_data.get('npcs', [])) if isinstance(primary_data.get('npcs', []), list) else 0
        cache_like = (
            self._is_cache_like_name(character_dir.name)
            or self._is_cache_like_name(folder.name)
            or self._is_cache_like_name(save_name)
        )
        if npc_count <= 0 and cache_like:
            return None

        try:
            modified_ts = primary_path.stat().st_mtime
        except Exception:
            modified_ts = 0.0

        label = f"{character_dir.name} | {save_name} ({folder.name})"
        return {
            'label': label,
            'metadata': {
                'save_root': str(save_root),
                'character_dir': str(character_dir),
                'save_folder': str(folder),
                'slot_mtime': modified_ts,
                'npc_count': npc_count,
                'cache_like': cache_like,
            },
            'modified_ts': modified_ts,
            'cache_like': cache_like,
            'npc_count': npc_count,
        }

    def discover_saves(self):
        self.refresh_detected_paths()
        self.terminal.log_info("Scanning for save slots across detected save roots...")
        previous_folder = None
        if self.current_save_folder:
            previous_folder = str(self.current_save_folder)
        else:
            current_meta = self.save_combo.currentData() if hasattr(self, 'save_combo') else None
            if isinstance(current_meta, dict):
                previous_folder = current_meta.get('save_folder')

        self.save_combo.blockSignals(True)
        self.save_combo.clear()

        if not self.detected_save_roots:
            self.save_combo.blockSignals(False)
            attempted = "\n".join(str(path) for path in _candidate_save_roots())
            self.terminal.log_error("No save roots detected")
            self.status.showMessage("❌ No save roots detected")
            QMessageBox.warning(
                self,
                "Save Roots Not Found",
                f"No save roots were found. Checked:\n{attempted}\n\nPlease ensure the game has been launched and at least one save exists."
            )
            return

        preferred_slots: List[Dict[str, Any]] = []
        fallback_slots: List[Dict[str, Any]] = []
        for save_root in self.detected_save_roots:
            try:
                character_dirs = [p for p in save_root.iterdir() if p.is_dir()]
            except Exception as e:
                self.terminal.log_warning(f"Skipping save root {save_root}: {e}")
                continue
            for character_dir in sorted(character_dirs, key=lambda p: p.name.lower()):
                save_data_dir = character_dir / 'SaveData'
                if not save_data_dir.exists() or not save_data_dir.is_dir():
                    continue
                slot_dirs = [p for p in save_data_dir.iterdir() if p.is_dir()]
                for folder in slot_dirs:
                    entry = self._build_slot_entry(save_root, character_dir, folder)
                    if not entry:
                        continue
                    if entry['cache_like']:
                        fallback_slots.append(entry)
                    else:
                        preferred_slots.append(entry)

        slots = preferred_slots if preferred_slots else fallback_slots
        slots.sort(key=lambda e: (e['cache_like'], -e['modified_ts'], e['label'].lower()))

        selected_index = 0
        for idx, entry in enumerate(slots):
            self.save_combo.addItem(entry['label'], entry['metadata'])
            self.terminal.log_success(f"Found save: {entry['label']}")
            if previous_folder and entry['metadata'].get('save_folder') == previous_folder:
                selected_index = idx

        self.save_combo.blockSignals(False)
        self.status.showMessage(f"Found {len(slots)} save slot(s)")
        self.terminal.log_info(f"Total save slots found: {len(slots)}")
        if fallback_slots and not preferred_slots:
            self.terminal.log_warning("Only cache-like slot names were found; showing fallback candidates.")

        if slots:
            self.save_combo.setCurrentIndex(selected_index)

    def _select_character_by_name(self, character_name: Optional[str]) -> bool:
        if not character_name:
            return False
        for i in range(self.char_tree.topLevelItemCount()):
            item = self.char_tree.topLevelItem(i)
            if item and item.text(0) == character_name:
                self.char_tree.setCurrentItem(item)
                return True
        return False

    def _load_save_folder(self, save_folder: pathlib.Path, preserve_character_name: Optional[str] = None):
        self.current_save_folder = save_folder
        save_root = save_folder.parent.parent if save_folder.parent and save_folder.parent.parent else None
        self.current_save_root = save_root if isinstance(save_root, pathlib.Path) else None
        self.current_save_bundle_paths = self.get_bundle_file_paths(self.current_save_folder)
        self.current_save_path = self.current_save_bundle_paths[PRIMARY_SAVE_FILE]

        self.terminal.log_info(f"Loading save bundle: {self.current_save_folder}")
        self.save_bundle_data = {}
        for bundle_name, path in self.current_save_bundle_paths.items():
            bundle_data = self.load_bundle_file(path)
            if bundle_data is not None:
                self.save_bundle_data[bundle_name] = bundle_data
                self.terminal.log_info(f"Loaded {bundle_name}")

        self.save_data = self.save_bundle_data.get(PRIMARY_SAVE_FILE)
        if not isinstance(self.save_data, dict):
            raise ValueError(f"{PRIMARY_SAVE_FILE} did not contain valid JSON object data")

        self.original_data = json.loads(json.dumps(self.save_data))
        self.terminal.log_success("Save bundle loaded successfully")

        newly_discovered = self.discover_items_from_bundle(self.save_bundle_data)
        if newly_discovered:
            self.terminal.log_change(f"Discovered {len(newly_discovered)} new item IDs across save bundle")
            self.update_item_db_stats()
            self.refresh_item_table()
        else:
            self.terminal.log_info("No new items discovered")

        self.gold_display.blockSignals(True)
        self.gold_display.setValue(int(self.save_data.get('wealth', 0)))
        self.gold_display.blockSignals(False)

        watched = self.file_watcher.files()
        if watched:
            try:
                self.file_watcher.removePaths(watched)
            except Exception:
                pass

        self.populate_character_tree()
        if preserve_character_name:
            self._select_character_by_name(preserve_character_name)
        self.populate_raw_json()
        self.modified = False
        self.update_save_button()

        new_paths = [str(path) for path in self.current_save_bundle_paths.values() if path.exists()]
        if new_paths:
            self.file_watcher.addPaths(new_paths)
            self.terminal.log_info("File watcher enabled for bundle files")

        self.refresh_reflection_view()
        self.terminal.log_system("=" * 40)

    def on_save_selected(self, index: int):
        if index < 0:
            return
        metadata = self.save_combo.itemData(index)
        if not metadata:
            return
        try:
            self._load_save_folder(pathlib.Path(metadata['save_folder']))
        except Exception as e:
            self.terminal.log_error(f"Failed to load save bundle: {e}")
            self.status.showMessage(f"❌ Error loading save bundle: {e}")
            QMessageBox.critical(self, 'Error', f'Failed to load save bundle:\n{e}')

    def _write_json_file_robust(self, path: pathlib.Path, data: Any) -> Optional[str]:
        tmp_path = path.with_name(f"{path.name}.editor_tmp")
        payload = json.dumps(data, indent=2, ensure_ascii=False)
        last_error = None
        for attempt in range(5):
            try:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
                return None
            except Exception as e:
                last_error = e
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass
                time.sleep(0.15 * (attempt + 1))

        for attempt in range(3):
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                return None
            except Exception as e:
                last_error = e
                time.sleep(0.2 * (attempt + 1))
        return str(last_error) if last_error else 'Unknown write error'

    def write_bundle_files(self):
        failures = []
        for bundle_name, path in self.current_save_bundle_paths.items():
            data = self.save_bundle_data.get(bundle_name)
            if data is None:
                continue
            err = self._write_json_file_robust(path, data)
            if err:
                failures.append(f"{bundle_name}: {err}")
            else:
                self.terminal.log_success(f"Wrote {bundle_name}")
        if failures:
            raise PermissionError(
                'Some save bundle files could not be written. The game may still be holding them open.\n\n'
                + '\n'.join(failures)
            )

    def save_changes(self):
        if not self.current_save_path or not isinstance(self.save_data, dict):
            self.terminal.log_error('No save file loaded!')
            QMessageBox.warning(self, 'Error', 'No save file loaded!')
            return

        reply = QMessageBox.question(
            self, 'Confirm Save',
            'This will overwrite the active save bundle. A backup will be created first.\n\n'
            'Editing while the game is open is best-effort only because the game may hold or overwrite files.\n\nContinue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            self.terminal.log_warning('Save cancelled by user')
            return

        preserve_character_name = self.current_character_data.get('unitname') if isinstance(self.current_character_data, dict) else None
        self._is_saving = True
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            QApplication.processEvents()
            self.terminal.log_info('Saving changes across save bundle...')
            self.backup_bundle_files(silent=True)
            if self.raw_json_dirty:
                self.sync_raw_json_to_save_data()
            self.update_character_from_widgets()
            self.save_data['wealth'] = self.gold_display.value()
            self.save_bundle_data[PRIMARY_SAVE_FILE] = self.save_data
            self.propagate_changes_to_bundle()
            self.write_bundle_files()

            self.modified = False
            self.update_save_button()
            self.populate_raw_json()
            self.refresh_reflection_view()
            self.status.showMessage('✅ Save successful!')
            self.terminal.log_success('Save bundle updated successfully!')
            self.terminal.log_info('Weapon mastery rows edit the actual mastery level array (weaponMastery), not weaponMasteryEXP.')
            self.terminal.log_info('If the game is open, it may still keep older values cached until the slot is reloaded or the game is restarted.')
            self.terminal.log_system('=' * 40)
            QMessageBox.information(self, 'Success', 'Save bundle updated successfully!')
        except Exception as e:
            self.terminal.log_error(f'Save failed: {e}')
            self.status.showMessage(f'❌ Save failed: {e}')
            QMessageBox.critical(
                self, 'Error',
                f'Failed to save:\n{e}\n\nTip: close the game before editing if Windows is holding a save file open.'
            )
        finally:
            QApplication.restoreOverrideCursor()
            self._is_saving = False
            if self.current_save_folder and self.current_save_folder.exists() and preserve_character_name:
                pass

    def reload_save(self):
        if not self.current_save_folder:
            return
        if self.modified:
            reply = QMessageBox.question(
                self, 'Discard Unsaved Changes?',
                'Reloading will discard unsaved changes in the editor. Continue?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        preserve_character_name = self.current_character_data.get('unitname') if isinstance(self.current_character_data, dict) else None
        self._is_reloading = True
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            QApplication.processEvents()
            self.terminal.log_info('Reloading save bundle from disk...')
            self._load_save_folder(self.current_save_folder, preserve_character_name=preserve_character_name)
            self.status.showMessage('✅ Save bundle reloaded')
        except Exception as e:
            self.terminal.log_error(f'Reload failed: {e}')
            self.status.showMessage(f'❌ Reload failed: {e}')
            QMessageBox.critical(self, 'Reload Failed', f'Could not reload save bundle:\n{e}')
        finally:
            QApplication.restoreOverrideCursor()
            self._is_reloading = False

    def on_save_file_changed(self, path: str):
        if self._is_saving or self._is_reloading:
            return
        self.terminal.log_warning(f'Bundle file changed on disk: {path}')
        self.status.showMessage('⚠️ Save bundle changed on disk - Reload recommended')

    def _score_alias_list(self, text: str, aliases: List[str]) -> float:
        best = 0.0
        for alias in aliases:
            best = max(best, self._fuzzy_match_score(text, alias))
        return best

    def _weight_branch_penalty(self, path_parts: Tuple[Any, ...]) -> float:
        normalized = {self._normalize_token(part) for part in path_parts if not isinstance(part, int)}
        if normalized & {'items', 'item', 'equips', 'equip', 'inventory', 'stash', 'caravan'}:
            return 0.55
        return 1.0

    def _discover_weight_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        current_character_name = npc.get('unitname') if isinstance(npc, dict) else None
        by_label: Dict[str, List[Dict[str, Any]]] = {'Encumbrance': [], 'Carry Capacity': []}
        for bundle_name, bundle_data in self.save_bundle_data.items():
            if not isinstance(bundle_data, (dict, list)):
                continue
            for candidate in self._iter_fuzzy_numeric_candidates(bundle_data):
                path_parts = tuple(candidate.get('path', ()))
                match_text = f"{bundle_name} {candidate.get('match_text', '')}"
                penalty = self._weight_branch_penalty(path_parts)
                current_score = self._score_alias_list(match_text, self.EXTRA_ENCUMBRANCE_ALIASES) * penalty
                capacity_score = self._score_alias_list(match_text, self.EXTRA_CAPACITY_ALIASES) * penalty

                normalized_path = ' '.join(self._normalize_token(part) for part in path_parts if not isinstance(part, int))
                if any(token in normalized_path for token in ('encumbr', 'carryweight', 'currentweight', 'bagweight', 'burden', 'load')):
                    current_score = max(current_score, 0.92 * penalty)
                if any(token in normalized_path for token in ('maxcarry', 'maxweight', 'capacity', 'weightlimit', 'loadlimit', 'maxload')):
                    capacity_score = max(capacity_score, 0.92 * penalty)

                if current_score >= 0.62:
                    hit = dict(candidate)
                    hit.update({
                        'bundle_name': bundle_name,
                        'label': 'Encumbrance',
                        'score': current_score,
                        'selected_character': current_character_name,
                        'is_float': isinstance(candidate.get('value'), float) and not float(candidate.get('value')).is_integer(),
                    })
                    by_label['Encumbrance'].append(hit)
                if capacity_score >= 0.62:
                    hit = dict(candidate)
                    hit.update({
                        'bundle_name': bundle_name,
                        'label': 'Carry Capacity',
                        'score': capacity_score,
                        'selected_character': current_character_name,
                        'is_float': isinstance(candidate.get('value'), float) and not float(candidate.get('value')).is_integer(),
                    })
                    by_label['Carry Capacity'].append(hit)

        bindings = {}
        for label, hits in by_label.items():
            if not hits:
                continue
            hits = self._dedupe_fuzzy_hits(hits)
            char_hits = [hit for hit in hits if current_character_name and hit.get('context_character') == current_character_name]
            preferred_hits = char_hits if char_hits else hits
            preferred_hits = sorted(preferred_hits, key=lambda hit: self._rank_fuzzy_hit(hit, current_character_name), reverse=True)
            best_hit = preferred_hits[0]
            selected_hits = char_hits if char_hits else [best_hit]
            targets = []
            seen_targets = set()
            for hit in selected_hits:
                target_key = (hit['bundle_name'], tuple(hit['path']))
                if target_key in seen_targets:
                    continue
                seen_targets.add(target_key)
                targets.append({
                    'bundle_name': hit['bundle_name'],
                    'path': tuple(hit['path']),
                    'display_path': self._friendly_path_label(hit['path']),
                    'source': hit.get('source', 'path'),
                })
            bindings[label] = {
                'label': label,
                'value': best_hit['value'],
                'is_float': bool(best_hit['is_float']),
                'original_type': float if isinstance(best_hit['value'], float) else int,
                'targets': targets,
                'context_character': best_hit.get('context_character'),
                'score': best_hit['score'],
                'bundle_sources': sorted({target['bundle_name'] for target in targets}),
            }
        return bindings

    def _discover_fuzzy_stat_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        bindings = super()._discover_fuzzy_stat_bindings(npc)
        if 'Encumbrance' not in bindings or 'Carry Capacity' not in bindings:
            weight_bindings = self._discover_weight_bindings(npc)
            for label, binding in weight_bindings.items():
                if label not in bindings or float(binding.get('score', 0.0)) > float(bindings[label].get('score', 0.0)):
                    bindings[label] = binding
        return bindings

    def rebuild_dynamic_attribute_widgets(self, npc: Dict[str, Any]):
        super().rebuild_dynamic_attribute_widgets(npc)
        if self.special_attr_info_label is None:
            return
        base = self.special_attr_info_label.text().strip()
        note = ' Weapon masteries are EXP values, not mastery levels. 1000 EXP = level 10.'
        if note.strip() not in base:
            self.special_attr_info_label.setText((base + note).strip())



class PatchedSaveGameEditorV48(PatchedSaveGameEditorV45):
    """Current branch: v4.5 freeze/save fixes + working weaponMastery level bindings."""
    WEAPON_MASTERY_ARRAY_KEY = 'weaponMastery'
    DIRECT_CURRENT_WEIGHT_KEYS = {
        'encumbrance', 'encumberance', 'carryweight', 'currentweight', 'weightcurrent',
        'bagweight', 'inventoryweight', 'totalweight', 'load', 'burden', 'currentload'
    }
    DIRECT_CAPACITY_KEYS = {
        'carrycapacity', 'maxcarry', 'maximumcarry', 'maxweight', 'weightcapacity',
        'capacity', 'loadlimit', 'weightlimit', 'carrylimit', 'burdenlimit',
        'maximumload', 'maxload', 'maxburden'
    }

    def _discover_direct_weight_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        bindings: Dict[str, Dict[str, Any]] = {}
        if not isinstance(npc, dict):
            return bindings
        current_character_name = npc.get('unitname') if isinstance(npc.get('unitname'), str) else None
        current_hits: List[Dict[str, Any]] = []
        capacity_hits: List[Dict[str, Any]] = []

        for path_parts, value in self._iter_numeric_leaf_paths(npc):
            if not path_parts:
                continue
            normalized_parts = [self._normalize_token(part) for part in path_parts if not isinstance(part, int)]
            if not normalized_parts:
                continue
            joined = '.'.join(normalized_parts)
            leaf = normalized_parts[-1]
            hit = {
                'bundle_name': PRIMARY_SAVE_FILE,
                'context_character': current_character_name,
                'value': value,
                'is_float': isinstance(value, float) and not float(value).is_integer(),
                'original_type': float if isinstance(value, float) else int,
                'path': ('npcs', self.current_character_index, *path_parts) if self.current_character_index is not None else tuple(path_parts),
                'display_path': self._friendly_path_label(path_parts),
                'source': 'direct-npc-weight',
                'score': 0.99,
            }
            if leaf in self.DIRECT_CURRENT_WEIGHT_KEYS or any(token in joined for token in ('encumbr', 'carryweight', 'currentweight', 'bagweight', 'burden', 'currentload')):
                current_hits.append(dict(hit))
            if leaf in self.DIRECT_CAPACITY_KEYS or any(token in joined for token in ('maxcarry', 'maxweight', 'capacity', 'weightlimit', 'loadlimit', 'maxload', 'maxburden')):
                capacity_hits.append(dict(hit))

        def pick(label: str, hits: List[Dict[str, Any]]):
            if not hits:
                return
            hits.sort(key=lambda h: (h['score'], -len(h['path'])), reverse=True)
            best = hits[0]
            bindings[label] = {
                'label': label,
                'value': best['value'],
                'is_float': bool(best['is_float']),
                'original_type': best['original_type'],
                'targets': [{
                    'bundle_name': best['bundle_name'],
                    'path': tuple(best['path']),
                    'display_path': best['display_path'],
                    'source': best['source'],
                }],
                'context_character': best.get('context_character'),
                'score': best['score'],
                'bundle_sources': [best['bundle_name']],
                'source': best['source'],
            }

        pick('Encumbrance', current_hits)
        pick('Carry Capacity', capacity_hits)
        return bindings

    def _discover_fuzzy_stat_bindings(self, npc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        bindings = super()._discover_fuzzy_stat_bindings(npc)
        direct_weight = self._discover_direct_weight_bindings(npc)
        for label, binding in direct_weight.items():
            if label not in bindings or float(binding.get('score', 0.0)) >= float(bindings[label].get('score', 0.0)):
                bindings[label] = binding
        return bindings

    def rebuild_dynamic_attribute_widgets(self, npc: Dict[str, Any]):
        super().rebuild_dynamic_attribute_widgets(npc)
        if self.special_attr_info_label is None:
            return
        exact_found = [label for label in self.EXACT_WEAPON_MASTERY_LABELS if label in self.dynamic_attr_bindings]
        weight_found = [label for label in ('Encumbrance', 'Carry Capacity') if label in self.dynamic_attr_bindings]
        if exact_found:
            msg = (
                'Weapon masteries are bound directly from weaponMastery[0..6] '
                '(Unarmed, One-handed, Two-handed, Shield, Ranged, Dual, Polearms).'
            )
            if weight_found:
                msg += ' Weight fields detected: ' + ', '.join(weight_found) + '.'
            self.special_attr_info_label.setText(msg)
        elif weight_found:
            self.special_attr_info_label.setText('Weight fields detected: ' + ', '.join(weight_found) + '.')



class PatchedSaveGameEditorV49(PatchedSaveGameEditorV48):
    """v4.9: force initial selected slot to load after discovery so first-open data populates reliably."""

    def _deferred_activate_slot(self, index: int):
        if index < 0 or index >= self.save_combo.count():
            return
        metadata = self.save_combo.itemData(index)
        target_folder = metadata.get('save_folder') if isinstance(metadata, dict) else None
        needs_load = (
            not target_folder
            or self.save_data is None
            or self.current_save_folder is None
            or str(self.current_save_folder) != str(target_folder)
        )

        if self.save_combo.currentIndex() != index:
            self.save_combo.setCurrentIndex(index)
            if not needs_load:
                return

        if needs_load:
            self.on_save_selected(index)

    def discover_saves(self):
        self.refresh_detected_paths()
        self.terminal.log_info("Scanning for save slots across detected save roots...")
        previous_folder = None
        if self.current_save_folder:
            previous_folder = str(self.current_save_folder)
        else:
            current_meta = self.save_combo.currentData() if hasattr(self, 'save_combo') else None
            if isinstance(current_meta, dict):
                previous_folder = current_meta.get('save_folder')

        self.save_combo.blockSignals(True)
        self.save_combo.clear()

        if not self.detected_save_roots:
            self.save_combo.blockSignals(False)
            attempted = "\n".join(str(path) for path in _candidate_save_roots())
            self.terminal.log_error("No save roots detected")
            self.status.showMessage("❌ No save roots detected")
            QMessageBox.warning(
                self,
                "Save Roots Not Found",
                f"No save roots were found. Checked:\n{attempted}\n\nPlease ensure the game has been launched and at least one save exists."
            )
            return

        preferred_slots = []
        fallback_slots = []
        for save_root in self.detected_save_roots:
            try:
                character_dirs = [p for p in save_root.iterdir() if p.is_dir()]
            except Exception as e:
                self.terminal.log_warning(f"Skipping save root {save_root}: {e}")
                continue
            for character_dir in sorted(character_dirs, key=lambda p: p.name.lower()):
                save_data_dir = character_dir / 'SaveData'
                if not save_data_dir.exists() or not save_data_dir.is_dir():
                    continue
                slot_dirs = [p for p in save_data_dir.iterdir() if p.is_dir()]
                for folder in slot_dirs:
                    entry = self._build_slot_entry(save_root, character_dir, folder)
                    if not entry:
                        continue
                    if entry['cache_like']:
                        fallback_slots.append(entry)
                    else:
                        preferred_slots.append(entry)

        slots = preferred_slots if preferred_slots else fallback_slots
        slots.sort(key=lambda e: (e['cache_like'], -e['modified_ts'], e['label'].lower()))

        selected_index = 0
        for idx, entry in enumerate(slots):
            self.save_combo.addItem(entry['label'], entry['metadata'])
            self.terminal.log_success(f"Found save: {entry['label']}")
            if previous_folder and entry['metadata'].get('save_folder') == previous_folder:
                selected_index = idx

        self.save_combo.blockSignals(False)
        self.status.showMessage(f"Found {len(slots)} save slot(s)")
        self.terminal.log_info(f"Total save slots found: {len(slots)}")
        if fallback_slots and not preferred_slots:
            self.terminal.log_warning("Only cache-like slot names were found; showing fallback candidates.")

        if slots:
            self.save_combo.setCurrentIndex(selected_index)
            QTimer.singleShot(0, lambda idx=selected_index: self._deferred_activate_slot(idx))
        else:
            self.current_save_folder = None
            self.current_save_path = None
            self.save_data = None
            self.original_data = None
            self.current_character_data = None
            self.current_character_index = None
            self.char_tree.clear()
            self.raw_json_text.clear()
            self.inventory_text.clear()



# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(EDITOR_NAME)
    app.setApplicationVersion(EDITOR_VERSION)

    window = PatchedSaveGameEditorV49()
    window.show()

    sys.exit(app.exec())
