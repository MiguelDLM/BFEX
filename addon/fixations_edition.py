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
        
        # Verificar si obj es un string o un objeto
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Asegurarse que estamos seleccionando el objeto correcto
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            # Cambiar a modo edición
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            
            # Activar el grupo de vértices
            obj.vertex_groups.active_index = obj.vertex_groups[self.group_name].index
            
            # Seleccionar el grupo de vértices
            bpy.ops.object.vertex_group_select()
            
            # Obtener atributos de fixation desde propiedades personalizadas
            if "fixation_attributes" in obj and self.group_name in obj["fixation_attributes"]:
                attrs = obj["fixation_attributes"][self.group_name]
                context.scene.fixation_x = attrs.get("fixation_x", False)
                context.scene.fixation_y = attrs.get("fixation_y", False)
                context.scene.fixation_z = attrs.get("fixation_z", False)
            else:
                # Si no hay propiedades establecidas para este grupo, inicializar como False
                context.scene.fixation_x = False
                context.scene.fixation_y = False
                context.scene.fixation_z = False
            
            # Guardar el grupo actual seleccionado
            context.scene.current_fixation_group = self.group_name
            
            # Forzar actualización de la UI para mantener el resaltado
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            # Imprimir los valores de los atributos para depuración
            print("fixation_x:", context.scene.fixation_x, 
                  "fixation_y:", context.scene.fixation_y, 
                  "fixation_z:", context.scene.fixation_z)
            
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
        
        # Verificar si obj es un string o un objeto
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)
        
        if obj and hasattr(obj, 'vertex_groups') and self.group_name in obj.vertex_groups:
            # Eliminar el grupo de vértices
            vgroup = obj.vertex_groups[self.group_name]
            obj.vertex_groups.remove(vgroup)
            
            # Limpiar la referencia al grupo actual si era este
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
            
        # Verificar que el grupo existe
        if context.scene.current_fixation_group not in obj.vertex_groups:
            self.report({'ERROR'}, f"Vertex group {context.scene.current_fixation_group} not found")
            return {'CANCELLED'}
        
        # Almacenar valores como propiedades personalizadas del grupo de vértices
        group_name = context.scene.current_fixation_group
        
        # Crear un diccionario de propiedades si no existe
        if "fixation_attributes" not in obj:
            obj["fixation_attributes"] = {}
            
        # Acceder al diccionario
        fixation_attrs = obj["fixation_attributes"]
        
        # Crear o actualizar la entrada para este grupo
        if group_name not in fixation_attrs:
            fixation_attrs[group_name] = {}
            
        # Actualizar los valores para este grupo
        fixation_attrs[group_name] = {
            "fixation_x": context.scene.fixation_x,
            "fixation_y": context.scene.fixation_y,
            "fixation_z": context.scene.fixation_z
        }
            
        # Guardar de vuelta en el objeto
        obj["fixation_attributes"] = fixation_attrs
        
        self.report({'INFO'}, f"Updated attributes for group: {group_name}")
        return {'FINISHED'}