#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import json
from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty


class VIEW3D_OT_SubmitFixationPointOperator(Operator):
    bl_idname = "view3d.submit_fixation_point"
    bl_label = "Submit Fixation Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point as Fixation Point."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)
    
    def execute(self, context):
        point_type = context.scene.fixation_type
        bpy.ops.object.mode_set(mode='OBJECT') 
        selected_verts = [v for v in context.active_object.data.vertices if v.select]
    
        if not selected_verts:
            self.report({'ERROR'}, f"No vertex selected as {point_type.capitalize()} Point")
            return {'FINISHED'}
    
        if point_type == 'constraint' and len(selected_verts) > 1:
            self.report({'ERROR'}, "Only one vertex can be selected to create a constraint point.")
            return {'CANCELLED'}
    
        direction = [axis for axis, selected in [('x', context.scene.fixation_x), ('y', context.scene.fixation_y), ('z', context.scene.fixation_z)] if selected]
    
        if "fixations" not in context.scene:
            context.scene["fixations"] = []
    
        json_data = json.loads(context.scene["fixations"]) if context.scene["fixations"] else []
    
        for i, vert in enumerate(selected_verts):
            bpy.ops.object.mode_set(mode='OBJECT')  
            context.active_object.data.vertices.foreach_set("select", [False] * len(context.active_object.data.vertices))  
            vert.select = True  
            bpy.ops.object.mode_set(mode='EDIT') 
    
            vertex_group_name = f"{point_type}_point{i + 1 + len(json_data)}"
            bpy.ops.object.vertex_group_add()
            vertex_group = context.active_object.vertex_groups[-1]
            vertex_group.name = vertex_group_name
            bpy.ops.object.vertex_group_assign()
    
            bpy.ops.object.mode_set(mode='OBJECT') 
            nodes = [list(vert.co.to_tuple())]  
    
            new_data = {
                "name": vertex_group_name,
                "nodes": nodes,
                "direction": direction
            }
    
            json_data.append(new_data)
    
        json_str = json.dumps(json_data, indent=4, separators=(',', ': '), ensure_ascii=False)
        context.scene["fixations"] = json_str
    
        self.report({'INFO'}, f"Stored data: {json_str}")
        return {'FINISHED'}
      