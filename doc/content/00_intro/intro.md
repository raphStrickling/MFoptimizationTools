# Getting Started

This optimization toolbox is a collection of python tools and scripts for multi-fidelity shape optimization optimization with Dakota, OpenFOAM an FreeCAD

## Installation
It is recommended to install the optimization toolbox with conda. Please use the provided `environment.yml` file for the installation.

```sh
conda env create -f environment.yaml
```

This creates a new conda environment called `geom_opt` which can then be activated for the optimizations.

### Optional: define OpenFOAM path
To use the example, you have to define the location of your OpenFOAM installation. For this, configure the environment variable `FOAM_SOURCE` to point to the shell script that you source when loading OpenFOAM
```sh
# activate environment
conda activate geom_opt

# set environment variable
conda env config vars set FOAM_SOURCE=<PATH TO OPENFOAM SCRIPT>
```

```{tableofcontents}
```
