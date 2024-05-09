#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from mathutils import Vector
import mathutils


class VIEW3D_OT_SubmitFocalPointOperator(Operator):
    bl_idname = "view3d.submit_focal_point"
    bl_label = "Submit Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable."
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name)
    
    def execute(self, context):
        active_object = context.active_object

        # Check if the active object exists
        if not active_object:
            self.report({'ERROR'}, "No active object.")
            return {'CANCELLED'}

        # Check if the active object is a mesh
        if active_object.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh.")
            return {'CANCELLED'}

        if active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        # Check if at least one vertex is selected
        if len(selected_vertices) == 0:
            self.report({'ERROR'}, "Please select at least one vertex as the Focal Point.")
            return {'CANCELLED'}
        def get_transformed_coordinates(obj, coordinates):

            matrix_world = obj.matrix_world
            original_vector = mathutils.Vector(coordinates)
            transformed_vector = matrix_world @ original_vector
            return transformed_vector.x, transformed_vector.y, transformed_vector.z
        
        # Calculate the average coordinates of the selected vertices
        avg_coordinates = sum(selected_vertices, Vector()) / len(selected_vertices)
        x, y, z = get_transformed_coordinates(active_object, avg_coordinates)

        context.scene.focal_point_coordinates = f"{x:.3f},{y:.3f},{z:.3f}"
        self.report({'INFO'}, f"Focal Point coordinates: {context.scene.focal_point_coordinates}")

        return {'FINISHED'}
    