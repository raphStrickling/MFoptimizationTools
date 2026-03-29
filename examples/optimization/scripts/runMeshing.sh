#!/bin/bash

# modify geometry 
timeout 240 modifyGeom settings.yaml
if [[ $? == 124 ]]; then
    echo "ERROR: modifying geometry took longer than expected! Timeout detected, aborting"
    echo "FAIL" >> results.out
    exit;
fi

# load OpenFOAM: $FOAM_SOURCE points to OpenFOAM/etc/bashrc
source $FOAM_SOURCE

. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions        # Tutorial run functions
#------------------------------------------------------------------------------

# scale stl file to mm
runApplication surfaceTransformPoints constant/triSurface/burner_wedge.stl constant/triSurface/burner_wedge_scaled.stl -write-scale 1e-3

# extract edgeMesh for edge refinement
runApplication surfaceFeatureExtract

# generate feature edge mesh which works better with cfMesh
runApplication surfaceFeatureEdges -angle 40 constant/triSurface/burner_wedge_scaled.stl constant/triSurface/featureEdges.fms

# turn on binary writing for meshing and simulation to save storage space
sed -i -e 's/writeFormat         ascii/writeFormat         binary/' system/controlDict

# run cfMesh
runApplication cartesianMesh

# create cyclic patches
runApplication createPatch -overwrite

#------------------------------------------------------------------------------
