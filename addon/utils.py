"""Utility functions used across the BFEX add-on."""

import bpy
from mathutils import Vector


def set_object_mode(obj: bpy.types.Object, mode: str) -> None:
    """Safely set the mode of ``obj``.

    Parameters
    ----------
    obj: bpy.types.Object
        The object to operate on.
    mode: str
        Target mode (e.g. 'OBJECT', 'EDIT').
    """
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)


def to_world_coordinates(obj: bpy.types.Object, vector: Vector) -> Vector:
    """Return ``vector`` transformed to world space using ``obj``'s matrix."""
    return obj.matrix_world @ vector
