#!/usr/bin/env python
import sys
import pyvista as pv
import numpy as np
import yaml


if __name__ == '__main__':
    assert len(sys.argv) == 3, f"Please pass the case path and the settings yaml as arguments to this script!"
    case_path = sys.argv[1]
    yaml_file = sys.argv[2]
    with open(yaml_file, 'r') as settings_file:
        settings = yaml.safe_load(settings_file)

    ## try to read case path. If no reconstructed timestep is not found, the simulation has failed.
    try:
        reader = pv.POpenFOAMReader(case_path)
        reader.cell_to_point_creation = False
        reader.case_type = 'reconstructed'

        time = reader.time_values[-1]
        reader.set_active_time_value(time)

        multiblock = reader.read()
    except (IndexError, AttributeError) as e:
        # Dakota captures "FAIL" and can try recovery methods
        print('FAIL')
        exit()

    # assert that the domain has the expected length.
    # if not, the design is most likely infeasible
    xmax = multiblock['internalMesh'].points[:,0].max()
    if not np.isclose(xmax, settings['domain_length'] * 1e-3, atol=0.2e-3):
        print('FAIL')
        exit()

    # compute mean pressure loss as objective function
    p_in = multiblock['boundary']['inletAir']['p'].mean()
    p_out = multiblock['boundary']['outlet']['p'].mean()
    pressure_loss = p_in - p_out

    print(f"{pressure_loss} objectiveFunction")
 
