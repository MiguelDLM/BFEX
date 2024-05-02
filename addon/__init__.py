bl_info = {
    "name": "FEITO",
    "blender": (2, 80, 0),
    "category": "Mesh",
    "author": "E. Miguel Diaz de Leon-Munoz",
    "description": "An Add-on for generating files for Fossil software (Finite Elements Analysis) files in Blender.",
    "version": (1, 0, 0),
    "location": "View3D > Tools",
    "warning": " Before using this add-on, ensure that your meshes are free from errors such as Non-Manifold edges, intersecting faces, etc. We recommend using the 3D-Print add-on for optimal results.",
    "tracker_url": "https://github.com/MiguelDLM",
    "support": "COMMUNITY",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy.props import StringProperty, EnumProperty, FloatProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
import os
import math
import json
import re
import subprocess
import ctypes
import mathutils
import random
from mathutils import Vector, kdtree

# Utilities 
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)
    
def get_transformed_coordinates(obj, coordinates):

    matrix_world = obj.matrix_world
    original_vector = mathutils.Vector(coordinates)
    transformed_vector = matrix_world @ original_vector
    return transformed_vector.x, transformed_vector.y, transformed_vector.z
    
def find_and_format_nearest_point(original_point, tree):
    vector_point = Vector(map(float, original_point.split(',')))
    nearest_point = find_nearest(tree, vector_point)[0]
    formatted_point = ', '.join([f"{coord:.6f}" for coord in nearest_point])
    return formatted_point
    
def process_point(operator, context, point_type):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    active_object = bpy.context.active_object
    vertices = [v.co for v in context.active_object.data.vertices if v.select]

    if vertices:
        # Count the vertex groups that match the prefix
        matching_vertex_groups = sorted(filter(lambda vg: vg.name.startswith(f"{point_type}_point"), context.active_object.vertex_groups), key=lambda vg: vg.name)
        
        # If the point type is 'constraint' and there are already two vertex groups, cancel the operation
        if point_type == 'constraint' and len(matching_vertex_groups) >= 2:
            operator.report({'ERROR'}, "Only two constraint points are allowed. Delete one of the existing constraint points before adding a new one.")
            return

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        selected_verts = [v.co for v in context.active_object.data.vertices if v.select]
        
        # Rename the existing vertex groups in sequential order
        for i, vertex_group in enumerate(matching_vertex_groups, start=1):
            vertex_group.name = f"{point_type}_point{i}"
        
        point_number = len(matching_vertex_groups) + 1

        vertex_group_name = f"{point_type}_point{point_number}"
        vertex_group = context.active_object.vertex_groups.get(vertex_group_name)

        bpy.ops.object.vertex_group_add()
        vertex_group = context.active_object.vertex_groups[-1]
        vertex_group.name = vertex_group_name
        bpy.ops.object.vertex_group_assign()
        
        set_object_mode(context.active_object, 'OBJECT')
    else:
        operator.report({'ERROR'}, f"No vertex selected as {point_type.capitalize()} Point {point_number}")
# Interface Panel
class VIEW3D_PT_FilePathPanel_PT(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_FilePathPanel_PT"
    bl_label = "FEITO"
    bl_category = "FEITO"
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
        col2.operator("view3d.delete_last_muscle_attachment", text="Delete last parameters submitted", icon='TRASH')
        
        # Contact Points Section
        box = layout.box()
        box.label(text="Contact Points", icon='FORCE_FORCE')

        col = box.column(align=True)
            
        col.prop(context.scene, "contact_point_coordinates", text="Contact Point Coordinates", emboss=False, icon='VIEW3D')
        col.operator("view3d.select_contact_point", text="Select Contact Point", icon='RESTRICT_SELECT_OFF')

        # Select Axes Section for Contact Points
        row = box.row(align=True)
        row.label(text="Select Axes:")
        row.prop(context.scene, "contact_x", text="X")
        row.prop(context.scene, "contact_y", text="Y")
        row.prop(context.scene, "contact_z", text="Z")       
        # Submit Contact Points

        row = box.row()
        row.operator("view3d.submit_contact_point", text="Submit Contact Point", icon='EXPORT')


        # Constraint Points Section
        box = layout.box()
        box.label(text="Constraint Points", icon='CONSTRAINT_BONE')

        # Column for Constraint Point 1
        col = box.column(align=True)
        col.prop(context.scene, "constraint_point_coordinates", text="Constraint Point Coordinates", emboss=False, icon='VIEW3D')
        col.operator("view3d.select_constraint_point", text="Select Constraint Point", icon='RESTRICT_SELECT_OFF')

        # Select Axes Section for Constraint Point 
        row = box.row(align=True)
        row.label(text="Select Axes (CP1):")
        row.prop(context.scene, "constraint1_x", text="X")
        row.prop(context.scene, "constraint1_y", text="Y")
        row.prop(context.scene, "constraint1_z", text="Z")

        # Select Axes Section for Constraint Point 2
        row = box.row(align=True)
        row.label(text="Select Axes (CP2):")
        row.prop(context.scene, "constraint2_x", text="X")
        row.prop(context.scene, "constraint2_y", text="Y")
        row.prop(context.scene, "constraint2_z", text="Z")

        # Constraint Point 
        col = box.column(align=True)
        col.operator("view3d.submit_constraint_point", text="Submit Constraint Point", icon='EXPORT')

        # Material Properties Section
        box = layout.box()
        box.label(text="Material Properties")
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        # Text boxes to enter values
        col1.prop(context.scene, "youngs_modulus", text="Young's Modulus")
        col2.prop(context.scene, "poissons_ratio", text="Poisson's Ratio")


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
        row.operator("view3d.apply_forces_parameters", text="Apply")
        
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
        box = layout.box()
        box.label(text="Export for Sensitivity Analysis")
        row = box.row()
        row.prop(context.scene, "sample_name", text="Sample name", icon='GREASEPENCIL')
        split = box.split(factor=0.5)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        col1.operator("view3d.start_selection", text="Start Selection", icon='RESTRICT_SELECT_OFF')
        col2.operator("view3d.submit_sample", text="Submit Sample", icon='EXPORT')
        row = box.row()
        row.prop(context.scene, "scale_factor", text="Scale Factor")
        row.prop(context.scene, "total_faces", text="Number of faces")
        row = box.row()
        row.operator("view3d.export_sensitivity_analysis", text="Export for Sensitivity Analysis")
   
class VIEW3D_OT_BrowseFolderOperator(Operator, ImportHelper):
    bl_idname = "view3d.browse_folder"
    bl_label = "Browse Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select the folder where files will be stored. If there is any text in the 'Browse Folder' window, delete the text."

    def execute(self, context):
        context.scene.selected_folder = self.filepath
        return {'FINISHED'}

class VIEW3D_OT_CreateFolderOperator(Operator):
    bl_idname = "view3d.create_folder"
    bl_label = "Create Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create a folder and collection using the chosen name."
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_folder and context.scene.new_folder_name)

    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name

        if file_path and new_folder_name:
            try:
                # Create new folder
                folder_path = os.path.join(file_path, new_folder_name)
                os.makedirs(folder_path, exist_ok=True)
                self.report({'INFO'}, f"Folder created at: {folder_path}")

                # Create new collection
                collection = bpy.data.collections.new(new_folder_name)
                bpy.context.scene.collection.children.link(collection)

            except Exception as e:
                self.report({'ERROR'}, f"Failed to create folder: {e}")
        else:
            self.report({'ERROR'}, "Please provide a valid file path and folder name")

        return {'FINISHED'}
        
class VIEW3D_OT_SubmitMainObjectOperator(Operator):
    bl_idname = "view3d.submit_object"
    bl_label = "Submit Object"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select one object before clicking here. This button stores the name of the current active object as the main bone/mesh to be used in the FEA."

    def execute(self, context):
        active_object = bpy.context.active_object
        main_object = bpy.context.active_object

        if active_object:
            context.scene.selected_main_object = active_object.name
            self.report({'INFO'}, f"Main object set to: {context.scene.selected_main_object}")
            context.scene.total_faces = len(main_object.data.polygons)

        else:
            self.report({'ERROR'}, "No active object.")

        return {'FINISHED'}
                
class VIEW3D_OT_StartSelectionOperator(Operator):
    bl_idname = "view3d.start_selection"
    bl_label = "Start Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and activates the Lasso Select tool. Ensure that the active object is the one you want to use for creating the sub-mesh. Be cautious, as this operation subtracts the sub-mesh from the active object."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)

    def execute(self, context):
        active_object = bpy.data.objects.get(context.scene.selected_main_object)
        context.view_layer.objects.active = active_object
    
        # Ensure the active object is in 'OBJECT' mode before deselecting all
        if active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      
        bpy.context.tool_settings.mesh_select_mode[2] = True        
        bpy.context.tool_settings.mesh_select_mode[0] = False 
        bpy.context.tool_settings.mesh_select_mode[1] = False        
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso", space_type='VIEW_3D')
    
        return {'FINISHED'}

class VIEW3D_OT_SubmitSelectionOperator(Operator):
    bl_idname = "view3d.submit_selection"
    bl_label = "Submit Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a sub-mesh from the selected surface and stores it in the specified collection."
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name and context.scene.new_folder_name)
    
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

        # Check if vertex group already exists
        vgroup = bpy.context.active_object.vertex_groups.get(submesh_name)
        if vgroup is not None:
            # If it exists, remove it
            bpy.context.active_object.vertex_groups.remove(vgroup)

        # Create vertex group
        vgroup = bpy.context.active_object.vertex_groups.new(name=submesh_name)
        selected_vertices = [v.index for v in bpy.context.active_object.data.vertices if v.select]
        vgroup.add(selected_vertices, 1.0, 'REPLACE')

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
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.delete(type='FACE')
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create new mesh: {str(e)}")
                return {'CANCELLED'}

            # Rename mesh
            bpy.context.active_object.name = submesh_name


            # Delete duplicated mesh
            original_collection = bpy.context.active_object.users_collection[0]
            
            # Move new mesh to the collection
            collection.objects.link(bpy.context.active_object)

            original_collection.objects.unlink(bpy.context.active_object)

            self.report({'INFO'}, f"Submesh '{submesh_name}' created and added to collection '{collection_name}'")

        else:
            self.report({'ERROR'}, f"Collection '{collection_name}' not found. Please create it first.")
            return {'CANCELLED'}

        return {'FINISHED'}

class VIEW3D_OT_SelectVertexOperator(Operator):
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)

    def execute(self, context):
        object_name = context.scene.selected_main_object
        obj = bpy.data.objects.get(object_name)

        # Check if the object exists
        if not obj:
            self.report({'ERROR'}, f"Object '{object_name}' not found.")
            return {'CANCELLED'}

        # Check if the object is a mesh
        if obj.type != 'MESH':
            self.report({'ERROR'}, f"Object '{object_name}' is not a mesh.")
            return {'CANCELLED'}

        # Make the object the active object
        context.view_layer.objects.active = obj

        # Ensure the active object is in 'OBJECT' mode before switching to 'EDIT' mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True 
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False
        return {'FINISHED'}

class VIEW3D_OT_SelectFocalPointOperator(Operator):
    bl_idname = "view3d.select_focal_point"
    bl_label = "Select Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, allowing you to select a point to be used as the force direction for the previously created muscle attachment area."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name and context.scene.selected_main_object)

    def execute(self, context):
        object_name = context.scene.selected_main_object
        obj = bpy.data.objects.get(object_name)

        # Check if the object exists
        if not obj:
            self.report({'ERROR'}, f"Object '{object_name}' not found.")
            return {'CANCELLED'}

        # Check if the object is a mesh
        if obj.type != 'MESH':
            self.report({'ERROR'}, f"Object '{object_name}' is not a mesh.")
            return {'CANCELLED'}

        # Make the object the active object
        context.view_layer.objects.active = obj

        # Ensure the active object is in 'OBJECT' mode before switching to 'EDIT' mode
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True 
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False
        return {'FINISHED'}
    
class VIEW3D_OT_SubmitFocalPointOperator(Operator):
    bl_idname = "view3d.submit_focal_point"
    bl_label = "Submit Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable."
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name)

    def execute(self, context):
        active_object = context.active_object

        # Check if the active object exists
        if not active_object:
            self.report({'ERROR'}, "No active object.")
            return {'CANCELLED'}

        # Check if the active object is a mesh
        if active_object.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh.")
            return {'CANCELLED'}

        if active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        # Check if at least one vertex is selected
        if len(selected_vertices) == 0:
            self.report({'ERROR'}, "Please select at least one vertex as the Focal Point.")
            return {'CANCELLED'}

        # Calculate the average coordinates of the selected vertices
        avg_coordinates = sum(selected_vertices, Vector()) / len(selected_vertices)
        x, y, z = get_transformed_coordinates(active_object, avg_coordinates)

        context.scene.focal_point_coordinates = f"{x:.3f},{y:.3f},{z:.3f}"
        self.report({'INFO'}, f"Focal Point coordinates: {context.scene.focal_point_coordinates}")

        return {'FINISHED'}

class VIEW3D_OT_SubmitParametersOperator(Operator):
    bl_idname = "view3d.submit_parameters"
    bl_label = "Submit Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the parameters (Name of the last sub-mesh created, Focal Point, Force, and loading scenario) in a dictionary."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.submesh_name)

    def execute(self, context):
        
        last_submesh_name = context.scene.submesh_name
        file_name = f"{last_submesh_name}.stl" 
        force_value = context.scene.force_value
        selected_option = context.scene.selected_option
        focal_point_coordinates = [float(coord) for coord in context.scene.focal_point_coordinates.split(",")]

        # Convert coords to JSON
        focal_point_coordinates_str = json.dumps(focal_point_coordinates, indent=None)
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

        # Store values into a dictionary
        data = {
            'file': f"f'{{path}}/" + f"{file_name}'",  
            'force': force_value,
            'focalpt': focal_point_coordinates,  
            'method': selected_option
        }
        muscle_parameters.append(data)  
        json_str = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)
        context.scene["muscle_parameters"] = json_str
        self.report({'INFO'}, "Stored data:\n" + json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False))
        return {'FINISHED'}

class VIEW3D_OT_DeleteLastMuscleAttachmentOperator(Operator):
    bl_idname = "view3d.delete_last_muscle_attachment"
    bl_label = "Delete Last Muscle Attachment"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Deletes the last parameters stored in a dictionary. Be aware, if you click it before submitting the parameters, the last input parameters will be deleted. WARNING: Use with caution!"

    def execute(self, context):
        
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

       
        if muscle_parameters:
            last_entry = muscle_parameters[-1]          
            muscle_parameters.pop()

            json_str = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)
            context.scene["muscle_parameters"] = json_str

            self.report({'INFO'}, f"Deleted last muscle attachment parameters. Updated muscle parameters:\n{json_str}")

            context.scene.submesh_name = "" 

        else:
            self.report({'WARNING'}, "No muscle attachments to delete.")

        return {'FINISHED'}

class VIEW3D_OT_SelectContactPointOperator(VIEW3D_OT_SelectVertexOperator):
    
    bl_idname = "view3d.select_contact_point"
    bl_label = "Select Contact Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, enabling you to select a point to be used as a contact point where the force will be applied during the FEA."
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)
        
class VIEW3D_OT_SubmitContactPointOperator(Operator):
    bl_idname = "view3d.submit_contact_point"
    bl_label = "Submit Contact Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point as Contact Point."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)

    def execute(self, context):
        process_point(self,context, 'contact')
        return {'FINISHED'}

class VIEW3D_OT_SelectConstraintPointOperator(VIEW3D_OT_SelectVertexOperator):
    bl_idname = "view3d.select_constraint_point"
    bl_label = "Select Constraint Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, enabling you to select a point to be used as a constraint point where the object will be fixed during the FEA."

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)       

class VIEW3D_OT_SubmitConstraintPointOperator(Operator):
    bl_idname = "view3d.submit_constraint_point"
    bl_label = "Submit Constraint Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable to be used as constraint point"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.selected_main_object)
        
    def execute(self, context):
        process_point(self, context, 'constraint')
        return {'FINISHED'}
        
class VIEW3D_OT_ExportMeshesOperator(bpy.types.Operator):
    bl_idname = "view3d.export_meshes"
    bl_label = "Export Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Export all the files required for the FEA in Fossils. This includes the main mesh/bone, sub-meshes of the main object/bone (Attachment muscle areas), and a Python file with the parameters inputted by the user."
    
    @classmethod
    def poll(cls, context):
        # Verifica si los requisitos están cumplidos
        main_object_name = context.scene.selected_main_object
        main_object = bpy.data.objects.get(main_object_name)

        return (
            context.scene.selected_folder and
            context.scene.new_folder_name and
            main_object and
            any(vg.name.startswith("contact_point") for vg in main_object.vertex_groups) and
            any(vg.name.startswith("constraint_point") for vg in main_object.vertex_groups)
        )
    
    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)

        if file_path:
            try:
                
                collection_name = context.scene.new_folder_name
                collection = bpy.data.collections.get(collection_name)
                selected_main_object = context.scene.selected_main_object                
                muscle_parameters = str(context.scene.get("muscle_parameters", {})).replace('"', "'")
                muscle_parameters = re.sub("''", "'", muscle_parameters)
                muscle_parameters = re.sub("'f'", "f'", muscle_parameters)
                youngs_modulus = context.scene.youngs_modulus
                poissons_ratio = round(context.scene.poissons_ratio, 3)
                                      
                contact_x = context.scene.contact_x
                contact_y = context.scene.contact_y
                contact_z = context.scene.contact_z

                selected_axes = [f"'{axis}'" for axis, selected in [('x', contact_x), ('y', contact_y), ('z', contact_z)] if selected]
                contact_axes = ','.join(selected_axes)

                constraint1_x = context.scene.constraint1_x
                constraint1_y = context.scene.constraint1_y
                constraint1_z = context.scene.constraint1_z

                selected_axes_cp1 = [f"'{axis}'" for axis, selected in [('x', constraint1_x), ('y', constraint1_y), ('z', constraint1_z)] if selected]
                constraint_axes_cp1 = ','.join(selected_axes_cp1)

                constraint2_x = context.scene.constraint2_x
                constraint2_y = context.scene.constraint2_y
                constraint2_z = context.scene.constraint2_z

                selected_axes_cp2 = [f"'{axis}'" for axis, selected in [('x', constraint2_x), ('y', constraint2_y), ('z', constraint2_z)] if selected]
                constraint_axes_cp2 = ','.join(selected_axes_cp2)
    
                
                # get the global coordinates of the contact points stored in the vertex groups of the main object
                contact_pts = []
                constraint_pts = []
                constraint_pts_list = []
                selected_main_object = bpy.data.objects.get(context.scene.selected_main_object)


                for group in selected_main_object.vertex_groups:
                    group_name = group.name
                    if group_name.startswith(("constraint_point")):
                        # Count the number of constraint points
                        constraint_pts_list.append(group_name)
                num_constraint_pts = len(constraint_pts_list)
                
                if num_constraint_pts == 1: 
                    constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}]"
                elif num_constraint_pts == 2:
                    constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}],\n\t\t'axis_pt2': [{constraint_axes_cp2}]"

                # Add debug info
                self.report({'ERROR'}, f"Number of constraint points: {num_constraint_pts}")  
                for group in selected_main_object.vertex_groups:
                    group_name = group.name
                    if group_name.startswith(("contact_point", "constraint_point")):
                        # Get the vertex indices of the group
                        group_index = group.index
                        vertices_indices = [v.index for v in selected_main_object.data.vertices if group_index in [g.group for g in v.groups]]
                        # Get the vertex coordinates of the group in local coordinates
                        vertex_coordinates_local = [selected_main_object.data.vertices[i].co for i in vertices_indices]
                        # Convert local coordinates to global coordinates
                        matrix_world = selected_main_object.matrix_world
                        vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                        vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                        # Store the coordinates in the dictionary
                        if group_name.startswith("contact_point"):
                            contact_pts.append(vertex_coordinates_serializable)
                        elif group_name.startswith("constraint_point"):
                            constraint_pts.append(vertex_coordinates_serializable)

                contact_pts = ', '.join(json.dumps(sublist) for sublist in contact_pts)


                # Remove one left bracket and one right bracket successively
                contact_pts = re.sub(r'\[\[', '[', contact_pts)
                contact_pts = re.sub(r'\]\]', ']', contact_pts)

                constraint_pts = '\n    '.join(f"p['axis_pt{i+1}'] = {json.dumps(sublist)[1:-1]}" for i, sublist in enumerate(constraint_pts))
   
                if collection:
                    
                   
                    selected_main_object = context.scene.selected_main_object
                    main_object = bpy.data.objects.get(selected_main_object)

                    if main_object:
                        bpy.context.view_layer.objects.active = main_object
                        bpy.ops.object.select_all(action='DESELECT')
                        main_object.select_set(True)
                 
                        file_name_main = f"{main_object.name}.stl"
                        file_path_stl_main = os.path.join(file_path, collection_name, file_name_main)
                        bpy.ops.export_mesh.stl(filepath=file_path_stl_main, use_selection=True, ascii=False)

                        bpy.context.view_layer.objects.active = None

                    else:
                        self.report({'ERROR'}, f"Main object '{selected_main_object}' not found")
                       
                    for obj in collection.objects:                          
                        if obj.type == 'MESH':
                        
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)

                            file_name = f"{obj.name}.stl"
                            file_path_stl = os.path.join(file_path, collection_name, file_name)
                            bpy.ops.export_mesh.stl(filepath=file_path_stl, use_selection=True, ascii=False)
                            bpy.context.view_layer.objects.active = None
                            
                    # Create python script
                    script_content = f"""\
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{collection_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{collection_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['contact_pts'] = [{contact_pts}]
    {constraint_pts}
    p['muscles'] = {muscle_parameters}
    p['fixations'] = {{
        'contact_pts': [{contact_axes}],
        {constraint_axes}
        
    }}

    
    # material properties
    p['density'] = 1.662e-9  # [T/mm³]
    p['Young'] = {youngs_modulus}     # [MPa]
    p['Poisson'] = {poissons_ratio}      # [-]

    # p['use_gmshOld'] = True

    p.update(d)
    return p


def getMetafor(p={{}}):
    import bonemodel as model
    return model.getMetafor(parms(p))


if __name__ == "__main__":
    import models.bonemodel2 as model
    model.solve(parms())

# Areas of interest

"""

                    script_file_path = os.path.join(file_path, "script.py")
                    with open(script_file_path, "w") as script_file:
                        script_file.write(script_content)
                        
                        
                        self.report({'INFO'}, f"Meshes and script exported to: {file_path}")
                else:
                    self.report({'ERROR'}, f"Collection '{collection_name}' not found")

            except Exception as e:
                self.report({'ERROR'}, f"Failed to export meshes and script: {e}")

        else:
            self.report({'ERROR'}, "Please provide a valid file path")

        return {'FINISHED'}

class VIEW3D_OT_RunFossilsOperator(bpy.types.Operator):
    bl_idname = "view3d.run_fossils"
    bl_label = "Run Fossils"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Run Fossils with the script.py file stored in the selected folder in Browse folder option. If fossils open and crash, check the correct location and names of the files. script.py is te default name"

    def execute(self, context):

        python_file_path = bpy.path.abspath(context.scene.selected_folder)
        python_file_path = os.path.join(python_file_path, "script.py")
        user_folder = os.path.expanduser("~")
        external_program_path = os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "fossils.exe")
        args = [python_file_path]

        if context.scene.display_existing_results:
            args.append("--post")

        if not context.scene.open_results_when_finish:
            args.append("--nogui")

        try:
            
            if context.scene.run_as_admin:
                
                args = ' '.join(args)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", external_program_path, args, python_file_path, 1)
            else:

                subprocess.Popen([external_program_path] + args, creationflags=subprocess.CREATE_NEW_CONSOLE)

                
            self.report({'INFO'}, f"External program '{external_program_path}' started successfully with Python file: '{python_file_path}'")
        except Exception as e:
            self.report({'ERROR'}, f"Error starting external program: {e} be sure that fossils is instaled in ..\AppData\Local\Programs\Fossils\fossils.exe and the selected folder cointain the script.py file and folder with sub-meshes")

        return {'FINISHED'}

class VIEW3D_OT_OpenFEAResultsFolderOperator(bpy.types.Operator):
    bl_idname = "view3d.open_fea_results_folder"
    bl_label = "Open FEA Results Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open the folder containing FEA results"

    def execute(self, context):
        # Carpeta del usuario
        user_folder = os.path.expanduser("~")
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name.lower()

        fea_results_folders = [
            os.path.join(file_path, "workspace",new_folder_name+"_script"),
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "_internal", "workspace"),
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "workspace")
        ]

        found_folder = None
        for fea_results_folder in fea_results_folders:
            if os.path.exists(fea_results_folder):
                found_folder = fea_results_folder
                break

        if found_folder:
            bpy.ops.wm.path_open(filepath=found_folder)
            self.report({'INFO'}, f"FEA results folder opened: {found_folder}")
        else:
            self.report({'ERROR'}, f"FEA results folder not found. Verify Fossils is installed in {user_folder}\Appdata\Local\Programs or you have run a FEA before")

        return {'FINISHED'}

def generate_random_color():
    return (random.random(), random.random(), random.random(), 1.0)


class VIEW3D_OT_ApplyForcesParametersOperator(bpy.types.Operator):
    bl_idname = "view3d.apply_forces_parameters"
    bl_label = "Apply Forces and Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add some visual elements with the information generated before exporting the files"
        
    def execute(self, context):
    
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        collection_name = "Visual elements"

        visual_elements_collection = bpy.data.collections.get(collection_name)
        if visual_elements_collection:
        
            for obj in visual_elements_collection.objects:
                bpy.data.objects.remove(obj)           
            bpy.data.collections.remove(visual_elements_collection)

        visual_elements_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(visual_elements_collection)

        red_material = bpy.data.materials.new(name="RedMaterial")
        red_material.diffuse_color = (1, 0, 0, 1)  # RGB and alpha

        yellow_material = bpy.data.materials.new(name="YellowMaterial")
        yellow_material.diffuse_color = (1, 1, 0, 1) 

        blue_material = bpy.data.materials.new(name="BlueMaterial")
        blue_material.diffuse_color = (0, 0, 1, 1) 
        
        if context.scene.show_attachment_areas:
            # Obtener la colección especificada
            attachment_collection = bpy.data.collections.get(context.scene.new_folder_name)

            if attachment_collection:
                for obj in attachment_collection.objects:

                    if obj.type == 'MESH':
                        random_color = generate_random_color()
                        
                        new_material = bpy.data.materials.new(name="AttachmentMaterial")
                        new_material.diffuse_color = random_color
                        
                        if len(obj.data.materials) > 0:
                            obj.data.materials[0] = new_material
                        else:
                            obj.data.materials.append(new_material)

        if not visual_elements_collection:
            visual_elements_collection = bpy.data.collections.new("Visual elements")
            bpy.context.scene.collection.children.link(visual_elements_collection)

        if context.scene.show_force_directions:

            muscle_parameters = context.scene.get("muscle_parameters", [])
            muscle_parameters = json.loads(muscle_parameters)

            for entry in muscle_parameters:
                focal_point_coords = entry.get('focalpt', [])
                
                if isinstance(focal_point_coords, list):
                    coords = focal_point_coords
                else:
                    coords = [focal_point_coords.get('x', 0.0), focal_point_coords.get('y', 0.0), focal_point_coords.get('z', 0.0)]

                focal_point_name = entry.get('file', '')
                focal_point_name_clean = focal_point_name.replace(f"f'{{path}}/", "").replace(".stl'", "")
                self.create_combined_object_at_location(coords, visual_elements_collection, f"ForceDirection_{focal_point_name_clean}",material=blue_material)
        
        selected_main_object = context.scene.selected_main_object  
        main_object = bpy.data.objects.get(selected_main_object)
        #check all the vertex groups of the main object to find the contact points and get their coordinates
        contact_pts_list = []
        for group in main_object.vertex_groups:
            group_name = group.name
            if group_name.startswith("contact_point"):
                # Count the number of contact points
                contact_pts_list.append(group_name)
                #Get the coordinates of the contact points
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                contact_pts_list.append(vertex_coordinates_serializable)

        # Create a combined object for each contact point
        if context.scene.show_contact_points:
            for i in range(0, len(contact_pts_list), 2):
                contact_point_name = contact_pts_list[i]
                contact_point_coords = contact_pts_list[i + 1]
                contact_point_coords = contact_point_coords[0]      
                self.create_combined_object_at_location(contact_point_coords, visual_elements_collection, f"{contact_point_name}",orientation='RIGHT', material=red_material)
        #Create a combined object for each constraint point
        constraint_pts_list = []
        for group in main_object.vertex_groups:
            group_name = group.name
            if group_name.startswith("constraint_point"):
                # Count the number of constraint points
                constraint_pts_list.append(group_name)
                #Get the coordinates of the constraint points
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                constraint_pts_list.append(vertex_coordinates_serializable)
        if context.scene.show_constraint_points:
            for i in range(0, len(constraint_pts_list), 2):
                constraint_point_name = constraint_pts_list[i]
                constraint_point_coords = constraint_pts_list[i + 1]
                constraint_point_coords = constraint_point_coords[0]      
                self.create_combined_object_at_location(constraint_point_coords, visual_elements_collection, f"{constraint_point_name}", orientation='UP', material=yellow_material)
        
        return {'FINISHED'}

    def create_combined_object_at_location(self, location_coords, collection, object_name, orientation='DOWN', material=None ):
        if location_coords:
            
            bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=1, depth=1, location=location_coords, rotation=(0, 0, math.radians(90)))
            cone = bpy.context.object
            cone.name = object_name

            bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(location_coords[0], location_coords[1], location_coords[2] - 1), rotation=(0, 0, 0))
            cylinder = bpy.context.object
            cylinder.name = object_name + "_Cylinder"

            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.select_all(action='DESELECT')
            cone.select_set(True)
            cylinder.select_set(True)
            bpy.context.view_layer.objects.active = cone
            bpy.ops.object.join()

            if orientation == 'DOWN':
                cone.rotation_euler = (math.radians(90), 0, 0)
            elif orientation == 'UP':
                cone.rotation_euler = (math.radians(-90), 0, 0)
            elif orientation == 'RIGHT':
                cone.rotation_euler = (0, math.radians(180), 0)
            elif orientation == 'LEFT':
                cone.rotation_euler = (0, math.radians(0), 0)

            collection.objects.link(cone)

            for old_collection in cone.users_collection:
                if old_collection.name != "Visual elements":
                    old_collection.objects.unlink(cone)
                    
            if material:
                cone.data.materials.append(material)
                

class VIEW3D_OT_SubmitSampleOperator(bpy.types.Operator):
    bl_idname = "view3d.submit_sample"
    bl_label = "Submit Sample"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a vertex group for the sensitivity analysis"
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene.sample_name and context.scene.new_folder_name)
        
    def execute(self, context):
        sample_name = context.scene.sample_name

        # Set object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Check if vertex group already exists
        vgroup_name = f"{sample_name}_sample"
        vgroup = bpy.context.active_object.vertex_groups.get(vgroup_name)
        if vgroup is not None:
            # If it exists, remove all vertices from the group
            bpy.ops.object.vertex_group_set_active(group=vgroup_name)
            bpy.ops.object.vertex_group_remove(all=False)

        # Create vertex group
        vgroup = bpy.context.active_object.vertex_groups.new(name=vgroup_name)
        selected_vertices = [v.index for v in bpy.context.active_object.data.vertices if v.select]
        vgroup.add(selected_vertices, 1.0, 'REPLACE')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.active_object
        bpy.context.active_object.select_set(True)

        return {'FINISHED'}

#Logic of fossil parameters chechboxes        
def update_checkboxes(self, context):
    if context.scene.display_existing_results:
        context.scene.open_results_when_finish = False

    if context.scene.open_results_when_finish:
        context.scene.display_existing_results = False
        
def find_nearest(tree, point):
    return tree.find(point)

class VIEW3D_OT_ExportSensitivityAnalysisOperator(Operator):
    bl_idname = "view3d.export_sensitivity_analysis"
    bl_label = "Export for Sensitivity Analysis"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        #Import variables
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name
        collection_to_copy = bpy.data.collections.get(new_folder_name)
        selected_main_object = context.scene.selected_main_object
        main_object = bpy.data.objects.get(selected_main_object)
        file_name_main = f"{main_object.name}.stl"
        sensitivity_collection_name = "Sensitivity Analysis"
        sensitivity_collection = bpy.data.collections.get(sensitivity_collection_name)
        muscle_parameters = str(context.scene.get("muscle_parameters", {})).replace('"', "'")
        muscle_parameters = re.sub("''", "'", muscle_parameters)
        muscle_parameters = re.sub("'f'", "f'", muscle_parameters)
        youngs_modulus = context.scene.youngs_modulus
        poissons_ratio = round(context.scene.poissons_ratio, 3) 
        scale_factor = context.scene.scale_factor
        
                
        contact_x = context.scene.contact_x
        contact_y = context.scene.contact_y
        contact_z = context.scene.contact_z

        selected_axes = [f"'{axis}'" for axis, selected in [('x', contact_x), ('y', contact_y), ('z', contact_z)] if selected]
        contact_axes = ','.join(selected_axes)

        constraint1_x = context.scene.constraint1_x
        constraint1_y = context.scene.constraint1_y
        constraint1_z = context.scene.constraint1_z

        selected_axes_cp1 = [f"'{axis}'" for axis, selected in [('x', constraint1_x), ('y', constraint1_y), ('z', constraint1_z)] if selected]
        constraint_axes_cp1 = ','.join(selected_axes_cp1)

        constraint2_x = context.scene.constraint2_x
        constraint2_y = context.scene.constraint2_y
        constraint2_z = context.scene.constraint2_z

        selected_axes_cp2 = [f"'{axis}'" for axis, selected in [('x', constraint2_x), ('y', constraint2_y), ('z', constraint2_z)] if selected]
        constraint_axes_cp2 = ','.join(selected_axes_cp2) 
        
        # Verificar si la colección ya existe
        if sensitivity_collection is None:
            # Si no existe, crearla
            sensitivity_collection = bpy.data.collections.new(sensitivity_collection_name)
            bpy.context.scene.collection.children.link(sensitivity_collection)
        else:
            # Si ya existe, vaciar la colección eliminando todos los objetos
            for obj in sensitivity_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        if main_object is None:
            self.report({'ERROR'}, "Main object not found. Please submit a main object first.")
            return {'CANCELLED'}

        # Crear una copia independiente del objeto principal
        copy_main_object = main_object.copy()
        copy_main_object.data = main_object.data.copy()
        copy_main_object.animation_data_clear()

        # Mover la copia a la nueva colección
        sensitivity_collection.objects.link(copy_main_object)

        if scale_factor == 1:
            # No hacer ninguna operación, ya que el factor de escala es 1
            pass
        else:

            # Establecer copy_main_object como el objeto activo
            bpy.context.view_layer.objects.active = copy_main_object

            if scale_factor < 1:
                # Si el factor de escala es menor a 1, aplicar directamente el decimate
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = scale_factor
            else:
                # Acceder a los datos de malla
                mesh = copy_main_object.data

                # Calcular el número de cortes para subdivide edges
                if scale_factor <= 4:
                    num_cuts = 1
                elif scale_factor <= 9:
                    num_cuts = 2
                elif scale_factor <= 16:
                    num_cuts = 3

                # Aplicar subdivide edges directamente en los datos de malla
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.subdivide(number_cuts=num_cuts, smoothness=0)
                bpy.ops.object.mode_set(mode='OBJECT')

                # Calcular el factor de decimación
                decimate_factor = scale_factor / ((num_cuts + 1) ** 2)

                # Aplicar el operador decimate con el factor calculado
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = decimate_factor

            # Aplicar el modificador decimate
            bpy.ops.object.modifier_apply(modifier="Decimate")


 
        if collection_to_copy is None:
            self.report({'ERROR'}, "Source collection not found. Please create it first.")
            return {'CANCELLED'}


        # Crear un árbol kD de vértices para el objeto decimado
        vertices = [v.co for v in copy_main_object.data.vertices]
        tree = kdtree.KDTree(len(vertices))
        for i, vertex in enumerate(vertices):
            tree.insert(copy_main_object.matrix_world @ vertex, i)
        tree.balance()

        constraint_pts_list = []  # Initialize the constraint_pts_list variable

        for group in main_object.vertex_groups:
            group_name = group.name
            if group_name.startswith(("constraint_point")):
                # Count the number of constraint points
                constraint_pts_list.append(group_name)
        
        num_constraint_pts = len(constraint_pts_list)
        
        if num_constraint_pts == 1: 
            constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}]"
        elif num_constraint_pts == 2:
            constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}],\n\t\t'axis_pt2': [{constraint_axes_cp2}]"
        #get the contact and constraint points in the main object stored in the vertex groups
        contact_points = []
        constraint_points = []
        for group in main_object.vertex_groups:
            group_name = group.name
            if group_name.startswith("contact_point"):
                #Get the coordinates of the contact points
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                contact_points.append(vertex_coordinates_serializable)
            elif group_name.startswith("constraint_point"):
                #Get the coordinates of the constraint points
                group_index = group.index
                vertices_indices = [v.index for v in main_object.data.vertices if group_index in [g.group for g in v.groups]]
                vertex_coordinates_local = [main_object.data.vertices[i].co for i in vertices_indices]
                matrix_world = main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                constraint_points.append(vertex_coordinates_serializable)
        
        #find the nearest point in the decimated object to the contact and constraint points
        for contact_point in contact_points:
            nearest_contact_point = find_nearest(tree, contact_point[0])
            if isinstance(nearest_contact_point, int):
                contact_point[0] = vertices[nearest_contact_point]
            else:
                print(f"Skipping contact point {contact_point} because nearest_contact_point is not an integer: {nearest_contact_point}")

        for constraint_point in constraint_points:
            nearest_constraint_point = find_nearest(tree, constraint_point[0])
            if isinstance(nearest_constraint_point, int):
                constraint_point[0] = vertices[nearest_constraint_point]
            else:
                print(f"Skipping constraint point {constraint_point} because nearest_constraint_point is not an integer: {nearest_constraint_point}")
        
        # Create the contact and constraint points data in the format required by the script
        contact_pts = ', '.join(json.dumps(sublist) for sublist in contact_points)
        constraint_pts = '\n    '.join(f"p['axis_pt{i+1}'] = {json.dumps(sublist)[1:-1]}" for i, sublist in enumerate(constraint_points))
            
        bpy.context.view_layer.objects.active = copy_main_object
        vertex_group_coordinates = {}
        
        for group in copy_main_object.vertex_groups:

            if "_sample" not in group.name and not group.name.startswith(("contact_point", "constraint_point")):
                # Cambiar a modo de edición y seleccionar el grupo de vértices
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_set_active(group=group.name)
                bpy.ops.object.vertex_group_select()

                # Crear un nuevo objeto solo con las caras seleccionadas
                bpy.ops.mesh.duplicate_move()
                bpy.ops.mesh.select_linked()
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')  

                new_mesh = bpy.context.selected_objects[-1]
                # Renombrar el objeto con el nombre del grupo de vértices
                new_mesh.name = f"{group.name}.001"
                
        for group in copy_main_object.vertex_groups:
            group_name = group.name
            if group_name.endswith("_sample"):
                # Obtener los índices de los vértices del grupo
                group_index = group.index
                vertices_indices = [v.index for v in copy_main_object.data.vertices if group_index in [g.group for g in v.groups]]
                # Obtener las coordenadas de los vértices del grupo en coordenadas locales
                vertex_coordinates_local = [copy_main_object.data.vertices[i].co for i in vertices_indices]
                # Convertir las coordenadas locales a coordenadas globales
                matrix_world = copy_main_object.matrix_world
                vertex_coordinates_global = [matrix_world @ coord for coord in vertex_coordinates_local]
                vertex_coordinates_serializable = [[coord.x, coord.y, coord.z] for coord in vertex_coordinates_global]
                # Almacenar las coordenadas en el diccionario
                vertex_group_coordinates[group_name] = json.dumps(vertex_coordinates_serializable)  
        
        if sensitivity_collection is not None:
            # Obtiene la ruta de la carpeta seleccionada
            folder_path = bpy.path.abspath(bpy.context.scene.selected_folder)
            folder_name = str(round(len(copy_main_object.data.polygons)))+ "_faces"
            full_path = os.path.join(folder_path, folder_name)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

            # Itera sobre todos los objetos en la colección "Sensitivity Analysis"
            for obj in sensitivity_collection.objects:
                # Deselecciona todos los objetos
                bpy.ops.object.select_all(action='DESELECT')

                # Selecciona el objeto que quieres exportar
                obj.select_set(True)

                # Elimina el sufijo ".001" del nombre del objeto
                obj_name = obj.name.split('.')[0]

                # Define el nombre del archivo .stl basado en el nombre del objeto
                mesh_path = os.path.join(folder_path,folder_name, f"{obj_name}.stl")

                # Exporta el objeto seleccionado a un archivo .stl
                bpy.ops.export_mesh.stl(filepath=mesh_path, use_selection=True)
                
        else:
            print("La colección 'Sensitivity Analysis' no existe")
            

                    

        
        # Create python script
        script_content = f"""\
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{folder_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{folder_name}')
    p['bone'] = f'{{path}}/{file_name_main}'
    p['contact_pts'] = {contact_pts}
    {''.join(constraint_pts)}
    p['muscles'] = {muscle_parameters}
    p['fixations'] = {{
        'contact_pts': [{contact_axes}],
        {constraint_axes}
    }}

    
    # material properties
    p['density'] = 1.662e-9  # [T/mm³]
    p['Young'] = {youngs_modulus}     # [MPa]
    p['Poisson'] = {poissons_ratio}      # [-]

    # p['use_gmshOld'] = True

    p.update(d)
    return p


def getMetafor(p={{}}):
    import bonemodel as model
    return model.getMetafor(parms(p))


if __name__ == "__main__":
    import models.bonemodel2 as model
    model.solve(parms())
    
# Areas of interest
"""
        for group_name, coordinates in vertex_group_coordinates.items():
            script_content += f"# {group_name}: {coordinates}\n"
            
        script_file_path = os.path.join(file_path, f"{folder_name}.py")
        with open(script_file_path, "w") as script_file:
            script_file.write(script_content)
            
        self.report({'INFO'}, f"Meshes and script exported to: {folder_name}")
        return {'FINISHED'}        
        
def register():
    bpy.utils.register_class(VIEW3D_PT_FilePathPanel_PT)
    bpy.utils.register_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitParametersOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitContactPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectContactPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectConstraintPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitConstraintPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.register_class(VIEW3D_OT_DeleteLastMuscleAttachmentOperator)
    bpy.utils.register_class(VIEW3D_OT_RunFossilsOperator)
    bpy.utils.register_class(VIEW3D_OT_OpenFEAResultsFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_ApplyForcesParametersOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSampleOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportSensitivityAnalysisOperator)




        
    bpy.types.Scene.constraint_point = bpy.props.StringProperty(
        name="Constraint Point ",
        default="",
        description="Name or identifier for Constraint Point "
    )

    bpy.types.Scene.selected_main_object = bpy.props.StringProperty(
        name="Selected Main Object",
        default="",
        description="Name or identifier for the selected main object"
    )

    bpy.types.Scene.muscle_parameters = bpy.props.StringProperty(
        name="Muscle Parameters",
        description="Parameters for muscles in a specific format"
    )

    bpy.types.Scene.contact_x = bpy.props.BoolProperty(
        name="Contact X",
        default=False,
        description="Enable or disable X axis for contact points"
    )

    bpy.types.Scene.contact_y = bpy.props.BoolProperty(
        name="Contact Y",
        default=False,
        description="Enable or disable Y axis for contact points"
    )

    bpy.types.Scene.contact_z = bpy.props.BoolProperty(
        name="Contact Z",
        default=False,
        description="Enable or disable Z axis for contact points"
    )

    bpy.types.Scene.constraint1_x = bpy.props.BoolProperty(
        name="Constraint 1 X",
        default=False,
        description="Enable or disable X axis for Constraint Point 1"
    )

    bpy.types.Scene.constraint1_y = bpy.props.BoolProperty(
        name="Constraint 1 Y",
        default=False,
        description="Enable or disable Y axis for Constraint Point 1"
    )

    bpy.types.Scene.constraint1_z = bpy.props.BoolProperty(
        name="Constraint 1 Z",
        default=False,
        description="Enable or disable Z axis for Constraint Point 1"
    )

    bpy.types.Scene.constraint2_x = bpy.props.BoolProperty(
        name="Constraint 2 X",
        default=False,
        description="Enable or disable X axis for Constraint Point 2"
    )

    bpy.types.Scene.constraint2_y = bpy.props.BoolProperty(
        name="Constraint 2 Y",
        default=False,
        description="Enable or disable Y axis for Constraint Point 2"
    )

    bpy.types.Scene.constraint2_z = bpy.props.BoolProperty(
        name="Constraint 2 Z",
        default=False,
        description="Enable or disable Z axis for Constraint Point 2"
    )

    bpy.types.Scene.youngs_modulus = bpy.props.FloatProperty(
        name="Young's Modulus",
        default=18000,
        min=0.0,
        precision=1,
        step=1,
        description="Young's modulus value for material in MPa"
    )

    bpy.types.Scene.poissons_ratio = bpy.props.FloatProperty(
        name="Poisson's Ratio",
        default=0.3,
        min=-1,
        max=1.0,
        precision=3,
        step=1,
        unit='NONE',
        description="Poisson's ratio value for material"
    )

    bpy.types.Scene.selected_folder = StringProperty(
        name="Selected Folder",
        default="",
        description="Selected folder for file storage"
    )

    bpy.types.Scene.new_folder_name = StringProperty(
        name="New Folder Name",
        default="",
        description="Name for the new folder to be created"
    )

    bpy.types.Scene.submesh_name = StringProperty(
        name="Submesh Name",
        default="",
        description="Name for the submesh to be created"
    )

    bpy.types.Scene.focal_point_coordinates = StringProperty(
        name="Focal Point Coordinates",
        default="",
        description="Coordinates of the selected Focal Point",
    )

    bpy.types.Scene.force_value = FloatProperty(
        name="Force Value",
        default=0.0,
        min=0.0,
        description="Value of the force in Newtons",
    )

    bpy.types.Scene.selected_option = EnumProperty(
        items=[
            ('U', "Uniform-traction", "U: Uniform-traction"),
            ('T', "Tangential-traction", "T: Tangential-traction"),
            ('T+N', "Tangential-plus-normal-traction", "TN: Tangential-plus-normal-traction"),
        ],
        name="Options",
        default='T+N',
        description="Select an option",
    )
    bpy.types.Scene.select_more_iterations = bpy.props.IntProperty(
        name="Select More Iterations",
        default=0,
        min=0,
        max=30,
        description="Number of times to apply 'Select More'"
    )

    bpy.types.Scene.contact_point_coordinates = StringProperty(
        name="Contact Point Coordinates",
        default="",
        description="Coordinates of the selected Contact Point",
    )
    
    bpy.types.Scene.constraint_point_coordinates = StringProperty(
        name="Constraint Point Coordinates",
        default="",
        description="Coordinates of the selected Constraint Point",
    )

    bpy.types.Scene.contact_points = CollectionProperty(type=bpy.types.PropertyGroup)
    
    bpy.types.Scene.display_existing_results = bpy.props.BoolProperty(
        name="Display Existing Results",
        default=False,
        update=update_checkboxes
    )

    bpy.types.Scene.open_results_when_finish = bpy.props.BoolProperty(
        name="Open Results When Finish",
        default=False,
        update=update_checkboxes
    )
    
    bpy.types.Scene.run_as_admin = bpy.props.BoolProperty(
        name="Open Results When Finish",
        default=False,
        update=update_checkboxes
    )   
    
    bpy.types.Scene.show_constraint_points = bpy.props.BoolProperty(
        name="Show Constraint Points",
        default=False,
        description="Display arrows at Constraint Points locations"
    )

    bpy.types.Scene.show_contact_points = bpy.props.BoolProperty(
        name="Show Contact Points",
        default=False,
        description="Display arrows at Contact Points locations"
    )

    bpy.types.Scene.show_attachment_areas = bpy.props.BoolProperty(
        name="Show Attachment Areas",
        default=False,
        description="Enable to display attachment areas with random colors. Move the collection above others for better visibility."
    )


    bpy.types.Scene.show_force_directions = bpy.props.BoolProperty(
        name="Show Force Directions",
        default=False,
        description="Display arrows indicating force directions"
    )
    def update_total_faces(self, context):
        main_object = bpy.data.objects.get(getattr(bpy.context.scene, "selected_main_object", ""))
        
        if main_object:
            self.total_faces = round(len(main_object.data.polygons) * self.scale_factor)
        else:
            self.total_faces = 0
            
    def update_scale_factor(self, context):
        main_object = bpy.data.objects.get(getattr(bpy.context.scene, "selected_main_object", ""))
        
        if main_object:
            self.scale_factor = self.total_faces / len(main_object.data.polygons)
        else:
            self.scale_factor = 0
            
    bpy.types.Scene.sample_name = StringProperty(
        name="Sample Name",
        default="",
        description="Name for the submesh to be created"
    )
    bpy.types.Scene.scale_factor = bpy.props.FloatProperty(
        name="Scale Factor",
        default=1,
        min=0.01,
        max=16,
        description="Scaling factor for the mesh",
        update=update_total_faces, 
    )

    bpy.types.Scene.total_faces = bpy.props.IntProperty(
        name="Total Faces",
        default=0,
        min=1,
        soft_max=10000000,
        update=update_scale_factor,
    )
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_FilePathPanel_PT)
    bpy.utils.unregister_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectFocalPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitFocalPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitParametersOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitContactPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectContactPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectConstraintPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitConstraintPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.unregister_class(VIEW3D_OT_DeleteLastMuscleAttachmentOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RunFossilsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_OpenFEAResultsFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ApplyForcesParametersOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ExportSensitivityAnalysisOperator)


    del bpy.types.Scene.selected_folder
    del bpy.types.Scene.new_folder_name
    del bpy.types.Scene.submesh_name
    del bpy.types.Scene.focal_point_coordinates
    del bpy.types.Scene.force_value
    del bpy.types.Scene.selected_option
    del bpy.types.Scene.contact_x
    del bpy.types.Scene.contact_y
    del bpy.types.Scene.contact_z
    del bpy.types.Scene.constraint1_x
    del bpy.types.Scene.constraint1_y
    del bpy.types.Scene.constraint1_z
    del bpy.types.Scene.constraint2_x
    del bpy.types.Scene.constraint2_y
    del bpy.types.Scene.constraint2_z
    del bpy.types.Scene.display_existing_results
    del bpy.types.Scene.open_results_when_finish

if __name__ == "__main__":
    register()
