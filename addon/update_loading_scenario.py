import bpy
from bpy.types import Operator

class VIEW3D_OT_UpdateLoadingScenario(Operator):
    bl_idname = "view3d.update_loading_scenario"
    bl_label = "Update Loading Scenario"
    bl_description = "Update the loading scenario with the selected option"
    
    def execute(self, context):
        selected_muscle = context.scene.selected_muscle
        if selected_muscle:
            selected_muscle["Loading scenario"] = context.scene.selected_option
            self.report({'INFO'}, f"Updated loading scenario to {context.scene.selected_option}")
        return {'FINISHED'}