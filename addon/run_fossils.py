#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import os
import subprocess
import platform
import ctypes
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
        python_file_path = os.path.join(python_file_path, "script.py")
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
            if platform.system() == 'Windows' and context.scene.run_as_admin:
                args = ' '.join(args)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", fossils_path, args, python_file_path, 1)
            else:
                if platform.system() == 'Windows':
                    subprocess.Popen([fossils_path] + args, creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif platform.system() == 'Linux':
                    subprocess.Popen(['xterm', '-e', fossils_path] + args)
            
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
        user_folder = os.path.expanduser("~")
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name.lower()
        prefs = bpy.context.preferences.addons[__name__].preferences
        fossils_path = prefs.fossils_path

        fea_results_folders = [
            os.path.join(file_path, "workspace",new_folder_name+"_script"),
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "_internal", "workspace"),
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "workspace")
        ]

        found_folder = None
        for fea_results_folder in fea_results_folders:
            if os.path.exists(fea_results_folder):
                found_folder = fea_results_folder
                break

        if found_folder:
            bpy.ops.wm.path_open(filepath=found_folder)
            self.report({'INFO'}, f"FEA results folder opened: {found_folder}")
        else:
            self.report({'ERROR'}, f"FEA results folder not found. Verify Fossils is installed in {fossils_path} or you have run a FEA before")

        return {'FINISHED'}
