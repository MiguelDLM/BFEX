#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

class VIEW3D_OT_BrowseFolderOperator(Operator, ImportHelper):
    bl_idname = "view3d.browse_folder"
    bl_label = "Browse Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select the folder where files will be stored. If there is any text in the 'Browse Folder' window, delete the text."

    def execute(self, context):
        context.scene.selected_folder = self.filepath
        return {'FINISHED'}