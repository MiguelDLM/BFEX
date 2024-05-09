#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator


class VIEW3D_OT_StartSelectionOperator(Operator):
    bl_idname = "view3d.start_selection"
    bl_label = "Start Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and activates the Lasso Select tool. Ensure that the active object is the one you want to use for creating the sub-mesh. Be cautious, as this operation subtracts the sub-mesh from the active object."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)

    def execute(self, context):
        active_object = bpy.data.objects.get(context.scene.selected_main_object)
        context.view_layer.objects.active = active_object
    
        # Ensure the active object is in 'OBJECT' mode before deselecting all
        if active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      
        bpy.context.tool_settings.mesh_select_mode[2] = True        
        bpy.context.tool_settings.mesh_select_mode[0] = False 
        bpy.context.tool_settings.mesh_select_mode[1] = False        
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso", space_type='VIEW_3D')
    
        return {'FINISHED'}