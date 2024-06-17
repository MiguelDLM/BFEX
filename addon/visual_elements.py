#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import math
import random
import json
from bpy.types import Operator
from mathutils import Vector
import bmesh

class VIEW3D_OT_VisualElementsOperator(Operator):
    bl_idname = "view3d.visual_elements"
    bl_label = "Visual Elements Operator"
    bl_options = {'REGISTER', 'UNDO'}


    def create_material(self, name, color):
        material = bpy.data.materials.new(name=name)
        material.diffuse_color = color
        return material

    def clear_or_init_collection(self, collection_name):
        collection = bpy.data.collections.get(collection_name)
        if collection:
            for obj in collection.objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(collection)
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def create_combined_object_at_location(self, location_coords, collection, object_name, orientation='DOWN', material=None):
        if location_coords:
            bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1, depth=1, location=location_coords, rotation=(0, 0, math.radians(90)))
            cone = bpy.context.object
            cone.name = object_name
    
            bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=2, location=(location_coords[0], location_coords[1], location_coords[2] - 1), rotation=(0, 0, 0))
            cylinder = bpy.context.object
            cylinder.name = object_name + "_Cylinder"
    
            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.select_all(action='DESELECT')
            cone.select_set(True)
            cylinder.select_set(True)
            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.join()
            

            if isinstance(orientation, str):
                if orientation == 'DOWN':
                    cone.rotation_euler = (math.radians(90), 0, 0)
                elif orientation == 'UP':
                    cone.rotation_euler = (math.radians(-90), 0, 0)
                elif orientation == 'RIGHT':
                    cone.rotation_euler = (0, math.radians(180), 0)
                elif orientation == 'LEFT':
                    cone.rotation_euler = (0, math.radians(0), 0)
            elif isinstance(orientation, (tuple, list)) and len(orientation) == 3:
                orientation_vector = Vector(orientation)
                default_direction = Vector((0, 0, 1))
                rotation_difference = default_direction.rotation_difference(orientation_vector)
                cone.rotation_euler = rotation_difference.to_euler()
    
            collection.objects.link(cone)

            bpy.ops.object.mode_set(mode='EDIT')
            obj = bpy.context.active_object
            mesh = bmesh.from_edit_mesh(obj.data)
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            mesh.verts.ensure_lookup_table()
            for v in mesh.verts:
                v.select = False
            mesh.select_flush(False)
            if len(mesh.verts) > 12:
                mesh.verts[12].select = True
                mesh.select_flush(True)
                bmesh.update_edit_mesh(obj.data)
                bpy.ops.view3d.snap_cursor_to_selected()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.context.scene.cursor.location = location_coords
            obj.location = bpy.context.scene.cursor.location

            # scale the cone using the value in arrows_size property
            obj.scale = (bpy.context.scene.arrows_size, bpy.context.scene.arrows_size, bpy.context.scene.arrows_size)

    
            for old_collection in cone.users_collection:
                if old_collection.name != "Visual elements":
                    old_collection.objects.unlink(cone)
    
            if material:
                cone.data.materials.append(material)


    def execute(self, context):
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        visual_elements_collection = self.clear_or_init_collection("Visual elements")
        selected_main_object = context.scene.selected_main_object
        main_object = bpy.data.objects.get(selected_main_object)
        red_material = self.create_material("RedMaterial", (1, 0, 0, 1))
        yellow_material = self.create_material("YellowMaterial", (1, 1, 0, 1))
        blue_material = self.create_material("BlueMaterial", (0, 0, 1, 1))

        if context.scene.show_attachment_areas:
            attachment_collection = bpy.data.collections.get(context.scene.new_folder_name)
            if attachment_collection:
                for obj in attachment_collection.objects:
                    if obj.type == 'MESH':
                        random_color = (random.random(), random.random(), random.random(), 1.0)
                        new_material = self.create_material("AttachmentMaterial", random_color)
                        if len(obj.data.materials) > 0:
                            obj.data.materials[0] = new_material
                        else:
                            obj.data.materials.append(new_material)
        
        if context.scene.show_force_directions:
            if "muscle_parameters" not in context.scene:
                self.report({'WARNING'}, "Muscles not defined. Please define the muscles first.")
            else:
                muscle_parameters = json.loads(context.scene["muscle_parameters"])
                for entry in muscle_parameters:
                    # Obtener coordenadas de focalpt
                    focal_point_coords = entry.get('focalpt', [])
                    if isinstance(focal_point_coords, list):
                        coords = focal_point_coords
                    else:
                        coords = [focal_point_coords.get('x', 0.0), focal_point_coords.get('y', 0.0), focal_point_coords.get('z', 0.0)]
                        
                    focal_point = Vector(coords)
                    focal_point_name = entry.get('file', '').replace(f"f'{{path}}/", "").replace(".stl'", "")
                    
                    if focal_point_name in main_object.vertex_groups:
                        vg = main_object.vertex_groups[focal_point_name]
                        vertices = [v.co for v in main_object.data.vertices if vg.index in [g.group for g in v.groups]]
                        
                        if vertices:

                            centroid = sum(vertices, Vector()) / len(vertices)
                            centroid_global = main_object.matrix_world @ centroid
                            direction = (focal_point - centroid_global).normalized()
                            orientation = (direction.x, direction.y, direction.z)
                        
                            self.report({'INFO'}, f"Orientation: {orientation}")
                            
                            self.create_combined_object_at_location(focal_point, visual_elements_collection, f"ForceDirection_{focal_point_name}", orientation=orientation, material=blue_material)
                        else:
                            self.report({'WARNING'}, f"No vertices found in the group {focal_point_name}.")
                    else:
                        self.report({'WARNING'}, f"Vertex group {focal_point_name} not found in the main object.")


        if main_object and context.scene.show_contact_points:
            contact_point_groups = [group for group in main_object.vertex_groups if group.name.startswith("contact_point")]
            for group in contact_point_groups:
                vertices_indices = [v.index for v in main_object.data.vertices if group.index in [g.group for g in v.groups]]
                vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co for i in vertices_indices]
                for coord in vertex_coordinates_global:
                    self.create_combined_object_at_location(coord, visual_elements_collection, f"{group.name}", orientation='RIGHT', material=red_material)

        if main_object and context.scene.show_constraint_points:
            constraint_point_groups = [group for group in main_object.vertex_groups if group.name.startswith("constraint_point")]
            for group in constraint_point_groups:
                vertices_indices = [v.index for v in main_object.data.vertices if group.index in [g.group for g in v.groups]]
                vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co for i in vertices_indices]
                for coord in vertex_coordinates_global:
                    self.create_combined_object_at_location(coord, visual_elements_collection, f"{group.name}", orientation='UP', material=yellow_material)
        
        
        if main_object and context.scene.show_contact_points:
            contact_point_groups = [group for group in main_object.vertex_groups if group.name.endswith("_load")]
            loads = json.loads(context.scene["loads"])
            for group in contact_point_groups:
                vertices_indices = [v.index for v in main_object.data.vertices if group.index in [g.group for g in v.groups]]
                vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co for i in vertices_indices]
                group_name_without_load = group.name.removesuffix('_load')
                orientation_values = None
                for load in loads:
                    if load["name"] == group_name_without_load:
                        orientation_values = load["values"]
                        break                  
                if orientation_values:
                    vector = Vector(orientation_values)
                    vector.normalize()
                    orientation = (-vector.x, -vector.y, -vector.z)

                else:
                    orientation = 'RIGHT'
                    self.report({'WARNING'}, f"Orientation values not found for {group_name_without_load}. Using default orientation.")               
                for coord in vertex_coordinates_global:
                    self.create_combined_object_at_location(coord, visual_elements_collection, f"{group.name}", orientation=orientation, material=red_material)

        return {'FINISHED'}