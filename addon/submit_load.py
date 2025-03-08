#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import mathutils
import json  

class View3D_OT_Submit_load(Operator):
    bl_idname = "view3d.submit_load"
    bl_label = "Submit Load"
    bl_description = "Creates a vertex group with load properties for selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                context.scene.load_name.strip() != "" and
                context.mode == 'EDIT_MESH')

    def execute(self, context):
        active_object = context.active_object
        mesh = active_object.data
    
        if active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
    
        selected_vertices_indices = [v.index for v in mesh.vertices if v.select]
    
        if not selected_vertices_indices:
            self.report({'ERROR'}, "No vertices selected.")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
    
        # Create vertex group
        vertex_group_name = f"{context.scene.load_name.strip()}_load"
        
        # Check if vertex group already exists
        if vertex_group_name in active_object.vertex_groups:
            self.report({'ERROR'}, f"Load name '{context.scene.load_name.strip()}' already exists. Please use a different name.")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
            
        vertex_group = active_object.vertex_groups.new(name=vertex_group_name)
    
        # Add selected vertices to the group
        for vertex_index in selected_vertices_indices:
            vertex_group.add([vertex_index], 1.0, 'ADD')
    
        num_vertices = len(selected_vertices_indices)

        # Calculate load values
        if context.scene.load_input_method == 'VERTICES':
            # Get the selected vertex position
            selected_vertex = mesh.vertices[selected_vertices_indices[0]]
            selected_vertex_position = active_object.matrix_world @ selected_vertex.co.copy()
            
            # Get the focal point
            if not hasattr(context.scene, 'loads_focal') or context.scene.loads_focal == "":
                self.report({'ERROR'}, "No focal point defined. Select a focal point first.")
                bpy.ops.object.mode_set(mode='EDIT')
                return {'CANCELLED'}
                
            focal_point_list = json.loads(context.scene.loads_focal)
            focal_point_position = mathutils.Vector(focal_point_list)
            force_vector = focal_point_position - selected_vertex_position
            force_direction = force_vector.normalized()

            total_force = context.scene.load_force
            adjusted_load_x = (force_direction.x * total_force) * -1
            adjusted_load_y = (force_direction.y * total_force)
            adjusted_load_z = (force_direction.z * total_force) * -1

        elif context.scene.load_input_method == 'MANUAL':
            adjusted_load_x = context.scene.load_x / num_vertices
            adjusted_load_y = context.scene.load_y / num_vertices
            adjusted_load_z = context.scene.load_z / num_vertices
        else:
            self.report({'ERROR'}, "Invalid load input method")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Store load properties in the object
        if "load_attributes" not in active_object:
            active_object["load_attributes"] = {}
            
        # Create a dictionary with the load properties
        active_object["load_attributes"][vertex_group_name] = {
            "load_x": adjusted_load_x,
            "load_y": adjusted_load_y,
            "load_z": adjusted_load_z,
            "total_force": total_force if context.scene.load_input_method == 'VERTICES' else 
                           (context.scene.load_x**2 + context.scene.load_y**2 + context.scene.load_z**2)**0.5,
            "method": context.scene.load_input_method
        }
        
        # Add load attributes to the mesh 
        load_attrs = ["load_x", "load_y", "load_z"]
        try:
            # Create or access the vertex attributes dictionary
            for attr_name in load_attrs:
                if attr_name not in mesh.attributes:
                    mesh.attributes.new(attr_name, 'FLOAT', 'POINT')
                    
                    # Initialize the attribute for all vertices
                    for i in range(len(mesh.vertices)):
                        try:
                            mesh.attributes[attr_name].data[i].value = 0.0
                        except IndexError:
                            # This can happen if the mesh has more vertices than the attribute
                            print(f"Warning: Mesh has more vertices than the attribute '{attr_name}'")
                    
            # Assign the load values to the selected vertices
            for vertex_index in selected_vertices_indices:
                mesh.attributes["load_x"].data[vertex_index].value = adjusted_load_x
                mesh.attributes["load_y"].data[vertex_index].value = adjusted_load_y
                mesh.attributes["load_z"].data[vertex_index].value = adjusted_load_z
                
        except Exception as e:
            self.report({'WARNING'}, f"Warning: Could not update some attributes: {str(e)}")

        
        # Return to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        self.report({'INFO'}, f"Created load '{vertex_group_name}' with {num_vertices} vertices")
        return {'FINISHED'}