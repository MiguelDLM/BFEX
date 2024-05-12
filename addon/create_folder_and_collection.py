#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import os
from bpy.types import Operator


class VIEW3D_OT_CreateFolderOperator(Operator):
    bl_idname = "view3d.create_folder"
    bl_label = "Create Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create a folder and collection using the chosen name."
    
    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name

        if file_path and new_folder_name:
            # Check if the collection already exists
            if new_folder_name in bpy.data.collections:
                self.report({'ERROR'}, f"A collection named '{new_folder_name}' already exists. Please choose a different name or delete the existing collection.")
                return {'CANCELLED'}

            try:
                # Create new folder
                folder_path = os.path.join(file_path, new_folder_name)
                os.makedirs(folder_path, exist_ok=True)
                self.report({'INFO'}, f"Folder created at: {folder_path}")

                # Create new collection
                collection = bpy.data.collections.new(new_folder_name)
                bpy.context.scene.collection.children.link(collection)

            except Exception as e:
                self.report({'ERROR'}, f"Failed to create folder, check the folder path: {e}")
        else:
            self.report({'ERROR'}, "Please provide a valid file path and folder name")

        return {'FINISHED'}