# -*- coding: utf-8 -*-
"""
Set Group - User Interface
===========================
Main toolbar UI with flow layout for set buttons.
Features: create, add, remove, overwrite, rename, delete, change namespace, change color.

Compatible with Maya 2018 (Python 2.7 + PySide2), Maya 2022 (Python 3.7+ + PySide2),
and Maya 2025 (Python 3.11+ + PySide6).
"""
import maya.cmds as cmds

# PySide compatibility: Maya 2024+ uses PySide6, earlier versions use PySide2
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from . import core
from . import utils


def _display_info(msg):
    """Print info message compatible with all Maya versions."""
    print(msg)


class FlowLayout(QtWidgets.QLayout):
    """
    Custom flow layout that arranges widgets left-to-right and wraps to next line.
    Buttons fill the horizontal space and wrap when the row is full.
    """
    
    def __init__(self, parent=None, margin=2, spacing=4):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self._item_list.append(item)
    
    def count(self):
        return len(self._item_list)
    
    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None
    
    def expandingDirections(self):
        # Qt5/Qt6 compatible: return empty orientations
        try:
            return QtCore.Qt.Orientations()
        except (TypeError, AttributeError):
            # Fallback for different Qt versions
            return QtCore.Qt.Orientation(0)
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        return self._doLayout(QtCore.QRect(0, 0, width, 0), True)
    
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QtCore.QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
    
    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        
        for item in self._item_list:
            spaceX = self.spacing()
            spaceY = self.spacing()
            
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        
        return y + lineHeight - rect.y()


class SetGroupWidget(QtWidgets.QWidget):
    """
    Main widget for the Set Group toolbar.
    Displays set buttons in a wrapping flow layout.
    """
    
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 28
    
    def __init__(self, parent=None):
        super(SetGroupWidget, self).__init__(parent)
        self._buttons = {}
        self._create_ui()
        self.refresh()
    
    def _create_ui(self):
        """Build the UI layout."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)
        
        # Scroll area containing flow layout (+ button and set buttons in same row)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.flow_widget = QtWidgets.QWidget()
        self.flow_layout = FlowLayout(self.flow_widget, margin=2)
        self.flow_layout.setSpacing(4)
        
        # Add button as first item in the flow
        self.add_btn = QtWidgets.QPushButton("+")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setToolTip("Create new selection set from current selection")
        self.add_btn.clicked.connect(self.create_set)
        self.flow_layout.addWidget(self.add_btn)
        
        scroll.setWidget(self.flow_widget)
        main_layout.addWidget(scroll)
    
    def refresh(self):
        """Reload and refresh all set buttons."""
        # Remove old set buttons (keep + button)
        for btn in list(self._buttons.values()):
            self.flow_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        
        # Create new buttons
        sets = core.get_sets()
        for s in sets:
            self._add_set_button(s)
        
        # Update layout
        self.flow_widget.update()
    
    def _add_set_button(self, s):
        """Create and add a single set button."""
        name = s["name"]
        color = s["color"]
        
        btn = QtWidgets.QPushButton(name)
        btn.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        btn.setToolTip("Click to select | Right-click for options")
        
        # Apply color style
        r, g, b, a = color
        cr, cg, cb = utils.get_contrast_color(r, g, b)
        
        btn.setStyleSheet("""
            QPushButton {{
                background-color: rgba({0}, {1}, {2}, {3});
                color: rgba({4}, {5}, {6}, 255);
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border: 2px solid #ffffff;
            }}
            QPushButton:pressed {{
                background-color: rgba({0}, {1}, {2}, 200);
            }}
        """.format(
            int(r * 255), int(g * 255), int(b * 255), int(a * 255),
            int(cr * 255), int(cg * 255), int(cb * 255)
        ))
        
        btn.clicked.connect(lambda checked=False, n=name: self.on_select_set(n))
        btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, n=name: self.on_context_menu(n, pos)
        )
        
        self.flow_layout.addWidget(btn)
        self._buttons[name] = btn
    
    def on_select_set(self, name):
        """Select all objects in the set preserving recorded order."""
        s = core.get_set(name)
        if not s:
            return
        
        items = s.get("items", [])
        if not items:
            return
        
        with utils.chunk_undo("Select Set: " + name):
            valid_items = []
            for item in items:
                if cmds.objExists(item):
                    valid_items.append(item)
                else:
                    # Try to find by short name (handles namespace changes or renames)
                    short = item.split("|")[-1]
                    if short:
                        matches = cmds.ls(short, long=True)
                        if matches:
                            valid_items.append(matches[0])
            
            if valid_items:
                cmds.select(clear=True)
                for item in valid_items:
                    cmds.select(item, add=True)
    
    def on_context_menu(self, name, pos):
        """Show right-click context menu for a set button."""
        menu = QtWidgets.QMenu(self)
        menu.setToolTipsVisible(True)
        
        menu.addAction("Add Selected", lambda: self.add_to_set(name))
        menu.addAction("Remove Selected", lambda: self.remove_from_set(name))
        menu.addAction("Overwrite", lambda: self.overwrite_set(name))
        menu.addSeparator()
        menu.addAction("Rename", lambda: self.rename_set(name))
        menu.addAction("Change Color", lambda: self.change_color(name))
        menu.addSeparator()
        menu.addAction("Change Namespace", lambda: self.change_namespace(name))
        menu.addSeparator()
        menu.addAction("Delete", lambda: self.delete_set(name))
        
        menu.exec_(self._buttons[name].mapToGlobal(pos))
    
    def create_set(self):
        """Create a new selection set from current selection."""
        sel = utils.get_selected_ordered()
        if not sel:
            cmds.warning("[SetGroup] Please select at least one controller.")
            return
        
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Create Selection Set", "Set Name:"
        )
        if not ok or not name.strip():
            return
        
        name = name.strip()
        try:
            core.add_set(name, sel)
            self.refresh()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e))
    
    def add_to_set(self, name):
        """Add current selection to an existing set."""
        sel = utils.get_selected_ordered()
        if not sel:
            cmds.warning("[SetGroup] Nothing selected to add.")
            return
        
        core.add_to_set(name, sel)
        _display_info("[SetGroup] Added {0} object(s) to '{1}'.".format(len(sel), name))
    
    def remove_from_set(self, name):
        """Remove current selection from a set."""
        sel = utils.get_selected_ordered()
        if not sel:
            cmds.warning("[SetGroup] Nothing selected to remove.")
            return
        
        core.remove_from_set(name, sel)
        _display_info("[SetGroup] Removed selected object(s) from '{0}'.".format(name))
    
    def overwrite_set(self, name):
        """Overwrite set contents with current selection."""
        sel = utils.get_selected_ordered()
        
        if not sel:
            reply = QtWidgets.QMessageBox.question(
                self, "Confirm Overwrite",
                "No objects selected. This will clear the set.\nContinue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        
        core.update_set_items(name, sel)
        count = len(sel)
        _display_info("[SetGroup] Overwrote '{0}' with {1} object(s).".format(name, count))
    
    def rename_set(self, name):
        """Rename a selection set."""
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Rename Set", "New Name:", text=name
        )
        if not ok or not new_name.strip() or new_name.strip() == name:
            return
        
        try:
            core.rename_set(name, new_name.strip())
            self.refresh()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "Error", str(e))
    
    def change_color(self, name):
        """Change a set's button color."""
        s = core.get_set(name)
        if not s:
            return
        
        color = s["color"]
        qcolor = QtGui.QColor(
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        )
        
        new_color = QtWidgets.QColorDialog.getColor(qcolor, self)
        if new_color.isValid():
            new_rgba = [
                new_color.redF(),
                new_color.greenF(),
                new_color.blueF(),
                1.0
            ]
            core.update_set_color(name, new_rgba)
            self.refresh()
    
    def change_namespace(self, name):
        """Replace namespace prefix for all items in a set."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Change Namespace")
        dialog.setMinimumWidth(250)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        old_ns_input = QtWidgets.QLineEdit()
        old_ns_input.setPlaceholderText("e.g. NS1 (without colon)")
        new_ns_input = QtWidgets.QLineEdit()
        new_ns_input.setPlaceholderText("e.g. NS2 (without colon)")
        
        layout.addRow("Old Namespace:", old_ns_input)
        layout.addRow("New Namespace:", new_ns_input)
        
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        
        old_ns = old_ns_input.text().strip()
        new_ns = new_ns_input.text().strip()
        
        if not old_ns:
            QtWidgets.QMessageBox.warning(self, "Error", "Old namespace cannot be empty.")
            return
        
        core.change_set_namespace(name, old_ns, new_ns)
        _display_info(
            "[SetGroup] Changed namespace '{0}' -> '{1}' for set '{2}'.".format(
                old_ns, new_ns, name
            )
        )
    
    def delete_set(self, name):
        """Delete a selection set after confirmation."""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Delete",
            "Delete selection set '{0}'?".format(name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            core.remove_set(name)
            self.refresh()
            _display_info("[SetGroup] Deleted set '{0}'.".format(name))
