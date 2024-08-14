#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import bpy
import re
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, FloatProperty, CollectionProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper



class VIEW3D_OT_ExportMeshesOperator(Operator):
    bl_idname = "view3d.export_meshes"
    bl_label = "Export Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Export all the files required for the FEA in Fossils. This includes the main mesh/bone, sub-meshes of the main object/bone (Attachment muscle areas), and a Python file with the parameters inputted by the user."
    
    @classmethod
    def poll(cls, context):
        # Verify that the selected folder, new folder name, and main object are valid
        main_object_name = context.scene.selected_main_object
        main_object = bpy.data.objects.get(main_object_name)

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
                selected_main_object = context.scene.selected_main_object                
                muscle_parameters = str(context.scene.get("muscle_parameters", {})).replace('"', "'")
                muscle_parameters = re.sub("''", "'", muscle_parameters)
                muscle_parameters = re.sub("'f'", "f'", muscle_parameters)
                youngs_modulus = context.scene.youngs_modulus
                poissons_ratio = round(context.scene.poissons_ratio, 3)
                fixations = context.scene.get("fixations", [])
                loads = context.scene.get("loads", [])
                                      
                selected_main_object = bpy.data.objects.get(context.scene.selected_main_object)
   
                if collection:
                    
                   
                    selected_main_object = context.scene.selected_main_object
                    main_object = bpy.data.objects.get(selected_main_object)

                    if main_object:
                        bpy.context.view_layer.objects.active = main_object
                        bpy.ops.object.select_all(action='DESELECT')
                        main_object.select_set(True)
                 
                        file_name_main = f"{main_object.name}.stl"
                        file_path_stl_main = os.path.join(file_path, collection_name, file_name_main)
                        bpy.ops.wm.stl_export(filepath=file_path_stl_main, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')

                        bpy.context.view_layer.objects.active = None

                    else:
                        self.report({'ERROR'}, f"Main object '{selected_main_object}' not found")
                       
                    for obj in collection.objects:                          
                        if obj.type == 'MESH':
                        
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)

                            file_name = f"{obj.name}.stl"
                            file_path_stl = os.path.join(file_path, collection_name, file_name)
                            bpy.ops.wm.stl_export(filepath=file_path_stl, export_selected_objects=True, ascii_format=False, forward_axis='Y', up_axis='Z')
                            bpy.context.view_layer.objects.active = None
                            
                    # Create python script
                    script_content = f"""\
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{collection_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{collection_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['muscles'] = {muscle_parameters}
    p['fixations'] = {fixations}
    p['loads'] = {loads}
    
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

                    script_file_path = os.path.join(file_path, "script.py")
                    with open(script_file_path, "w") as script_file:
                        script_file.write(script_content)
                        
                        
                        self.report({'INFO'}, f"Meshes and script exported to: {file_path}")
                else:
                    self.report({'ERROR'}, f"Collection '{collection_name}' not found")

            except Exception as e:
                self.report({'ERROR'}, f"Failed to export meshes and script: {e}")

        else:
            self.report({'ERROR'}, "Please provide a valid file path")

        return {'FINISHED'}