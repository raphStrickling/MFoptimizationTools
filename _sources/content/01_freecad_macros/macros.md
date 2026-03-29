# Custom FreeCAD Macros

These custom macros can facilitate your work with FreeCAD

## Invert Selected Faces

To invert the selection of faces (particularly useful for selecting all faces belonging to the wall patch), use this macro

```py
# Get current selection (can include faces or whole objects)
sel=Gui.Selection.getSelection()
# Gui.Selection.clearSelection()
for i in range(len(sel)):
    for j in enumerate(sel[i].Shape.Faces):  # search Faces
        if not Gui.Selection.isSelected(FreeCAD.ActiveDocument.getObject(sel[i].Name), 'Face'+str(j[0]+1)):
            objetSelect = Gui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(sel[i].Name), 'Face'+str(j[0]+1))
        else:
            objectDeselect = Gui.Selection.removeSelection(FreeCAD.ActiveDocument.getObject(sel[i].Name), 'Face'+str(j[0]+1))

FreeCAD.ActiveDocument.recompute(None,True,True)
```

## Select all Faces

To select all faces of an object, use the following macro

```py
sel=Gui.Selection.getSelection()
Gui.Selection.clearSelection()
for i in range(len(sel)):
    for j in enumerate(sel[i].Shape.Faces):                         # search Faces
        objetSelect = Gui.Selection.addSelection(FreeCAD.ActiveDocument.getObject(sel[i].Name), 'Face'+str(j[0]+1))

FreeCAD.ActiveDocument.recompute(None,True,True)
```

