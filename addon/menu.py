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

        # Scale Section
        box = layout.box()
        row = box.row(align=True)
        row.prop(context.scene, "show_scale_section", text="Scale", icon='DISCLOSURE_TRI_DOWN' if context.scene.show_scale_section else 'DISCLOSURE_TRI_RIGHT', emboss=False)
        
        if context.scene.show_scale_section:
            row = box.row(align=True)
            row.operator("view3d.calculate_area", text="Calculate Area", icon='DRIVER_DISTANCE')
            row.prop(context.scene, "calculated_area", text="Area", emboss=False)
            row = box.row(align=True)
            row.operator("view3d.scale_to_target_area", text="Scale to Target Area", icon='DRIVER_DISTANCE')
            row.prop(context.scene, "target_area", text="Target Area", emboss=False)

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

        # Muscle Properties Section

        selected_muscle = context.scene.selected_muscle
        if selected_muscle:
            # Force property - as float
            if "Force" in selected_muscle.keys():
                row = box.row(align=True)
                row.label(text="Force (N):")
                row.prop(selected_muscle, '["Force"]', text="")

            if "Focal point" in selected_muscle.keys():
                box.label(text="Focal point:")

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


        # Fixation Groups Section
    
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

                        op = row.operator("view3d.select_fixation_group", 
                                         text=vgroup.name, 
                                         icon='GROUP_VERTEX')
                        op.group_name = vgroup.name
                    
                    delete_op = row.operator("view3d.delete_fixation_group", text="", icon='X')
                    delete_op.group_name = vgroup.name
                    
                    if is_active and "fixation_attributes" in main_obj and vgroup.name in main_obj["fixation_attributes"]:
                        attrs = main_obj["fixation_attributes"][vgroup.name]

                        fixation_box = box_groups.box()
                        
                        row = fixation_box.row(align=True)
                        row.label(text="Select Axes:")
                        row.prop(context.scene, "fixation_x", text="X")
                        row.prop(context.scene, "fixation_y", text="Y")
                        row.prop(context.scene, "fixation_z", text="Z")

                        row = fixation_box.row(align=True)
                        row.operator("view3d.update_fixation_attributes", text="Update Fixation Axes", icon='CHECKMARK')
                        
            if not has_groups:
                box_groups.label(text="No fixation groups found")
        else:
            box_groups.label(text="No main object selected")

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
        
        # Existing Loads Section
        box_loads = box.box()
        box_loads.label(text="Stored Loads")
        
        main_obj = None
        if context.scene.selected_main_object:
            if isinstance(context.scene.selected_main_object, str):
                main_obj = bpy.data.objects.get(context.scene.selected_main_object)
            else:
                main_obj = context.scene.selected_main_object
        
        if main_obj and hasattr(main_obj, 'vertex_groups'):
            has_loads = False

            for vgroup in main_obj.vertex_groups:
                if vgroup.name.endswith("_load"):
                    has_loads = True
                    

                    row = box_loads.row(align=True)

                    is_active = (context.scene.current_load_group == vgroup.name)
                    if is_active:
                        op = row.operator("view3d.select_load_group", 
                                         text=vgroup.name, 
                                         icon='FORCE_MAGNETIC',
                                         depress=True) 
                    else:
                        op = row.operator("view3d.select_load_group", 
                                         text=vgroup.name, 
                                         icon='FORCE_MAGNETIC')
                    op.group_name = vgroup.name

                    delete_op = row.operator("view3d.delete_load_group", text="", icon='X')
                    delete_op.group_name = vgroup.name
                    

                    if is_active and "load_attributes" in main_obj and vgroup.name in main_obj["load_attributes"]:
                        attrs = main_obj["load_attributes"][vgroup.name]
                        

                        load_box = box_loads.box()
                        
                        row = load_box.row(align=True)
                        row.prop(context.scene, "edit_load_x", text="X")
                        row.prop(context.scene, "edit_load_y", text="Y") 
                        row.prop(context.scene, "edit_load_z", text="Z")
                        

                        row = load_box.row(align=True)
                        row.operator("view3d.update_load_attributes", text="Update Load Values", icon='CHECKMARK')
                        
            if not has_loads:
                box_loads.label(text="No loads created yet")
        else:
            box_loads.label(text="No main object selected")

            
        # Visual elements section
        box = layout.box()
        box.label(text="Visual elements")

        # Checkbox: Show Constraint Points and Show Contact Points
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
        
