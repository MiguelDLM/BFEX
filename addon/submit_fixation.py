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
        bpy.ops.object.mode_set(mode='EDIT')
        active_object = bpy.context.active_object
        selected_verts = [v for v in context.active_object.data.vertices if v.select]

        if selected_verts:
            # Count the vertex groups that match the prefix
            matching_vertex_groups = sorted(filter(lambda vg: vg.name.startswith(f"{point_type}_point"), context.active_object.vertex_groups), key=lambda vg: vg.name)
            
            # If the point type is 'constraint' and there are already two vertex groups, cancel the operation
            if point_type == 'constraint' and len(matching_vertex_groups) >= 2:
                self.report({'ERROR'}, "Only two constraint points are allowed. Delete one of the existing constraint points before adding a new one.")
                return

            # If the point type is 'constraint' and more than one vertex is selected, cancel the operation
            if point_type == 'constraint' and len(selected_verts) > 1:
                self.report({'ERROR'}, "Only one vertex can be selected to create a constraint point.")
                return
            
            # Get the selected axes for contact points
            direction = [axis for axis, selected in [('x', context.scene.fixation_x), ('y', context.scene.fixation_y), ('z', context.scene.fixation_z)] if selected]
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

            # Define a global variable for the data in context.scene if it doesn't exist
            if "fixations" not in context.scene:
                context.scene["fixations"] = []
            
            for i, vert in enumerate(selected_verts, start=len(matching_vertex_groups) + 1):
                vertex_group_name = f"{point_type}_point{i}"
                vertex_group = context.active_object.vertex_groups.get(vertex_group_name)
            
                if context.active_object.type != 'MESH':
                    self.report({'ERROR'}, "Active object is not a mesh")
                else:
                    bpy.ops.object.mode_set(mode='EDIT')
                    vert.select = True
                    if not vert.select:
                        self.report({'ERROR'}, "Vertex is not selected")
                    else:
                        bpy.ops.object.vertex_group_add()
                        vertex_group = context.active_object.vertex_groups[-1]
                        vertex_group.name = vertex_group_name
                        bpy.ops.object.vertex_group_assign()
                        # Get the existing data from the scene, or use an empty list if no data exists
                        json_data = json.loads(context.scene["fixations"]) if context.scene["fixations"] else []

                        # Get the selected vertices
                        selected_verts = [v.co for v in bpy.context.active_object.data.vertices if v.select]

                        # Convert the vertices to a list of lists (each inner list is a coordinate)
                        nodes = [list(vert.to_tuple()) for vert in selected_verts]

                        # Create a dictionary for the new data
                        new_data = {
                            "name": vertex_group_name,
                            "nodes": nodes,
                            "direction": direction
                        }

                        json_data.append(new_data)

                        # Convert the list to a JSON string
                        json_str = json.dumps(json_data, indent=4, separators=(',', ': '), ensure_ascii=False)

                        # Store the JSON string in the scene
                        context.scene["fixations"] = json_str

                        self.report({'INFO'}, f"Stored data: {json_str}")
            
                        bpy.ops.object.mode_set(mode='OBJECT')

        else:
            self.report({'ERROR'}, f"No vertex selected as {point_type.capitalize()} Point")     
        return {'FINISHED'}
      