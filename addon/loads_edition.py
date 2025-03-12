import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class VIEW3D_OT_SelectLoadGroup(Operator):
    bl_idname = "view3d.select_load_group"
    bl_label = "Select Load Group"
    bl_description = "Select a load group to view or edit its properties"
    
    group_name: StringProperty(
        name="Group Name",
        description="Name of the load group to select"
    )
    
    def execute(self, context):
        obj = context.scene.selected_main_object
        
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Select the object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            # Change to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            
            # Activate the vertex group
            obj.vertex_groups.active_index = obj.vertex_groups[self.group_name].index
            
            # Select vertices in the group
            bpy.ops.object.vertex_group_select()
            
            # Get the load attributes if they exist
            if "load_attributes" in obj and self.group_name in obj["load_attributes"]:
                attrs = obj["load_attributes"][self.group_name]
                context.scene.edit_load_x = attrs.get("load_x", 0.0)
                context.scene.edit_load_y = attrs.get("load_y", 0.0)
                context.scene.edit_load_z = attrs.get("load_z", 0.0)
            else:
                context.scene.edit_load_x = 0.0
                context.scene.edit_load_y = 0.0
                context.scene.edit_load_z = 0.0
            
            # Store the selected group
            context.scene.current_load_group = self.group_name
            
            # Force redraw
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            self.report({'INFO'}, f"Selected load group: {self.group_name}")
        else:
            self.report({'ERROR'}, f"Load group {self.group_name} not found")
        
        return {'FINISHED'}

class VIEW3D_OT_DeleteLoadGroup(Operator):
    bl_idname = "view3d.delete_load_group"
    bl_label = "Delete Load Group"
    bl_description = "Delete the selected load group"
    
    group_name: StringProperty(
        name="Group Name",
        description="Name of the load group to delete"
    )
    
    def execute(self, context):
        obj = context.scene.selected_main_object
        
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Delete the vertex group
            vgroup = obj.vertex_groups[self.group_name]
            obj.vertex_groups.remove(vgroup)
            
            # Delete the load attributes if they exist
            if "load_attributes" in obj and self.group_name in obj["load_attributes"]:
                load_attrs = obj["load_attributes"]
                if self.group_name in load_attrs:
                    del load_attrs[self.group_name]
                    obj["load_attributes"] = load_attrs
            
            # Clear the current load group if it was the one deleted
            if context.scene.current_load_group == self.group_name:
                context.scene.current_load_group = ""
                
            self.report({'INFO'}, f"Deleted load group: {self.group_name}")
        else:
            self.report({'ERROR'}, f"Load group {self.group_name} not found")
        
        return {'FINISHED'}

class VIEW3D_OT_UpdateLoadAttributes(Operator):
    bl_idname = "view3d.update_load_attributes"
    bl_label = "Update Load Attributes"
    bl_description = "Update load attributes for the selected load group"
    
    def execute(self, context):
        if not context.scene.current_load_group:
            self.report({'ERROR'}, "No load group selected")
            return {'CANCELLED'}
            
        obj = context.scene.selected_main_object
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
            
        if not obj or not hasattr(obj, 'vertex_groups'):
            self.report({'ERROR'}, "No valid object selected")
            return {'CANCELLED'}
            
        # Verify that the load group exists
        if context.scene.current_load_group not in obj.vertex_groups:
            self.report({'ERROR'}, f"Load group {context.scene.current_load_group} not found")
            return {'CANCELLED'}
            
        # Update the load attributes
        group_name = context.scene.current_load_group
        mesh = obj.data
        
        # Create the load attributes dictionary if it doesn't exist
        if "load_attributes" not in obj:
            obj["load_attributes"] = {}
            
        if group_name not in obj["load_attributes"]:
            obj["load_attributes"][group_name] = {}
        
        # Actualizar los valores de carga
        load_attrs = obj["load_attributes"][group_name]
        load_attrs["load_x"] = context.scene.edit_load_x
        load_attrs["load_y"] = context.scene.edit_load_y
        load_attrs["load_z"] = context.scene.edit_load_z
        
        # Update the total force
        total_force = (context.scene.edit_load_x**2 + context.scene.edit_load_y**2 + context.scene.edit_load_z**2)**0.5
        load_attrs["total_force"] = total_force
        
        # Update the load method
        obj["load_attributes"][group_name] = load_attrs
        
        try:
            # Get the selected vertices
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.vertex_group_select()
            selected_vertices_indices = [v.index for v in mesh.vertices if v.select]
            
            # Update the load values
            if "load_x" in mesh.attributes:
                for idx in selected_vertices_indices:
                    mesh.attributes["load_x"].data[idx].value = context.scene.edit_load_x
                    
            if "load_y" in mesh.attributes:
                for idx in selected_vertices_indices:
                    mesh.attributes["load_y"].data[idx].value = context.scene.edit_load_y
                    
            if "load_z" in mesh.attributes:
                for idx in selected_vertices_indices:
                    mesh.attributes["load_z"].data[idx].value = context.scene.edit_load_z
                    
            # Return to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
        except Exception as e:
            self.report({'WARNING'}, f"Warning: Could not update some attributes: {str(e)}")
        
        self.report({'INFO'}, f"Updated load values for {group_name}")
        return {'FINISHED'}