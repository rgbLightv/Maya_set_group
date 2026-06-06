# -*- coding: utf-8 -*-
"""
Set Group - Maya Plugin Entry Point
====================================
Dockable toolbar for managing ordered selection sets in Maya 2018+.

Supports:
  - Maya 2018 (Python 2.7 + PySide2)
  - Maya 2020-2023 (Python 3.7+ + PySide2)
  - Maya 2024-2025 (Python 3.10+ + PySide6)

Usage:
    import set_group
    set_group.show()

Installation:
    1. Copy 'set_group' folder to your Maya scripts directory
    2. Restart Maya or run:
       import set_group; set_group.show()
"""
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# PySide compatibility: Maya 2024+ uses PySide6, earlier versions use PySide2
try:
    from PySide6 import QtWidgets
    import shiboken6 as shiboken
except ImportError:
    from PySide2 import QtWidgets
    import shiboken2 as shiboken

import maya.OpenMayaUI as omui

# Python 2/3 compatibility: 'long' does not exist in Python 3
try:
    long
except NameError:
    long = int

# Python 2/3 compatibility: reload() moved in Python 3
try:
    from importlib import reload
except ImportError:
    pass

WINDOW_NAME = "set_group_toolbar"
WINDOW_TITLE = "Set Group"

_widget_instance = None


def _get_main_window():
    """Get Maya main window as QWidget."""
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
    return None


class SetGroupWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """
    Dockable window wrapper for the Set Group toolbar.
    Supports docking to all areas of the Maya workspace.
    """
    
    def __init__(self, parent=None):
        super(SetGroupWindow, self).__init__(parent)
        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(WINDOW_NAME)
        self.setMinimumWidth(200)
        self.setMinimumHeight(80)
        
        # Import here to support module reload during development
        from . import ui
        self._widget = ui.SetGroupWidget(self)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._widget)
    
    def refresh(self):
        """Refresh the inner widget."""
        if self._widget:
            self._widget.refresh()


def show():
    """
    Show or raise the Set Group dockable toolbar.
    
    The window can be docked to left, right, top, or bottom of the Maya workspace.
    
    Returns:
        SetGroupWindow: The window instance.
    """
    global _widget_instance
    
    # Support module reload for development
    try:
        from . import core, ui, utils
        reload(core)
        reload(ui)
        reload(utils)
    except Exception:
        pass
    
    # Close existing instance
    if _widget_instance is not None:
        try:
            _widget_instance.close()
        except Exception:
            pass
        _widget_instance = None
    
    # Delete old workspace control if exists
    ctrl_name = WINDOW_NAME + "WorkspaceControl"
    if cmds.workspaceControl(ctrl_name, exists=True):
        cmds.deleteUI(ctrl_name, control=True)
    
    _widget_instance = SetGroupWindow()
    _widget_instance.show(
        dockable=True,
        area="right",
        floating=False,
        width=300,
        height=150
    )
    
    # Tab next to Attribute Editor for convenience
    if cmds.workspaceControl(ctrl_name, exists=True):
        try:
            cmds.workspaceControl(ctrl_name, edit=True,
                                  tabToControl=["AttributeEditor", -1])
        except Exception:
            pass
    
    return _widget_instance


def close():
    """Close the Set Group window if open."""
    global _widget_instance
    if _widget_instance is not None:
        try:
            _widget_instance.close()
        except Exception:
            pass
        _widget_instance = None
