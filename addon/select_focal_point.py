#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

class VIEW3D_OT_SelectFocalPointOperator(Operator):
    bl_idname = "view3d.select_focal_point"
    bl_label = "Select Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, allowing you to select a point to be used as the force direction for the previously created muscle attachment area."

    @classmethod
    def poll(cls, context):
        return context.scene.selected_reference_object is not None

    def execute(self, context):
        obj = context.scene.selected_reference_object

        #Change to object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Check if the object is a mesh
        if obj.type != 'MESH':
            self.report({'ERROR'}, f"Object '{obj.name}' is not a mesh.")
            return {'CANCELLED'}
        
        # Ensure the active object is in 'OBJECT' mode before switching to 'EDIT' mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')    
        obj.select_set(True)
        context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        
        return {'FINISHED'}