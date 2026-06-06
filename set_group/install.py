# -*- coding: utf-8 -*-
"""
Set Group - Installer
=====================
Single-file installer for Set Group Maya plugin.

Supports Maya 2018 (Python 2.7), Maya 2022 (Python 3.7+), Maya 2025 (Python 3.11+).

Run this in Maya's Script Editor (Python tab):
    exec(open(r"C:\path\to\install.py").read())

Or drag-and-drop this file into Maya viewport.
"""
import os
import sys
import shutil
import maya.cmds as cmds
import maya.mel as mel

# Python 2/3 compatibility: reload() moved in Python 3
try:
    from importlib import reload
except ImportError:
    pass

# ============================================================
# CONFIGURATION
# ============================================================
MODULE_NAME = "set_group"
WINDOW_NAME = "set_group_toolbar"
BUTTON_LABEL = "SG"
BUTTON_ANNOTATION = "Set Group - Ordered Selection Sets"

# ============================================================
# UTILITIES
# ============================================================
def get_maya_scripts_dir():
    """Get user Maya scripts directory for current version."""
    maya_app_dir = cmds.internalVar(userAppDir=True)
    version = cmds.about(version=True)
    # version may be like "2018" or "2018.5"
    version_major = version.split(".")[0]
    scripts_dir = os.path.join(maya_app_dir, version_major, "scripts")
    return os.path.normpath(scripts_dir)


def get_install_source_dir():
    """Get directory where this install.py lives."""
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # When run via exec() without __file__
        return os.getcwd()


def get_module_source_dir():
    """Get source set_group module directory.
    
    Supports two layouts:
      1. install.py is next to a 'set_group/' folder (parent directory)
      2. install.py is inside the 'set_group/' folder itself
    """
    src = get_install_source_dir()
    
    # Case 1: install.py is in parent directory, next to set_group/
    module_src = os.path.join(src, MODULE_NAME)
    if os.path.isdir(module_src):
        return module_src
    
    # Case 2: install.py is inside set_group/ directory
    # Detect by checking for core module files
    markers = ["__init__.py", "core.py", "ui.py", "utils.py"]
    if all(os.path.isfile(os.path.join(src, m)) for m in markers):
        return src
    
    return None


# ============================================================
# UNINSTALL OLD VERSION
# ============================================================
def uninstall_old_version():
    """Remove old plugin files and close open windows."""
    print("[SetGroup Installer] Uninstalling old version...")
    
    # Close open window
    ctrl_name = WINDOW_NAME + "WorkspaceControl"
    if cmds.workspaceControl(ctrl_name, exists=True):
        try:
            cmds.deleteUI(ctrl_name, control=True)
            print("  -> Closed existing dockable window.")
        except Exception as e:
            print("  -> Warning: could not close window: {0}".format(e))
    
    # Remove module from sys.modules to force reload
    modules_to_remove = [key for key in sys.modules.keys() if key.startswith(MODULE_NAME)]
    for mod in modules_to_remove:
        try:
            del sys.modules[mod]
        except KeyError:
            pass
    print("  -> Cleared {0} cached module(s).".format(len(modules_to_remove)))
    
    # Delete old directory
    scripts_dir = get_maya_scripts_dir()
    old_module_dir = os.path.join(scripts_dir, MODULE_NAME)
    if os.path.isdir(old_module_dir):
        try:
            shutil.rmtree(old_module_dir)
            print("  -> Removed old module directory: {0}".format(old_module_dir))
        except Exception as e:
            print("  -> Warning: could not remove old directory: {0}".format(e))
    else:
        print("  -> No old installation found.")


# ============================================================
# INSTALL
# ============================================================
def install_module():
    """Copy module files to Maya scripts directory."""
    print("[SetGroup Installer] Installing new version...")
    
    module_src = get_module_source_dir()
    if not module_src:
        raise RuntimeError(
            "Cannot find '{0}' folder next to install.py.\n"
            "Please ensure install.py is in the same directory as the '{0}' folder."
            .format(MODULE_NAME)
        )
    
    scripts_dir = get_maya_scripts_dir()
    if not os.path.isdir(scripts_dir):
        os.makedirs(scripts_dir)
        print("  -> Created scripts directory: {0}".format(scripts_dir))
    
    dst_dir = os.path.join(scripts_dir, MODULE_NAME)
    shutil.copytree(module_src, dst_dir)
    print("  -> Copied module to: {0}".format(dst_dir))
    
    # Add to sys.path if not present
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        print("  -> Added to sys.path.")
    
    return dst_dir


# ============================================================
# CREATE SHELF BUTTON
# ============================================================
def _safe_str(value):
    """Convert value to str, handling both Python 2/3 safely."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    try:
        return str(value)
    except Exception:
        try:
            return repr(value)
        except Exception:
            return "[unprintable]"


def create_shelf_button():
    """Create a shelf button on the current active shelf."""
    print("[SetGroup Installer] Creating shelf button...")
    
    # Get current shelf
    top_level = mel.eval("$tmp = $gShelfTopLevel")
    current_shelf = cmds.tabLayout(top_level, query=True, selectTab=True)
    current_shelf = _safe_str(current_shelf)
    
    if not current_shelf:
        print("  -> Warning: No active shelf found. Skipping button creation.")
        return
    
    # Check if button already exists
    children = cmds.shelfLayout(current_shelf, query=True, childArray=True) or []
    for child in children:
        if cmds.objectTypeUI(child) == "shelfButton":
            ann = cmds.shelfButton(child, query=True, annotation=True) or ""
            ann = _safe_str(ann)
            if BUTTON_ANNOTATION in ann or BUTTON_LABEL in ann:
                print("  -> Button already exists on shelf '{}'".format(current_shelf))
                return
    
    # Create button
    btn = cmds.shelfButton(
        parent=current_shelf,
        annotation=BUTTON_ANNOTATION,
        label=BUTTON_LABEL,
        image1="menuIconFile.png",
        command="import set_group; set_group.show()",
        sourceType="python",
        width=32,
        height=32
    )
    btn_str = _safe_str(btn)
    print("  -> Created button on shelf '{}': {}".format(current_shelf, btn_str))


# ============================================================
# MAIN
# ============================================================
def main():
    """Run full installation: uninstall old, install new, create button, launch."""
    print("=" * 60)
    print("Set Group - Installer")
    print("=" * 60)
    
    try:
        uninstall_old_version()
        install_module()
        create_shelf_button()
        
        # Launch
        print("[SetGroup Installer] Launching plugin...")
        import set_group
        set_group.show()
        
        print("=" * 60)
        print("Installation complete!")
        print("=" * 60)
        print("[SetGroup] Installation complete. Shelf button created.")
        
    except Exception as e:
        error_msg = "[SetGroup Installer] ERROR: {0}".format(_safe_str(e))
        print(error_msg)
        cmds.error(error_msg)
        raise


# Run immediately when executed in Maya
main()
