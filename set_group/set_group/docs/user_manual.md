# Set Group - User Manual

## Introduction

**Set Group** is a dockable toolbar for Maya that lets you create, organize, and recall ordered selection sets. Unlike Maya's default sets, this tool:
- **Preserves selection order** — objects are selected in the exact sequence you recorded.
- **Survives scene saves** — all data is stored inside the Maya file via a scriptNode.
- **Supports namespace switching** — easily retarget sets when importing references or changing namespaces.
- **Color-coded buttons** — visually organize sets with custom colors for quick identification.
- **Toolbar layout** — `+` button and all set buttons flow together in a single wrapping row.

**Supported Maya Versions:** 2018 / 2020-2023 / 2024-2025

## Installation

### Automatic Installation (Recommended)

The easiest way to install is using the included `install.py` script.

**Method 1: Script Editor**
1. In Maya's **Script Editor** (Python tab), run:
   ```python
   exec(open(r"C:\path\to\set_group\install.py").read())
   ```
   Replace the path with the actual location of `install.py` on your machine.

**Method 2: Drag-and-Drop**
1. Drag `install.py` directly into the Maya viewport.

**What the installer does:**
- Closes any open Set Group windows
- Removes cached module imports
- Deletes any old version of the plugin
- Copies new files to your Maya scripts directory
- Creates a shelf button labeled **SG** on your current active shelf
- Launches the toolbar automatically

> **Note:** Make sure a shelf tab is active in Maya before running the installer, otherwise the shelf button cannot be created.

### Manual Installation

If you prefer to install manually:

1. Copy the `set_group` folder into your Maya scripts directory:
   - Windows: `C:\Users\<user>\Documents\maya\<version>\scripts\`
   - macOS: `~/Library/Preferences/Autodesk/maya/<version>/scripts/`
   - Linux: `~/maya/<version>/scripts/`
   
   Replace `<version>` with your Maya version (e.g. `2018`, `2022`, `2025`).

2. In Maya, run in the Python tab of the Script Editor:
   ```python
   import set_group
   set_group.show()
   ```

3. The toolbar appears docked to the right side of Maya. You can drag it to any edge or leave it floating.

## Interface Overview

The toolbar consists of a single scrolling area containing:
- **+ button** (fixed at the left): Creates a new selection set from current selection.
- **Set buttons** (flow to the right): Each represents a saved selection set.

Buttons wrap to the next row when the current row is full:
```
+  [Body]  [Face]  [Hands]  [Props]  [Lights]...
   [Cameras]  [Rig] ...
```

Each set button shows:
- The set's **name**
- The set's **color** as the button background
- **White or black text** (automatically chosen for readability)

## Creating a Selection Set

1. **Select** the controllers/objects you want in the set **in the desired order**.
   - The order you select them is the order that will be recorded.
2. Click the **+** button in the toolbar.
3. Enter a **name** in the dialog and press OK.
4. A colored button appears representing your new set.

> **Tip:** The selection order is recorded. When you click the set button later, objects will be selected in that exact same order. This is especially useful for FK chains, facial controls, and ordered workflows.

> **Tip:** If you don't select anything, the set will not be created and a warning appears in the Script Editor.

## Using a Selection Set

- **Left-click** a set button to select all objects in that set.
- Objects are selected in the **recorded order**.
- If an object no longer exists at its original path, the plugin will try to find it by short name.

## Right-Click Menu Options

Right-click any set button to open the context menu:

### Add Selected
- Adds the currently selected objects to the set.
- Duplicate entries are automatically prevented.
- New items are appended to the end, preserving existing order.

### Remove Selected
- Removes the currently selected objects from the set.
- Only removes exact DAG path matches.

### Overwrite
- Replaces the entire set contents with the current selection.
- Useful when a rig has been updated and you want to refresh the set.
- **If nothing is selected**, a confirmation dialog asks if you want to clear the set.

### Rename
- Changes the set's display name.
- Names must be unique — an error dialog appears if the name is already taken.

### Change Color
- Opens a color picker dialog.
- Changes the button's background color.
- Text color (black or white) adjusts automatically for readability based on brightness.

### Change Namespace
- Replaces the namespace prefix for all objects in the set.
- Opens a dialog with two fields:
  - **Old Namespace**: The namespace to replace (e.g. `NS1`, without colon).
  - **New Namespace**: The replacement namespace (e.g. `NS2`, without colon).

**Example:**  
If your set contains `|rig|NS1:hand_L` and you change namespace from `NS1` to `NS2`, the item becomes `|rig|NS2:hand_L`.

> Only the namespace prefix is replaced. Objects without the specified namespace are left unchanged. Nested namespaces like `NS1:SUB:ctrl` become `NS2:SUB:ctrl`.

### Delete
- Permanently removes the set after a confirmation dialog.
- This cannot be undone through the plugin UI.

## Docking the Toolbar

The toolbar is fully dockable within Maya's workspace:
- Drag the title bar to snap to **left**, **right**, **top**, or **bottom**.
- Double-click the title bar to toggle between docked and floating.
- Resize the panel to see buttons wrap to new rows automatically.
- The default position is tabbed next to the **Attribute Editor** on the right side.

## Data Persistence

All sets are saved **inside the Maya scene file** automatically. There are no external files to manage.

- Data is stored in a hidden `scriptNode` named `set_group_data_node`.
- The node is saved and loaded with your `.ma` or `.mb` file.
- When you open the scene on another machine, the sets are available as long as the `set_group` plugin is installed.

> **Warning:** The scriptNode stores full DAG paths. If you rename or reparent objects, you may need to use **Overwrite** or **Change Namespace** to update the set.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Buttons don't appear after creating a set | Check that at least one object was selected before clicking **+**. |
| Set selects nothing when clicked | The original objects may have been renamed, deleted, or reparented. Use **Overwrite** to refresh the set, or **Change Namespace** if only the namespace changed. |
| Namespace change had no effect | Ensure the old namespace matches exactly (case-sensitive, no colon). Only objects with that prefix are modified. |
| Window disappears on restart | Run `set_group.show()` again. Maya does not auto-restore custom tools on startup. |
| Colors look wrong | The plugin automatically picks black or white text for readability. If a color is hard to read, use **Change Color** to adjust. |
| Install fails with PySide error | Ensure you are running Maya 2018 or later. Earlier versions are not supported. |
| Shelf button not created | Check that a shelf tab is active/visible in Maya before running the installer. |
| Multiple SG buttons on shelf | The installer detects duplicates, but if you see extras, right-click the shelf button and choose **Delete** to remove them. |
| Plugin doesn't load after install | Restart Maya or run `import set_group; set_group.show()` manually. |

## Shelf Button

The automatic installer creates a shelf button labeled **SG** with a default Maya icon. Clicking it runs:
```python
import set_group
set_group.show()
```

### Creating a Shelf Button Manually

If the installer didn't create one, or you want to add it to a different shelf:

1. Open the Script Editor and switch to the Python tab.
2. Enter:
   ```python
   import set_group
   set_group.show()
   ```
3. Select the code and drag it to your shelf.
4. Right-click the new shelf button → **Edit**.
5. Set Label to **SG** and adjust the icon if desired.

## Tips for Best Results

- **Use full DAG paths** when possible to avoid name clashes between identically named objects in different hierarchies.
- **Create sets early** in your workflow and use **Overwrite** to update them as the rig evolves.
- **Use color coding** consistently for quick visual identification:
  - Blue for body controls
  - Red for face controls
  - Green for props/environment
  - Yellow for cameras
  - Purple for lighting
- **Namespace changes** are great for reusing animation between characters with identical rigs. Create sets on one character, then use Change Namespace to retarget to another.
- **Reinstall** using `install.py` whenever you update the plugin code — it will cleanly replace the old version without leaving stale files.
- **Order matters** — the selection sequence is preserved, so select objects in the order you want them selected later (e.g., root to tip for FK chains).
