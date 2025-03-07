#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator, Panel
from .update_loading_scenario import VIEW3D_OT_UpdateLoadingScenario

class VIEW3D_PT_BFEXMenu_PT(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BFEXMenu_PT"
    bl_label = "BFEX"
    bl_category = "BFEX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout

        # Data Storage Location
        box = layout.box()
        box.label(text="Data storage folder",icon='FILE_FOLDER')

        row = box.row()
        row.operator("view3d.browse_folder", text="Browse Folder", icon='FILE_FOLDER')
        row.prop(context.scene, "selected_folder", text="")

        row = box.row()
        row.prop(context.scene, "new_folder_name", text="New Folder Name", icon='GREASEPENCIL')
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        row
        row.operator("view3d.create_folder", text="Create Folder", icon='NEWFOLDER')

        row = box.row()

        row.prop(context.scene, "selected_main_object", text="Main Object", icon='OBJECT_DATA')
        row = box.row()
        row.prop(context.scene, "selected_reference_object", text="Reference Object", icon='OBJECT_DATA')

        # Extract Surfaces Section
        box = layout.box()
        box.label(text="Extract muscle attachment areas and properties")

        row = box.row()
        row.prop(context.scene, "submesh_name", text="Muscle name", icon='GREASEPENCIL')
        row = box.row()
        
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.operator("view3d.start_selection", text="Start Selection", icon='RESTRICT_SELECT_OFF')
        col2.operator("view3d.submit_selection", text="Submit Selection", icon='EXPORT')

        row = box.row()
        row.prop(context.scene, "selected_muscle", text="Selected Muscle", icon='OBJECT_DATA')

        # Replace the custom properties section with this code
        selected_muscle = context.scene.selected_muscle
        if selected_muscle:
            # Force property - as float
            if "Force" in selected_muscle.keys():
                row = box.row(align=True)
                row.label(text="Force (N):")
                row.prop(selected_muscle, '["Force"]', text="")

            # Focal point property - as vector coordinates
            if "Focal point" in selected_muscle.keys():
                box.label(text="Focal point:")
                # Parse the stored string to display as coordinates
                focal_coords = selected_muscle["Focal point"].split(',')
                if len(focal_coords) == 3:
                    try:
                        x, y, z = map(float, focal_coords)
                        col = box.column(align=True)
                        row = col.row(align=True)
                        row.label(text="X:")
                        row.label(text=str(round(x, 4)))
                        row = col.row(align=True)
                        row.label(text="Y:")
                        row.label(text=str(round(y, 4)))
                        row = col.row(align=True)
                        row.label(text="Z:")
                        row.label(text=str(round(z, 4)))
                    except ValueError:
                        row = box.row()
                        row.prop(selected_muscle, '["Focal point"]', text="Focal point")
                    # Focal Point Coordinates
                    row = box.row()
                    split = box.split(factor=0.5)
                    col1 = split.column(align=True)
                    col2 = split.column(align=True)

                    col1.operator("view3d.select_focal_point", text="Select Focal Point", icon='RESTRICT_SELECT_OFF')
                    col2.operator("view3d.submit_focal_point", text="Submit Focal Point", icon='EXPORT')

            if "Loading scenario" in selected_muscle.keys():
                row = box.row(align=True)
                row.label(text="Loading scenario:")

                sub_row = row.row()
                sub_row.prop(context.scene, "selected_option", text="")
        
        # Contact Points Section
        box = layout.box()
        box.label(text="Fixation Points", icon='FORCE_FORCE')

        col = box.column(align=True)
            
        col.prop(context.scene, "fixation_point_coordinates", text="Fixation Point Coordinates", emboss=False, icon='VIEW3D')
        col = box.column(align=True)
        col.prop(context.scene, "fixation_type", text="Fixation Type")
        col = box.column(align=True)
        col.operator("view3d.select_fixation_point", text="Select fixation Point", icon='RESTRICT_SELECT_OFF')
        row = box.row()
        row.operator("view3d.submit_fixation_point", text="Submit fixation Point", icon='EXPORT')

        box_groups = box.box()
        box_groups.label(text="Fixation Groups")

        main_obj = None
        if context.scene.selected_main_object:
            if isinstance(context.scene.selected_main_object, str):
                main_obj = bpy.data.objects.get(context.scene.selected_main_object)
            else:
                main_obj = context.scene.selected_main_object

        
        if main_obj and hasattr(main_obj, 'vertex_groups'):
            has_groups = False
            for vgroup in main_obj.vertex_groups:
                if vgroup.name.startswith(("contact_", "constraint_")):
                    has_groups = True
                    row = box_groups.row(align=True)
                    
                    is_active = (context.scene.current_fixation_group == vgroup.name)
                    if is_active:
                        op = row.operator("view3d.select_fixation_group", 
                                         text=vgroup.name, 
                                         icon='GROUP_VERTEX',
                                         depress=True) 
                        op.group_name = vgroup.name
                    else:
                        # Grupo normal
                        op = row.operator("view3d.select_fixation_group", 
                                         text=vgroup.name, 
                                         icon='GROUP_VERTEX')
                        op.group_name = vgroup.name
                    
                    delete_op = row.operator("view3d.delete_fixation_group", text="", icon='X')
                    delete_op.group_name = vgroup.name
                    
            if not has_groups:
                box_groups.label(text="No fixation groups found")
        else:
            box_groups.label(text="No main object selected")
        
        # Select Axes Section for Contact Points (como estaba antes)
        row = box.row(align=True)
        row.label(text="Select Axes:")
        row.prop(context.scene, "fixation_x", text="X")
        row.prop(context.scene, "fixation_y", text="Y")
        row.prop(context.scene, "fixation_z", text="Z")  
        # Después de los checkboxes X, Y, Z
        if context.scene.current_fixation_group:
            row.operator("view3d.update_fixation_attributes", text="Apply", icon='CHECKMARK')

        # Material Properties Section
        box = layout.box()
        box.label(text="Material Properties")
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        # Text boxes to enter values
        col1.prop(context.scene, "youngs_modulus", text="Young's Modulus")
        col2.prop(context.scene, "poissons_ratio", text="Poisson's Ratio")

        # Loads Section
        box = layout.box()
        box.label(text="Loads", icon='FORCE_MAGNETIC')
        
        row = box.row()
        row.prop(context.scene, "load_input_method", expand=True)
        
        if context.scene.load_input_method == 'VERTICES':

            row = box.row()
            row.prop(context.scene, "load_name", text="Load name")
            row = box.row()
            row.operator("view3d.select_fixation_point", text="Select Load points", icon='RESTRICT_SELECT_OFF')
            row.prop(context.scene, "load_force", text="Load Force")
            row = box.row()
            row.operator("view3d.submit_focal_load", text="Submit Focal Load", icon='EXPORT')
            row.operator("view3d.submit_load", text="Submit Load", icon='EXPORT')
            row = box.row()
            row.operator("view3d.refresh_loads", text="Refresh loads list", icon='TRASH')
        elif context.scene.load_input_method == 'MANUAL':
            row = box.row()
            row.prop(context.scene, "load_name", text="Load name")
            row = box.row()
            box.label(text="Input the load forces in Newtons (N)")
            row = box.row()
            row.prop(context.scene, "load_x", text="Load in X")
            row.prop(context.scene, "load_y", text="Load in Y")
            row.prop(context.scene, "load_z", text="Load in Z")
            row = box.row()
            row.operator("view3d.select_fixation_point", text="Select Load Faces", icon='RESTRICT_SELECT_OFF')
            row.operator("view3d.submit_load", text="Submit Load", icon='EXPORT')
            row = box.row()
            row.operator("view3d.refresh_loads", text="Refresh loads list", icon='TRASH')
            


        # Visual elements section
        box = layout.box()
        box.label(text="Visual elements")

        # Checkbox: Show Constraint Points y Show Contact Points
        row = box.row()
        row.prop(context.scene, "show_constraint_points", text="Show Constraint Points")
        row.prop(context.scene, "show_contact_points", text="Show Contact Points")

        # Checkbox: Show Attachment Areas y Show Force Directions
        row = box.row()
        row.prop(context.scene, "show_attachment_areas", text="Show Attachment Areas")     
        row.prop(context.scene, "show_force_directions", text="Show Force Directions")

        # Apply button
        row = box.row()
        row.prop(context.scene, "arrows_size", text="Arrow Size")
        row.operator("view3d.visual_elements", text="Apply")
        
        # Export Files Section
        box = layout.box()
        box.label(text="Export and run", icon='EXPORT') 
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.prop(context.scene, "display_existing_results", text="Display Existing Results")
        col1.prop(context.scene, "open_results_when_finish", text="Open Results When Finish")
        col1.prop(context.scene, "run_as_admin", text="Run as Admin")

        col2.operator("view3d.export_meshes", text="Export files", icon='EXPORT')
        col2.operator("view3d.run_fossils", text="Run Fossils", icon='PLAY')
        col2.operator("view3d.open_fea_results_folder", text="Open FEA Results Folder", icon='FILE_FOLDER')


        # Export for Sensitivity Analysis Section
        # box = layout.box()
        # box.label(text="Export for Sensitivity Analysis")
        # row = box.row()
        # row.prop(context.scene, "sample_name", text="Sample name", icon='GREASEPENCIL')
        # split = box.split(factor=0.5)
        # col1 = split.column(align=True)
        # col2 = split.column(align=True)

        # col1.operator("view3d.start_selection", text="Start Selection", icon='RESTRICT_SELECT_OFF')
        # col2.operator("view3d.submit_sample", text="Submit Sample", icon='EXPORT')
        # row = box.row()
        # row.prop(context.scene, "scale_factor", text="Scale Factor")
        # row.prop(context.scene, "total_faces", text="Number of faces")
        # row = box.row()
        # row.operator("view3d.export_sensitivity_analysis", text="Export for Sensitivity Analysis")

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