#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import math
import bmesh

class VIEW3D_OT_CalculateAreaOperator(Operator):
    bl_idname = "view3d.calculate_area"
    bl_label = "Calculate Area"
    bl_description = "Calculate the surface area of the main object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.selected_main_object is not None

    def execute(self, context):
        main_obj = context.scene.selected_main_object
        
        if main_obj:
            # Make sure we are working with the correct object
            bpy.ops.object.select_all(action='DESELECT')
            main_obj.select_set(True)
            
            # Calculate area
            area = 0
            if main_obj.type == 'MESH' and main_obj.data:
                mesh = main_obj.data
                area = sum(face.area for face in mesh.polygons)
                
                # Apply object scale
                scale_x = main_obj.scale.x
                scale_y = main_obj.scale.y
                scale_z = main_obj.scale.z
                area *= (scale_x * scale_y + scale_y * scale_z + scale_z * scale_x) / 3
                
                # Format the result for display
                context.scene.calculated_area = f"{area:.2f} mm²"
                # Save the numeric value for scaling use
                context.scene.calculated_area_value = area
                self.report({'INFO'}, f"Surface area: {area:.2f} mm²")
            else:
                context.scene.calculated_area = "Not a valid mesh"
                self.report({'WARNING'}, "Not a valid mesh object")
        else:
            context.scene.calculated_area = "No object selected"
            self.report({'ERROR'}, "No main object selected")
            
        return {'FINISHED'}

class VIEW3D_OT_ScaleToTargetAreaOperator(Operator):
    bl_idname = "view3d.scale_to_target_area"
    bl_label = "Scale to Target Area"
    bl_description = "Scale the main object to achieve the target surface area"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.scene.selected_main_object is not None and 
                context.scene.target_area > 0 and 
                context.scene.calculated_area_value > 0)

    def execute(self, context):
        main_obj = context.scene.selected_main_object
        target_area = context.scene.target_area
        current_area = context.scene.calculated_area_value
        
        if main_obj and target_area > 0 and current_area > 0:
            # Calculate scale factor (area is proportional to the square of the scale)
            scale_factor = math.sqrt(target_area / current_area)
            
            # Save the original scale
            original_scale = main_obj.scale.copy()
            
            # Apply new scale factor
            main_obj.scale.x *= scale_factor
            main_obj.scale.y *= scale_factor
            main_obj.scale.z *= scale_factor
            
            # Update the calculated area
            new_area = current_area * (scale_factor ** 2)
            context.scene.calculated_area = f"{new_area:.2f} mm²"
            context.scene.calculated_area_value = new_area
            # Apply the scale to the object
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            self.report({'INFO'}, f"Object scaled by factor {scale_factor:.3f}. New area: {new_area:.2f} mm²")
        else:
            if not main_obj:
                self.report({'ERROR'}, "No main object selected")
            elif target_area <= 0:
                self.report({'ERROR'}, "Target area must be greater than zero")
            else:
                self.report({'ERROR'}, "Calculate area first")
                
        return {'FINISHED'}
    
class VIEW3D_OT_CalculateVolumeOperator(Operator):
    bl_idname = "view3d.calculate_volume"
    bl_label = "Calculate Volume"
    bl_description = "Calculate the volume of the main object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.selected_main_object is not None

    def execute(self, context):
        main_obj = context.scene.selected_main_object
        
        if main_obj:
            # Make sure we are working with the correct object
            bpy.ops.object.select_all(action='DESELECT')
            main_obj.select_set(True)
            
            # Calculate volume
            volume = 0
            if main_obj.type == 'MESH' and main_obj.data:
                mesh = main_obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                
                # Calculate volume
                volume = bm.calc_volume()
                
                # Apply object scale
                scale_x = main_obj.scale.x
                scale_y = main_obj.scale.y
                scale_z = main_obj.scale.z
                volume *= (scale_x * scale_y * scale_z)
                
                # Format result for display
                context.scene.calculated_volume = f"{volume:.2f} mm³"
                # Save numeric value for scaling use
                context.scene.calculated_volume_value = volume
                self.report({'INFO'}, f"Volume: {volume:.2f} mm³")
                
                bm.free()
            else:
                context.scene.calculated_volume = "Not a valid mesh"
                self.report({'WARNING'}, "Not a valid mesh object")
        else:
            context.scene.calculated_volume = "No object selected"
            self.report({'ERROR'}, "No main object selected")
        return {'FINISHED'}
    
class VIEW3D_OT_ScaleToTargetVolumeOperator(Operator):
    bl_idname = "view3d.scale_to_target_volume"
    bl_label = "Scale to Target Volume"
    bl_description = "Scale the main object to achieve the target volume"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.scene.selected_main_object is not None and 
                context.scene.target_volume > 0 and 
                context.scene.calculated_volume_value > 0)

    def execute(self, context):
        main_obj = context.scene.selected_main_object
        target_volume = context.scene.target_volume
        current_volume = context.scene.calculated_volume_value
        
        if main_obj and target_volume > 0 and current_volume > 0:
            # Calculate scale factor (volume is proportional to the cube of the scale)
            scale_factor = (target_volume / current_volume) ** (1/3)
            
            # Save original scale
            original_scale = main_obj.scale.copy()
            
            # Apply new scale factor
            main_obj.scale.x *= scale_factor
            main_obj.scale.y *= scale_factor
            main_obj.scale.z *= scale_factor
            
            # Update calculated volume
            new_volume = current_volume * (scale_factor ** 3)
            context.scene.calculated_volume = f"{new_volume:.2f} mm³"
            context.scene.calculated_volume_value = new_volume

            # Apply the scale to the object
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            self.report({'INFO'}, f"Object scaled by factor {scale_factor:.3f}. New volume: {new_volume:.2f} mm³")
        else:
            if not main_obj:
                self.report({'ERROR'}, "No main object selected")
            elif target_volume <= 0:
                self.report({'ERROR'}, "Target volume must be greater than zero")
            else:
                self.report({'ERROR'}, "Calculate volume first")
                
        return {'FINISHED'}