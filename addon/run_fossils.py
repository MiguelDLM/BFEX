#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import os
import subprocess
import platform
from bpy.types import Operator




class VIEW3D_OT_RunFossilsOperator(Operator):
    bl_idname = "view3d.run_fossils"
    bl_label = "Run Fossils"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Run Fossils with the script.py file stored in the selected folder in Browse folder option. Define the path to Fossils in the preferences"
    @classmethod
    def poll(cls, context):
        from . import __name__ as __main__
        prefs = bpy.context.preferences.addons[__main__].preferences
        fossils_path = prefs.fossils_path
        return bool(fossils_path) 
    
    def execute(self, context):
        python_file_path = bpy.path.abspath(context.scene.selected_folder)
        python_file = context.scene.new_folder_name + ".py"
        python_file_path = os.path.join(python_file_path, python_file)
        args = [python_file_path]
        from . import __name__ as __main__
        prefs = bpy.context.preferences.addons[__main__].preferences
        fossils_path = prefs.fossils_path
        self.report({'INFO'}, f"Running Fossils from path: {fossils_path}")


        if context.scene.display_existing_results:
            args.append("--post")
        
        if not context.scene.open_results_when_finish:
            args.append("--nogui")
        
        try:
            cmd = [fossils_path] + args
            if platform.system() == 'Windows':
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=os.path.dirname(python_file_path))
            elif platform.system() == 'Linux':
                subprocess.Popen(['xterm', '-e'] + cmd, cwd=os.path.dirname(python_file_path))
            
            self.report({'INFO'}, f"External program '{fossils_path}' started successfully with Python file: '{python_file_path}'")
        except Exception as e:
            self.report({'ERROR'}, f"Error starting external program: {e}. Be sure to have the correct path to Fossils in the preferences. Command: {fossils_path} {args}")
        return {'FINISHED'}
    

class VIEW3D_OT_OpenFEAResultsFolderOperator(Operator):
    bl_idname = "view3d.open_fea_results_folder"
    bl_label = "Open FEA Results Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open the folder containing FEA results"

    def execute(self, context):
        # Carpeta del usuario
        file_path = bpy.path.abspath(context.scene.selected_folder)

        if os.path.exists(file_path):
            bpy.ops.wm.path_open(filepath=file_path)
            self.report({'INFO'}, f"FEA results folder opened: {file_path}")
        else:
            self.report({'ERROR'}, f"FEA results folder not found: {file_path}")

        return {'FINISHED'}
