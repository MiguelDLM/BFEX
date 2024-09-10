import shutil
import tempfile
import subprocess
import os
import bpy
import platform

class InstantMeshesRemesh(bpy.types.Operator):
    """Remesh by using the Instant Meshes program"""
    bl_idname = "object.instant_meshes_remesh"
    bl_label = "Instant Meshes Remesh"
    bl_options = {'REGISTER', 'UNDO'}

    loc = None
    rot = None
    scl = None
    meshname = None

    def execute(self, context):
        return instant_meshes_remesh(self, context)

def instant_meshes_remesh(operator, context):
    # Verificar si el complemento de exportación de OBJ está habilitado
    if not bpy.ops.wm.obj_export.poll():
        operator.report({'ERROR'}, "El complemento de exportación de OBJ no está habilitado.")
        return {'CANCELLED'}

    # Definir la ruta del ejecutable de Instant Meshes dependiendo del sistema operativo
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Windows":
        exe = os.path.join(addon_dir, 'instant_remesh', 'Instant Meshes.exe')
    else:
        exe = os.path.join(addon_dir, 'instant_remesh', 'Instant Meshes')

    orig = os.path.join(tempfile.gettempdir(), 'original.obj')
    output = os.path.join(tempfile.gettempdir(), 'out.obj')

    exported = False
    deterministic = False
    dominant = False
    intrinsic = False
    boundaries = False
    crease = 0
    verts = context.scene.instant_vertex_count
    smooth = context.scene.instant_smooth
    remeshIt = True
    openUI = False

    if remeshIt:
        if not exported:
            try:
                os.remove(orig)
            except:
                pass
            meshname = bpy.context.active_object.name
            mesh = bpy.context.active_object
            bpy.ops.wm.obj_export(
                filepath=orig,
                check_existing=False,
                filter_blender=False,
                filter_backup=False,
                filter_image=False,
                filter_movie=False,
                filter_python=False,
                filter_font=False,
                filter_sound=False,
                filter_text=False,
                filter_archive=False,
                filter_btx=False,
                filter_collada=False,
                filter_alembic=False,
                filter_usd=False,
                filter_obj=False,
                filter_volume=False,
                filter_folder=True,
                filter_blenlib=False,
                filemode=8,
                display_type='DEFAULT',
                sort_method='DEFAULT',
                export_animation=False,
                start_frame=-2147483648,
                end_frame=2147483647,
                forward_axis='NEGATIVE_Z',
                up_axis='Y',
                global_scale=1.0,
                apply_modifiers=True,
                export_eval_mode='DAG_EVAL_VIEWPORT',
                export_selected_objects=True,
                export_uv=True,
                export_normals=True,
                export_colors=False,
                export_materials=True,
                export_pbr_extensions=False,
                path_mode='AUTO',
                export_triangulated_mesh=False,
                export_curves_as_nurbs=False,
                export_object_groups=False,
                export_material_groups=False,
                export_vertex_groups=False,
                export_smooth_groups=False,
                smooth_group_bitflags=False,
                filter_glob='*.obj;*.mtl'
            )

            exported = True

        mesh = bpy.data.objects[meshname]
        mesh.hide_viewport = False
        options = ['-c', str(crease),
                   '-v', str(verts),
                   '-S', str(smooth),
                   '-o', output]
        if deterministic:
            options.append('-d')
        if dominant:
            options.append('-D')
        if intrinsic:
            options.append('-i')
        if boundaries:
            options.append('-b')

        cmd = [exe] + options + [orig]

        print(cmd)

        if openUI:
            os.chdir(os.path.dirname(orig))
            shutil.copy2(orig, output)
            subprocess.run([exe, output])
            openUI = False
        else:
            subprocess.run(cmd)

        bpy.ops.wm.obj_import(
            filepath=output,
            directory='',
            files=[],
            check_existing=False,
            filter_blender=False,
            filter_backup=False,
            filter_image=False,
            filter_movie=False,
            filter_python=False,
            filter_font=False,
            filter_sound=False,
            filter_text=False,
            filter_archive=False,
            filter_btx=False,
            filter_collada=False,
            filter_alembic=False,
            filter_usd=False,
            filter_obj=False,
            filter_volume=False,
            filter_folder=True,
            filter_blenlib=False,
            filemode=8,
            display_type='DEFAULT',
            sort_method='DEFAULT',
            global_scale=1.0,
            clamp_size=0.0,
            forward_axis='NEGATIVE_Z',
            up_axis='Y',
            use_split_objects=False,
            use_split_groups=False,
            import_vertex_groups=False,
            validate_meshes=True,
            collection_separator='',
            filter_glob='*.obj;*.mtl'
        )
        imported_mesh = bpy.context.selected_objects[0]
        
        # Eliminar la malla original
        original_collection = mesh.users_collection[0]
        bpy.data.objects.remove(mesh, do_unlink=True)
        
        # Renombrar la malla importada
        imported_mesh.name = meshname
        
        # Mover la malla importada a la colección original
        for collection in imported_mesh.users_collection:
            collection.objects.unlink(imported_mesh)
        original_collection.objects.link(imported_mesh)
        
        #for i in mesh.data.materials:
        #    imported_mesh.data.materials.append(i)
        for edge in imported_mesh.data.edges:
            edge.use_edge_sharp = False
        for other_obj in bpy.data.objects:
            other_obj.select_set(state=False)
        imported_mesh.select_set(state=True)
        #imported_mesh.active_material.use_nodes = False
        #imported_mesh.data.use_auto_smooth = False

        bpy.ops.object.shade_flat()
        bpy.ops.mesh.customdata_custom_splitnormals_clear()

        bpy.context.space_data.overlay.show_wireframes = True

        return {'FINISHED'}
    else:
        return {'FINISHED'}

classes = (
    InstantMeshesRemesh,
)

def register():
    from bpy.utils import register_class
    for c in classes:
        bpy.utils.register_class(c)

    try:
        os.remove(os.path.join(tempfile.gettempdir(), 'original.obj'))
        os.remove(os.path.join(tempfile.gettempdir(), 'out.obj'))
    except:
        pass

def unregister():
    from bpy.utils import unregister_class

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()