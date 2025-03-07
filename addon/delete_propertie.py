import bpy
from bpy.types import Operator


class VIEW3D_OT_DeleteCustomProperty(Operator):
    bl_idname = "view3d.delete_custom_property"
    bl_label = "Delete Custom Property"
    bl_description = "Delete a custom property from the selected muscle object"
    bl_options = {'UNDO'}

    property_name: bpy.props.StringProperty()

    def execute(self, context):
        selected_muscle = context.scene.selected_muscle
        if selected_muscle and self.property_name in selected_muscle.keys():
            del selected_muscle[self.property_name]
            self.report({'INFO'}, f"Deleted property '{self.property_name}'")
        else:
            self.report({'WARNING'}, f"Property '{self.property_name}' not found")
        return {'FINISHED'}