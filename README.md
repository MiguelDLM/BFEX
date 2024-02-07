# Fossils For Blender

Fossils For Blender is an add-on designed to facilitate the creation of files required for Finite Element Analysis (FEA) within Blender. The add-on offers a range of functionalities to streamline the process, allowing users to:
![Addon Menu](https://github.com/MiguelDLM/Fossils-File-Maker/raw/main/Addon%20menu.png)
## Features

1. **Create Muscle Attachment Surfaces:**
   - Generate sub-meshes/samples from the original mesh (bone) for use as muscle attachment surfaces.

2. **Generate Parameter Script:**
   - Create a Python script file containing all the parameters necessary for each muscle and model specifications.

3. **Export in Required Format:**
   - Export files in the necessary format for use in Finite Element Analysis.

4. **Preview Analysis Parameters:**
   - Provide a preview of the parameters used to execute the analysis.

## Installation

To install the add-on, follow these steps:

1. Download the Python file, `FossilFileMaker.py`.
2. In Blender, navigate to Edit > Preferences > Add-ons and click the "Install" button.
3. Locate and select the Python file.
4. Activate the add-on by checking the corresponding checkbox.

## Before You Start

### Check Mesh Quality

Ensure your mesh is free of errors by utilizing the 3D print add-on and clicking "Check All." Verify that your mesh does not contain errors such as Non-Manifold Edges, Bad Contiguous Edges, Intersect Faces, Zero Faces, Zero Edges, Non-Flat Faces, Thin Faces, or Sharp Edges. All error counts should be zero; otherwise, Fossils may crash. Overhang Faces are allowed in Fossils.

### Verify Correct Orientation

Blender employs a Z-Up world interface, where the Z-axis points upward. Some software, like MeshLab, uses a Y-Up world interface. Fossils assumes a Y-Up system, so ensure your model is correctly oriented before starting. The add-on provides a "Rotate Y to Z" button to adjust the orientation if needed.

## Usage

1. **Folder Setup:**
   - Click "Browse Folder" to select the destination for generated files.
   - Enter a name for the project/folder.
   - Click "Create New Folder" to establish a new folder and collection with the provided name.

2. **Main Mesh Selection:**
   - In Object mode, select the main mesh/bone for FEA.
   - Click "Submit Main Bone for FEA."

3. **Muscle Attachment Surface Creation:**
   - Type the name of the muscle/sub-mesh to be subtracted.
   - In Object mode, select the main bone/object.
   - Click "Start Selection" to enter Edit mode and activate the lasso selection tool.
   - Select surfaces for extraction and click "Submit Selection" to create a new submesh in the collection.

4. **Force Direction Setup:**
   - Click "Select Focal Point" to choose a point on a reference object where the force will be applied.
   - Click "Submit Focal Point" to store the coordinates.

5. **Input Force and Loading Scenario:**
   - Enter the force applied by the muscle and select the loading scenario (Uniform, Tangential, or Tangential plus Normal Traction).

6. **Parameter Submission:**
   - Click "Submit Parameters" to store all values (file name, focal point, force, and loading scenario) in a JSON dictionary.

7. **Undo Last Submission:**
   - If a mistake is made, click "Delete Last Muscle Attachment and Parameters" to remove the last values from the JSON dictionary.

8. **Repeat for Multiple Muscles:**
   - Repeat steps 3 to 7 for each muscle to be modeled.

9. **Contact and Constraint Points:**
   - Click "Select Contact Points" to switch to Edit mode and select vertices where loading forces will be applied.
   - Choose movement restrictions in the contact points.

10. **Export and Run Fossils:**
    - Set material properties like Young's Modulus and Poisson's Ratio.
    - Click "Export Files" to export submeshes and the Python script for Fossils.
    - Click "Run Fossils" to initiate the FEA analysis.

11. **Results and Visualization:**
    - Use buttons like "Open FEA Results Folder" and "Visual Elements" to navigate and visualize results.
   
## Common Issues

Fossils may encounter errors during execution if files are not generated correctly. In most cases, Fossils closes without warnings. To diagnose and resolve issues, examine the `stdout.txt` file located inside the workspace folder (next to the folder where meshes were stored). Below are common errors and suggested solutions:

### Error: `ZeroDivisionError: float division by zero`

This error occurs when sub-meshes contain zero faces (empty meshes). Before clicking "Export," ensure that the new collection and all elements inside are visible.

### Error: `0 successfully identified`
	identify_nodes_SaP...
    sweep and prune done in X.XX seconds
	(XXXX tests instead of XXXXX)
	1 to be identified
	0 successfully identified
This error occurs when nodes (contact/constraint points) are not identified.
#### Option 1
 Check your coordinate system and use the "Visual Elements" section to view the coordinates of the contact and constraint points. If the coordinates appear in a different location, you may not have applied the rotation changes to your meshes. Go to Object > Apply > Rotation or Object > Apply > Translation (Ctrl+A).

#### Option 2
Ensure that you selected the contact/constraint points over the main mesh. If you selected points on a different mesh, Fossils won't be able to find them.

### Error: Fossils don't start

Ensure that Fossils is installed in the directory: `~\AppData\Local\Programs\Fossils\fossils.exe`

## Extra

If you experience low performance in GMSH (software used for Fossils to visualize the results), it might be necessary to remove some elements from the scene to improve performance. You can do this before opening the results by editing the .opt file.

To simplify this process, you can download the `script_modify_opt.py` file and the `drag_and_drop_opt_here.bat` file. Copy both files to your results folder. To automatically modify the OPT file, simply drag and drop your OPT file onto the bat file. This will add some lines to hide certain elements in the visualization.

[Download script_modify_opt.py](https://github.com/MiguelDLM/Fossils-File-Maker/blob/main/script_modify_opt.py)  
[Download drag_and_drop_opt_here.bat](https://github.com/MiguelDLM/Fossils-File-Maker/blob/main/drag%20and%20drop%20opt%20here.bat)

## Contributing

We welcome pull requests. For major changes, please open an issue first to discuss the proposed changes. Be sure to update tests as appropriate.
