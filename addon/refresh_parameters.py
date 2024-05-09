#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import json
from bpy.types import Operator


class VIEW3D_OT_RefreshParametersOperator(Operator):
    bl_idname = "view3d.refresh_parameters"
    bl_label = "Refresh parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Refresh the muscle parameters list based on the objects in the 'Focal points' collection."

    def execute(self, context):
        # Get all objects in the 'Focal points' collection
        focal_points_collection = bpy.data.collections.get('Focal points')
        if not focal_points_collection:
            self.report({'ERROR'}, "No focal points have been saved yet")
            return {'CANCELLED'}
        focal_points = focal_points_collection.objects

        # Create a list of object names
        object_names = ["f'{path}/" + obj.name.split('_focal')[0] + ".stl'" for obj in focal_points]
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)
        # Check if there are any elements in the muscle_parameters list that match the object_names
        muscle_parameters2 = []
        for obj_name in object_names:
            for param in muscle_parameters:
                if param['file'] == obj_name:
                    muscle_parameters2.append(param)
        
        # Convert muscle_parameters to JSON
        json_str = json.dumps(muscle_parameters2, indent=4, separators=(',', ': '), ensure_ascii=False)
        context.scene["muscle_parameters"] = json_str

        self.report({'INFO'}, "Muscle parameters refreshed")
        self.report({'INFO'}, f"Muscle parameters: {json_str}")

        return {'FINISHED'}