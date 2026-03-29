# Examplary Simulation-based Shape Optimization Case

In this example, the pressure loss in a mesoscale burner nozzle is optimized.
DISCLAIMER: This simulation case setup is for demonstration purposes of the optimization framework only and does not aim to produce physically meaningful results. For productive runs, adjust the case setup and numerical configuration as needed.

## Create CAD Model: FreeCAD
1. model the 3D geometry of the burner
2. model the computational domain
3. subtract the burner geometry from the cylinder wedge to get your fluid domain
4. switch to the "Draft" workbench and use the "facebinder" tool to define boundary patches
    + the faces that represent walls should be named "wall"
    + there should be two patches for the wedge named "wedgeLeft" and "wedgeRight"
    + the names of the other patches can be chosen freely
5. put the FreeCAD document into the casebase/freeCAD directory

### Parameterize your Model
+ add a VarSet containing all your design variables and dependent variables
+ reference the variables from the VarSet when constraining your sketches or dimensioning / positioning your objects

## Adjust settings.yaml file
The file is located in the `paramdir` directory.
In this file, you define:
+ geometric parameters of your burner
+ name of your FreeCAD document
+ name of the varset that contains your design variables
+ names of the boundary patches

## Adjust Dakota design variables
Under the "variables" section in dakota_sample_design_space.in, the design variables are defined. Make sure that the names are consistent with the settings.yaml file and your CAD document.
You can define 
+ initial values (in mm)
+ upper and lower boundaries (in mm)
+ linear constraints (in mm, optional)

# Prerequisites

Dakota installation (tested with version 6.23)
OpenFOAM installation including the cfMesh plugin (tested with version 2512)

conda environment from this repository including optional dependencies for postprocessing. They can be installed using
```sh
pip install -e .[postproc]
```

# Running the Optimization

The sampling phase of the optimization process is executed using
```sh
dakota -i dakota_sampling.in
```

The optmization on the surrogate is executed using
```sh
dakota -i dakota_opt.in
```

