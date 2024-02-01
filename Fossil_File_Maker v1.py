bl_info = {
    "name": "Fossil File generator",
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
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, EnumProperty, FloatProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
import os
import math
import json
import re
import subprocess
import ctypes

# Utilities 
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)

# Interface Panel
class VIEW3D_PT_FilePathPanel_PT(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_FilePathPanel_PT"
    bl_label = "File Path"
    bl_category = "FossilFilesGenerator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout

        # Data Storage Location
        box = layout.box()
        box.label(text="Data Storage Location",icon='FILE_FOLDER')

        row = box.row()
        row.operator("view3d.browse_folder", text="Browse Folder", icon='FILE_FOLDER')
        row.prop(context.scene, "selected_folder", text="")

        row = box.row()
        row.prop(context.scene, "new_folder_name", text="New Folder Name", icon='GREASEPENCIL')

        row = box.row()
        row.operator("view3d.create_folder", text="Create Folder", icon='NEWFOLDER')

        # Select Main Object Section
        row = box.row()
        row.operator("view3d.submit_object", text="Submit main bone for FEA", icon='BONE_DATA')

        # Rotate Elements Section
        box = layout.box()
        box.label(text="Rotate Elements")

        # Rotate Axes
        row = box.row()
        row.operator("view3d.rotate_elements", text="Rotate Y to Z", icon='FILE_REFRESH')

        # Restore Orientation Axes Button
        row = box.row()
        row.operator("view3d.restore_orientation_axes", text="Restore Orientation Axes", icon='RECOVER_LAST')

        # Extract Surfaces Section
        box = layout.box()
        box.label(text="Extract muscle attachment areas and properties")

        row = box.row()
        row.prop(context.scene, "submesh_name", text="Muscle name", icon='GREASEPENCIL')

        row = box.row()
        row.operator("view3d.start_selection", text="Start Selection", icon='RESTRICT_SELECT_OFF')

        row = box.row()
        row.operator("view3d.submit_selection", text="Submit Selection", icon='EXPORT')

        box.label(text="Direction of the force")

        row = box.row()
        row.operator("view3d.select_focal_point", text="Select Focal Point", icon='RESTRICT_SELECT_OFF')

        # Add text box to display coordinates
        row = box.row()
        row.prop(context.scene, "focal_point_coordinates", text="Focal Point Coordinates", emboss=False, icon='VIEW3D')

        row = box.row()
        row.operator("view3d.submit_focal_point", text="Submit Focal Point", icon='EXPORT')

        box.label(text="Muscle Parameters")

        # Text box for force value
        row = box.row()
        row.prop(context.scene, "force_value", text="Force")

        # Dropdown list for loading scenario
        row = box.row()
        row.prop(context.scene, "selected_option", text="Loading scenario")

        # Button to submit parameters
        row = box.row()
        row.operator("view3d.submit_parameters", text="Submit Parameters", icon='EXPORT')
        row = box.row()
        row.operator("view3d.delete_last_muscle_attachment", text="Delete Last Muscle Attachment AND parameters", icon='TRASH')

        # Contact Points Section
        box = layout.box()
        box.label(text="Contact Points", icon='FORCE_FORCE')

        col = box.column(align=True)
        col.operator("view3d.select_contact_point", text="Select Contact Point", icon='RESTRICT_SELECT_OFF')

        # Text box to display selected vertex coordinates
        col.prop(context.scene, "contact_point_coordinates", text="Contact Point Coordinates", emboss=False, icon='VIEW3D')

        # Select Axes Section for Contact Points
        row = box.row(align=True)
        row.label(text="Select Axes:")
        row.prop(context.scene, "contact_x", text="X")
        row.prop(context.scene, "contact_y", text="Y")
        row.prop(context.scene, "contact_z", text="Z")

        col = box.column(align=True)
        col.operator("view3d.submit_contact_point1", text="Submit Contact Point 1", icon='EXPORT')
        col.operator("view3d.submit_contact_point2", text="Submit Contact Point 2", icon='EXPORT')
        col.operator("view3d.clear_contact_points", text="Clear Contact Points", icon='TRASH')

        # Visual separation between sections
        layout.separator()

        # Constraint Points Section
        box = layout.box()
        box.label(text="Constraint Points", icon='CONSTRAINT_BONE')

        # Column for Constraint Point 1
        col = box.column(align=True)
        col.operator("view3d.select_constraint_point", text="Select Constraint Point", icon='RESTRICT_SELECT_OFF')
        col.prop(context.scene, "constraint_point_coordinates", text="Constraint Point Coordinates", emboss=False, icon='VIEW3D')

        # Select Axes Section for Constraint Point 1
        row = box.row(align=True)
        row.label(text="Select Axes (CP1):")
        row.prop(context.scene, "constraint1_x", text="X")
        row.prop(context.scene, "constraint1_y", text="Y")
        row.prop(context.scene, "constraint1_z", text="Z")

        col = box.column(align=True)
        col.operator("view3d.submit_constraint_point1", text="Submit Constraint Point 1", icon='EXPORT')

        # Select Axes Section for Constraint Point 2
        row = box.row(align=True)
        row.label(text="Select Axes (CP2):")
        row.prop(context.scene, "constraint2_x", text="X")
        row.prop(context.scene, "constraint2_y", text="Y")
        row.prop(context.scene, "constraint2_z", text="Z")

        # Constraint Point 2
        col = box.column(align=True)
        col.operator("view3d.submit_constraint_point2", text="Submit Constraint Point 2", icon='EXPORT')
        col.operator("view3d.clear_constraint_points", text="Clear Constraint Points", icon='TRASH')

        # Material Properties Section
        box = layout.box()
        box.label(text="Material Properties")

        # Text boxes to enter values
        box.prop(context.scene, "youngs_modulus", text="Young's Modulus")
        box.prop(context.scene, "poissons_ratio", text="Poisson's Ratio")

        # Export Files Section
        box = layout.box()
        box.label(text="Export files", icon='EXPORT')

        # Export button
        row = box.row()
        row.operator("view3d.export_meshes", text="Export files", icon='EXPORT')
        
        #Run Fossils
        row = layout.row()
        row.prop(context.scene, "display_existing_results", text="Display Existing Results")
        row.prop(context.scene, "open_results_when_finish", text="Open Results When Finish")
        row.prop(context.scene, "run_as_admin", text="Run as Admin")

        row = layout.row()
        row.operator("view3d.run_fossils", text="Run Fossils", icon='PLAY')
        row.operator("view3d.open_fea_results_folder", text="Open FEA Results Folder", icon='FILE_FOLDER')

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

    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)
        new_folder_name = context.scene.new_folder_name

        if file_path and new_folder_name:
            try:
                # Crear la carpeta en el sistema de archivos
                folder_path = os.path.join(file_path, new_folder_name)
                os.makedirs(folder_path, exist_ok=True)
                self.report({'INFO'}, f"Folder created at: {folder_path}")

                # Crear la colección en Blender
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

        if active_object:
            context.scene.selected_main_object = active_object.name
            self.report({'INFO'}, f"Main object set to: {context.scene.selected_main_object}")
        else:
            self.report({'ERROR'}, "No active object.")

        return {'FINISHED'}
        
# Operador para rotar elementos
class VIEW3D_OT_RotateElementsOperator(bpy.types.Operator):
    bl_idname = "view3d.rotate_elements"
    bl_label = "Rotate Elements"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Rotate objects, changing the Y and Z axes to match other coordinate systems. Use with caution, as it affects the orientation of the objects. Make sure you are certain about the desired orientation before clicking."


    def execute(self, context):
        set_object_mode(context.active_object, 'OBJECT')

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.rotation_euler.rotate_axis("X", math.radians(-90))
                obj.rotation_euler.rotate_axis("Z", math.radians(-180))

        self.report({'INFO'}, "Elements rotated from Y to Z")
        return {'FINISHED'}

# Operador para restaurar orientación de ejes
class VIEW3D_OT_RestoreOrientationAxesOperator(bpy.types.Operator):
    bl_idname = "view3d.restore_orientation_axes"
    bl_label = "Restore Orientation Axes"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Restore the orientation of the axes. Click it only if needed or after exporting the files"


    def execute(self, context):
        set_object_mode(context.active_object, 'OBJECT')

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.rotation_euler.rotate_axis("Z", math.radians(180))
                obj.rotation_euler.rotate_axis("X", math.radians(90))

        self.report({'INFO'}, "Orientation Axes restored")
        return {'FINISHED'}
        
class VIEW3D_OT_StartSelectionOperator(Operator):
    bl_idname = "view3d.start_selection"
    bl_label = "Start Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and activates the Lasso Select tool. Ensure that the active object is the one you want to use for creating the sub-mesh. Be cautious, as this operation subtracts the sub-mesh from the active object."



    def execute(self, context):
        # Cambiar a modo de edición y activar la herramienta "lasso select" con "face select"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')       
        bpy.context.tool_settings.mesh_select_mode[0] = False 
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = True
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso", space_type='VIEW_3D')

        return {'FINISHED'}

class VIEW3D_OT_SubmitSelectionOperator(Operator):
    bl_idname = "view3d.submit_selection"
    bl_label = "Submit Selection"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Creates a sub-mesh from the selected surface and stores it in the specified collection."



    def execute(self, context):
        # Salir del modo de edición y volver a la vista de objeto
        bpy.ops.object.mode_set(mode='OBJECT')

        # Crear una nueva malla para la submalla
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.context.active_object
        bpy.context.active_object.select_set(True)

        # Crear una nueva malla solo con la parte seleccionada
        bpy.ops.object.duplicate(linked=False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Renombrar la nueva malla
        submesh_name = context.scene.submesh_name
        bpy.context.active_object.name = submesh_name

        # Mover la nueva malla a la colección creada previamente
        collection_name = context.scene.new_folder_name
        collection = bpy.data.collections.get(collection_name)

        if collection:
            collection.objects.link(bpy.context.active_object)
        else:
            self.report({'ERROR'}, f"Collection '{collection_name}' not found")

        # Quitar la malla de la colección original
        original_collection = bpy.context.active_object.users_collection[0]
        original_collection.objects.unlink(bpy.context.active_object)

        self.report({'INFO'}, f"Submesh '{submesh_name}' created and added to collection '{collection_name}'")

        return {'FINISHED'}
        
# Operador para seleccionar el punto focal
class VIEW3D_OT_SelectFocalPointOperator(Operator):
    bl_idname = "view3d.select_focal_point"
    bl_label = "Select Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, allowing you to select a point to be used as the force direction for the previously created muscle attachment area."


    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True  # Modo de selección de cara
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False
        return {'FINISHED'}

# Operador para enviar el punto focal
class VIEW3D_OT_SubmitFocalPointOperator(Operator):
    bl_idname = "view3d.submit_focal_point"
    bl_label = "Submit Focal Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable."


    def execute(self, context):
    
        set_object_mode(context.active_object, 'OBJECT')
        vertices = [v.co for v in context.active_object.data.vertices if v.select]

        if vertices:
            context.scene.focal_point_coordinates = f"{vertices[0][0]:.3f},{vertices[0][1]:.3f},{vertices[0][2]:.3f}"
            self.report({'INFO'}, f"Focal Point coordinates: {context.scene.focal_point_coordinates}")
        else:
            context.scene.focal_point_coordinates = ""
            self.report({'ERROR'}, "No vertex selected as Focal Point")

        return {'FINISHED'}

class VIEW3D_OT_SubmitParametersOperator(Operator):
    bl_idname = "view3d.submit_parameters"
    bl_label = "Submit Parameters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the parameters (Name of the last sub-mesh created, Focal Point, Force, and loading scenario) in a dictionary."


    def execute(self, context):
        # Obtener el nombre de la última submalla extraída
        last_submesh_name = context.scene.submesh_name

        # Construir el nombre del archivo STL
        file_name = f"{last_submesh_name}.stl"  # Agregar "/" antes del nombre del archivo

        # Obtener los valores de la fuerza y el método desde el contexto
        force_value = context.scene.force_value
        selected_option = context.scene.selected_option
        focal_point_coordinates = [float(coord) for coord in context.scene.focal_point_coordinates.split(",")]

        # Convertir las coordenadas del punto focal a una cadena JSON sin indentación
        focal_point_coordinates_str = json.dumps(focal_point_coordinates, indent=None)

        # Obtener el diccionario existente o crear uno nuevo
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

        # Almacenar los datos en un diccionario
        data = {
            'file': f"f'{{path}}/" + f"{file_name}'",  
            'force': force_value,
            'focalpt': focal_point_coordinates,  # Usar la cadena JSON de las coordenadas
            'method': selected_option
        }

        # Agregar la entrada al diccionario
        muscle_parameters.append(data)  # Utilizar append para agregar un nuevo elemento a la lista

        # Almacenar el diccionario como cadena JSON en la propiedad de la escena
        json_str = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)
        context.scene["muscle_parameters"] = json_str

        # Mostrar el diccionario en la consola
        self.report({'INFO'}, "Stored data:\n" + json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False))
        return {'FINISHED'}

class VIEW3D_OT_DeleteLastMuscleAttachmentOperator(Operator):
    bl_idname = "view3d.delete_last_muscle_attachment"
    bl_label = "Delete Last Muscle Attachment"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Deletes the last mesh and parameters stored in a dictionary. Be aware, if you click it before submitting the parameters, the last input parameters will be deleted along with the last sub-mesh created. WARNING: Use with caution!"

    def execute(self, context):
        # Obtener el diccionario existente o crear uno nuevo
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

        # Verificar si hay elementos en el diccionario antes de intentar eliminar
        if muscle_parameters:
            last_submesh_name = context.scene.submesh_name
            last_submesh_object = bpy.data.objects.get(last_submesh_name)

            if last_submesh_object:
                bpy.data.objects.remove(last_submesh_object, do_unlink=True)

            # Eliminar la última entrada del diccionario
            muscle_parameters.pop()

            # Almacenar el diccionario actualizado como cadena JSON en la propiedad de la escena
            json_str = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)
            context.scene["muscle_parameters"] = json_str
            context.scene.submesh_name = ""

            self.report({'INFO'}, f"Deleted last muscle attachment: {last_submesh_name}")
        else:
            self.report({'WARNING'}, "No muscle attachments to delete.")

        return {'FINISHED'}


# Definición de la clase VIEW3D_OT_SelectContactPointOperator
class VIEW3D_OT_SelectContactPointOperator(Operator):
    bl_idname = "view3d.select_contact_point"
    bl_label = "Select Contact Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, enabling you to select a point to be used as a contact point where the force will be applied during the FEA."



    def execute(self, context):
        # Cambiar a modo de edición y activar la herramienta "vertex select"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True  # Modo de selección de cara
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False

        return {'FINISHED'}


class VIEW3D_OT_SubmitContactPointOperator1(bpy.types.Operator):
    bl_idname = "view3d.submit_contact_point1"
    bl_label = "Submit Contact Point 1"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable to be used as contact point"

    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object and active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        if selected_vertices:
            coordinates = selected_vertices[0]
            coordinates_str = [f"{coordinates[0]:.6f}", f"{coordinates[1]:.6f}", f"{coordinates[2]:.6f}"]
            bpy.context.scene.Contact_point1 = ", ".join(coordinates_str)
            bpy.context.scene.contact_point_coordinates = ", ".join(coordinates_str)
            self.report({'INFO'}, f"Contact Point 1 coordinates: {bpy.context.scene.contact_point_coordinates}")
        else:
            self.report({'ERROR'}, "No vertex selected.")

        return {'FINISHED'}


class VIEW3D_OT_SubmitContactPointOperator2(bpy.types.Operator):
    bl_idname = "view3d.submit_contact_point2"
    bl_label = "Submit Contact Point 2"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Only needed if you want to use 2 contact points. Otherwise, you may skip this step. Stores the coordinates of the selected vertex/point in a variable to be used as a contact point."


    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object and active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        if selected_vertices:
            coordinates = selected_vertices[0]
            coordinates_str = [f"{coordinates[0]:.6f}", f"{coordinates[1]:.6f}", f"{coordinates[2]:.6f}"]
            bpy.context.scene.Contact_point2 = ", ".join(coordinates_str)
            bpy.context.scene.contact_point_coordinates = ", ".join(coordinates_str)
            self.report({'INFO'}, f"Contact Point 2 coordinates: {bpy.context.scene.contact_point_coordinates}")
        else:
            self.report({'ERROR'}, "No vertex selected.")

        return {'FINISHED'}


class VIEW3D_OT_ClearContactPointsOperator(Operator):
    bl_idname = "view3d.clear_contact_points"
    bl_label = "Clear Contact Points"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Delete contact points stored"

    def execute(self, context):
        # Limpiar las variables de Contact Point 1 y Contact Point 2
        context.scene.Contact_point1 = ""
        context.scene.Contact_point2 = ""
        context.scene.contact_point_coordinates = ""
        return {'FINISHED'}

class VIEW3D_OT_SelectConstraintPointOperator(Operator):
    bl_idname = "view3d.select_constraint_point"
    bl_label = "Select Constraint Point"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Switches to Edit Mode and Vertex selection, enabling you to select a point to be used as a constraint point where the object will be fixed during the FEA."


    def execute(self, context):       
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True 
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False

        return {'FINISHED'}

class VIEW3D_OT_SubmitConstraintPointOperator1(Operator):
    bl_idname = "view3d.submit_constraint_point1"
    bl_label = "Submit Constraint Point 1"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Stores the coordinates of the selected vertex/point in a variable to be used as constraint point"

    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object and active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        if selected_vertices:
            coordinates = selected_vertices[0]
            coordinates_str = [f"{coordinates[0]:.6f}", f"{coordinates[1]:.6f}", f"{coordinates[2]:.6f}"]
            bpy.context.scene.Constraint_point1 = ", ".join(coordinates_str)
            bpy.context.scene.constraint_point_coordinates = ", ".join(coordinates_str)
            self.report({'INFO'}, f"Constraint Point 1 coordinates: {bpy.context.scene.constraint_point_coordinates }")
        else:
            self.report({'ERROR'}, "No vertex selected.")

        return {'FINISHED'}

class VIEW3D_OT_SubmitConstraintPointOperator2(Operator):
    bl_idname = "view3d.submit_constraint_point2"
    bl_label = "Submit Constraint Point 2"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Only needed if you want to use 2 constraint points. Otherwise, you may skip this step. Stores the coordinates of the selected vertex/point in a variable to be used as a constraint point."


    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object and active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected_vertices = [v.co for v in active_object.data.vertices if v.select]

        if selected_vertices:
            coordinates = selected_vertices[0]
            coordinates_str = [f"{coordinates[0]:.6f}", f"{coordinates[1]:.6f}", f"{coordinates[2]:.6f}"]
            bpy.context.scene.Constraint_point2 = ", ".join(coordinates_str)
            bpy.context.scene.constraint_point_coordinates = ", ".join(coordinates_str)
            self.report({'INFO'}, f"Constraint Point 2 coordinates: {bpy.context.scene.constraint_point_coordinates }")
        else:
            self.report({'ERROR'}, "No vertex selected.")

        return {'FINISHED'}

class VIEW3D_OT_ClearConstraintPointsOperator(Operator):
    bl_idname = "view3d.clear_constraint_points"
    bl_label = "Clear Constraint Points"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Delete constraint points stored"

    def execute(self, context):
        # Limpiar las variables de Constraint Point 1 y Constraint Point 2
        context.scene.Constraint_point1 = ""
        context.scene.Constraint_point2 = ""
        context.scene.constraint_point_coordinates = ""  # Limpiar la variable de coordenadas
        return {'FINISHED'}
        
class VIEW3D_OT_ExportMeshesOperator(bpy.types.Operator):
    bl_idname = "view3d.export_meshes"
    bl_label = "Export Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Export all the files required for the FEA in Fossils. This includes the main mesh/bone, sub-meshes of the main object/bone (Attachment muscle areas), and a Python file with the parameters inputted by the user."

    def execute(self, context):
        file_path = bpy.path.abspath(context.scene.selected_folder)

        if file_path:
            try:
                # Iterar sobre las mallas en la colección y exportarlas
                collection_name = context.scene.new_folder_name
                collection = bpy.data.collections.get(collection_name)
                Contact_point1 = bpy.context.scene.Contact_point1
                Contact_point2 = bpy.context.scene.Contact_point2
                Constraint_point1 = bpy.context.scene.Constraint_point1
                Constraint_point2 = bpy.context.scene.Constraint_point2
                selected_main_object = context.scene.selected_main_object                
                muscle_parameters = str(context.scene.get("muscle_parameters", {})).replace('"', "'")
                muscle_parameters = re.sub("''", "'", muscle_parameters)
                muscle_parameters = re.sub("'f'", "f'", muscle_parameters)
                youngs_modulus = context.scene.youngs_modulus
                poissons_ratio = round(context.scene.poissons_ratio, 3)
                
                # Obtener valores de los checkboxes
                contact_x = context.scene.contact_x
                contact_y = context.scene.contact_y
                contact_z = context.scene.contact_z

                # Construir la variable con el formato deseado
                selected_axes = [f"'{axis}'" for axis, selected in [('x', contact_x), ('y', contact_y), ('z', contact_z)] if selected]
                contact_axes = ','.join(selected_axes)

                # Obtener valores de los checkboxes para Constraint Point 1
                constraint1_x = context.scene.constraint1_x
                constraint1_y = context.scene.constraint1_y
                constraint1_z = context.scene.constraint1_z

                # Construir la variable con el formato deseado para Constraint Point 1
                selected_axes_cp1 = [f"'{axis}'" for axis, selected in [('x', constraint1_x), ('y', constraint1_y), ('z', constraint1_z)] if selected]
                constraint_axes_cp1 = ','.join(selected_axes_cp1)

                # Obtener valores de los checkboxes para Constraint Point 2
                constraint2_x = context.scene.constraint2_x
                constraint2_y = context.scene.constraint2_y
                constraint2_z = context.scene.constraint2_z

                # Construir la variable con el formato deseado para Constraint Point 2
                selected_axes_cp2 = [f"'{axis}'" for axis, selected in [('x', constraint2_x), ('y', constraint2_y), ('z', constraint2_z)] if selected]
                constraint_axes_cp2 = ','.join(selected_axes_cp2)              
        
                if collection:
                    # Verificar si Contact Point 2 existe
                    if Contact_point2:
                        # Ambos Contact Points están presentes
                        contact_pts = [[float(coord) for coord in Contact_point1.split(",")],
                                       [float(coord) for coord in Contact_point2.split(",")]]
                    else:
                        # Solo Contact Point 1 está presente
                        contact_pts = [[float(coord) for coord in Contact_point1.split(",")]]
                        
                    # Verificar si Constraint Point 2 existe
                    if Constraint_point2:
                        # Ambos Constraint Points están presentes
                        constraint_pts = [
                            f"p['axis_pt1'] = {[float(coord) for coord in Constraint_point1.split(',')]}\n",
                            f"    p['axis_pt2'] = {[float(coord) for coord in Constraint_point2.split(',')]}\n"
                        ]
                        constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}],\n\t\t'axis_pt2': [{constraint_axes_cp2}]"

                    else:
                        # Solo Constraint Point 1 está presente
                        constraint_axes = f"'axis_pt1': [{constraint_axes_cp1}]"
                        constraint_pts = [f"p['axis_pt1'] = {[float(coord) for coord in Constraint_point1.split(',')]}\n"]
                    #Exportar malla principal
                    selected_main_object = context.scene.selected_main_object
                    main_object = bpy.data.objects.get(selected_main_object)

                    if main_object:
                        bpy.context.view_layer.objects.active = main_object
                        bpy.ops.object.select_all(action='DESELECT')
                        main_object.select_set(True)

                        # Construir el nombre de archivo y exportar la malla en formato STL
                        file_name_main = f"{main_object.name}.stl"
                        file_path_stl_main = os.path.join(file_path, collection_name, file_name_main)
                        bpy.ops.export_mesh.stl(filepath=file_path_stl_main, use_selection=True, ascii=False)

                        # Desactivar la malla después de la exportación
                        bpy.context.view_layer.objects.active = None
                    else:
                        self.report({'ERROR'}, f"Main object '{selected_main_object}' not found")
                       
                    for obj in collection.objects:                          
                        if obj.type == 'MESH':
                        
                            # Activar y seleccionar solo la malla que se exportará
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)

                            # Construir el nombre de archivo y exportar la malla en formato STL
                            file_name = f"{obj.name}.stl"
                            file_path_stl = os.path.join(file_path, collection_name, file_name)
                            bpy.ops.export_mesh.stl(filepath=file_path_stl, use_selection=True, ascii=False)

                            # Desactivar la malla después de la exportación
                            bpy.context.view_layer.objects.active = None

                    # Crear el script y guardarlo en la misma carpeta
                    script_content = f"""\
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# **{collection_name}**


def parms(d={{}}):
    p = {{}}
    import os
    path = os.path.join(os.path.dirname(__file__), '{collection_name}')
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
        # Ruta al archivo Python
        python_file_path = bpy.path.abspath(context.scene.selected_folder)
        python_file_path = os.path.join(python_file_path, "script.py")

        # Carpeta del usuario
        user_folder = os.path.expanduser("~")

        # Ruta al ejecutable del programa externo
        external_program_path = os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "fossils.exe")

        args = [python_file_path]

        if context.scene.display_existing_results:
            args.append("--post")

        if not context.scene.open_results_when_finish:
            args.append("--nogui")

        try:
            # Verificar si se debe ejecutar como administrador
            if context.scene.run_as_admin:
                # Ejecutar el programa externo con privilegios de administrador
                args = ' '.join(args)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", external_program_path, args, python_file_path, 1)
            else:
                # Ejecutar el programa externo sin privilegios de administrador
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

        # Rutas posibles de las carpetas de resultados de FEA
        fea_results_folders = [
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "_internal", "workspace"),
            os.path.join(user_folder, "AppData", "Local", "Programs", "Fossils", "workspace")
        ]

        # Verificar la existencia de las carpetas
        found_folder = None
        for fea_results_folder in fea_results_folders:
            if os.path.exists(fea_results_folder):
                found_folder = fea_results_folder
                break

        # Abrir la carpeta encontrada o emitir un mensaje de error
        if found_folder:
            bpy.ops.wm.path_open(filepath=found_folder)
            self.report({'INFO'}, f"FEA results folder opened: {found_folder}")
        else:
            self.report({'ERROR'}, f"FEA results folder not found. Verify Fossils is installed in {user_folder}\Appdata\Local\Programs or you have run a FEA before")

        return {'FINISHED'}


def update_checkboxes(self, context):
    if context.scene.display_existing_results:
        context.scene.open_results_when_finish = False

    if context.scene.open_results_when_finish:
        context.scene.display_existing_results = False
        
# Registro de clases y propiedades
def register():
    bpy.utils.register_class(VIEW3D_PT_FilePathPanel_PT)
    bpy.utils.register_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.register_class(VIEW3D_OT_RotateElementsOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_RestoreOrientationAxesOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitParametersOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitContactPointOperator1)
    bpy.utils.register_class(VIEW3D_OT_SubmitContactPointOperator2)
    bpy.utils.register_class(VIEW3D_OT_SelectContactPointOperator)
    bpy.utils.register_class(VIEW3D_OT_ClearContactPointsOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectConstraintPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitConstraintPointOperator1)
    bpy.utils.register_class(VIEW3D_OT_SubmitConstraintPointOperator2)
    bpy.utils.register_class(VIEW3D_OT_ClearConstraintPointsOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.register_class(VIEW3D_OT_DeleteLastMuscleAttachmentOperator)
    bpy.utils.register_class(VIEW3D_OT_RunFossilsOperator)
    bpy.utils.register_class(VIEW3D_OT_OpenFEAResultsFolderOperator)

    bpy.types.Scene.Contact_point1 = bpy.props.StringProperty(
        name="Contact Point 1",
        default="",
        description="Name or identifier for Contact Point 1"
    )

    bpy.types.Scene.Contact_point2 = bpy.props.StringProperty(
        name="Contact Point 2",
        default="",
        description="Name or identifier for Contact Point 2"
    )

    bpy.types.Scene.Constraint_point1 = bpy.props.StringProperty(
        name="Constraint Point 1",
        default="",
        description="Name or identifier for Constraint Point 1"
    )

    bpy.types.Scene.Constraint_point2 = bpy.props.StringProperty(
        name="Constraint Point 2",
        default="",
        description="Name or identifier for Constraint Point 2"
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
        default='U',
        description="Select an option",
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

# Eliminación de clases y propiedades
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_FilePathPanel_PT)
    bpy.utils.unregister_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RotateElementsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectFocalPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitFocalPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RestoreOrientationAxesOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitParametersOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitContactPointOperator1)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitContactPointOperator2)
    bpy.utils.unregister_class(VIEW3D_OT_SelectContactPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ClearContactPointsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectConstraintPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitConstraintPointOperator1)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitConstraintPointOperator2)
    bpy.utils.unregister_class(VIEW3D_OT_ClearConstraintPointsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.unregister_class(VIEW3D_OT_DeleteLastMuscleAttachmentOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RunExternalProgramOperator)
    bpy.utils.unregister_class(VIEW3D_OT_OpenFEAResultsFolderOperator)

    del bpy.types.Scene.selected_folder
    del bpy.types.Scene.new_folder_name
    del bpy.types.Scene.submesh_name
    del bpy.types.Scene.focal_point_coordinates
    del bpy.types.Scene.force_value
    del bpy.types.Scene.selected_option
    del bpy.types.Scene.Contact_point1
    del bpy.types.Scene.Contact_point2
    del bpy.types.Scene.Constraint_point1
    del bpy.types.Scene.Constraint_point2
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
