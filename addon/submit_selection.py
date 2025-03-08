#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import re
from bpy.types import Operator


class VIEW3D_OT_SubmitSelectionOperator(Operator):
    bl_idname = "view3d.submit_selection"
    bl_label = "Submit Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a sub-mesh from the selected surface and stores it in the specified collection."
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == 'EDIT' and
                bool(context.scene.submesh_name and context.scene.new_folder_name))
    
    def is_valid_name(self, name):
        # Check if name is not empty
        if not name:
            return False

        # Check if name is not too long
        if len(name) > 64:
            return False

        # Check if name contains only letters, numbers, and underscores
        if not re.match('^[a-zA-Z0-9_]+$', name):
            return False

        return True
      
    def execute(self, context):
        submesh_name = context.scene.submesh_name

        # Validate names
        if not self.is_valid_name(submesh_name):
            self.report({'ERROR'}, f"Invalid submesh name '{submesh_name}'. The submesh name must be non-empty, contain only letters, numbers, and underscores, and be less than 64 characters long.")
            return {'CANCELLED'}

        # Set object mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set object mode: {str(e)}")
            return {'CANCELLED'}

        # # Check if vertex group already exists
        # vgroup = bpy.context.active_object.vertex_groups.get(submesh_name)
        # if vgroup is not None:
        #     # If it exists, remove it
        #     bpy.context.active_object.vertex_groups.remove(vgroup)

        # # Create vertex group
        # vgroup = bpy.context.active_object.vertex_groups.new(name=submesh_name)
        # selected_vertices = [v.index for v in bpy.context.active_object.data.vertices if v.select]
        # vgroup.add(selected_vertices, 1.0, 'REPLACE')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.active_object
        bpy.context.active_object.select_set(True)

        # Check if object with the same name exists in the collection
        collection_name = context.scene.new_folder_name
        collection = bpy.data.collections.get(collection_name)

        if collection:
            existing_object = bpy.data.objects.get(submesh_name)
            if existing_object:
                # If the object exists, unlink and delete it
                existing_object.user_clear()
                bpy.data.objects.remove(existing_object)

            # Create new mesh
            try:

                bpy.ops.object.duplicate(linked=False)
                bpy.ops.object.mode_set(mode='OBJECT')
                temp_vgroup = bpy.context.active_object.vertex_groups.new(name="temp_selection")
                selected_vertices = [v.index for v in bpy.context.active_object.data.vertices if v.select]
                temp_vgroup.add(selected_vertices, 1.0, 'REPLACE')
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.reveal()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.delete(type='FACE')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.context.active_object.vertex_groups.remove(temp_vgroup)

                # Rename mesh
                bpy.context.active_object.name = submesh_name

                # Delete duplicated mesh
                original_collection = bpy.context.active_object.users_collection[0]
                
                # Move new mesh to the collection
                collection.objects.link(bpy.context.active_object)

                original_collection.objects.unlink(bpy.context.active_object)

              
                # Create custom properties for the mesh
                bpy.context.active_object["Focal point"] = "0.0,0.0,0.0"  # Format as float coordinates
                bpy.context.active_object["Loading scenario"] = "T+N"      # Default enum option
                bpy.context.active_object["Force"] = 0.0                   # Float value, not string
            

                context.scene.muscle_created = True
                context.scene.selected_muscle = bpy.context.active_object

                self.report({'INFO'}, f"Submesh '{submesh_name}' created and added to collection '{collection_name}'")

            except Exception as e:
                self.report({'ERROR'}, f"Failed to create new mesh: {str(e)}")
                return {'CANCELLED'}


        else:
            self.report({'ERROR'}, f"Collection '{collection_name}' not found. Please create it first.")
            return {'CANCELLED'}

        return {'FINISHED'}