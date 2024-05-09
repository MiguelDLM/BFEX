#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import math
import random
import json
from bpy.types import Operator


class VIEW3D_OT_VisualElementsOperator(Operator):
    bl_idname = "view3d.visual_elements"
    bl_label = "Apply Forces and Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add some visual elements with the information generated before exporting the files"
        
    def execute(self, context):
    
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        collection_name = "Visual elements"

        visual_elements_collection = bpy.data.collections.get(collection_name)
        if visual_elements_collection:
        
            for obj in visual_elements_collection.objects:
                bpy.data.objects.remove(obj)           
            bpy.data.collections.remove(visual_elements_collection)

        visual_elements_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(visual_elements_collection)

        red_material = bpy.data.materials.new(name="RedMaterial")
        red_material.diffuse_color = (1, 0, 0, 1)  # RGB and alpha

        yellow_material = bpy.data.materials.new(name="YellowMaterial")
        yellow_material.diffuse_color = (1, 1, 0, 1) 

        blue_material = bpy.data.materials.new(name="BlueMaterial")
        blue_material.diffuse_color = (0, 0, 1, 1) 
        def generate_random_color():
             return (random.random(), random.random(), random.random(), 1.0)
        if context.scene.show_attachment_areas:
            # Obtener la colección especificada
            attachment_collection = bpy.data.collections.get(context.scene.new_folder_name)

            if attachment_collection:
                for obj in attachment_collection.objects:

                    if obj.type == 'MESH':
                        random_color = generate_random_color()
                        
                        new_material = bpy.data.materials.new(name="AttachmentMaterial")
                        new_material.diffuse_color = random_color
                        
                        if len(obj.data.materials) > 0:
                            obj.data.materials[0] = new_material
                        else:
                            obj.data.materials.append(new_material)

        if not visual_elements_collection:
            visual_elements_collection = bpy.data.collections.new("Visual elements")
            bpy.context.scene.collection.children.link(visual_elements_collection)

        if context.scene.show_force_directions:

            #verification to see if the muscle_parameters already exist
            if "muscle_parameters" not in context.scene:
                self.report({'WARNING'}, "Muscles not defined. Please define the muscles first.")

            else:
        
                muscle_parameters = context.scene.get("muscle_parameters", [])
                muscle_parameters = json.loads(muscle_parameters)

                for entry in muscle_parameters:
                    focal_point_coords = entry.get('focalpt', [])
                    
                    if isinstance(focal_point_coords, list):
                        coords = focal_point_coords
                    else:
                        coords = [focal_point_coords.get('x', 0.0), focal_point_coords.get('y', 0.0), focal_point_coords.get('z', 0.0)]

                    focal_point_name = entry.get('file', '')
                    focal_point_name_clean = focal_point_name.replace(f"f'{{path}}/", "").replace(".stl'", "")
                    self.create_combined_object_at_location(coords, visual_elements_collection, f"ForceDirection_{focal_point_name_clean}",material=blue_material)
            
        selected_main_object = context.scene.selected_main_object  
        main_object = bpy.data.objects.get(selected_main_object)
        
        # Create a list of all vertex groups that start with "contact_point"
        contact_point_groups = [group for group in main_object.vertex_groups if group.name.startswith("contact_point")]
        
        # Check if there are any vertex groups that start with "contact_point"
        if contact_point_groups:
            # Get the coordinates of the contact points
            contact_pts_list = []
            for group in contact_point_groups:
                group_name = group.name
                contact_pts_list.append(group_name)
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                contact_pts_list.append(vertex_coordinates_serializable)
        
            # Create a combined object for each contact point
            if context.scene.show_contact_points:
                for i in range(0, len(contact_pts_list), 2):
                    contact_point_name = contact_pts_list[i]
                    contact_point_coords = contact_pts_list[i + 1]
                    contact_point_coords = contact_point_coords[0]      
                    self.create_combined_object_at_location(contact_point_coords, visual_elements_collection, f"{contact_point_name}",orientation='RIGHT', material=red_material)
        else:
            self.report({'WARNING'}, "No contact points found.")


        #Create a combined object for each constraint point
        constraint_pts_list = []
        for group in main_object.vertex_groups:
            group_name = group.name
            if group_name.startswith("constraint_point"):
                # Count the number of constraint points
                constraint_pts_list.append(group_name)
                #Get the coordinates of the constraint points
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                constraint_pts_list.append(vertex_coordinates_serializable)
        if context.scene.show_constraint_points:
            for i in range(0, len(constraint_pts_list), 2):
                constraint_point_name = constraint_pts_list[i]
                constraint_point_coords = constraint_pts_list[i + 1]
                print("constraint_point_coords:", constraint_point_coords)
                constraint_point_coords = constraint_point_coords[0]      
                self.create_combined_object_at_location(constraint_point_coords, visual_elements_collection, f"{constraint_point_name}", orientation='UP', material=yellow_material)
        
        return {'FINISHED'}

    def create_combined_object_at_location(self, location_coords, collection, object_name, orientation='DOWN', material=None ):
        if location_coords:
            
            bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1, depth=1, location=location_coords, rotation=(0, 0, math.radians(90)))
            cone = bpy.context.object
            cone.name = object_name

            bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(location_coords[0], location_coords[1], location_coords[2] - 1), rotation=(0, 0, 0))
            cylinder = bpy.context.object
            cylinder.name = object_name + "_Cylinder"

            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.select_all(action='DESELECT')
            cone.select_set(True)
            cylinder.select_set(True)
            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.join()

            if orientation == 'DOWN':
                cone.rotation_euler = (math.radians(90), 0, 0)
            elif orientation == 'UP':
                cone.rotation_euler = (math.radians(-90), 0, 0)
            elif orientation == 'RIGHT':
                cone.rotation_euler = (0, math.radians(180), 0)
            elif orientation == 'LEFT':
                cone.rotation_euler = (0, math.radians(0), 0)

            collection.objects.link(cone)

            for old_collection in cone.users_collection:
                if old_collection.name != "Visual elements":
                    old_collection.objects.unlink(cone)
                    
            if material:
                cone.data.materials.append(material)