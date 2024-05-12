#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import os
import json
import re
from mathutils import Vector
from bpy.types import Operator
from mathutils import kdtree


class VIEW3D_OT_ExportSensitivityAnalysisOperator(Operator):
    bl_idname = "view3d.export_sensitivity_analysis"
    bl_label = "Export for Sensitivity Analysis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        #Import variables
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name
        collection_to_copy = bpy.data.collections.get(new_folder_name)
        selected_main_object = context.scene.selected_main_object
        main_object = bpy.data.objects.get(selected_main_object)
        file_name_main = f"{main_object.name}.stl"
        sensitivity_collection_name = "Sensitivity Analysis"
        sensitivity_collection = bpy.data.collections.get(sensitivity_collection_name)
        muscle_parameters = str(context.scene.get("muscle_parameters", {})).replace('"', "'")
        muscle_parameters = re.sub("''", "'", muscle_parameters)
        muscle_parameters = re.sub("'f'", "f'", muscle_parameters)
        youngs_modulus = context.scene.youngs_modulus
        poissons_ratio = round(context.scene.poissons_ratio, 3) 
        scale_factor = context.scene.scale_factor
        fixations = context.scene.get("fixations", [])
        loads = context.scene.get("loads", [])
        
        # Check if the collection already exists
        if sensitivity_collection is None:
            # If it doesn't exist, create it
            sensitivity_collection = bpy.data.collections.new(sensitivity_collection_name)
            bpy.context.scene.collection.children.link(sensitivity_collection)
        else:
            # If it already exists, empty the collection by removing all objects
            for obj in sensitivity_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        if main_object is None:
            self.report({'ERROR'}, "Main object not found. Please submit a main object first.")
            return {'CANCELLED'}

        # Create an independent copy of the main object
        copy_main_object = main_object.copy()
        copy_main_object.data = main_object.data.copy()
        copy_main_object.animation_data_clear()

        # Move the copy to the new collection
        sensitivity_collection.objects.link(copy_main_object)

        if scale_factor == 1:
            # Do not perform any operation, as the scale factor is 1
            pass
        else:

            # Set copy_main_object as the active object
            bpy.context.view_layer.objects.active = copy_main_object

            if scale_factor < 1:
                # If the scale factor is less than 1, apply decimate directly
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = scale_factor
            else:
                # Calculate the number of cuts for subdivide edges
                if scale_factor <= 4:
                    num_cuts = 1
                elif scale_factor <= 9:
                    num_cuts = 2
                elif scale_factor <= 16:
                    num_cuts = 3

                # Apply subdivide edges directly on the mesh data
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.subdivide(number_cuts=num_cuts, smoothness=0)
                bpy.ops.object.mode_set(mode='OBJECT')

                # Calculate the decimation factor
                decimate_factor = scale_factor / ((num_cuts + 1) ** 2)

                # Apply the decimate operator with the calculated factor
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = decimate_factor

            # Apply the decimate modifier
            bpy.ops.object.modifier_apply(modifier="Decimate")

        if collection_to_copy is None:
            self.report({'ERROR'}, "Source collection not found. Please create it first.")
            return {'CANCELLED'}

        # Create a copy of the global fixations variable
        new_fixations = fixations
        # Convert the JSON string to a Python list
        new_fixations_list = json.loads(new_fixations)       
        # Create a kD vertex tree for the decimated object
        vertices = [copy_main_object.matrix_world @ v.co for v in copy_main_object.data.vertices]
        tree = kdtree.KDTree(len(vertices))
        for i, vertex in enumerate(vertices):
            tree.insert(vertex, i)
        tree.balance()
        
        def find_nearest(tree, point):
            return tree.find(point)
        
        for fixation in new_fixations_list:
            for node in fixation['nodes']:
                # Transform the node coordinates to world space
                node_world = copy_main_object.matrix_world @ Vector(node)
                nearest_vertex = find_nearest(tree, node_world)
                if nearest_vertex:
                    # Convert from left-handed to right-handed coordinates
                    nearest_vertex_coordinates = list(nearest_vertex[0])
                    nearest_vertex_coordinates[1] *= -1
                    nearest_vertex_coordinates[0] *= -1
                    node[:] = nearest_vertex_coordinates  
                else:
                    print(f"Skipping node {node} because nearest_vertex is None")

        new_loads = loads
        new_loads_list = json.loads(new_loads)
        for load in new_loads_list:
            for node in load['nodes']:
                # Transform the node coordinates to world space
                node_world = copy_main_object.matrix_world @ Vector(node)
                nearest_vertex = find_nearest(tree, node_world)
                if nearest_vertex:
                    # Convert from left-handed to right-handed coordinates
                    nearest_vertex_coordinates = list(nearest_vertex[0])
                    nearest_vertex_coordinates[1] *= -1
                    nearest_vertex_coordinates[0] *= -1
                    node[:] = nearest_vertex_coordinates  
                else:
                    print(f"Skipping node {node} because nearest_vertex is None")

        #convert the list to a JSON string
        new_fixations = json.dumps(new_fixations_list, indent=4, separators=(',', ': '), ensure_ascii=False)
        new_loads = json.dumps(new_loads_list, indent=4, separators=(',', ': '), ensure_ascii=False)        

        bpy.context.view_layer.objects.active = copy_main_object
        vertex_group_coordinates = {}
        
        for group in copy_main_object.vertex_groups:

            if "_sample" not in group.name and not group.name.startswith(("contact_point", "constraint_point")):
                # Cambiar a modo de edición y seleccionar el grupo de vértices
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group=group.name)
                bpy.ops.object.vertex_group_select()

                # Crear un nuevo objeto solo con las caras seleccionadas
                bpy.ops.mesh.duplicate_move()
                bpy.ops.mesh.select_linked()
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')  

                new_mesh = bpy.context.selected_objects[-1]
                # Renombrar el objeto con el nombre del grupo de vértices
                new_mesh.name = f"{group.name}.001"
                
        for group in copy_main_object.vertex_groups:
            group_name = group.name
            if group_name.endswith("_sample"):
                # Obtener los índices de los vértices del grupo
                group_index = group.index
                vertices_indices = [v.index for v in copy_main_object.data.vertices if group_index in [g.group for g in v.groups]]
                # Obtener las coordenadas de los vértices del grupo en coordenadas locales
                vertex_coordinates_local = [copy_main_object.data.vertices[i].co for i in vertices_indices]
                # Convertir las coordenadas locales a coordenadas globales
                matrix_world = copy_main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                # Almacenar las coordenadas en el diccionario
                vertex_group_coordinates[group_name] = json.dumps(vertex_coordinates_serializable)  
        
        if sensitivity_collection is not None:
            # Obtiene la ruta de la carpeta seleccionada
            folder_path = bpy.path.abspath(bpy.context.scene.selected_folder)
            folder_name = str(round(len(copy_main_object.data.polygons)))+ "_faces"
            full_path = os.path.join(folder_path, folder_name)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

            # Itera sobre todos los objetos en la colección "Sensitivity Analysis"
            for obj in sensitivity_collection.objects:
                # Deselecciona todos los objetos
                bpy.ops.object.select_all(action='DESELECT')

                # Selecciona el objeto que quieres exportar
                obj.select_set(True)

                # Elimina el sufijo ".001" del nombre del objeto
                obj_name = obj.name.split('.')[0]

                # Define el nombre del archivo .stl basado en el nombre del objeto
                mesh_path = os.path.join(folder_path,folder_name, f"{obj_name}.stl")

                # Exporta el objeto seleccionado a un archivo .stl
                bpy.ops.export_mesh.stl(filepath=mesh_path, use_selection=True,axis_forward='-Y', axis_up='Z')
                
        else:
            print("La colección 'Sensitivity Analysis' no existe")
            

                    

        
        # Create python script
        script_content = f"""\
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{folder_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{folder_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['muscles'] = {muscle_parameters}
    p['fixations'] = {new_fixations}
    p['loads'] = {new_loads}
    
    # material properties
    p['density'] = 1.662e-9  # [T/mm³]
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
    
# Areas of interest
"""
        for group_name, coordinates in vertex_group_coordinates.items():
            script_content += f"# {group_name}: {coordinates}\n"
            
        script_file_path = os.path.join(file_path, f"{folder_name}.py")
        with open(script_file_path, "w") as script_file:
            script_file.write(script_content)
            
        self.report({'INFO'}, f"Meshes and script exported to: {folder_name}")
        return {'FINISHED'}        
        