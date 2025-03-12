import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

class VIEW3D_OT_SelectFixationGroup(Operator):
    bl_idname = "view3d.select_fixation_group"
    bl_label = "Select Fixation Group"
    bl_description = "Select vertices in the specified fixation group"
    
    group_name: StringProperty(
        name="Group Name",
        description="Name of the vertex group to select"
    )
    
    def execute(self, context):
        obj = context.scene.selected_main_object
        
        # Verify if obj is a string or an object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Check if the object is in edit mode
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            
            # Activating the vertex group
            obj.vertex_groups.active_index = obj.vertex_groups[self.group_name].index
            
            # Select vertices in the group
            bpy.ops.object.vertex_group_select()
            
            # Get the fixation attributes if they exist
            if "fixation_attributes" in obj and self.group_name in obj["fixation_attributes"]:
                attrs = obj["fixation_attributes"][self.group_name]
                context.scene.fixation_x = attrs.get("fixation_x", False)
                context.scene.fixation_y = attrs.get("fixation_y", False)
                context.scene.fixation_z = attrs.get("fixation_z", False)
            else:
                # Reset the attributes if they don't exist
                context.scene.fixation_x = False
                context.scene.fixation_y = False
                context.scene.fixation_z = False
            
            # save the selected group
            context.scene.current_fixation_group = self.group_name
            
            # Force the redraw
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            self.report({'INFO'}, f"Selected vertex group: {self.group_name}")
        else:
            self.report({'ERROR'}, f"Vertex group {self.group_name} not found")
        
        return {'FINISHED'}

class VIEW3D_OT_DeleteFixationGroup(Operator):
    bl_idname = "view3d.delete_fixation_group"
    bl_label = "Delete Fixation Group"
    bl_description = "Delete the specified fixation group"
    
    group_name: StringProperty(
        name="Group Name",
        description="Name of the vertex group to delete"
    )
    
    def execute(self, context):
        obj = context.scene.selected_main_object
        
        # Verify if obj is a string or an object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Delete the vertex group
            vgroup = obj.vertex_groups[self.group_name]
            obj.vertex_groups.remove(vgroup)
            
            # Clear the fixation attributes if they exist
            if context.scene.current_fixation_group == self.group_name:
                context.scene.current_fixation_group = ""
                
            self.report({'INFO'}, f"Deleted vertex group: {self.group_name}")
        else:
            self.report({'ERROR'}, f"Vertex group {self.group_name} not found")
        
        return {'FINISHED'}

class VIEW3D_OT_UpdateFixationAttributes(Operator):
    bl_idname = "view3d.update_fixation_attributes"
    bl_label = "Update Fixation Attributes"
    bl_description = "Update fixation attributes for the current vertex group"
    
    def execute(self, context):
        if not context.scene.current_fixation_group:
            self.report({'ERROR'}, "No fixation group selected")
            return {'CANCELLED'}
            
        obj = context.scene.selected_main_object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            
        if not obj or not hasattr(obj, 'vertex_groups'):
            self.report({'ERROR'}, "No valid object selected")
            return {'CANCELLED'}
            
        # Verify if the vertex group exists
        if context.scene.current_fixation_group not in obj.vertex_groups:
            self.report({'ERROR'}, f"Vertex group {context.scene.current_fixation_group} not found")
            return {'CANCELLED'}
        
        # Save the attributes for the current group
        group_name = context.scene.current_fixation_group
        
        # Create the fixation attributes if they don't exist
        if "fixation_attributes" not in obj:
            obj["fixation_attributes"] = {}
            
        # Access the fixation attributes
        fixation_attrs = obj["fixation_attributes"]
        
        # Create the attributes for this group if they don't exist
        if group_name not in fixation_attrs:
            fixation_attrs[group_name] = {}
            
        # Update the attributes
        fixation_attrs[group_name] = {
            "fixation_x": context.scene.fixation_x,
            "fixation_y": context.scene.fixation_y,
            "fixation_z": context.scene.fixation_z
        }
            
        # Save the updated attributes
        obj["fixation_attributes"] = fixation_attrs
        
        self.report({'INFO'}, f"Updated attributes for group: {group_name}")
        return {'FINISHED'}