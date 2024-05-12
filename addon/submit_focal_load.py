#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bpy.types import Operator
import mathutils
import bpy
import json

class View3D_OT_SubmitFocalLoad(Operator):
    bl_idname = "view3d.submit_focal_load"
    bl_label = "Submit Focal Load"
    bl_description = "Submit the focal load to the server"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_object = context.active_object

        if active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices_indices = [v.index for v in active_object.data.vertices if v.select]

        if not selected_vertices_indices:
            self.report({'ERROR'}, "No vertices selected.")
            return {'CANCELLED'}

        def get_transformed_coordinates(obj, coordinates):
            matrix_world = obj.matrix_world
            original_vector = mathutils.Vector(coordinates)
            transformed_vector = matrix_world @ original_vector
            return transformed_vector

        if len(selected_vertices_indices) > 1:
            # Calculate the centroid of selected vertices
            sum_coords = mathutils.Vector((0, 0, 0))
            for vertex_index in selected_vertices_indices:
                sum_coords += active_object.data.vertices[vertex_index].co
            centroid = sum_coords / len(selected_vertices_indices)
            # Transform centroid to global coordinates
            transformed_centroid = get_transformed_coordinates(active_object, centroid)
            loads_focal_str = json.dumps([transformed_centroid.x, transformed_centroid.y, transformed_centroid.z])
        else:
            # Handle the single vertex case (or no vertex, which is caught earlier)
            vertex_coords = active_object.data.vertices[selected_vertices_indices[0]].co
            transformed_coords = get_transformed_coordinates(active_object, vertex_coords)
            loads_focal_str = json.dumps([transformed_coords.x, transformed_coords.y, transformed_coords.z])
        
        context.scene.loads_focal = loads_focal_str

        self.report({'INFO'}, f"Loads: {context.scene.loads_focal}")
        return {'FINISHED'}