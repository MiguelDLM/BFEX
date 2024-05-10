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

import sys

# the following code allows us to reload the add-on without restarting Blender
# this is useful during development
# see https://blenderartists.org/t/how-to-reload-blender-addon-with-nested-modules-using-reload-scripts/1477986
if "bpy" in locals():
    if __name__ in sys.modules:
        del sys.modules[__name__]

    dotted = __name__ + "."
    for name in tuple(sys.modules):
        if name.startswith(dotted):
            del sys.modules[name]

import bpy
from bpy.types import Operator, PropertyGroup, UIList
from bpy.props import StringProperty, EnumProperty, FloatProperty, CollectionProperty, IntProperty
import os
import math
import json
import subprocess
import ctypes
import mathutils
import random
from mathutils import Vector, kdtree

from .menu import VIEW3D_PT_FilePathPanel_PT
from .browse_folder import VIEW3D_OT_BrowseFolderOperator
from .create_folder_and_collection import VIEW3D_OT_CreateFolderOperator
from .submit_main_object import VIEW3D_OT_SubmitMainObjectOperator
from .start_selection import VIEW3D_OT_StartSelectionOperator
from .submit_selection import VIEW3D_OT_SubmitSelectionOperator
from .select_vertex import VIEW3D_OT_SelectVertexOperator
from .select_focal_point import VIEW3D_OT_SelectFocalPointOperator
from .submit_focal import VIEW3D_OT_SubmitFocalPointOperator
from .submit_parameters import VIEW3D_OT_SubmitParametersOperator
from .refresh_parameters import VIEW3D_OT_RefreshParametersOperator
from .submit_fixation import VIEW3D_OT_SubmitFixationPointOperator
from .export_meshes import VIEW3D_OT_ExportMeshesOperator
from .run_fossils import VIEW3D_OT_RunFossilsOperator, VIEW3D_OT_OpenFEAResultsFolderOperator
from .visual_elements import VIEW3D_OT_VisualElementsOperator
from .submit_sample import VIEW3D_OT_SubmitSampleOperator
from .sensitivity_analysis import VIEW3D_OT_ExportSensitivityAnalysisOperator
from .refresh_fixations import View3D_OT_Refresh_FixationsOperator



# Utilities 
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)
    


def register():
    bpy.utils.register_class(VIEW3D_PT_FilePathPanel_PT)
    bpy.utils.register_class(VIEW3D_OT_BrowseFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_CreateFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.register_class(VIEW3D_OT_StartSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSelectionOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectVertexOperator)
    bpy.utils.register_class(VIEW3D_OT_SelectFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitFocalPointOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitParametersOperator)
    bpy.utils.register_class(VIEW3D_OT_RefreshParametersOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitFixationPointOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportMeshesOperator)
    bpy.utils.register_class(VIEW3D_OT_RunFossilsOperator)
    bpy.utils.register_class(VIEW3D_OT_OpenFEAResultsFolderOperator)
    bpy.utils.register_class(VIEW3D_OT_VisualElementsOperator)
    bpy.utils.register_class(VIEW3D_OT_SubmitSampleOperator)
    bpy.utils.register_class(VIEW3D_OT_ExportSensitivityAnalysisOperator)
    bpy.utils.register_class(View3D_OT_Refresh_FixationsOperator)
    

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
           
    def update_checkboxes(self, context):
        if context.scene.display_existing_results:
            context.scene.open_results_when_finish = False

        if context.scene.open_results_when_finish:
            context.scene.display_existing_results = False

    bpy.types.Scene.selected_main_object = bpy.props.StringProperty(
        name="Selected Main Object",
        default="",
        description="Name or identifier for the selected main object"
    )

    bpy.types.Scene.muscle_parameters = bpy.props.StringProperty(
        name="Muscle Parameters",
        description="Parameters for muscles in a specific format"
    )

    bpy.types.Scene.fixations = bpy.props.StringProperty(
        name="Fixations",
        description="Fixations for the model in a specific format"
    )

    bpy.types.Scene.fixation_x = bpy.props.BoolProperty(
        name="Fixation X",
        default=False,
        description="Enable or disable X axis for fixation points"
    )

    bpy.types.Scene.fixation_y = bpy.props.BoolProperty(
        name="Fixation Y",
        default=False,
        description="Enable or disable Y axis for fixation points"
    )

    bpy.types.Scene.fixation_z = bpy.props.BoolProperty(
        name="Fixation Z",
        default=False,
        description="Enable or disable Z axis for fixation points"
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
            ('D', "Directional-Tractional", "D: Directional-Tractional"),
            ('N', "Normal-traction", "N: Normal-traction"), 
        ],
        name="Options",
        default='T+N',
        description="Select an option",
    )

    bpy.types.Scene.fixation_type = EnumProperty(
        items=[
            ('contact', "Contact point", "Contact: Contact point (i.e. bite point)"),
            ('constraint', "Constraint point", "Constraint: Constraint point(i.e. condyle point)"),
        ],
        name="Fixation Type",
        default='contact',
        description="Select a fixation type",
    )

    bpy.types.Scene.fixation_point_coordinates = StringProperty(
        name="Contact Point Coordinates",
        default="",
        description="Coordinates of the selected Contact Point",
    )
    
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
    bpy.utils.unregister_class(VIEW3D_OT_SubmitFixationPointOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitMainObjectOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RefreshParametersOperator)
    bpy.utils.unregister_class(VIEW3D_OT_RunFossilsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_OpenFEAResultsFolderOperator)
    bpy.utils.unregister_class(VIEW3D_OT_VisualElementsOperator)
    bpy.utils.unregister_class(VIEW3D_OT_ExportSensitivityAnalysisOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SubmitSampleOperator)
    bpy.utils.unregister_class(VIEW3D_OT_SelectVertexOperator)
    bpy.utils.unregister_class(View3D_OT_Refresh_FixationsOperator)


    del bpy.types.Scene.selected_folder
    del bpy.types.Scene.new_folder_name
    del bpy.types.Scene.submesh_name
    del bpy.types.Scene.focal_point_coordinates
    del bpy.types.Scene.force_value
    del bpy.types.Scene.selected_option
    del bpy.types.Scene.fixation_x
    del bpy.types.Scene.fixation_y
    del bpy.types.Scene.fixation_z
    del bpy.types.Scene.display_existing_results
    del bpy.types.Scene.open_results_when_finish
    del bpy.types.Scene.run_as_admin
    del bpy.types.Scene.show_constraint_points
    del bpy.types.Scene.show_contact_points
    del bpy.types.Scene.show_attachment_areas
    del bpy.types.Scene.show_force_directions
    del bpy.types.Scene.selected_main_object
    del bpy.types.Scene.muscle_parameters
    del bpy.types.Scene.fixations
    del bpy.types.Scene.fixation_type
    del bpy.types.Scene.fixation_point_coordinates
    del bpy.types.Scene.youngs_modulus
    del bpy.types.Scene.poissons_ratio
    del bpy.types.Scene.sample_name
    del bpy.types.Scene.scale_factor
    del bpy.types.Scene.total_faces
    

if __name__ == "__main__":
    register()
