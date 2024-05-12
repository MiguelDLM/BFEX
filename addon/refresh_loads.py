#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bpy.types import Operator
import json

class VIEW3D_OT_RefreshLoadsOperator(Operator):
    bl_idname = "view3d.refresh_loads"
    bl_label = "Refresh Loads"
    bl_description = "Refresh loads from the file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the main object
        main_object = context.scene.selected_main_object
        main_object = context.scene.objects.get(main_object)
        if not main_object:
            self.report({'ERROR'}, "Main object not found")
            return {'CANCELLED'}
        if not context.scene.loads or context.scene.loads == '[]':
            self.report({'ERROR'}, "No load points have been defined yet")
            return {'CANCELLED'}
        # Get all vertex groups in the main object
        vertex_groups = main_object.vertex_groups

        # Create a list of vertex group names
        group_names = [group.name[:-5] if group.name.endswith('_load') else group.name for group in vertex_groups]

        load_points_str = context.scene.loads


        load_points = json.loads(load_points_str)

        # Check if there are any elements in the loads_points list that match the group_names
        load_points2 = []
        for group_name in group_names:
            for point in load_points:
                if point['name'] == group_name:
                    load_points2.append(point)

        # Convert loads_points to JSON
        json_str = json.dumps(load_points2, indent=4, separators=(',', ': '), ensure_ascii=False)

        context.scene["loads"] = json_str
        self.report({'INFO'}, "Loads refreshed")
        self.report({'INFO'}, f"Loads: {json_str}")

        return {'FINISHED'}