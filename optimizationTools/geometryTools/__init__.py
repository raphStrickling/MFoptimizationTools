"""
geometryTools
=============

This package contains useful tools for modifying a FreeCAD document and handling import and export from python
"""

import os

# FreeCAD imports
import freecad
import FreeCAD
import Mesh
import MeshPart
import Part
import Sketcher

# use gmsh for stl generation
import gmsh


def load_document(doc_path: str) -> FreeCAD.Document:
    """
    Load a FreeCAD document

    :param doc_path: path to FreeCAD document (.FCStd)
    :return: FreeCAD document object
    """
    return FreeCAD.openDocument(doc_path)


def get_object_by_label(document: FreeCAD.Document, object_name: str):
    """
    Find an object in a FreeCAD document by its name

    :param document: FreeCAD document
    :param object_name: name of object in FreeCAD document
    :return: requested FreeCAD object
    """
    tmp = document.getObjectsByLabel(object_name)

    # labels are always unique in FreeCAD
    # if len == 0, the object does not exist
    if len(tmp) == 0:
        raise ValueError(f"No object with label {object_name} found in FreeCAD document {document.FileName}")
    this_object = tmp[0]
    return this_object


def modify_sketch(doc: FreeCAD.Document, sketch, datum_name: str, datum_val: float, unit: str = "mm"):
    """
    Set a datum (constraint) in a sketch to a value. The datum is found by its label

    :param doc: FreeCAD document
    :param sketch: sketch object (type: Sketcher.SketchObject; no type hinting possible)
    :param datum_name: name of the datum that is modified
    :param datum_val: new value for the specified datum
    :param unit: 'mm' for lengths or 'deg' for angles
    """
    try:
        sketch.setDatum(datum_name, FreeCAD.Units.Quantity(f"{datum_val:.6f} {unit}"))
    except ValueError as e:
        raise ValueError(f"{e} in sketch {sketch.Label} in FreeCAD") from e
    doc.recompute()


def prepare_output_directory(path: str):
    """
    Create an output directory if it does not exist yet.

    :param path: path to directory that is checked. Should not be a path to file!
    """
    if path[-1] != "/":
        path = path + "/"
    if not os.path.exists(path):
        print(f"INFO: creating directory {path}")
        os.makedirs(path)


def prepare_output_path(path: str):
    """
    Check if the output file is to be saved in a directory
    and if true, prepare the output directory

    :param path: path to output file
    """
    # check if output path contains a directory
    if len(path.split("/")) >= 2 + int(path[0] == "/" or path[:2] == "./"):
        output_dir = "/".join(path.split("/")[:-1])
        prepare_output_directory(output_dir)


def face_to_step(doc: FreeCAD.Document, face_name: str, output_path: str):
    """
    Export a FreeCAD FaceBinder object to a .step file

    :param doc: FreeCAD document
    :param face_name: Label of the FaceBinder object that is exported
    :param output_path: path where the .step file is saved
    """
    facebinder_obj = get_object_by_label(doc, face_name)
    prepare_output_path(output_path)
    Part.export([facebinder_obj], output_path)


def face_to_stl(doc: FreeCAD.Document, face_name: str, output_path: str, max_length: float = 0.4):
    """
    Export a FreeCAD FaceBinder object to a .stl file using FreeCAD's .stl exporter

    :param doc: FreeCAD document
    :param face_name: Label of the FaceBinder object that is exported
    :param output_path: path where the .stl file is saved
    :param max_length: resolution of .stl mesh (max length of any triangle side in mm)
    """
    facebinder_obj = get_object_by_label(doc, face_name)
    prepare_output_path(output_path)

    # generate mesh from part
    this_mesh = doc.addObject("Mesh::Feature", face_name)
    this_mesh.Mesh = MeshPart.meshFromShape(Shape=facebinder_obj.Shape, MaxLength=max_length)
    this_mesh.Label = face_name + "_mesh"

    # export to .stl
    # the .stl must be written as a plain ASCII text file
    # changing the extension to from .stl to .ast forces FreeCAD
    # to write a plain text file
    if ".ast" not in output_path:
        raise ValueError(
            f"Output path {output_path} must contain .ast (ASCII stl) extension when exporting directly to .stl without intermediate .step files"
        )
    Mesh.export([this_mesh], output_path)

    # clean up FreeCAD document: remove intermediate mesh
    doc.removeObject(this_mesh.Name)
    doc.recompute()


def step_to_stl(step_path: str, stl_path: str, stl_resolution: float = 0.15):
    """
    Convert a .step file to .stl using gmsh

    :param step_path: path to .step file
    :param stl_path: path where the generated .stl file is saved
    :param stl_resolution: Resolution of the triangulated mesh in the .stl
    """
    gmsh.initialize()
    # load .step file in gmsh
    gmsh.merge(step_path)
    gmsh.model.mesh.setSize(gmsh.model.getEntities(0), stl_resolution)

    # generate surface mesh (--> parameter dim=2)
    gmsh.model.mesh.generate(dim=2)

    prepare_output_path(stl_path)
    gmsh.write(stl_path)
    gmsh.finalize()


def merge_stls(stl_paths: dict, output_path: str):
    """
    Merge multiple .stls into one preserving their distinction by utilizing stl regions

    :param stl_paths: dictionary faceName -> stl_path
    :param output_path: output path of combined .stl
    """
    # store the lines of all .stl files in a list
    combined_stl = []

    # read stls
    for face_name, stl_path in stl_paths.items():
        if not os.path.isfile(stl_path):
            raise FileNotFoundError(f"stl file {stl_path} not found")

        # if the stl was created with FreeCAD (extionsion .ast), the region is called "Mesh"
        # if the stl was created with gmsh, the region is called "Created by Gmsh"
        if ".ast" in stl_path and ".stl" not in stl_path:
            region_name = "Mesh"
        else:
            region_name = "Created by Gmsh"

        # rename the stl region to the boundary patch name so that the meshing software for
        # the CFD mesh recognizes the correct boundary patches
        with open(stl_path) as stl_file:
            tmp = stl_file.readlines()
            tmp[0] = tmp[0].replace(f"solid {region_name}", f"solid {face_name}")
            tmp[-1] = tmp[-1].replace(f"endsolid {region_name}", f"endsolid {face_name}")
        combined_stl = [*combined_stl, *tmp]

    # save combined stl
    prepare_output_path(output_path)
    with open(output_path, "w") as output_file:
        output_file.writelines(combined_stl)
