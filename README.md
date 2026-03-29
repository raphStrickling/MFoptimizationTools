# Multi-fidelity Shape Optimization Toolbox
[![codecov](https://codecov.io/github/raphStrickling/MFoptimizationTools/graph/badge.svg?token=41FEMC1IA4)](https://codecov.io/github/raphStrickling/MFoptimizationTools)

The optimization toolbox is a collection of python tools and scripts for multi-fidelity shape optimization optimization with Dakota, OpenFOAM an FreeCAD

## Usage and Documentation
You can find an example optimization case in the [examples directory](./examples/).

For more information about the code, please visit the [documentation page](https://raphstrickling.github.io/MFoptimizationTools/)

## Installation
It is recommended to install the optimization toolbox with conda. Please use the provided `environment.yml` file for the installation.

```sh
conda env create -f environment.yml
```

This creates a new conda environment called `geom_opt` which can then be activated for the optimizations.

### Optional: Define OpenFOAM path
To use the example, you have to define the location of your OpenFOAM installation. For this, configure the environment variable `FOAM_SOURCE` to point to `<OpenFOAM SRC>/etc/bashrc`:

```sh
# activate environment
conda activate geom_opt

# set environment variable
conda env config vars set FOAM_SOURCE=<PATH TO OPENFOAM SCRIPT>
```

