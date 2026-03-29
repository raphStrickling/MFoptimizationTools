import os
import pytest
import numpy as np

import optimizationTools as ot


def parse_stl(stl_content: str):
    normals = []
    vertices = []

    for line in stl_content.splitlines():
        line = line.strip()

        if line.startswith("facet normal"):
            entries = line.split()
            normals.append([float(entries[-3]), float(entries[-2]), float(entries[-1])])

        elif line.startswith("vertex"):
            entries = line.split()
            vertices.append([float(entries[-3]), float(entries[-2]), float(entries[-1])])

    return np.array(normals), np.array(vertices)


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
        normals, vertices = parse_stl((test_tmp / "stl" / f"{face_name}.stl").read_text())
        normals_ref, vertices_ref = parse_stl((test_root / "test_geometryTools" / f"{face_name}.stl").read_text())

        np.testing.assert_allclose(normals, normals_ref, rtol=1e-6)
        np.testing.assert_allclose(vertices, vertices_ref, rtol=1e-6)


def test_stl_export_freecad(test_root, test_tmp):
    doc = ot.geometryTools.load_document(f"{test_root}/test_geometryTools/test_document.FCStd")

    for face_name in ["face_sphere", "face_cube"]:
        # convert to .stl with FreeCAD
        # (.ast is ascii-formatted .stl in FreeCAD)
        with pytest.raises(ValueError):
            ot.geometryTools.face_to_stl(doc=doc, face_name=face_name, output_path=f"{test_tmp}/stl/{face_name}.stl")

        ot.geometryTools.face_to_stl(doc=doc, face_name=face_name, output_path=f"{test_tmp}/stl/{face_name}.ast")
        # check generated stls against reference
        normals, vertices = parse_stl((test_tmp / "stl" / f"{face_name}.ast").read_text())
        normals_ref, vertices_ref = parse_stl((test_root / "test_geometryTools" / f"{face_name}.ast").read_text())
        np.testing.assert_allclose(normals, normals_ref, rtol=1e-6)
        np.testing.assert_allclose(vertices, vertices_ref, rtol=1e-6)


def test_stl_merge(test_root, test_tmp):
    nonexisting_stls = {"a": f"{test_tmp}/stl/a.stl", "b": f"{test_tmp}/stl/b.stl"}
    with pytest.raises(FileNotFoundError):
        ot.geometryTools.merge_stls(nonexisting_stls, f"{test_tmp}/stl/merged.stl")

    stls_to_merge = {"face_sphere": f"{test_tmp}/stl/face_sphere.stl", "face_cube": f"{test_tmp}/stl/face_cube.stl"}
    # merge .stls from gmsh
    ot.geometryTools.merge_stls(stls_to_merge, f"{test_tmp}/stl/merged_faces_gmsh.stl")

    asts_to_merge = {"face_sphere": f"{test_tmp}/stl/face_sphere.ast", "face_cube": f"{test_tmp}/stl/face_cube.ast"}

    # merge .stls from FreeCAD
    ot.geometryTools.merge_stls(asts_to_merge, f"{test_tmp}/stl/merged_faces_FC.stl")

    # check against reference
    normals_gmsh, vertices_gmsh = parse_stl((test_tmp / "stl" / "merged_faces_gmsh.stl").read_text())
    normals_FC, vertices_FC = parse_stl((test_tmp / "stl" / "merged_faces_FC.stl").read_text())
    normals_gmsh_ref, vertices_gmsh_ref = parse_stl(
        (test_root / "test_geometryTools" / "merged_faces_gmsh.stl").read_text()
    )
    normals_FC_ref, vertices_FC_ref = parse_stl((test_root / "test_geometryTools" / "merged_faces_FC.stl").read_text())

    np.testing.assert_allclose(normals_gmsh, normals_gmsh_ref, rtol=1e-6)
    np.testing.assert_allclose(vertices_gmsh, vertices_gmsh_ref, rtol=1e-6)
    np.testing.assert_allclose(normals_FC, normals_FC_ref, rtol=1e-6)
    np.testing.assert_allclose(vertices_FC, vertices_FC_ref, rtol=1e-6)
