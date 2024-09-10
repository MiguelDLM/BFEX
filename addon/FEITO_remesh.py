import bpy
from bpy.types import Operator
import bmesh
import math
from .instant_remesh import instant_meshes_remesh

class VIEW3D_OT_FEITO_remesh(Operator):
    bl_idname = "view3d.feito_remesh"
    bl_label = "FEITO Remesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
    
        selected_main_object = context.scene.selected_main_object
        main_object = bpy.data.objects.get(selected_main_object)
        sensitivity_collection_name = "Sensitivity Analysis"
        sensitivity_collection = bpy.data.collections.get(sensitivity_collection_name)
        scene = context.scene

        # Check if the collection already exists
        if sensitivity_collection is None:
            # If it doesn't exist, create it
            sensitivity_collection = bpy.data.collections.new(sensitivity_collection_name)
            bpy.context.scene.collection.children.link(sensitivity_collection)
        else:
            # If it already exists, empty the collection by removing all objects
            for obj in sensitivity_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        if main_object is None:
            self.report({'ERROR'}, "Main object not found. Please submit a main object first.")
            return {'CANCELLED'}

        # Create an independent copy of the main object
        copy_main_object = main_object.copy()
        copy_main_object.data = main_object.data.copy()
        copy_main_object.animation_data_clear()

        # Move the copy to the new collection
        sensitivity_collection.objects.link(copy_main_object)
        obj = copy_main_object
        
        # Select the copy
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        # Set the copy as the active object
        bpy.context.view_layer.objects.active = obj

        if scene.remesh_mode == 'VOXEL':
            voxel_size = obj.data.remesh_voxel_size
            voxel_adaptivity = obj.data.remesh_voxel_adaptivity
            bpy.ops.object.voxel_remesh()
            self.report({'INFO'}, f"Applying Voxel Remesh with size {voxel_size} and adaptivity {voxel_adaptivity}")

        elif scene.remesh_mode == 'QUAD':
            quad_target_faces = scene.quad_target_faces
            print(f"quad_target_faces from scene: {quad_target_faces}")
            
            # Verificar si el valor es válido
            if not isinstance(quad_target_faces, int) or quad_target_faces <= 0:
                self.report({'ERROR'}, f"Invalid target faces value: {quad_target_faces}")
                return {'CANCELLED'}
            
            print(f"Applying Quad Remesh with target faces: {quad_target_faces}")
            try:
                bpy.ops.object.quadriflow_remesh(
                    use_mesh_symmetry=True,
                    use_preserve_sharp=False,
                    use_preserve_boundary=False,
                    preserve_attributes=False,
                    smooth_normals=False,
                    mode='FACES',
                    target_faces=quad_target_faces,
                    seed=0
                )
                self.report({'INFO'}, f"Applying Quad Remesh with target faces {quad_target_faces}")
            except Exception as e:
                self.report({'ERROR'}, f"Quad Remesh failed: {str(e)}")
                print(f"Quad Remesh failed: {str(e)}")

        elif scene.remesh_mode == 'INSTANT':
            vertex_count = scene.instant_vertex_count
            print(f"Applying Instant Remesh with vertex count: {vertex_count}")
            instant_meshes_remesh(self, context)
            obj = bpy.context.selected_objects[0]

            self.report({'INFO'}, f"Applying Instant Remesh with vertex count {vertex_count}")

        elif scene.remesh_mode == 'MODIFIER':
            self.report({'INFO'}, f"Applying Remesh Modifier with octree depth {scene.modifier_octree_depth} and scale {scene.modifier_scale}")
            # Aquí iría el código para aplicar el remesh Modifier
        elif scene.remesh_mode == 'DECIMATE':
            self.report({'INFO'}, f"Applying Decimate Modifier with ratio {scene.scale_factor}")

        # Calcular la desviación estándar de las áreas de las caras
        std_dev_area, num_faces = self.calculate_face_area_std_dev(obj)
        self.report({'INFO'}, f"Standard deviation of face areas: {std_dev_area:.6f}, Number of faces: {num_faces}")

        return {'FINISHED'}

    def calculate_face_area_std_dev(self, obj):
        # Crear un BMesh a partir del objeto
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Calcular las áreas de las caras
        face_areas = [face.calc_area() for face in bm.faces]

        # Limpiar el BMesh
        bm.free()

        # Verificar si hay caras en la malla
        if not face_areas:
            self.report({'ERROR'}, "No faces found in the mesh")
            return 0.0, 0

        # Calcular la media de las áreas
        mean_area = sum(face_areas) / len(face_areas)

        # Calcular la varianza
        variance = sum((area - mean_area) ** 2 for area in face_areas) / len(face_areas)

        # Calcular la desviación estándar
        std_dev = math.sqrt(variance)
        print(f"Mean area: {mean_area}")
        print(f"Variance: {variance}")
        print(f"Standard deviation: {std_dev}")

        return std_dev, len(face_areas)
