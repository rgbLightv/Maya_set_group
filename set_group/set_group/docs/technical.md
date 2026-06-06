# Set Group - Technical Documentation

## Overview

Set Group is a Maya dockable toolbar plugin for managing ordered selection sets. Selection sets are persisted in the Maya scene file via a `scriptNode`, ensuring data travels with the scene.

**Supported Maya Versions:**
- Maya 2018 (Python 2.7 + PySide2)
- Maya 2020-2023 (Python 3.7+ + PySide2)
- Maya 2024-2025 (Python 3.10+ + PySide6)

## Architecture

```
set_group/
├── install.py      # One-click installer with auto-uninstall and shelf button creation
├── __init__.py     # Entry point, dockable window wrapper, PySide auto-detection
├── core.py         # Data persistence layer (scriptNode + JSON)
├── ui.py           # PySide UI (FlowLayout, buttons, context menus)
├── utils.py        # Helper utilities (namespace, colors, undo)
└── docs/
    ├── technical.md    # This file
    └── user_manual.md  # End-user guide
```

### Module Responsibilities

| Module | Role |
|--------|------|
| `install.py` | Standalone installer script. Automatically uninstalls old versions, copies new files to Maya scripts directory, creates a shelf button on the current active shelf, and launches the plugin. Supports being run from inside or outside the `set_group` folder. |
| `__init__.py` | Plugin bootstrap. Creates a `MayaQWidgetDockableMixin` window that can dock to any Maya workspace area. Handles module reload for development. Auto-detects PySide2/PySide6 at runtime. |
| `core.py` | Data layer. Reads/writes JSON to a `scriptNode` named `set_group_data_node`. Provides full CRUD operations for selection sets, including color management and namespace transformations. |
| `ui.py` | Visual interface. Custom `FlowLayout` arranges `+` button and set buttons horizontally in a single wrapping row. Buttons fill available width and wrap to the next line when the row is full. Compatible with both Qt5 (PySide2) and Qt6 (PySide6). |
| `utils.py` | Cross-cutting utilities: ordered selection retrieval (`cmds.ls(selection=True, long=True)`), namespace string manipulation, YIQ brightness calculation for automatic contrast text, and undo chunk context manager. |

## Data Persistence

### Storage Format

Data is stored as JSON in a custom string attribute (`sgData`) on a `script` node:

```json
{
  "version": 1,
  "sets": [
    {
      "name": "Face Controls",
      "color": [1.0, 0.5, 0.0, 1.0],
      "items": ["|grp|NS:ctrl_eye_L", "|grp|NS:ctrl_eye_R"]
    }
  ]
}
```

### Why scriptNode?

- **Scene-bound**: The node is saved inside the `.ma`/`.mb` file automatically.
- **No external files**: No dependency on external JSON files that could be lost.
- **Undo support**: Attribute changes participate in Maya's undo queue.
- **Invisible**: The node is not selectable and does not clutter the Outliner.

### Node Setup

```python
node = cmds.createNode("script", name="set_group_data_node", skipSelect=True)
cmds.addAttr(node, longName="sgData", dataType="string")
cmds.setAttr(node + ".sgData", '{"version":1,"sets":[]}', type="string")
```

## UI Layout System

### FlowLayout

A custom `QLayout` subclass that arranges widgets horizontally, wrapping to the next line when the right edge is reached.

Key behavior:
- The `+` button is placed as the **first widget** in the flow.
- Set buttons are placed immediately after the `+` button, flowing left-to-right.
- Each button has a fixed width (100px) and height (28px).
- When a button would exceed the right boundary, the entire row wraps to the next line.
- `heightForWidth()` allows the parent `QScrollArea` to adjust its vertical size correctly.

Visual layout:
```
+  [Set1] [Set2] [Set3] [Set4] [Set5]...
   [Set7] [Set8] ...
```

### Button Styling

Buttons use QSS (Qt Style Sheets) with dynamic colors:
- **Background**: Set color (RGBA from data), fully opaque.
- **Text**: Automatically black or white based on YIQ brightness calculation of the background.
- **Hover**: White border highlight (`2px solid #ffffff`).
- **Pressed**: Slightly transparent background for visual feedback.
- **Border**: 1px solid gray with 4px border-radius.

### Scroll Area

The entire flow layout is wrapped in a `QScrollArea`:
- `widgetResizable=True`: Allows the inner widget to resize with the container.
- Horizontal scrollbar is hidden (`ScrollBarAlwaysOff`).
- Vertical scrollbar appears automatically when buttons wrap to multiple rows.

## Namespace Handling

The `change_namespace()` utility in `utils.py` operates on the short name (last `|` segment) of a DAG path:

```
|group1|NS1:ctrl_hand   ->  |group1|NS2:ctrl_hand
|group1|NS1:SUB:ctrl    ->  |group1|NS2:SUB:ctrl
|group1|other:ctrl      ->  |group1|other:ctrl    (unchanged)
```

Only items whose short name starts with the old namespace prefix are modified. Others are preserved unchanged.

### Change Namespace Dialog

A custom `QDialog` with two `QLineEdit` fields:
- **Old Namespace**: The namespace prefix to search for (e.g. `NS1`).
- **New Namespace**: The replacement prefix (e.g. `NS2`).
- Validates that old namespace is not empty.
- Uses `utils.change_namespace()` to transform all items in the set.

## Selection Order Preservation

When creating or overwriting a set:
1. `cmds.ls(selection=True, long=True)` returns the selection in the exact order the user clicked or shift-selected.
2. This order is stored as a list in the JSON `items` array.
3. When restoring selection via left-click, `cmds.select(item, add=True)` is called sequentially, reproducing the original order.

### Fallback for Missing Objects

If a stored DAG path no longer exists:
1. Try the exact path with `cmds.objExists()`.
2. If not found, extract the short name (last segment after `|`).
3. Search by short name using `cmds.ls(short, long=True)`.
4. Use the first match if found.

## Docking (Workspace)

The plugin uses `MayaQWidgetDockableMixin` to create a `workspaceControl`:
- **Default area**: Right side (tabbed next to Attribute Editor).
- **Allowed areas**: All (left, right, top, bottom, or floating).
- **Mode**: Toolbar-style thin window, suitable for horizontal button layouts.
- **Minimum size**: 200x80 pixels.

### Window Management

- `WINDOW_NAME = "set_group_toolbar"` is used as the object name and workspace control name.
- Opening a new instance automatically closes any existing instance.
- The `show()` function deletes old workspace controls before creating new ones.

## Compatibility

| Requirement | Version |
|-------------|---------|
| Maya | 2018 / 2020-2023 / 2024-2025 |
| Python | 2.7 / 3.7 / 3.11+ |
| Qt | PySide2 (Qt5) / PySide6 (Qt6) |

### Cross-Version Strategies

**PySide/shiboken auto-detection** (`__init__.py`):
```python
try:
    from PySide6 import QtWidgets
    import shiboken6 as shiboken   # Maya 2024+
except ImportError:
    from PySide2 import QtWidgets
    import shiboken2 as shiboken   # Maya 2018-2023
```

**Python 2/3 `long` type** (`__init__.py`):
```python
try:
    long
except NameError:
    long = int   # Python 3 has no long type
```

**Qt5/Qt6 API differences** (`ui.py`):
- `exec_()` is used for dialog execution (available in both Qt5 and Qt6).
- `Qt.Orientations()` has a try/except fallback for constructor differences.

**Python 2/3 `reload`** (`__init__.py`, `install.py`):
```python
try:
    from importlib import reload   # Python 3
except ImportError:
    pass   # Python 2 has builtin reload
```

**String handling in installer** (`install.py`):
- `_safe_str()` function handles both Python 2 (`unicode`/`str`) and Python 3 (`str`/`bytes`) string types.
- Uses `isinstance` checks with exception fallbacks for safe conversion.

## Installation

### Automatic (Recommended)

Run `install.py` in Maya's Script Editor:
```python
exec(open(r"C:\path\to\set_group\install.py").read())
```

Or drag-and-drop `install.py` into the Maya viewport.

The installer performs these steps in order:
1. **Uninstall**: Closes any open Set Group windows, removes cached module imports from `sys.modules`, deletes old installation directory.
2. **Install**: Detects Maya version's scripts directory, creates it if missing, copies the `set_group` module files.
3. **Path**: Adds the scripts directory to `sys.path` if not already present.
4. **Shelf Button**: Creates a shelf button labeled **SG** on the current active shelf (checks for duplicates).
5. **Launch**: Imports `set_group` and calls `show()` to open the toolbar.

### Layout Detection

The installer supports two folder layouts:
- `install.py` is inside the `set_group/` folder (current structure).
- `install.py` is in a parent directory next to a `set_group/` folder.

Detected by checking for core module files (`__init__.py`, `core.py`, `ui.py`, `utils.py`).

### Manual

1. Copy the `set_group` folder to your Maya scripts directory:
   - Windows: `C:\Users\<user>\Documents\maya\<version>\scripts\`
   - macOS: `~/Library/Preferences/Autodesk/maya/<version>/scripts/`
   - Linux: `~/maya/<version>/scripts/`

2. In Maya, run:
   ```python
   import set_group
   set_group.show()
   ```

## Development & Reloading

For rapid iteration, `set_group.show()` automatically reloads all submodules before creating the window:

```python
from . import core, ui, utils
reload(core)
reload(ui)
reload(utils)
```

This allows code changes to take effect without restarting Maya. The installer also clears `sys.modules` cache during uninstall.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Duplicate set name | `ValueError` raised; UI shows `QMessageBox.warning` dialog. |
| Selecting deleted objects | Button click skips missing objects and tries short-name fallback. |
| Empty namespace input | Dialog validation prevents empty old namespace with `QMessageBox.warning`. |
| No selection on create | `cmds.warning()` logged to Maya script editor; set not created. |
| Qt version mismatch | Auto-detects PySide2/PySide6 at import time via try/except. |
| Shelf button exists | Installer detects existing button by annotation/label and skips creation. |

## API Reference

### core.py Functions

| Function | Description |
|----------|-------------|
| `load_data()` | Load JSON data from scriptNode. Returns dict. |
| `save_data(data)` | Save dict as JSON to scriptNode. |
| `get_sets()` | Get all selection sets as list of dicts. |
| `get_set(name)` | Get single set by name, or None. |
| `add_set(name, items, color=None)` | Create new set with ordered items. Auto-assigns color if None. |
| `remove_set(name)` | Delete set by name. |
| `rename_set(old, new)` | Rename set. Raises ValueError if name exists. |
| `update_set_items(name, items)` | Overwrite set's item list. |
| `add_to_set(name, items)` | Append items, avoiding duplicates. |
| `remove_from_set(name, items)` | Remove specific items from set. |
| `update_set_color(name, color)` | Update set's RGBA color. |
| `change_set_namespace(name, old_ns, new_ns)` | Replace namespace prefix for all items. |

### utils.py Functions

| Function | Description |
|----------|-------------|
| `get_selected_ordered()` | Get selection as ordered list of full DAG paths. |
| `change_namespace(path, old, new)` | Replace namespace prefix in a DAG path. |
| `get_contrast_color(r, g, b)` | Calculate black or white text color for a background. |
| `chunk_undo(name)` | Context manager for Maya undo chunk. |
