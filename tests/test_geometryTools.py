import os
import pytest
import numpy as np
import trimesh

import optimizationTools as ot


def compare_stls(result, reference):
    # Compare bounding box
    np.testing.assert_allclose(result.bounds, reference.bounds, atol=5e-4)

    # Compare volume and surface area
    assert abs(result.volume - reference.volume) < 1e-4
    assert abs(result.area - reference.area) < 1e-4

    # Compare center of mass
    np.testing.assert_allclose(result.center_mass, reference.center_mass, atol=1e-4)



def test_varset_modification(test_root):
    # make sure to raise and exception if document is not found
    with pytest.raises(OSError):
        doc = ot.geometryTools.load_document("mydocument.FCStd")

    doc = ot.geometryTools.load_document(f"{test_root}/test_geometryTools/test_document.FCStd")

    # make sure exception is raised if object not found
    with pytest.raises(ValueError):
        varset = ot.geometryTools.get_object_by_label(doc, "myVars1")

    varset = ot.geometryTools.get_object_by_label(doc, "myVars")

    # check original values
    assert varset.myLength == 10
    assert varset.myAngle == 5
    # modify
    varset.myLength = 20
    varset.myAngle = 45
    # check modified values
    assert varset.myLength == 20
    assert varset.myAngle == 45


def test_sketch_modification(test_root):
    doc = ot.geometryTools.load_document(f"{test_root}/test_geometryTools/test_document.FCStd")
    sketch = ot.geometryTools.get_object_by_label(doc, "Sketch")

    # make sure the measurements are found and original values match
    measurement_length = ot.geometryTools.get_object_by_label(doc, "Distance: 20,00 mm")
    measurement_angle = ot.geometryTools.get_object_by_label(doc, "Angle: 60,00 °")
    assert np.isclose(float(measurement_length.Distance), 20, rtol=1e-5)
    assert np.isclose(float(measurement_angle.Angle), 60, rtol=1e-5)

    # modify geometry
    with pytest.raises(ValueError):  # invalid input
        ot.geometryTools.modify_sketch(doc, sketch, "sketchLength", "2,4")

    ot.geometryTools.modify_sketch(doc, sketch, "sketchLength", 30)
    ot.geometryTools.modify_sketch(doc, sketch, "sketchAngle", 110, unit="deg")
    doc.recompute()

    # make sure the geometry was modified and the measurements are updated
    assert np.isclose(float(measurement_length.Distance), 30, rtol=1e-5)
    assert np.isclose(float(measurement_angle.Angle), 70, rtol=1e-5)


def test_prepare_output_dir(test_tmp):
    assert not os.path.exists(f"{test_tmp}/test")
    ot.geometryTools.prepare_output_directory(f"{test_tmp}/test")
    assert os.path.exists(f"{test_tmp}/test")
    os.rmdir(f"{test_tmp}/test")


def test_stl_export_gmsh(test_root, test_tmp):
    doc = ot.geometryTools.load_document(f"{test_root}/test_geometryTools/test_document.FCStd")
    for face_name in ["face_sphere", "face_cube"]:
        # convert to .step with FreeCAD
        ot.geometryTools.face_to_step(doc=doc, face_name=face_name, output_path=f"{test_tmp}/step/{face_name}.step")
        # convert .step to .stl with gmsh
        ot.geometryTools.step_to_stl(
            step_path=f"{test_tmp}/step/{face_name}.step", stl_path=f"{test_tmp}/stl/{face_name}.stl"
        )
        # check stl against reference
        result = trimesh.load_mesh(test_tmp / "stl" / f"{face_name}.stl")
        reference = trimesh.load_mesh(test_root / "test_geometryTools" / f"{face_name}.stl")

        compare_stls(result, reference)


def test_stl_export_freecad(test_root, test_tmp):
    doc = ot.geometryTools.load_document(f"{test_root}/test_geometryTools/test_document.FCStd")

    for face_name in ["face_sphere", "face_cube"]:
        # convert to .stl with FreeCAD
        # (.ast is ascii-formatted .stl in FreeCAD)
        with pytest.raises(ValueError):
            ot.geometryTools.face_to_stl(doc=doc, face_name=face_name, output_path=f"{test_tmp}/stl/{face_name}.stl")

        ot.geometryTools.face_to_stl(doc=doc, face_name=face_name, output_path=f"{test_tmp}/stl/{face_name}.ast")
        # check generated stls against reference
        result = trimesh.load_mesh(test_tmp / "stl" / f"{face_name}.ast", file_type='stl')
        reference = trimesh.load_mesh(test_root / "test_geometryTools" / f"{face_name}.ast", file_type='stl')
        compare_stls(result, reference)


def test_stl_merge(test_root, test_tmp):
    nonexisting_stls = {"a": f"{test_tmp}/stl/a.stl", "b": f"{test_tmp}/stl/b.stl"}
    with pytest.raises(FileNotFoundError):
        ot.geometryTools.merge_stls(nonexisting_stls, f"{test_tmp}/stl/merged.stl")

    stls_to_merge = {"face_sphere": f"{test_root}/test_geometryTools/face_sphere.stl", "face_cube": f"{test_root}/test_geometryTools/face_cube.stl"}
    # merge .stls from gmsh
    ot.geometryTools.merge_stls(stls_to_merge, f"{test_tmp}/stl/merged_faces_gmsh.stl")

    asts_to_merge = {"face_sphere": f"{test_root}/test_geometryTools/face_sphere.ast", "face_cube": f"{test_root}/test_geometryTools/face_cube.ast"}

    # merge .stls from FreeCAD
    ot.geometryTools.merge_stls(asts_to_merge, f"{test_tmp}/stl/merged_faces_FC.stl")

    # check against reference
    result_FC = trimesh.load_mesh(test_tmp / "stl" / f"merged_faces_FC.stl")
    reference_FC = trimesh.load_mesh(test_root / "test_geometryTools" / f"merged_faces_FC.stl")
    compare_stls(result_FC, reference_FC)

    result_gmsh = trimesh.load_mesh(test_tmp / "stl" / f"merged_faces_gmsh.stl")
    reference_gmsh = trimesh.load_mesh(test_root / "test_geometryTools" / f"merged_faces_gmsh.stl")
    compare_stls(result_gmsh, reference_gmsh)

