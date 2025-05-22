from __future__ import annotations
'\nEnhanced font handling for watermarks and text operations.\n\nThis module provides cross-platform font selection, font loading from path,\nand font management capabilities for the Media Processor Plugin.\n'
import os
import sys
import platform
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import ImageFont, Image, ImageDraw
from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLineEdit, QDialog, QTabWidget, QScrollArea, QGroupBox, QFormLayout, QSpinBox
class FontManager:
    def __init__(self, logger: Any) -> None:
        self._logger = logger
        self._system_fonts: List[str] = []
        self._custom_fonts: Dict[str, str] = {}
        self._loaded_fonts: Dict[str, ImageFont.FreeTypeFont] = {}
        self._initialize_system_fonts()
    def _initialize_system_fonts(self) -> None:
        try:
            qt_fonts = QFontDatabase().families()
            self._system_fonts = [font for font in qt_fonts]
            self._system_fonts.sort()
            self._logger.info(f'Loaded {len(self._system_fonts)} system fonts')
        except Exception as e:
            self._logger.error(f'Error initializing system fonts: {str(e)}')
            self._system_fonts = ['Arial', 'Times New Roman', 'Courier New', 'Verdana']
    def get_system_fonts(self) -> List[str]:
        return self._system_fonts
    def get_custom_fonts(self) -> Dict[str, str]:
        return self._custom_fonts
    def add_custom_font(self, name: str, path: str) -> bool:
        try:
            font = ImageFont.truetype(path, 12)
            self._custom_fonts[name] = path
            self._logger.info(f'Added custom font: {name} from {path}')
            return True
        except Exception as e:
            self._logger.error(f'Error adding custom font {name} from {path}: {str(e)}')
            return False
    def remove_custom_font(self, name: str) -> bool:
        if name in self._custom_fonts:
            del self._custom_fonts[name]
            if name in self._loaded_fonts:
                del self._loaded_fonts[name]
            self._logger.info(f'Removed custom font: {name}')
            return True
        return False
    def get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        try:
            cache_key = f'{font_name}_{size}'
            if cache_key in self._loaded_fonts:
                return self._loaded_fonts[cache_key]
            if font_name in self._custom_fonts:
                font_path = self._custom_fonts[font_name]
                font = ImageFont.truetype(font_path, size)
                self._loaded_fonts[cache_key] = font
                return font
            if os.path.isabs(font_name) and os.path.exists(font_name):
                font = ImageFont.truetype(font_name, size)
                self._loaded_fonts[cache_key] = font
                return font
            try:
                font = ImageFont.truetype(font_name, size)
                self._loaded_fonts[cache_key] = font
                return font
            except Exception:
                font_paths = self._get_system_font_paths(font_name)
                for path in font_paths:
                    try:
                        if os.path.exists(path):
                            font = ImageFont.truetype(path, size)
                            self._loaded_fonts[cache_key] = font
                            return font
                    except Exception:
                        continue
                self._logger.warning(f"Font '{font_name}' not found, using default")
                font = ImageFont.load_default()
                self._loaded_fonts[cache_key] = font
                return font
        except Exception as e:
            self._logger.error(f'Error loading font {font_name}: {str(e)}')
            raise ValueError(f'Error loading font {font_name}: {str(e)}')
    def _get_system_font_paths(self, font_name: str) -> List[str]:
        paths = []
        system = platform.system()
        extensions = ['.ttf', '.ttc', '.otf']
        normalized_name = font_name.lower().replace(' ', '')
        if system == 'Windows':
            font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            for ext in extensions:
                paths.append(os.path.join(font_dir, f'{font_name}{ext}'))
            for ext in extensions:
                paths.append(os.path.join(font_dir, f'{normalized_name}{ext}'))
        elif system == 'Darwin':
            paths.append(f'/System/Library/Fonts/{font_name}.ttf')
            paths.append(f'/System/Library/Fonts/{normalized_name}.ttf')
            user_font_dir = os.path.expanduser('~/Library/Fonts')
            for ext in extensions:
                paths.append(os.path.join(user_font_dir, f'{font_name}{ext}'))
                paths.append(os.path.join(user_font_dir, f'{normalized_name}{ext}'))
        else:
            font_dirs = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts')]
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for ext in extensions:
                        paths.append(os.path.join(font_dir, f'{font_name}{ext}'))
                        paths.append(os.path.join(font_dir, f'{normalized_name}{ext}'))
        return paths
    def render_font_preview(self, font_name: str, size: int=24, text: str='AaBbCcYyZz123', width: int=300, height: int=60, color: Tuple[int, int, int]=(0, 0, 0), background: Tuple[int, int, int]=(255, 255, 255)) -> Optional[bytes]:
        try:
            image = Image.new('RGB', (width, height), background)
            draw = ImageDraw.Draw(image)
            try:
                font = self.get_font(font_name, size)
            except Exception:
                font = ImageFont.load_default()
            text_width, text_height = draw.textsize(text, font=font)
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, font=font, fill=color)
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception as e:
            self._logger.error(f'Error rendering font preview: {str(e)}')
            return None
class FontSelector(QWidget):
    fontSelected = Signal(str)
    def __init__(self, font_manager: FontManager, logger: Any, initial_font: str='Arial', parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._font_manager = font_manager
        self._logger = logger
        self._initial_font = initial_font
        self._init_ui()
        self._select_initial_font()
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Search:'))
        self._search_edit = QLineEdit()
        self._search_edit.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_edit)
        system_layout.addLayout(search_layout)
        self._font_list = QListWidget()
        self._font_list.setAlternatingRowColors(True)
        self._font_list.currentItemChanged.connect(self._on_font_changed)
        system_layout.addWidget(self._font_list, 1)
        preview_group = QGroupBox('Preview')
        preview_layout = QVBoxLayout(preview_group)
        preview_options = QHBoxLayout()
        preview_options.addWidget(QLabel('Size:'))
        self._size_spin = QSpinBox()
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(24)
        self._size_spin.valueChanged.connect(self._update_preview)
        preview_options.addWidget(self._size_spin)
        self._preview_text = QLineEdit('AaBbCcYyZz123')
        self._preview_text.textChanged.connect(self._update_preview)
        preview_options.addWidget(self._preview_text, 1)
        preview_layout.addLayout(preview_options)
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(70)
        self._preview_label.setStyleSheet('background-color: white; border: 1px solid #ccc;')
        preview_layout.addWidget(self._preview_label)
        system_layout.addWidget(preview_group)
        custom_tab = QWidget()
        custom_layout = QVBoxLayout(custom_tab)
        self._custom_font_list = QListWidget()
        self._custom_font_list.setAlternatingRowColors(True)
        self._custom_font_list.currentItemChanged.connect(self._on_custom_font_changed)
        custom_layout.addWidget(self._custom_font_list, 1)
        buttons_layout = QHBoxLayout()
        self._add_font_btn = QPushButton('Add Font...')
        self._add_font_btn.clicked.connect(self._on_add_font)
        buttons_layout.addWidget(self._add_font_btn)
        self._remove_font_btn = QPushButton('Remove')
        self._remove_font_btn.clicked.connect(self._on_remove_font)
        self._remove_font_btn.setEnabled(False)
        buttons_layout.addWidget(self._remove_font_btn)
        custom_layout.addLayout(buttons_layout)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('Font Path:'))
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        path_layout.addWidget(self._path_edit, 1)
        browse_btn = QPushButton('Browse...')
        browse_btn.clicked.connect(self._on_browse_font)
        path_layout.addWidget(browse_btn)
        custom_layout.addLayout(path_layout)
        self._tabs.addTab(system_tab, 'System Fonts')
        self._tabs.addTab(custom_tab, 'Custom Fonts')
        layout.addWidget(self._tabs, 1)
        selected_layout = QHBoxLayout()
        selected_layout.addWidget(QLabel('Selected Font:'))
        self._selected_font_label = QLabel(self._initial_font)
        self._selected_font_label.setStyleSheet('font-weight: bold;')
        selected_layout.addWidget(self._selected_font_label, 1)
        layout.addLayout(selected_layout)
        self._populate_system_fonts()
        self._populate_custom_fonts()
    def _populate_system_fonts(self) -> None:
        self._font_list.clear()
        system_fonts = self._font_manager.get_system_fonts()
        search_text = self._search_edit.text().lower()
        for font_name in system_fonts:
            if search_text and search_text not in font_name.lower():
                continue
            item = QListWidgetItem(font_name)
            self._font_list.addItem(item)
    def _populate_custom_fonts(self) -> None:
        self._custom_font_list.clear()
        custom_fonts = self._font_manager.get_custom_fonts()
        for name, path in custom_fonts.items():
            item = QListWidgetItem(name)
            item.setToolTip(path)
            self._custom_font_list.addItem(item)
    def _select_initial_font(self) -> None:
        custom_fonts = self._font_manager.get_custom_fonts()
        if self._initial_font in custom_fonts:
            self._tabs.setCurrentIndex(1)
            for i in range(self._custom_font_list.count()):
                item = self._custom_font_list.item(i)
                if item.text() == self._initial_font:
                    self._custom_font_list.setCurrentItem(item)
                    break
            return
        system_fonts = self._font_manager.get_system_fonts()
        if self._initial_font in system_fonts:
            for i in range(self._font_list.count()):
                item = self._font_list.item(i)
                if item.text() == self._initial_font:
                    self._font_list.setCurrentItem(item)
                    break
        self._selected_font_label.setText(self._initial_font)
        self._update_preview()
    @Slot()
    def _on_search_changed(self) -> None:
        self._populate_system_fonts()
    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_font_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if current:
            font_name = current.text()
            self._selected_font_label.setText(font_name)
            self.fontSelected.emit(font_name)
            self._update_preview()
    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_custom_font_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if current:
            font_name = current.text()
            font_path = current.toolTip()
            self._selected_font_label.setText(font_name)
            self._path_edit.setText(font_path)
            self._remove_font_btn.setEnabled(True)
            self.fontSelected.emit(font_name)
            self._update_preview()
        else:
            self._path_edit.clear()
            self._remove_font_btn.setEnabled(False)
    @Slot()
    def _on_add_font(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Font File', '', 'Font Files (*.ttf *.otf *.ttc *.pfb);;All Files (*.*)')
        if not file_path:
            return
        font_name = os.path.splitext(os.path.basename(file_path))[0]
        name_dialog = QDialog(self)
        name_dialog.setWindowTitle('Font Name')
        dialog_layout = QVBoxLayout(name_dialog)
        dialog_layout.addWidget(QLabel('Enter a name for this font:'))
        name_edit = QLineEdit(font_name)
        dialog_layout.addWidget(name_edit)
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(name_dialog.accept)
        buttons_layout.addWidget(ok_btn)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(name_dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(buttons_layout)
        if name_dialog.exec() == QDialog.Accepted:
            font_name = name_edit.text().strip()
            if not font_name:
                font_name = os.path.splitext(os.path.basename(file_path))[0]
            if self._font_manager.add_custom_font(font_name, file_path):
                self._populate_custom_fonts()
                for i in range(self._custom_font_list.count()):
                    item = self._custom_font_list.item(i)
                    if item.text() == font_name:
                        self._custom_font_list.setCurrentItem(item)
                        break
    @Slot()
    def _on_remove_font(self) -> None:
        current = self._custom_font_list.currentItem()
        if not current:
            return
        font_name = current.text()
        if self._font_manager.remove_custom_font(font_name):
            self._populate_custom_fonts()
            self._path_edit.clear()
            self._remove_font_btn.setEnabled(False)
    @Slot()
    def _on_browse_font(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Font File', '', 'Font Files (*.ttf *.otf *.ttc *.pfb);;All Files (*.*)')
        if not file_path:
            return
        self._path_edit.setText(file_path)
        font_name = os.path.splitext(os.path.basename(file_path))[0]
        if self._font_manager.add_custom_font(font_name, file_path):
            self._populate_custom_fonts()
            for i in range(self._custom_font_list.count()):
                item = self._custom_font_list.item(i)
                if item.text() == font_name:
                    self._custom_font_list.setCurrentItem(item)
                    break
    def _update_preview(self) -> None:
        font_name = self._selected_font_label.text()
        size = self._size_spin.value()
        text = self._preview_text.text() or 'AaBbCcYyZz123'
        preview_data = self._font_manager.render_font_preview(font_name, size=size, text=text)
        if preview_data:
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(preview_data)
            self._preview_label.setPixmap(pixmap)
        else:
            self._preview_label.setText('Preview not available')
    def get_selected_font(self) -> str:
        return self._selected_font_label.text()
class FontSelectorDialog(QDialog):
    def __init__(self, font_manager: FontManager, logger: Any, initial_font: str='Arial', parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._font_manager = font_manager
        self._logger = logger
        self._initial_font = initial_font
        self._init_ui()
        self.setWindowTitle('Select Font')
        self.resize(500, 600)
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._font_selector = FontSelector(self._font_manager, self._logger, self._initial_font, self)
        layout.addWidget(self._font_selector, 1)
        buttons_layout = QHBoxLayout()
        self._cancel_btn = QPushButton('Cancel')
        self._cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self._cancel_btn)
        buttons_layout.addStretch()
        self._ok_btn = QPushButton('OK')
        self._ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self._ok_btn)
        layout.addLayout(buttons_layout)
    def get_selected_font(self) -> str:
        return self._font_selector.get_selected_font()