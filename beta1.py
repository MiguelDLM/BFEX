bl_info = {
    "name": "Fossil File generator",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, EnumProperty, FloatProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
import os
import math

# Utilidades
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)

# Panel de la interfaz
class VIEW3D_PT_FilePathPanel(bpy.types.Panel):
    bl_idname = "PT_FilePathPanel"
    bl_label = "File Path"
    bl_category = "FossilFilesGenerator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
      
        box = layout.box()
        box.label(text="Data Storage Location")

        row = box.row()
        row.operator("view3d.browse_folder", text="Browse Folder")
        row.prop(context.scene, "selected_folder", text="")

        row = box.row()
        row.prop(context.scene, "new_folder_name", text="New Folder Name")

        row = box.row()
        row.operator("view3d.create_folder", text="Create Folder")
        
        # Sección "Select main object"
        row = box.row()
        row.operator("view3d.submit_object", text="Submit Object")

        # Sección "Rotate Elements"
        box = layout.box()
        box.label(text="Rotate Elements")
        
        #Rotar ejes
        row = box.row()
        row.operator("view3d.rotate_elements", text="Rotate Y to Z")
        
        # Botón para restaurar la orientación de los ejes
        row = box.row()
        row.operator("view3d.restore_orientation_axes", text="Restore Orientation Axes")

        # Sección "Extract Surfaces"
        box = layout.box()
        box.label(text="Extract Surfaces")

        row = box.row()
        row.prop(context.scene, "submesh_name", text="Submesh Name")

        row = box.row()
        row.operator("view3d.start_selection", text="Start Selection")

        row = box.row()
        row.operator("view3d.submit_selection", text="Submit Selection")

        # Sección "Focal Point"
        box = layout.box()
        box.label(text="Focal Point")

        row = box.row()
        row.operator("view3d.select_focal_point", text="Select Focal Point")

        # Agregar caja de texto para mostrar coordenadas
        row = box.row()
        row.prop(context.scene, "focal_point_coordinates", text="Focal Point Coordinates", emboss=False, icon='VIEW3D')

        row = box.row()
        row.operator("view3d.submit_focal_point", text="Submit Focal Point")
        
        # Nueva sección para los parámetros
        box = layout.box()
        box.label(text="Muscle Parameters")

        # Caja de texto para ingresar el valor de la fuerza
        row = box.row()
        row.prop(context.scene, "force_value", text="Force")

        # Lista de opciones para seleccionar
        row = box.row()
        row.prop(context.scene, "selected_option", text="Options")

        # Botón para enviar los parámetros
        row = box.row()
        row.operator("view3d.submit_parameters", text="Submit Parameters")

        #Seccion contact points
        box = layout.box()
        box.label(text="Contact Points")

        row = box.row()
        row.operator("view3d.select_contact_point", text="Select Contact Point")
        
        # Cuadro de texto para mostrar las coordenadas del vértice seleccionado
        row = box.row()
        row.prop(context.scene, "contact_point_coordinates", text="Contact Point Coordinates", emboss=False, icon='VIEW3D')


        row = box.row()
        row.operator("view3d.submit_contact_point1", text="Submit Contact Point 1")
        
        row = box.row()
        row.operator("view3d.submit_contact_point2", text="Submit Contact Point 2")

        row = box.row()
        row.operator("view3d.clear_contact_points", text="Clear Contact Points")
        
        # Sección "Constraint Points"
        box = layout.box()
        box.label(text="Constraint Points")

        row = box.row()
        row.operator("view3d.select_constraint_point", text="Select Constraint Point")

        # Cuadro de texto para mostrar las coordenadas del vértice seleccionado
        row = box.row()
        row.prop(context.scene, "constraint_point_coordinates", text="Constraint Point Coordinates", emboss=False, icon='VIEW3D')

        row = box.row()
        row.operator("view3d.submit_constraint_point1", text="Submit Constraint Point 1")

        row = box.row()
        row.operator("view3d.submit_constraint_point2", text="Submit Constraint Point 2")

        row = box.row()
        row.operator("view3d.clear_constraint_points", text="Clear Constraint Points")



        # Sección "Export files"
        box = layout.box()
        box.label(text="Export files")
        
        # Botón de exportación
        row = box.row()
        row.operator("view3d.export_meshes", text="Export files")

class VIEW3D_OT_BrowseFolderOperator(Operator, ImportHelper):
    bl_idname = "view3d.browse_folder"
    bl_label = "Browse Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.selected_folder = self.filepath
        return {'FINISHED'}

class VIEW3D_OT_CreateFolderOperator(Operator):
    bl_idname = "view3d.create_folder"
    bl_label = "Create Folder"
    bl_options = {'REGISTER', 'UNDO'}

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

    def execute(self, context):
        # Cambiar a modo de edición y activar la herramienta "lasso select" con "face select"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = False  # Modo de selección de cara
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = True

        return {'FINISHED'}

class VIEW3D_OT_SubmitSelectionOperator(Operator):
    bl_idname = "view3d.submit_selection"
    bl_label = "Submit Selection"
    bl_options = {'REGISTER', 'UNDO'}

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

import json
class VIEW3D_OT_SubmitParametersOperator(Operator):
    bl_idname = "view3d.submit_parameters"
    bl_label = "Submit Parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Obtener el nombre de la última submalla extraída
        last_submesh_name = context.scene.submesh_name

        # Construir el nombre del archivo STL
        file_name = f"{last_submesh_name}.stl"  # Agregar "/" antes del nombre del archivo

        # Obtener los valores de la fuerza y el método desde el contexto
        force_value = context.scene.force_value
        selected_option = context.scene.selected_option
        focal_point_coordinates = context.scene.focal_point_coordinates

        # Obtener el diccionario existente o crear uno nuevo
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

        # Almacenar los datos en un diccionario
        data = {
            'file': f"/{file_name}",  
            'force': force_value,
            'focalpt': focal_point_coordinates,  # Convertir las coordenadas a una lista de floats
            'method': selected_option
        }

        # Agregar la entrada al diccionario
        muscle_parameters.append(data)  # Utilizar append para agregar un nuevo elemento a la lista

        # Almacenar el diccionario como cadena JSON en la propiedad de la escena
        context.scene["muscle_parameters"] = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)

        # Mostrar el diccionario en la consola
        self.report({'INFO'}, "Stored data:\n" + json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False))
        return {'FINISHED'}






# Definición de la clase VIEW3D_OT_SelectContactPointOperator
class VIEW3D_OT_SelectContactPointOperator(Operator):
    bl_idname = "view3d.select_contact_point"
    bl_label = "Select Contact Point"
    bl_options = {'REGISTER', 'UNDO'}

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

    def execute(self, context):
        # Cambiar a modo de edición y activar la herramienta "vertex select"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.tool_settings.mesh_select_mode[0] = True  # Modo de selección de cara
        bpy.context.tool_settings.mesh_select_mode[1] = False
        bpy.context.tool_settings.mesh_select_mode[2] = False

        return {'FINISHED'}

class VIEW3D_OT_SubmitConstraintPointOperator1(Operator):
    bl_idname = "view3d.submit_constraint_point1"
    bl_label = "Submit Constraint Point 1"
    bl_options = {'REGISTER', 'UNDO'}

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
                muscle_parameters = context.scene.get("muscle_parameters", {})
                
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
                    else:
                        # Solo Constraint Point 1 está presente
                        constraint_pts = [f"    p['axis_pt1'] = {[float(coord) for coord in Constraint_point1.split(',')]}\n"]
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


# Registro de clases y propiedades
def register():
    bpy.utils.register_class(VIEW3D_PT_FilePathPanel)
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

    bpy.types.Scene.Contact_point1 = bpy.props.StringProperty()
    bpy.types.Scene.Contact_point2 = bpy.props.StringProperty()
    bpy.types.Scene.Constraint_point1 = bpy.props.StringProperty()
    bpy.types.Scene.Constraint_point2 = bpy.props.StringProperty()
    bpy.types.Scene.selected_main_object = bpy.props.StringProperty(name="Selected Main Object")
    bpy.types.Scene.muscle_parameters = bpy.props.StringProperty()


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
        description="Value of the force",
    )

    bpy.types.Scene.selected_option = EnumProperty(
        items=[
            ('U', "Uniform-traction", "U: Uniform-traction"),
            ('T', "Tangential-traction", "T: Tangential-traction"),
            ('TN', "Tangential-plus-normal-traction", "TN: Tangential-plus-normal-traction"),
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

# Eliminación de clases y propiedades
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_FilePathPanel)
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

if __name__ == "__main__":
    register()
