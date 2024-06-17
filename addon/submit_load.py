#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import mathutils
import json  

class View3D_OT_Submit_load(Operator):
    bl_idname = "view3d.submit_load"
    bl_label = "Submit Load"
    bl_description = "Stores the coordinates of the selected vertices in context.scene.loads."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and 
                context.scene.load_name.strip() != "" and
                context.mode == 'EDIT_MESH')

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
    
        if not hasattr(context.scene, 'loads') or not context.scene.loads:
            context.scene.loads = "[]"
    
        loads = json.loads(context.scene.loads)
    
        for load in loads:
            if load['name'] == context.scene.load_name.strip():
                self.report({'ERROR'}, "Load name already exists. Please assign a different name or press <refresh loads list> to update the existing load.")
                return {'CANCELLED'}
    
        # Crear un nuevo vertex group
        vertex_group_name = f"{context.scene.load_name.strip()}_load"
        vertex_group = active_object.vertex_groups.new(name=vertex_group_name)
    
        # Agregar los vértices seleccionados al vertex group
        for vertex_index in selected_vertices_indices:
            vertex_group.add([vertex_index], 1.0, 'ADD')
    
        # Calcular el centroide de los vértices seleccionados
        sum_coords = mathutils.Vector((0, 0, 0))
        for vertex_index in selected_vertices_indices:
            sum_coords += active_object.data.vertices[vertex_index].co

        num_vertices = len(selected_vertices_indices)

        if context.scene.load_input_method == 'VERTICES':
            selected_vertex = active_object.data.vertices[selected_vertices_indices[0]]
            selected_vertex_position = mathutils.Vector((selected_vertex.co.x, selected_vertex.co.y, selected_vertex.co.z))
            focal_point_list = json.loads(context.scene.loads_focal)
            focal_point_position = mathutils.Vector(focal_point_list)
            force_vector = focal_point_position - selected_vertex_position
            force_direction = force_vector.normalized()
            
            total_force = context.scene.load_force
            #convert the axes to the required system (x = -x, y = -z, z = -y)
            adjusted_load_x = (force_direction.y * total_force) / num_vertices
            adjusted_load_y = ((force_direction.z * total_force) / num_vertices) * -1
            adjusted_load_z = ((force_direction.x * total_force) / num_vertices) * -1
        elif context.scene.load_input_method == 'MANUAL':
            
            adjusted_load_x = context.scene.load_x / num_vertices
            adjusted_load_y = context.scene.load_y / num_vertices
            adjusted_load_z = context.scene.load_z / num_vertices

        else:
            self.report({'ERROR'}, "Invalid load input method")
            return {'CANCELLED'}
        
        for vertex_index in selected_vertices_indices:
            vertex_coordinates = active_object.data.vertices[vertex_index].co
            transformed_coordinates = get_transformed_coordinates(active_object, vertex_coordinates)
            load = {
                'name': context.scene.load_name.strip(),
                'nodes': [[transformed_coordinates.x, transformed_coordinates.y, transformed_coordinates.z]],
                'values': [
                    round(adjusted_load_x, 2), 
                    round(adjusted_load_y, 2),
                    round(adjusted_load_z, 2)  

                ]
            }
            loads.append(load)
        
        context.scene.loads = json.dumps(loads, indent=4, separators=(',', ': '), ensure_ascii=False)
        
        self.report({'INFO'}, "Processed selected vertices, updated loads, and created vertex group. Loads: " + context.scene.loads)
        return {'FINISHED'}