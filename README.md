# BFEX - Blender FEA Exporter

BFEX is an add-on designed to facilitate the creation of files required for Finite Element Analysis (FEA) within Blender. The add-on offers a range of functionalities to streamline the process, allowing users to:

![Addon Menu](https://github.com/MiguelDLM/BFEX/blob/main/Addon%20menu.png)

## Features

1. **Create Muscle Attachment Surfaces:**
   - Generate sub-meshes/samples from the original mesh (bone) for use as muscle attachment surfaces.

2. **Generate Parameter Script:**
   - Create a Python script file containing all the parameters necessary for each muscle and model specifications.

3. **Export in Required Format:**
   - Export files in the necessary format for use in Finite Element Analysis.

4. **Preview Analysis Parameters:**
   - Provide a preview of the parameters used to execute the analysis.

5. **Launch Fossils:**
   - Run the FEA software Fossils directly from Blender.

## Installation

To install the add-on, follow these steps:

1. Download the Add-on folder from the repository and compress it into a ZIP file or download the zip file directly from the releases [here](https://github.com/MiguelDLM/BFEX/releases).
2. In Blender, navigate to Edit > Preferences > Get Extensions, click on the right corner drop-down menu, and select "Install from disk."
3. Locate and select the zip file.
4. Activate the add-on by checking the corresponding checkbox.

## Before You Start

### Check Mesh Quality

Ensure your mesh is free of errors by utilizing the 3D print add-on and clicking "Check All." Verify that your mesh does not contain errors such as Non-Manifold Edges, Bad Contiguous Edges, Intersect Faces, Zero Faces, Zero Edges, Non-Flat Faces, Thin Faces, or Sharp Edges. All error counts should be zero; otherwise, Fossils may crash. Overhang Faces are allowed in Fossils.

![Mesh with good quality example](https://github.com/MiguelDLM/BFEX/blob/main/Quality%20of%20the%20mesh%20example.png)

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
   - Select surfaces for extraction and click "Submit Selection" to create a new sub-mesh in the collection.

4. **Force Direction Setup:**
   - Click "Select Focal Point" to choose a point on a reference object where the force will be applied.
   - Click "Submit Focal Point" to store the coordinates.

5. **Input Force and Loading Scenario:**
   - Enter the force applied by the muscle and select the loading scenario (Uniform, Tangential, or Tangential plus Normal Traction).

6. **Parameter Submission:**
   - Click "Submit Parameters" to store all values (file name, focal point, force, and loading scenario) in a JSON dictionary.
     Note: The stored parameters are displayed in Blender's console. Check regularly to ensure the data is being stored correctly.

7. **Undo Last Submission:**
   - If a mistake is made, delete the focal point created on the "Focal points" collection and click "Refresh parameters list" to update the list.

8. **Repeat for Multiple Muscles:**
   - Repeat steps 3 to 7 for each muscle to be modeled.

9. **Contact and Constraint Points:**
   - Click "Select Contact Points" to switch to Edit mode and select vertices where loading forces will be applied.
   - Choose movement restrictions in the contact points.

10. **Define Loads:**
      - Click "Select Load faces" to switch to Edit mode and select vertices where loads will be applied.
      - Input the load value on each axis

11. **Export and Run Fossils:**
    - Set material properties like Young's Modulus and Poisson's Ratio.
    - Click "Export Files" to export sub-meshes and the Python script for Fossils.
    - Click "Run Fossils" to initiate the FEA analysis (add the path to fossils in the preferences' menu)

12. **Results and Visualization:**
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

Ensure that Fossils is installed, and the path is correctly set in the add-on preferences. If Fossils is not installed, download it from the [Fossils website](https://https://gitlab.uliege.be/rboman/fossils/-/releases) and set the path in the add-on preferences.

## Extra

~~If you experience low performance in GMSH (software used for Fossils to visualize the results), it might be necessary to remove some elements from the scene to improve performance. You can do this before opening the results by editing the .opt file.~~

~~To simplify this process, you can download the `modify_opt.py` file. Copy the file to your results folder or any other folder in a upper level. To automatically modify the OPT file, simply drag and drop your OPT file onto the python file or use double click to search all the opt files in the folder and subfolders to modify all of them. This will add some lines to hide certain elements in the visualization.~~

~~[Download script_modify_opt.py](https://github.com/MiguelDLM/BFEX/blob/main/modify_opt.py)  ~~

~~Additionally, you can run Fossils in batch mode to avoid the GMSH interface. To do this, you can use the `batch.py` script. This script will run Fossils in batch mode. You only need to place the script in the same folder as your python scripts. You can choose which python scripts to run by inputting the number from the displayed list. The script will run the selected python script and close Fossils after the analysis is complete.~~

Now you can download the binaries to run Fossils in batch mode and convert the results to VTK and CSV files. The binaries consist of two executables, keep them in the same folder since they are dependent on each other. You can input the path of the Fossils installation and select the folder where your python script(s) are located. Once loaded the folder, you can select the python script to run o convert. If you want to convert the results, be sure the results are in a folder with the same name as the python script and next to it. The folders need to have the following structure:

```
Folder/
├── script.py
└── script/
    ├── Smooth_stress_tensor.msh
    ├── mesh.msh
    └── ...
```

We welcome pull requests. For major changes, please open an issue first to discuss the proposed changes. Be sure to update tests as appropriate.
