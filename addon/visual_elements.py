#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import math
import random
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
        main_object = bpy.data.objects.get(selected_main_object) if isinstance(selected_main_object, str) else selected_main_object
        red_material = self.create_material("RedMaterial", (1, 0, 0, 1))
        yellow_material = self.create_material("YellowMaterial", (1, 1, 0, 1))
        blue_material = self.create_material("BlueMaterial", (0, 0, 1, 1))

        # Mostrar áreas de fijación con colores aleatorios
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
        
        # Mostrar direcciones de fuerza (usando selección de músculos)
        if context.scene.show_force_directions:
            attachment_collection = bpy.data.collections.get(context.scene.new_folder_name)
            if attachment_collection:
                for muscle_obj in attachment_collection.objects:
                    if "Focal point" in muscle_obj:
                        try:
                            # Obtener punto focal desde las propiedades personalizadas
                            focal_point_str = muscle_obj["Focal point"]
                            focal_coords = focal_point_str.split(',')
                            focal_point = Vector([float(coord) for coord in focal_coords])
                            
                            # Obtener el grupo de vértices correspondiente
                            muscle_name = muscle_obj.name
                            if muscle_name in main_object.vertex_groups:
                                vg = main_object.vertex_groups[muscle_name]
                                vertices = [v.co for v in main_object.data.vertices 
                                           if vg.index in [g.group for g in v.groups]]
                                
                                if vertices:
                                    centroid = sum(vertices, Vector()) / len(vertices)
                                    centroid_global = main_object.matrix_world @ centroid
                                    direction = (focal_point - centroid_global).normalized()
                                    orientation = (direction.x, direction.y, direction.z)
                                    
                                    self.create_combined_object_at_location(
                                        focal_point, 
                                        visual_elements_collection, 
                                        f"ForceDirection_{muscle_name}", 
                                        orientation=orientation, 
                                        material=blue_material
                                    )
                                else:
                                    self.report({'WARNING'}, f"No vertices found in muscle group: {muscle_name}")
                            else:
                                self.report({'WARNING'}, f"Muscle group not found: {muscle_name}")
                        except Exception as e:
                            self.report({'ERROR'}, f"Error processing muscle {muscle_obj.name}: {str(e)}")
            else:
                self.report({'WARNING'}, "Attachment collection not found. Please define muscles first.")

        # Mostrar puntos de contacto
        if main_object and context.scene.show_contact_points:
            for group in main_object.vertex_groups:
                if group.name.startswith("contact_"):
                    vertices_indices = [v.index for v in main_object.data.vertices 
                                       if group.index in [g.group for g in v.groups]]
                    vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co 
                                               for i in vertices_indices]
                    
                    # Verificar si hay información de ejes fijos
                    has_x = has_y = has_z = False
                    if "fixation_attributes" in main_object and group.name in main_object["fixation_attributes"]:
                        attrs = main_object["fixation_attributes"][group.name]
                        has_x = attrs.get("fixation_x", False)
                        has_y = attrs.get("fixation_y", False)
                        has_z = attrs.get("fixation_z", False)
                    
                    for coord in vertex_coordinates_global:
                        self.create_combined_object_at_location(
                            coord, 
                            visual_elements_collection, 
                            f"{group.name}{'_X' if has_x else ''}{'_Y' if has_y else ''}{'_Z' if has_z else ''}", 
                            orientation='RIGHT', 
                            material=red_material
                        )

        # Mostrar puntos de restricción
        if main_object and context.scene.show_constraint_points:
            for group in main_object.vertex_groups:
                if group.name.startswith("constraint_"):
                    vertices_indices = [v.index for v in main_object.data.vertices 
                                       if group.index in [g.group for g in v.groups]]
                    vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co 
                                               for i in vertices_indices]
                    
                    # Verificar si hay información de ejes fijos
                    has_x = has_y = has_z = False
                    if "fixation_attributes" in main_object and group.name in main_object["fixation_attributes"]:
                        attrs = main_object["fixation_attributes"][group.name]
                        has_x = attrs.get("fixation_x", False)
                        has_y = attrs.get("fixation_y", False)
                        has_z = attrs.get("fixation_z", False)
                    
                    for coord in vertex_coordinates_global:
                        self.create_combined_object_at_location(
                            coord, 
                            visual_elements_collection, 
                            f"{group.name}{'_X' if has_x else ''}{'_Y' if has_y else ''}{'_Z' if has_z else ''}", 
                            orientation='UP', 
                            material=yellow_material
                        )
        
        # Mostrar cargas (loads)
        if main_object and context.scene.show_force_directions:
            for group in main_object.vertex_groups:
                if group.name.endswith("_load"):
                    vertices_indices = [v.index for v in main_object.data.vertices 
                                      if group.index in [g.group for g in v.groups]]
                    vertex_coordinates_global = [main_object.matrix_world @ main_object.data.vertices[i].co 
                                               for i in vertices_indices]
                    
                    # Obtener dirección de carga desde las propiedades personalizadas
                    orientation = 'RIGHT'  # Orientación por defecto
                    if "load_attributes" in main_object and group.name in main_object["load_attributes"]:
                        load_attrs = main_object["load_attributes"][group.name]
                        load_x = load_attrs.get("load_x", 0)
                        load_y = load_attrs.get("load_y", 0)
                        load_z = load_attrs.get("load_z", 0)
                        
                        # Crear vector de orientación
                        if any([load_x, load_y, load_z]):  # Si hay algún valor distinto de cero
                            vector = Vector((load_x, load_y, load_z))
                            vector.normalize()
                            orientation = (-vector.x, -vector.y, -vector.z)
                    
                    # Crear visualización para cada vértice en el grupo
                    for coord in vertex_coordinates_global:
                        self.create_combined_object_at_location(
                            coord, 
                            visual_elements_collection, 
                            f"{group.name}", 
                            orientation=orientation, 
                            material=red_material
                        )

        return {'FINISHED'}