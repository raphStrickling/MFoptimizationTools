#!/bin/sh
# The first and second command line arguments to the script are the
# names of the Dakota parameters and results files.
params=$1
results=$2

# --------------
# PRE-PROCESSING
# --------------

# Incorporate the parameters from Dakota into the template
cp -r ../../casebase/* .
cp ../../paramdir/settings.yaml ./
# update variables in setttings.yaml template
nVars=$(awk 'NR==1{print $1;}' $params) # get number of design variables
for i in $(seq 2 $(($nVars + 1))); do
    # extract label and value of this parameter
    val=$(awk "NR==$i{print \$1;}" $params)
    label=$(awk "NR==$i{print \$2;}" $params)
    # insert into settings.yaml file
    sed -i "s/{$label}/$val/g" settings.yaml
done

# geometry generation and meshing
srun -n 1 -c 1 --kill-on-bad-exit ../../scripts/runMeshing.sh &> log.geomMesh

# ---------
# EXECUTION
# ---------
. $FOAM_SOURCE

# Run OpenFOAM simulation
decomposePar &> log.decomposePar &
wait
srun -n 20 -c 1 -N 1 --exclusive --kill-on-bad-exit simpleFoam -parallel &>> log.openFOAM
reconstructPar &> log.reconstructPar &
wait
# Remove processor directories to save disk space
rm -r proc* &
wait

# ---------------
# POST-PROCESSING
# ---------------
# extract objective function value to $results
touch para.foam
../../scripts/eval_objective_function.py ./para.foam settings.yaml > $results

# rename para.foam to wdirXX.foam
wdir=$(pwd | awk -F '/' '{print $NF}')
mv para.foam "$wdir.foam"

