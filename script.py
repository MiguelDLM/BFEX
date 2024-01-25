bl_info = {
    "name": "Fossil File generator",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
from bpy.types import Operator, Panel
from bpy.props import StringProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
import os
import math

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
        
        # Sección "Rotate Elements"
        box = layout.box()
        box.label(text="Rotate Elements")

        row = box.row()
        row.label(text="Rotate elements around:")

        row = box.row()
        row.operator("view3d.rotate_elements", text="Rotate Y to Z")

        # Sección "Extract Surfaces"
        box = layout.box()
        box.label(text="Extract Surfaces")

        row = box.row()
        row.prop(context.scene, "submesh_name", text="Submesh Name")

        row = box.row()
        row.operator("view3d.start_selection", text="Start Selection")

        row = box.row()
        row.operator("view3d.submit_selection", text="Submit Selection")

        # Botón de exportación
        row = box.row()
        row.operator("view3d.export_meshes", text="Export Meshes")
        
class VIEW3D_OT_RotateElementsOperator(Operator):
    bl_idname = "view3d.rotate_elements"
    bl_label = "Rotate Elements"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Seleccionar todos los objetos en la escena
        bpy.ops.object.select_all(action='SELECT')

        # Rotar todos los objetos en la escena (o en la colección activa) de Y a Z
        for obj in bpy.context.selected_objects:
            obj.rotation_euler.rotate_axis("X", math.radians(-90))  
            obj.rotation_euler.rotate_axis("Z", math.radians(-180))

        self.report({'INFO'}, "Elements rotated from Y to Z")

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

class VIEW3D_OT_ExportMeshesOperator(Operator):
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

                if collection:
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

                    self.report({'INFO'}, f"Meshes exported to: {file_path}")

                else:
                    self.report({'ERROR'}, f"Collection '{collection_name}' not found")

            except Exception as e:
                self.report({'ERROR'}, f"Failed to export meshes: {e}")

        else:
            self.report({'ERROR'}, "Please provide a valid file path")

        return {'FINISHED'}



def register():
    bpy.utils.register_class(VIEW3D_PT_FilePathPanel)
    bpy.utils.register_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.register_class(VIEW3D_OT_RotateElementsOperator)
    
    bpy.types.Scene.selected_folder = bpy.props.StringProperty(
        name="Selected Folder",
        default="",
        description="Selected folder for file storage"
    )

    bpy.types.Scene.new_folder_name = bpy.props.StringProperty(
        name="New Folder Name",
        default="",
        description="Name for the new folder to be created"
    )

    bpy.types.Scene.submesh_name = bpy.props.StringProperty(
        name="Submesh Name",
        default="",
        description="Name for the submesh to be created"
    )


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_FilePathPanel)
    bpy.utils.unregister_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.unregister_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RotateElementsOperator)

    del bpy.types.Scene.selected_folder
    del bpy.types.Scene.new_folder_name
    del bpy.types.Scene.submesh_name

if __name__ == "__main__":
    register()
