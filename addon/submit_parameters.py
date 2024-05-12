#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bpy
import json
from bpy.types import Operator


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
        new_folder_name = context.scene.new_folder_name
        collection = bpy.data.collections.new(new_folder_name)

        if not context.scene.focal_point_coordinates or context.scene.focal_point_coordinates == "":
            self.report({'ERROR'}, "Please select a vertex as the Focal Point before submitting the parameters.")
            return {'CANCELLED'}
        else:
            focal_point_coordinates = [float(coord) for coord in context.scene.focal_point_coordinates.split(",")]

        # Create or clear the 'focal points' collection
        if 'Focal points' in bpy.data.collections:
            # Unlink the collection from all scenes
            for scene in bpy.data.scenes:
                if 'Focal points' in scene.collection.children:
                    scene.collection.children.unlink(bpy.data.collections['Focal points'])
            # Delete all objects in the collection
            for obj in bpy.data.collections['Focal points'].objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            # Delete the collection
            bpy.data.collections.remove(bpy.data.collections['Focal points'])


        # Create a new 'focal points' collection
        collection = bpy.data.collections.new('Focal points')
        bpy.context.scene.collection.children.link(collection)
        
        
        # Convert coords to JSON
        muscle_parameters_str = context.scene.get("muscle_parameters", "[]")
        muscle_parameters = json.loads(muscle_parameters_str)

        # Store values into a dictionary
        data = {
            'file': f"f'{{path}}/" + f"{file_name}'",  
            'force': force_value,
            'focalpt': focal_point_coordinates,  
            'method': selected_option
        }

        # Check if the name already exists in the 'file' field of any element in muscle_parameters
        if any(param['file'] == data['file'] for param in muscle_parameters):
            self.report({'ERROR'}, "New element not added, a focal point with this name already exists. Please delete the element from the scene and press 'update parameters'.")
            return {'CANCELLED'}
        else:
            muscle_parameters.append(data)

        json_str = json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False)
        context.scene["muscle_parameters"] = json_str


        # Create a new object for each element in the dictionary
        for data in muscle_parameters:
            mesh = bpy.data.meshes.new('mesh')  # create a new mesh
            name = data['file'][9:-5] + '_focal'
            obj = bpy.data.objects.new(name, mesh)  # create a new object using the mesh

            # Link the object to the scene
            bpy.context.collection.objects.link(obj)

            # Create a single vertex at the 'focalpt' position
            mesh.from_pydata([data['focalpt']], [], [])

            # Get the original collection of the object
            original_collection = obj.users_collection[0]

            # Add the object to the 'focal points' collection
            bpy.data.collections['Focal points'].objects.link(obj)

            # Remove the object from the original collection
            original_collection.objects.unlink(obj)

        context.scene.focal_point_coordinates = ""
        self.report({'INFO'}, "Stored data:\n" + json.dumps(muscle_parameters, indent=4, separators=(',', ': '), ensure_ascii=False))
        return {'FINISHED'}