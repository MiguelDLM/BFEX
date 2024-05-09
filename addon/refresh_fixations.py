#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
from bpy.types import Operator


class View3D_OT_Refresh_FixationsOperator(Operator):
    bl_idname = "view3d.refresh_fixation_points"
    bl_label = "Refresh Fixations"
    bl_description = "Refresh the Fixations list based on the vertex groups in the main object."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the main object
        main_object = context.scene.selected_main_object
        main_object = context.scene.objects.get(main_object)
        if not main_object:
            self.report({'ERROR'}, "Main object not found")
            return {'CANCELLED'}
        if not context.scene.fixations or context.scene.fixations == '[]':
            self.report({'ERROR'}, "No fixation points have been defined yet")
            return {'CANCELLED'}
        # Get all vertex groups in the main object
        vertex_groups = main_object.vertex_groups

        # Create a list of vertex group names
        group_names = [group.name for group in vertex_groups]

        fixation_points_str = context.scene.fixations


        fixation_points = json.loads(fixation_points_str)

        # Check if there are any elements in the fixation_points list that match the group_names
        fixation_points2 = []
        for group_name in group_names:
            for point in fixation_points:
                if point['name'] == group_name:
                    fixation_points2.append(point)

        # Convert fixation_points to JSON
        json_str = json.dumps(fixation_points2, indent=4, separators=(',', ': '), ensure_ascii=False)

        context.scene["fixations"] = json_str
        self.report({'INFO'}, "Fixations refreshed")
        self.report({'INFO'}, f"Fixations: {json_str}")

        return {'FINISHED'}