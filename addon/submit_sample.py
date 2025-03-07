#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator


class VIEW3D_OT_SubmitSampleOperator(Operator):
    bl_idname = "view3d.submit_sample"
    bl_label = "Submit Sample"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a vertex group for the sensitivity analysis"
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.sample_name and context.scene.new_folder_name)
        
    def execute(self, context):
        sample_name = context.scene.sample_name

        # Set object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Check if vertex group already exists
        vgroup_name = f"{sample_name}_sample"
        vgroup = bpy.context.active_object.vertex_groups.get(vgroup_name)
        if vgroup is not None:
            # If it exists, remove all vertices from the group
            bpy.ops.object.vertex_group_set_active(group=vgroup_name)
            bpy.ops.object.vertex_group_remove(all=False)

        # Create vertex group
        vgroup = bpy.context.active_object.vertex_groups.new(name=vgroup_name)
        selected_vertices = [v.index for v in bpy.context.active_object.data.vertices if v.select]
        vgroup.add(selected_vertices, 1.0, 'REPLACE')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.active_object
        bpy.context.active_object.select_set(True)


        return {'FINISHED'}
