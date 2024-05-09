#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

class VIEW3D_OT_SubmitMainObjectOperator(Operator):
    bl_idname = "view3d.submit_object"
    bl_label = "Submit Object"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select one object before clicking here. This button stores the name of the current active object as the main bone/mesh to be used in the FEA."

    def execute(self, context):
        active_object = bpy.context.active_object
        main_object = bpy.context.active_object

        if active_object:
            context.scene.selected_main_object = active_object.name
            self.report({'INFO'}, f"Main object set to: {context.scene.selected_main_object}")
            context.scene.total_faces = len(main_object.data.polygons)

        else:
            self.report({'ERROR'}, "No active object.")

        return {'FINISHED'}