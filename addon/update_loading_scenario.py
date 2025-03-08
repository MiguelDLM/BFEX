#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class VIEW3D_OT_UpdateLoadingScenario(Operator):
    bl_idname = "view3d.update_loading_scenario"
    bl_label = "Update Loading Scenario"
    bl_description = "Update loading scenario setting for the selected muscle"
    
    muscle_name: StringProperty(
        name="Muscle Name",
        description="Name of the muscle to update",
        default=""
    )
    
    def execute(self, context):
        if not self.muscle_name:
            if not context.scene.selected_muscle:
                self.report({'ERROR'}, "No muscle selected")
                return {'CANCELLED'}
            muscle = context.scene.selected_muscle
        else:
            # Find the muscle object
            muscle = bpy.data.objects.get(self.muscle_name)
            if not muscle:
                self.report({'ERROR'}, f"Muscle {self.muscle_name} not found")
                return {'CANCELLED'}
        
        # Update the loading scenario
        muscle["Loading scenario"] = context.scene.selected_option
        
        self.report({'INFO'}, f"Updated loading scenario for {muscle.name} to {context.scene.selected_option}")
        return {'FINISHED'}