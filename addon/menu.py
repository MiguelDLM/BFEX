#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator, Panel

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

        col1.operator("view3d.create_folder", text="Create Folder", icon='NEWFOLDER')
        col2.operator("view3d.submit_object", text="Submit main bone for FEA", icon='BONE_DATA')

        # Extract Surfaces Section
        box = layout.box()
        box.label(text="Extract muscle attachment areas and properties")

        row = box.row()
        row.prop(context.scene, "submesh_name", text="Muscle name", icon='GREASEPENCIL')
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.operator("view3d.start_selection", text="Start Selection", icon='RESTRICT_SELECT_OFF')
        col2.operator("view3d.submit_selection", text="Submit Selection", icon='EXPORT')


        box.label(text="Direction of the force")

        # Focal Point Coordinates
        row = box.row()
        row.prop(context.scene, "focal_point_coordinates", text="Focal Point Coordinates", emboss=False, icon='VIEW3D')
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.operator("view3d.select_focal_point", text="Select Focal Point", icon='RESTRICT_SELECT_OFF')
        col2.operator("view3d.submit_focal_point", text="Submit Focal Point", icon='EXPORT')

        #Muscle parameters section
        box.label(text="Muscle Parameters")
        row = box.row()
        row.prop(context.scene, "force_value", text="Force")

        # Dropdown list for loading scenario
        row = box.row()
        row.prop(context.scene, "selected_option", text="Loading scenario")

        # Submit Parameters and Delete last parameters submitted in two columns
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.operator("view3d.submit_parameters", text="Submit Parameters", icon='EXPORT')
        col2.operator("view3d.refresh_parameters", text="Refresh parameters list", icon='TRASH')
        
        # Contact Points Section
        box = layout.box()
        box.label(text="Fixation Points", icon='FORCE_FORCE')

        col = box.column(align=True)
            
        col.prop(context.scene, "fixation_point_coordinates", text="Fixation Point Coordinates", emboss=False, icon='VIEW3D')
        col = box.column(align=True)
        col.prop(context.scene, "fixation_type", text="Fixation Type")
        col = box.column(align=True)
        col.operator("view3d.select_fixation_point", text="Select fixation Point", icon='RESTRICT_SELECT_OFF')

        # Select Axes Section for Contact Points
        row = box.row(align=True)
        row.label(text="Select Axes:")
        row.prop(context.scene, "fixation_x", text="X")
        row.prop(context.scene, "fixation_y", text="Y")
        row.prop(context.scene, "fixation_z", text="Z")       

        row = box.row()
        row.operator("view3d.submit_fixation_point", text="Submit fixation Point", icon='EXPORT')
        row.operator("view3d.refresh_fixation_points", text="Refresh fixation points list", icon='TRASH')

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