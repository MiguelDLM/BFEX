#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator


class VIEW3D_OT_SelectVertexOperator(Operator):
    bl_idname = "view3d.select_fixation_point"
    bl_label = "Select Fixation Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)

    def execute(self, context):
        object_name = context.scene.selected_main_object
        obj = bpy.data.objects.get(object_name)

        # Check if the object exists
        if not obj:
            self.report({'ERROR'}, f"Object '{object_name}' not found.")
            return {'CANCELLED'}

        # Check if the object is a mesh
        if obj.type != 'MESH':
            self.report({'ERROR'}, f"Object '{object_name}' is not a mesh.")
            return {'CANCELLED'}

        # Make the object the active object
        context.view_layer.objects.active = obj

        # Ensure the active object is in 'OBJECT' mode before switching to 'EDIT' mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True 
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False
        return {'FINISHED'}