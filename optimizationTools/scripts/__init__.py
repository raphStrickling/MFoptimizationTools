#!/usr/bin/env python

"""
scripts
==============

This contains useful scripts that can be called from the command line
"""

import argparse
import os

import yaml

import optimizationTools as ot


def modify_geometry():
    """
    This function is specified to be called using the command `modifyGeom` from the terminal.

    *usage*: `modifyGeom [-h] [--noGmsh] settingsYaml`

    positional arguments:
      settingsYaml  YAML file containing the settings for the geometry modification

    options:
      -h, --help    show this help message and exit
      --noGmsh      Generate .stl file using FreeCADs native .stl exporter
    """
    parser = argparse.ArgumentParser(description="Modify a geometry in a FreeCAD document.")
    parser.add_argument(
        "settingsYaml", type=str, help="YAML file containing the settings for the geometry modification"
    )
    parser.add_argument(
        "--noGmsh", action="store_true", help="Generate .stl file using FreeCADs native .stl exporter", default=False
    )
    args = parser.parse_args()

    # load settings.yaml file
    if not os.path.isfile(args.settingsYaml):
        raise FileNotFoundError(f"settings YAML file {args.settingsYaml} not found")

    with open(args.settingsYaml) as settings_file:
        settings = yaml.safe_load(settings_file)

    # load FreeCAD document
    doc = ot.geometryTools.load_document(settings["CAD_document"])

    ### check for FreeCAD version and maintain backward compatibility
    if "sketch_names" in settings and "varset_label" not in settings:
        # Old FreeCAD version < 1.0: find sketch constraints by label
        print("WARNING: You are using a deprecated document structure. Use FreeCAD's VarSet instead!")
        sketches = {}  # dict sketch_name -> sketch_object
        if settings["sketch_names"] is not None:
            # find sketches
            for sketch, sketch_label in settings["sketch_names"].items():
                sketches[sketch] = ot.geometryTools.get_object_by_label(doc, sketch_label)
            # change geometry
            for sketch in settings["parameter_labels"]:
                for param, label in settings["parameter_labels"][sketch].items():
                    if "angle" in label:
                        ot.geometryTools.modify_sketch(
                            doc, sketches[sketch], label, float(settings["parameter_values"][param]), unit="deg"
                        )
                    else:
                        ot.geometryTools.modify_sketch(
                            doc, sketches[sketch], label, float(settings["parameter_values"][param])
                        )

    elif "varset_label" in settings:  # New in FreeCAD v1.0: use VarSet instead to define all paramters
        # new default
        varset = ot.geometryTools.get_object_by_label(doc, settings["varset_label"])
        for parameter in settings["parameter_values"]:
            # change geometry
            if parameter not in varset.PropertiesList:
                raise ValueError(f"Parameter {parameter} not found in VarSet")
            setattr(varset, parameter, settings["parameter_values"][parameter])
    else:
        print("WARNING: No varset or sketches specified. Geometry cannot be modified.")

    doc.recompute()
    doc.save()

    if not args.noGmsh:
        # find boundary patches and export each as a step file
        step_patches = {}  # dict patch_name -> step_path
        for patch_name in settings["boundary_patches"]:
            ot.geometryTools.face_to_step(
                doc=doc, face_name=patch_name, output_path=f"{settings['step_output_dir']}/{patch_name}.step"
            )
            step_patches[patch_name] = f"{settings['step_output_dir']}/{patch_name}.step"

        # generate stls from step files
        stl_patches = {}  # dict patch_name -> stl_path
        for patch_name, step_file in step_patches.items():
            ot.geometryTools.step_to_stl(
                step_path=step_file, stl_path=f"{settings['mesh_output_dir']}/{patch_name}.stl"
            )
            stl_patches[patch_name] = f"{settings['mesh_output_dir']}/{patch_name}.stl"
    else:
        stl_patches = {}
        for patch_name in settings["boundary_patches"]:
            if "stl_resolution" in settings:
                print(
                    f"INFO: using specified stl resolution {settings['stl_resolution']} as max length for triangulation"
                )
                ot.geometryTools.face_to_stl(
                    doc=doc,
                    face_name=patch_name,
                    output_path=f"{settings['mesh_output_dir']}/{patch_name}.ast",
                    max_length=float(settings["stl_resolution"]),
                )
            else:
                ot.geometryTools.face_to_stl(
                    doc=doc, face_name=patch_name, output_path=f"{settings['mesh_output_dir']}/{patch_name}.ast"
                )
            stl_patches[patch_name] = f"{settings['mesh_output_dir']}/{patch_name}.ast"

    ot.geometryTools.merge_stls(stl_patches, settings["final_mesh"])

    print("Successfully modified geometry and created stl file! Exiting.")
