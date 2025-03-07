#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty


class VIEW3D_OT_SubmitFixationPointOperator(Operator):
    bl_idname = "view3d.submit_fixation_point"
    bl_label = "Submit Fixation Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a vertex group with selected vertices and assigns fixation constraints based on checkbox selections."

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == 'EDIT' and
                bool(context.scene.selected_main_object))
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
                
        # Switch to object mode to access vertex selection
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Get selected vertices
        selected_verts = [v for v in mesh.vertices if v.select]
        if not selected_verts:
            self.report({'ERROR'}, "No vertices selected for fixation")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Create a new vertex group with proper naming
        # Get fixation type from enum property
        fixation_type = context.scene.fixation_type  # 'contact' or 'constraint'
        
        # Find the highest existing number for this fixation type
        highest_num = 0
        prefix = f"{fixation_type}_"
        for group in obj.vertex_groups:
            if group.name.startswith(prefix):
                try:
                    num = int(group.name[len(prefix):])
                    highest_num = max(highest_num, num)
                except ValueError:
                    pass
        
        # Create new group name with incremental number
        group_name = f"{prefix}{highest_num + 1}"
        vgroup = obj.vertex_groups.new(name=group_name)
        
        # Add selected vertices to the group
        for v in selected_verts:
            vgroup.add([v.index], 1.0, 'REPLACE')
        # Create vertex attributes if they don't exist
        if "fixation_x" not in mesh.attributes:
            mesh.attributes.new("fixation_x", 'BOOLEAN', 'POINT')
        if "fixation_y" not in mesh.attributes:
            mesh.attributes.new("fixation_y", 'BOOLEAN', 'POINT')
        if "fixation_z" not in mesh.attributes:
            mesh.attributes.new("fixation_z", 'BOOLEAN', 'POINT')
            
        # Set attribute values for selected vertices
        fixation_x_attr = mesh.attributes["fixation_x"]
        fixation_y_attr = mesh.attributes["fixation_y"]
        fixation_z_attr = mesh.attributes["fixation_z"]
        
        for v in selected_verts:
            fixation_x_attr.data[v.index].value = False
            fixation_y_attr.data[v.index].value = False
            fixation_z_attr.data[v.index].value = False
        
        # Store the last selected vertex coordinates for display
        if selected_verts:
            last_vert = selected_verts[-1]
            coords_str = f"{last_vert.co.x:.4f}, {last_vert.co.y:.4f}, {last_vert.co.z:.4f}"
            context.scene.fixation_point_coordinates = coords_str
        
        # Return to edit mode
        bpy.ops.object.mode_set(mode='EDIT')

        # Activate the fixation group in context.current_fixation_group
        context.scene.current_fixation_group = group_name
    
        # Change the fixations to false
        context.scene.fixation_x = False
        context.scene.fixation_y = False
        context.scene.fixation_z = False

        
        self.report({'INFO'}, f"Created fixation group '{group_name}' with {len(selected_verts)} vertices")
        return {'FINISHED'}