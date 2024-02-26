#!/usr/bin/env python3.11

import trimesh
import numpy as np
import os
from scipy.spatial import cKDTree

# Get a list of all .obj, .ply and .stl files in the current directory
mesh_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith(('.obj', '.ply', '.stl'))]

# Print the list of mesh files and ask the user to select the base mesh
print("Available mesh files:")
for i, filename in enumerate(mesh_files):
    print(f"{i + 1}. {filename}")
base_mesh_index = int(input("Please select the number corresponding to the base mesh file: ")) - 1
base_mesh_filename = mesh_files[base_mesh_index]

# Load the base mesh
base_mesh = trimesh.load_mesh(base_mesh_filename)

# Ask the user to select the reference meshes
reference_mesh_indices = list(map(int, input("Please select the numbers corresponding to the reference mesh files (separated by commas): ").split(',')))
reference_mesh_filenames = [mesh_files[i - 1] for i in reference_mesh_indices]

for i, reference_mesh_filename in enumerate(reference_mesh_filenames):
    print(f"Processing reference mesh {i + 1} of {len(reference_mesh_filenames)}...")

    # Load the reference mesh
    reference_mesh = trimesh.load_mesh(reference_mesh_filename.strip())

    # Get the coordinates of the vertices of the two meshes
    vertices_reference = np.array([v for v in reference_mesh.vertices])

    # For each vertex in the reference mesh, find the nearest point on the surface of the base mesh
    nearest_points = base_mesh.nearest.on_surface(vertices_reference)[0]

    # Create a KDTree for the nearest points
    tree = cKDTree(nearest_points)

    # For each face in the base mesh, check if at least one of its vertices is among the nearest points
    # Allow a small tolerance in the match
    tolerance = 0.8
    selected_faces = [f for f in base_mesh.faces if any(tree.query(base_mesh.vertices[v], k=1)[0] <= tolerance for v in f)]

    selected_face_indices = [i for i, f in enumerate(base_mesh.faces) if any(tree.query(base_mesh.vertices[v], k=1)[0] <= tolerance for v in f)]

    new_mesh = base_mesh.submesh([selected_face_indices])[0]

    # Split the new mesh into connected components
    connected_components = new_mesh.split(only_watertight=False)

    # Find the largest component (the one with the most faces)
    largest_component = max(connected_components, key=lambda component: len(component.faces))

    # Create a subfolder with the name of the base mesh if it does not exist
    output_folder = os.path.splitext(base_mesh_filename)[0]
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save the largest component of the mesh in an STL file in the subfolder
    largest_component.export(f'{output_folder}/{os.path.splitext(os.path.basename(reference_mesh_filename.strip()))[0]}.stl')

print("All reference meshes processed.")

# Save the base mesh as an STL file in the final folder
base_mesh.export(f'{output_folder}/{os.path.splitext(os.path.basename(base_mesh_filename))[0]}.stl')
