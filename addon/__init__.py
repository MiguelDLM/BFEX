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

from .menu import VIEW3D_PT_FEITOMenu_PT
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
from .submit_load import View3D_OT_Submit_load
from .refresh_loads import VIEW3D_OT_RefreshLoadsOperator   
from .submit_focal_load import View3D_OT_SubmitFocalLoad



# Utilities 
def set_object_mode(obj, mode):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode=mode)
    


def register():
    bpy.utils.register_class(VIEW3D_PT_FEITOMenu_PT)
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
    bpy.utils.register_class(View3D_OT_Submit_load)
    bpy.utils.register_class(View3D_OT_SubmitFocalLoad)
    bpy.utils.register_class(VIEW3D_OT_RefreshLoadsOperator)
    
    

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
        name="Fixation Point Coordinates",
        default="",
        description="Coordinates of the selected Fixation Point",
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
    bpy.types.Scene.load_input_method = bpy.props.EnumProperty(
        name="Load Input Method",
        description="Choose how to define loads",
        items=[
            ('VERTICES', "Use Vertices", "Define loads using vertices"),
            ('MANUAL', "Define Manually", "Manually define load values"),
        ],
        default='MANUAL',
    )
    bpy.types.Scene.load_name = bpy.props.StringProperty(
        name="Load Name",
        default="",
        description="Name for the load"
    )
    bpy.types.Scene.load_value = bpy.props.FloatProperty(
        name="Load Value",
        default=0.0,
        min=0.0,
        description="Value for the load"
    )
    bpy.types.Scene.load_x = bpy.props.FloatProperty(
        name="X",
        default=0.0,
        description="Load value for X axis",
        precision=2,
    )
    bpy.types.Scene.load_y = bpy.props.FloatProperty(
        name="Y",
        default=0.0,
        description="Load value for Y axis",
        precision=2,
    )
    bpy.types.Scene.load_z = bpy.props.FloatProperty(
        name="Z",
        default=0.0,
        description="Load value for Z axis",
        precision=2,
    )
    bpy.types.Scene.load_force = bpy.props.FloatProperty(
            name="Load Force",
            default=0.0,
            description="Load force value",
        )
    bpy.types.Scene.loads = bpy.props.StringProperty(

        name="Loads",
        description="Loads for the model in a specific format"
    )
    bpy.types.Scene.loads_focal = bpy.props.StringProperty(
        name="Loads Focal",
        description="Loads for the model in a specific format"
    )

    bpy.types.Scene.arrows_size = bpy.props.FloatProperty(
        name="Arrows Size",
        default=1,
        min=0.01,
        description="Size of the arrows for visualization"
    )

def unregister():
    classes = [
        VIEW3D_PT_FEITOMenu_PT,
        VIEW3D_OT_StartSelectionOperator, 
        VIEW3D_OT_SubmitSelectionOperator,
        VIEW3D_OT_BrowseFolderOperator,
        VIEW3D_OT_CreateFolderOperator,
        VIEW3D_OT_ExportMeshesOperator,
        VIEW3D_OT_SelectFocalPointOperator,
        VIEW3D_OT_SubmitFocalPointOperator,
        VIEW3D_OT_SubmitParametersOperator,
        VIEW3D_OT_SubmitFixationPointOperator,
        VIEW3D_OT_SubmitMainObjectOperator,
        VIEW3D_OT_RefreshParametersOperator,
        VIEW3D_OT_RunFossilsOperator,
        VIEW3D_OT_OpenFEAResultsFolderOperator,
        VIEW3D_OT_VisualElementsOperator,
        VIEW3D_OT_ExportSensitivityAnalysisOperator,
        VIEW3D_OT_SubmitSampleOperator,
        VIEW3D_OT_SelectVertexOperator,
        View3D_OT_Refresh_FixationsOperator,
        View3D_OT_Submit_load,
        View3D_OT_SubmitFocalLoad,
        VIEW3D_OT_RefreshLoadsOperator,
    ]
    
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f"Error unregistering class {cls.__name__}: {e}")

    properties = [
        "selected_folder",
        "new_folder_name",
        "submesh_name",
        "focal_point_coordinates",
        "force_value",
        "selected_option",
        "fixation_x",
        "fixation_y",
        "fixation_z",
        "display_existing_results",
        "open_results_when_finish",
        "run_as_admin",
        "show_constraint_points",
        "show_contact_points",
        "show_attachment_areas",
        "show_force_directions",
        "selected_main_object",
        "muscle_parameters",
        "fixations",
        "fixation_type",
        "fixation_point_coordinates",
        "youngs_modulus",
        "poissons_ratio",
        "sample_name",
        "scale_factor",
        "total_faces",
        "load_input_method",
    ]
    
    for prop in properties:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)

    

if __name__ == "__main__":
    register()
