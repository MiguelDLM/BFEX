#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import json
from bpy.types import Operator


class VIEW3D_OT_SubmitParametersOperator(Operator):
    bl_idname = "view3d.submit_parameters"
    bl_label = "Submit Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the parameters (Name of the last sub-mesh created, Focal Point, Force, and loading scenario) in a dictionary."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name)

    def execute(self, context):
    
        context.scene.focal_point_coordinates = ""

        # Add muscle force and loading scenario as custom properties to the selected muscle
        selected_muscle = context.scene.selected_muscle
        selected_muscle["Force"] = context.scene.force_value
        selected_muscle["Loading scenario"] = context.scene.selected_option
        return {'FINISHED'}