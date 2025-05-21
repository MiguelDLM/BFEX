#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import math

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
            # Asegurarse de que estamos trabajando con el objeto correcto
            bpy.ops.object.select_all(action='DESELECT')
            main_obj.select_set(True)
            
            # Calcular el área
            area = 0
            if main_obj.type == 'MESH' and main_obj.data:
                mesh = main_obj.data
                area = sum(face.area for face in mesh.polygons)
                
                # Aplicar la escala del objeto
                scale_x = main_obj.scale.x
                scale_y = main_obj.scale.y
                scale_z = main_obj.scale.z
                area *= (scale_x * scale_y + scale_y * scale_z + scale_z * scale_x) / 3
                
                # Formatear el resultado para mostrarlo
                context.scene.calculated_area = f"{area:.2f} mm²"
                # Guardar el valor numérico para uso en escalado
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
            # Calcular factor de escala (área es proporcional al cuadrado de la escala)
            scale_factor = math.sqrt(target_area / current_area)
            
            # Guardar la escala original
            original_scale = main_obj.scale.copy()
            
            # Aplicar nuevo factor de escala
            main_obj.scale.x *= scale_factor
            main_obj.scale.y *= scale_factor
            main_obj.scale.z *= scale_factor
            
            # Actualizar el área calculada
            new_area = current_area * (scale_factor ** 2)
            context.scene.calculated_area = f"{new_area:.2f} mm²"
            context.scene.calculated_area_value = new_area
            
            self.report({'INFO'}, f"Object scaled by factor {scale_factor:.3f}. New area: {new_area:.2f} mm²")
        else:
            if not main_obj:
                self.report({'ERROR'}, "No main object selected")
            elif target_area <= 0:
                self.report({'ERROR'}, "Target area must be greater than zero")
            else:
                self.report({'ERROR'}, "Calculate area first")
                
        return {'FINISHED'}