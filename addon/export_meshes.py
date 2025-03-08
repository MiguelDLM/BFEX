#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import bpy
import json
import mathutils
from bpy.types import Operator

class VIEW3D_OT_ExportMeshesOperator(Operator):
    bl_idname = "view3d.export_meshes"
    bl_label = "Export Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Export all the files required for the FEA in Fossils. This includes the main mesh/bone, sub-meshes of the main object/bone (Attachment muscle areas), and a Python file with the parameters inputted by the user."
    
    @classmethod
    def poll(cls, context):
        # Verify that the selected folder, new folder name, and main object are valid
        main_object = context.scene.selected_main_object
        return (
            context.scene.selected_folder and
            context.scene.new_folder_name and
            main_object
        )
    
    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)

        if file_path:
            try:
                collection_name = context.scene.new_folder_name
                collection = bpy.data.collections.get(collection_name)
                
                # Obtener el objeto principal
                selected_main_object_name = context.scene.selected_main_object
                main_object = bpy.data.objects.get(selected_main_object_name) if isinstance(selected_main_object_name, str) else context.scene.selected_main_object
                
                # Obtener parámetros del material
                youngs_modulus = context.scene.youngs_modulus
                poissons_ratio = round(context.scene.poissons_ratio, 3)
                
                if not main_object:
                    self.report({'ERROR'}, f"Main object not found")
                    return {'CANCELLED'}
                
                if collection:
                    # Exportar el objeto principal
                    bpy.context.view_layer.objects.active = main_object
                    bpy.ops.object.select_all(action='DESELECT')
                    main_object.select_set(True)
                    
                    file_name_main = f"{main_object.name}.stl"
                    file_path_stl_main = os.path.join(file_path, collection_name, file_name_main)
                    
                    # Crear directorio si no existe
                    os.makedirs(os.path.join(file_path, collection_name), exist_ok=True)
                    
                    bpy.ops.wm.stl_export(filepath=file_path_stl_main, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')
                    
                    # Exportar objetos de la colección (músculos)
                    for obj in collection.objects:                          
                        if obj.type == 'MESH':
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)

                            file_name = f"{obj.name}.stl"
                            file_path_stl = os.path.join(file_path, collection_name, file_name)
                            bpy.ops.wm.stl_export(filepath=file_path_stl, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')
                    
                    # Construir la lista de fijaciones desde las propiedades personalizadas
                    fixations_list = []
                    for vgroup in main_object.vertex_groups:
                        if vgroup.name.startswith(("contact_", "constraint_")):
                            if "fixation_attributes" in main_object and vgroup.name in main_object["fixation_attributes"]:
                                attrs = main_object["fixation_attributes"][vgroup.name]
                                
                                # Determinar qué ejes están restringidos
                                direction = []
                                if attrs.get("fixation_x", False):
                                    direction.append("x")
                                if attrs.get("fixation_y", False):
                                    direction.append("y")
                                if attrs.get("fixation_z", False):
                                    direction.append("z")
                                
                                # Si no hay dirección especificada, continuamos
                                if not direction:
                                    continue
                                
                                # Obtener los vértices en este grupo
                                vertices_indices = [v.index for v in main_object.data.vertices 
                                                  if vgroup.index in [g.group for g in v.groups]]
                                
                                # Si no hay vértices, continuamos
                                if not vertices_indices:
                                    continue
                                
                                # Usar el primer vértice (normalmente es solo uno)
                                vertex_index = vertices_indices[0]
                                vertex_co = main_object.data.vertices[vertex_index].co.copy()
                                world_co = main_object.matrix_world @ vertex_co
                                
                                # Crear la entrada de fijación
                                fixation_entry = {
                                    "name": vgroup.name,
                                    "nodes": [[world_co.x, world_co.y, world_co.z]],
                                    "direction": direction
                                }
                                fixations_list.append(fixation_entry)
                    
                    # Construir la lista de cargas desde las propiedades personalizadas
                    loads_list = []
                    for vgroup in main_object.vertex_groups:
                        if vgroup.name.endswith("_load"):
                            if "load_attributes" in main_object and vgroup.name in main_object["load_attributes"]:
                                attrs = main_object["load_attributes"][vgroup.name]
                                
                                # Obtener los valores de carga
                                load_x = attrs.get("load_x", 0.0)
                                load_y = attrs.get("load_y", 0.0)
                                load_z = attrs.get("load_z", 0.0)
                                
                                # Obtener los vértices en este grupo
                                vertices_indices = [v.index for v in main_object.data.vertices 
                                                  if vgroup.index in [g.group for g in v.groups]]
                                
                                # Si no hay vértices, continuamos
                                if not vertices_indices:
                                    continue
                                
                                # Crear una entrada para cada vértice (normalmente es solo uno)
                                for vertex_index in vertices_indices:
                                    vertex_co = main_object.data.vertices[vertex_index].co.copy()
                                    world_co = main_object.matrix_world @ vertex_co
                                    
                                    # Crear la entrada de carga
                                    load_entry = {
                                        "name": vgroup.name.replace("_load", ""),
                                        "nodes": [[world_co.x, world_co.y, world_co.z]],
                                        "values": [round(load_x, 2), round(load_y, 2), round(load_z, 2)]
                                    }
                                    loads_list.append(load_entry)
                                    break  # Solo tomamos el primer vértice
                    
                    # Construir la lista de músculos desde los objetos en la colección
                    muscles_list = []
                    for obj in collection.objects:
                        if obj.type == 'MESH' and obj != main_object:
                            # Verificar si tiene las propiedades necesarias
                            if "Focal point" in obj and "Force" in obj:
                                try:
                                    # Obtener el punto focal
                                    focal_point_str = obj["Focal point"]
                                    focal_coords = focal_point_str.split(',')
                                    focal_point = [float(coord) for coord in focal_coords]
                                    
                                    # Obtener la fuerza
                                    force = obj["Force"]
                                    
                                    # Crear la entrada del músculo
                                    muscle_entry = {
                                        "name": obj.name,
                                        "focal_point": focal_point,
                                        "force": force
                                    }
                                    muscles_list.append(muscle_entry)
                                except (ValueError, IndexError):
                                    self.report({'WARNING'}, f"Could not process muscle data for {obj.name}")
                    
                    # Crear el contenido del script
                    script_content = f"""#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{collection_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{collection_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['muscles'] = {json.dumps(muscles_list, indent=4)}
    p['fixations'] = {json.dumps(fixations_list, indent=4)}
    p['loads'] = {json.dumps(loads_list, indent=4)}
    
    # material properties
    p['density'] = 1.662e-9  # [T/mm]
    p['Young'] = {youngs_modulus}     # [MPa]
    p['Poisson'] = {poissons_ratio}      # [-]

    # p['use_gmshOld'] = True

    p.update(d)
    return p


def getMetafor(p={{}}):
    import bonemodel as model
    return model.getMetafor(parms(p))


if __name__ == "__main__":
    import models.bonemodel2 as model
    model.solve(parms())
"""

                    # Escribir el archivo Python
                    script_file_path = os.path.join(file_path, f"{collection_name}.py")
                    with open(script_file_path, "w") as script_file:
                        script_file.write(script_content)
                        
                    self.report({'INFO'}, f"Meshes and script exported to: {file_path}")
                else:
                    self.report({'ERROR'}, f"Collection '{collection_name}' not found")

            except Exception as e:
                self.report({'ERROR'}, f"Failed to export meshes and script: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            self.report({'ERROR'}, "Please provide a valid file path")

        return {'FINISHED'}