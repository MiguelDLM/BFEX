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
                
                # Get the main object
                selected_main_object_name = context.scene.selected_main_object
                main_object = bpy.data.objects.get(selected_main_object_name) if isinstance(selected_main_object_name, str) else context.scene.selected_main_object
                
                # Obtain material properties
                youngs_modulus = context.scene.youngs_modulus
                poissons_ratio = round(context.scene.poissons_ratio, 3)
                
                if not main_object:
                    self.report({'ERROR'}, f"Main object not found")
                    return {'CANCELLED'}
                
                if collection:
                    # Export the main object (bone)
                    bpy.context.view_layer.objects.active = main_object
                    bpy.ops.object.select_all(action='DESELECT')
                    main_object.select_set(True)
                    
                    file_name_main = f"{main_object.name}.stl"
                    file_path_stl_main = os.path.join(file_path, collection_name, file_name_main)
                    
                    # Create the folder if it doesn't exist
                    os.makedirs(os.path.join(file_path, collection_name), exist_ok=True)
                    
                    bpy.ops.wm.stl_export(filepath=file_path_stl_main, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')
                    
                    # Export the sub-meshes (attachment muscle areas)
                    for obj in collection.objects:                          
                        if obj.type == 'MESH':
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)

                            file_name = f"{obj.name}.stl"
                            file_path_stl = os.path.join(file_path, collection_name, file_name)
                            bpy.ops.wm.stl_export(filepath=file_path_stl, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')
                    
                    # Build the list of fixations from the vertex groups
                    fixations_list = []
                    for vgroup in main_object.vertex_groups:
                        if vgroup.name.startswith(("contact_", "constraint_")):
                            if "fixation_attributes" in main_object and vgroup.name in main_object["fixation_attributes"]:
                                attrs = main_object["fixation_attributes"][vgroup.name]
                                
                                # Get the constraint axes
                                direction = []
                                if attrs.get("fixation_x", False):
                                    direction.append("x")
                                if attrs.get("fixation_y", False):
                                    direction.append("y")
                                if attrs.get("fixation_z", False):
                                    direction.append("z")
                                
                                # if no direction is set for the fixation, report a warning
                                if not direction:
                                    self.report({'WARNING'}, f"Fixation '{vgroup.name}' with no direction")
                                
                                
                                vertices_indices = [v.index for v in main_object.data.vertices 
                                                  if vgroup.index in [g.group for g in v.groups]]
                                
                                # if no vertices are in the group, report a warning
                                if not vertices_indices:
                                    self.report({'WARNING'}, f"Fixation '{vgroup.name}' with no vertices")
                                
                                # Use the first vertex in the group
                                vertex_index = vertices_indices[0]
                                vertex_co = main_object.data.vertices[vertex_index].co.copy()
                                world_co = main_object.matrix_world @ vertex_co
                                
                                # Create the fixation entry
                                fixation_entry = {
                                    "name": vgroup.name,
                                    "nodes": [[world_co.x, world_co.y, world_co.z]],
                                    "direction": direction
                                }
                                fixations_list.append(fixation_entry)
                    
                    # Build the list of loads from the vertex groups
                    loads_list = []
                    for vgroup in main_object.vertex_groups:
                        if vgroup.name.endswith("_load"):
                            if "load_attributes" in main_object and vgroup.name in main_object["load_attributes"]:
                                attrs = main_object["load_attributes"][vgroup.name]
                                
                                # Obtaining the load values
                                load_x = attrs.get("load_x", 0.0)
                                load_y = attrs.get("load_y", 0.0)
                                load_z = attrs.get("load_z", 0.0)
                                
                                # Obtaining the vertices in the group
                                vertices_indices = [v.index for v in main_object.data.vertices 
                                                  if vgroup.index in [g.group for g in v.groups]]
                                
                                # if no vertices are in the group, report a warning
                                if not vertices_indices:
                                    self.report({'WARNING'}, f"Load '{vgroup.name}' with no vertices")
                                
                                # Create the load entry
                                for vertex_index in vertices_indices:
                                    vertex_co = main_object.data.vertices[vertex_index].co.copy()
                                    world_co = main_object.matrix_world @ vertex_co
                                    
                                    load_entry = {
                                        "name": vgroup.name.replace("_load", ""),
                                        "nodes": [[world_co.x, world_co.y, world_co.z]],
                                        "values": [round(load_x, 2), round(load_y, 2), round(load_z, 2)]
                                    }
                                    loads_list.append(load_entry)
                                    break  
                    
                    
                    # Build the list of muscles from the collection
                    muscles_list = []
                    for obj in collection.objects:
                        if obj.type == 'MESH' and obj != main_object:
                            # Verify that the object has the required properties
                            missing_props = []
                            if "Focal point" not in obj:
                                missing_props.append("Focal point")
                            if "Force" not in obj:
                                missing_props.append("Force")
                            if "Loading scenario" not in obj:
                                missing_props.append("Loading scenario")
                                
                            if missing_props:
                                self.report({'WARNING'}, f"Muscle '{obj.name}' is missing required properties: {', '.join(missing_props)}")
                                continue
                                
                            try:
                                # Obtaining the focal point
                                focal_point_str = obj["Focal point"]
                                focal_coords = focal_point_str.split(',')
                                focal_point = [float(coord) for coord in focal_coords]
                                
                                # Obtaining the force and loading scenario
                                force = float(obj["Force"])
                                loading_scenario = obj["Loading scenario"]
                                
                                # Create the muscle entry
                                muscle_entry = {
                                    "file": f"{{path}}/{obj.name}.stl",
                                    "focalpt": focal_point,
                                    "force": force,
                                    "method": loading_scenario
                                }
                                muscles_list.append(muscle_entry)
                            except (ValueError, IndexError) as e:
                                self.report({'WARNING'}, f"Could not process muscle data for {obj.name}: {str(e)}")
                    
                    # Create the Python script content
                    script_content = f"""#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{collection_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{collection_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['muscles'] = ["""
                    
                    # Generate muscles list manually to preserve f-strings
                    for i, muscle in enumerate(muscles_list):
                        script_content += f"""
    {{
        'file': f'{{path}}/{muscle['file'].split('/')[-1]}',
        'force': {muscle['force']},
        'focalpt': {muscle['focalpt']},
        'method': '{muscle['method']}'
    }}"""
                        if i < len(muscles_list) - 1:
                            script_content += ","
                    
                    script_content += f"""
]
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

                    # write the script to a file
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