"""
Rubber band mode for 3D point picking
"""
import vtk
from vtk.util.numpy_support import vtk_to_numpy

class RubberBand(vtk.vtkInteractorStyleRubberBandPick):
    def __init__(self, renderWindow, renderer, pointcloud, interactor, area_picker, cm):
        print("entering rubber band mode")
        self.cm = cm
        self.renderWindow = renderWindow
        self.renderer = renderer
        self.pointcloud = pointcloud
        self.Interactor = interactor
        self.selected_mapper = vtk.vtkDataSetMapper()
        self.selected_actor = vtk.vtkActor()
        self.selected_actor.SetMapper(self.selected_mapper)
        self.area_picker = area_picker

        '# % SET VTK OBSERVERS'
        self.Interactor.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.Interactor.AddObserver("LeftButtonReleaseEvent", self.LeftButtonReleaseEvent)

    def leftButtonPressEvent(self, obj, event):
        print("LEFT BUTTON PRESSED")
        self.OnLeftButtonDown()
        '# % REMOVE THE CURRENT HIGHLIGHT ACTOR (IF THERE IS ONE) FROM SCREEN'
        try:
            self.renderer.RemoveActor(self.selected_actor)
        except AttributeError:
            pass
        self.renderWindow.Render()

    def LeftButtonReleaseEvent(self, obj, event):
        print("LEFT BUTTON RELEASED")
        self.OnLeftButtonUp()

        self.frustum = self.area_picker.GetFrustum()

        self.extract_geometry = vtk.vtkExtractGeometry()
        self.extract_geometry.SetImplicitFunction(self.frustum)
        self.extract_geometry.SetInputData(self.pointcloud.cm_poly_data)
        self.extract_geometry.Update()

        self.glyph_filter = vtk.vtkVertexGlyphFilter()
        self.glyph_filter.SetInputConnection(self.extract_geometry.GetOutputPort())
        self.glyph_filter.Update()

        self.selected = self.glyph_filter.GetOutput()
        self.p1 = self.selected.GetNumberOfPoints()
        self.p2 = self.selected.GetNumberOfCells()
        print("Number of points = %s" % self.p1)
        print("Number of cells = %s" % self.p2)

        '# % COLOR SELECTED POINTS RED'
        self.selected_mapper.SetInputData(self.selected)
        try:
            self.selected_actor.GetProperty().SetPointSize(10)
            self.selected_actor.GetProperty().SetColor(0, 0, 0)  # (R, G, B)
            self.color_picked()
        except AttributeError:
            pass

    def save_output(self):
        """CREATES A NEW NUMPY ARRAY of the cm FILE WITH SELECTED NODES REMOVED"""
        pass
        # np.column_stack((self.selected_cm_ids, self.selected_xyz))

    def color_picked(self):
        try:
            self.renderer.AddActor(self.selected_actor)
            self.renderWindow.Render()
        except AttributeError:
            pass