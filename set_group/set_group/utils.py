# -*- coding: utf-8 -*-
"""
Set Group - Utility Functions
=============================
Helper functions for namespace handling, color calculation, and Maya operations.

Compatible with Maya 2018 (Python 2.7), Maya 2022 (Python 3.7+), Maya 2025 (Python 3.11+).
"""
import maya.cmds as cmds


def get_selected_ordered():
    """
    Get currently selected objects preserving selection order.
    
    Returns:
        list: List of full DAG paths in selection order.
    """
    return cmds.ls(selection=True, long=True) or []


def change_namespace(dag_path, old_ns, new_ns):
    """
    Replace namespace prefix in a DAG path.
    
    Supports nested namespaces (e.g. NS:SUB:node -> NEW:SUB:node).
    
    Args:
        dag_path (str): Full DAG path like '|group|NS:ctrl'
        old_ns (str): Old namespace name (without colon)
        new_ns (str): New namespace name (without colon)
    
    Returns:
        str: Updated DAG path.
    """
    if not dag_path or not old_ns:
        return dag_path
    
    parts = dag_path.split('|')
    short_name = parts[-1]
    
    if not short_name:
        return dag_path
    
    ns_prefix = old_ns + ':'
    if short_name.startswith(ns_prefix):
        new_short = new_ns + ':' + short_name[len(ns_prefix):]
        parts[-1] = new_short
        return '|'.join(parts)
    
    return dag_path


def get_contrast_color(r, g, b):
    """
    Calculate contrasting text color (black or white) for a background color.
    
    Uses YIQ brightness formula for readability.
    
    Args:
        r, g, b (float): Background color channels (0-1).
    
    Returns:
        tuple: (r, g, b) text color (0 or 1 for each channel).
    """
    brightness = (r * 299.0 + g * 587.0 + b * 114.0) / 1000.0
    if brightness > 0.5:
        return (0.0, 0.0, 0.0)
    return (1.0, 1.0, 1.0)


def chunk_undo(name):
    """
    Context manager to wrap operations in a Maya undo chunk.
    
    Usage:
        with chunk_undo("My Operation"):
            cmds.move(1, 0, 0)
    
    Args:
        name (str): Undo chunk name shown in Maya's undo menu.
    
    Returns:
        _UndoChunk: Context manager instance.
    """
    class _UndoChunk(object):
        def __enter__(self):
            cmds.undoInfo(openChunk=True, chunkName=name)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            cmds.undoInfo(closeChunk=True)
            return False
    
    return _UndoChunk()
