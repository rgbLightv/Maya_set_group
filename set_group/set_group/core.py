# -*- coding: utf-8 -*-
"""
Set Group - Core Data Management
=================================
Handles persistent storage of selection sets using a Maya scriptNode.
Data is saved with the scene file automatically.

Compatible with Maya 2018 (Python 2.7), Maya 2022 (Python 3.7+), Maya 2025 (Python 3.11+).
"""
import json
import maya.cmds as cmds
from . import utils

SCRIPT_NODE_NAME = "set_group_data_node"

# Preset colors cycled through when creating new sets
DEFAULT_COLORS = [
    [0.26, 0.59, 0.98, 1.0],   # Blue
    [0.98, 0.26, 0.32, 1.0],   # Red
    [0.20, 0.80, 0.20, 1.0],   # Green
    [1.00, 0.65, 0.00, 1.0],   # Orange
    [0.60, 0.20, 0.80, 1.0],   # Purple
    [0.00, 0.80, 0.80, 1.0],   # Cyan
    [1.00, 0.84, 0.00, 1.0],   # Yellow
    [1.00, 0.41, 0.71, 1.0],   # Pink
    [0.50, 0.50, 0.50, 1.0],   # Gray
    [0.00, 0.40, 0.80, 1.0],   # Dark Blue
]


def _get_script_node():
    """
    Get or create the scriptNode used for data storage.
    
    Returns:
        str: Node name.
    """
    if cmds.objExists(SCRIPT_NODE_NAME):
        return SCRIPT_NODE_NAME
    
    node = cmds.createNode("script", name=SCRIPT_NODE_NAME, skipSelect=True)
    cmds.setAttr(node + ".scriptType", 0)
    cmds.setAttr(node + ".sourceType", 0)
    
    # Add custom string attribute for our JSON data
    cmds.addAttr(node, longName="sgData", dataType="string")
    cmds.setAttr(node + ".sgData", '{"version":1,"sets":[]}', type="string")
    
    return node


def load_data():
    """
    Load selection set data from the scriptNode.
    
    Returns:
        dict: Data dictionary with 'version' and 'sets' keys.
    """
    if not cmds.objExists(SCRIPT_NODE_NAME):
        return {"version": 1, "sets": []}
    
    try:
        data_str = cmds.getAttr(SCRIPT_NODE_NAME + ".sgData")
        if data_str:
            return json.loads(data_str)
    except Exception:
        pass
    
    return {"version": 1, "sets": []}


def save_data(data):
    """
    Save selection set data to the scriptNode.
    
    Args:
        data (dict): Data dictionary to serialize.
    """
    node = _get_script_node()
    data_str = json.dumps(data, ensure_ascii=False)
    
    with utils.chunk_undo("Save Set Group Data"):
        cmds.setAttr(node + ".sgData", data_str, type="string")


def get_sets():
    """
    Get all selection sets.
    
    Returns:
        list: List of set dictionaries.
    """
    data = load_data()
    return data.get("sets", [])


def get_set_names():
    """
    Get names of all selection sets.
    
    Returns:
        list: List of set name strings.
    """
    return [s["name"] for s in get_sets()]


def get_set(name):
    """
    Get a specific selection set by name.
    
    Args:
        name (str): Set name.
    
    Returns:
        dict or None: Set dictionary or None if not found.
    """
    for s in get_sets():
        if s["name"] == name:
            return s
    return None


def add_set(name, items, color=None):
    """
    Add a new selection set.
    
    Args:
        name (str): Set name.
        items (list): Ordered list of DAG paths.
        color (list or None): RGBA color [r, g, b, a] or None for auto-color.
    
    Raises:
        ValueError: If set name already exists.
    """
    if color is None:
        idx = len(get_sets()) % len(DEFAULT_COLORS)
        color = list(DEFAULT_COLORS[idx])
    
    data = load_data()
    
    for s in data["sets"]:
        if s["name"] == name:
            raise ValueError("Set name already exists: " + name)
    
    data["sets"].append({
        "name": name,
        "color": list(color),
        "items": list(items)
    })
    
    save_data(data)


def remove_set(name):
    """
    Delete a selection set.
    
    Args:
        name (str): Set name to remove.
    """
    data = load_data()
    data["sets"] = [s for s in data["sets"] if s["name"] != name]
    save_data(data)


def rename_set(old_name, new_name):
    """
    Rename a selection set.
    
    Args:
        old_name (str): Current name.
        new_name (str): New name.
    
    Raises:
        ValueError: If new name already exists.
    """
    if old_name == new_name:
        return
    
    data = load_data()
    
    for s in data["sets"]:
        if s["name"] == new_name:
            raise ValueError("Set name already exists: " + new_name)
    
    for s in data["sets"]:
        if s["name"] == old_name:
            s["name"] = new_name
            break
    
    save_data(data)


def update_set_items(name, items):
    """
    Overwrite a set's items.
    
    Args:
        name (str): Set name.
        items (list): New ordered list of DAG paths.
    """
    data = load_data()
    for s in data["sets"]:
        if s["name"] == name:
            s["items"] = list(items)
            break
    save_data(data)


def add_to_set(name, items):
    """
    Append items to a set (preserving order, avoiding duplicates).
    
    Args:
        name (str): Set name.
        items (list): Items to add.
    """
    data = load_data()
    for s in data["sets"]:
        if s["name"] == name:
            existing = set(s["items"])
            for item in items:
                if item not in existing:
                    s["items"].append(item)
            break
    save_data(data)


def remove_from_set(name, items):
    """
    Remove items from a set.
    
    Args:
        name (str): Set name.
        items (list): Items to remove.
    """
    data = load_data()
    remove_set_items = set(items)
    for s in data["sets"]:
        if s["name"] == name:
            s["items"] = [i for i in s["items"] if i not in remove_set_items]
            break
    save_data(data)


def update_set_color(name, color):
    """
    Update a set's display color.
    
    Args:
        name (str): Set name.
        color (list): RGBA color [r, g, b, a].
    """
    data = load_data()
    for s in data["sets"]:
        if s["name"] == name:
            s["color"] = list(color)
            break
    save_data(data)


def change_set_namespace(name, old_ns, new_ns):
    """
    Replace namespace prefix for all items in a set.
    
    Args:
        name (str): Set name.
        old_ns (str): Old namespace (without colon).
        new_ns (str): New namespace (without colon).
    """
    data = load_data()
    for s in data["sets"]:
        if s["name"] == name:
            s["items"] = [utils.change_namespace(i, old_ns, new_ns) for i in s["items"]]
            break
    save_data(data)
