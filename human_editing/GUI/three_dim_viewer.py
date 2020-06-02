"""
Three dimensional viewer for Py-cmeditor
"""

import matplotlib as mpl
mpl.use('WXAgg')
import wx
import wx.lib.agw.aui as aui
import numpy as np
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy
from rubber_band import RubberBand
from point_clouds import VtkPointCloud
from point_clouds import VtkPointCloudPredicted

class ThreeDimViewer(wx.Frame):
    """
    Three dimensional viewer for Py-cmeditor
    """
    def __init__(self, parent, id, title, cm, xyz, xyz_cm_id, xyz_meta_data,
                 xyz_cm_line_number, predicted_xyz, diff_xyz, difference_xyz, score_xyz):
        wx.Frame.__init__(self, None, wx.ID_ANY, '3D Viewer', size=(900, 700))

        # START AUI WINDOW MANAGER
        self.tdv_mgr = aui.AuiManager()

        # TELL THE AUI WHICH FRAME TO USE
        self.tdv_mgr.SetManagedWindow(self)

        # CREATE PANEL TO FILL WITH VTK INTERACTIVE DISPLAY (size in pixels)
        self.tdv_right_panel = wx.Panel(self, -1, size=(743, 543), style=wx.ALIGN_RIGHT | wx.BORDER_RAISED | wx.EXPAND)
        self.tdv_right_panel.SetBackgroundColour('blue')

        # CREATE PANEL TO FILL WITH BUTTONS (size in pixels)
        self.tdv_left_panel = wx.Panel(self, -1, size=(152, 152), style=wx.ALIGN_RIGHT | wx.BORDER_RAISED)
        self.tdv_left_panel.SetBackgroundColour('grey')

        # ADD THE PANES TO THE AUI MANAGER
        self.tdv_mgr.AddPane(self.tdv_right_panel, aui.AuiPaneInfo().Name('top').CenterPane())
        self.tdv_mgr.AddPane(self.tdv_left_panel, aui.AuiPaneInfo().Name('left').Left())
        self.tdv_mgr.Update()

        # SET THE VTK RENDERER AS AN OBJECT
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.8, 0.8, 0.8)

        # SET THE RENDER WINDOW AS AN OBJECT
        self.renderWindow = vtk.vtkRenderWindow()

        # ADD THE RENDERER TO THE RENDER WINDOW
        self.renderWindow.AddRenderer(self.renderer)

        # CREATE THE VTK INTERACTOR
        self.Interactor = wxVTKRenderWindowInteractor(self.tdv_right_panel, -1)
        self.Interactor.SetRenderWindow(self.renderWindow)
        # self.Interactor.RemoveObservers('KeyPressEvent')
        # self.Interactor.RemoveObservers('CharEvent')

        self.renderer.SetUseDepthPeeling(1)
        self.renderer.SetOcclusionRatio(0.1)
        self.renderer.SetMaximumNumberOfPeels(100)
        self.renderWindow.SetMultiSamples(0)
        self.renderWindow.SetAlphaBitPlanes(1)

        # SET VTK OBSERVERS
        self.Interactor.AddObserver("KeyPressEvent", self.keyPressEvent)

        # SET RENDERER CAMERA AS AN OBJECT
        self.cam = vtk.vtkCamera()
        self.renderer.SetActiveCamera(self.cam)
        self.get_cam()

        # SET THE DEFAULT INTERACTION STYLE as base_style
        self.base_style = vtk.vtkInteractorStyleTrackballCamera()
        self.Interactor.SetInteractorStyle(self.base_style)
        self.current_style = str('base_style')

        # ADD INTERACTOR WINDOW TO TOP BOX
        self.box_top = wx.BoxSizer(wx.VERTICAL)
        self.box_top.Add(self.Interactor, 1, wx.ALIGN_CENTRE | wx.EXPAND)

        # SET THE 3D MESH AXES SCALES
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.z_scale = 1.0

        # ADD MOUSE INTERACTION TOOLS ----------------------------------------------------------------------------------

        # CREATE TOOL BUTTONS ------------------------------------------------------------------------------------------

        # PICKER BUTTON
        self.picker_button = wx.Button(self.tdv_left_panel, -1, "Picking mode", size=(150, 20),
                                       style=wx.ALIGN_CENTRE)
        self.picker_button.Bind(wx.EVT_BUTTON, self.toggle_mode)

        # X SCALE SIZER SLIDER
        self.x_scale_text = wx.StaticText(self.tdv_left_panel, -1, "X-scale", style=wx.ALIGN_CENTRE)
        self.x_scale_slider = wx.Slider(self.tdv_left_panel, value=1.0, minValue=1.0, maxValue=5.0, size=(150, 20),
                                        style=wx.SL_HORIZONTAL)
        self.x_scale_slider.Bind(wx.EVT_SLIDER, self.set_x_scale)

        # Y SCALE SIZER SLIDER
        self.y_scale_text = wx.StaticText(self.tdv_left_panel, -1, "Y-scale", style=wx.ALIGN_CENTRE)
        self.y_scale_slider = wx.Slider(self.tdv_left_panel, value=1.0, minValue=1.0, maxValue=5.0, size=(150, 20),
                                        style=wx.SL_HORIZONTAL)
        self.y_scale_slider.Bind(wx.EVT_SLIDER, self.set_y_scale)

        # Z SCALE SIZER SLIDER
        self.z_scale_text = wx.StaticText(self.tdv_left_panel, -1, "Z-scale", style=wx.ALIGN_CENTRE)
        self.z_scale_slider = wx.Slider(self.tdv_left_panel, value=1.0, minValue=1.0, maxValue=10.0,
                                        size=(150, 20),
                                        style=wx.SL_HORIZONTAL)
        self.z_scale_slider.Bind(wx.EVT_SLIDER, self.set_z_scale)

        # POINT SIZER SLIDER
        self.size_text = wx.StaticText(self.tdv_left_panel, -1, "Point size", style=wx.ALIGN_CENTRE)
        self.size_slider = wx.Slider(self.tdv_left_panel, value=4.0, minValue=1.0, maxValue=10., size=(150, 20),
                                     style=wx.SL_HORIZONTAL)
        self.size_slider.Bind(wx.EVT_SLIDER, self.set_point_size)

        # ADD FLAG BUTTON
        self.flag_button = wx.Button(self.tdv_left_panel, -1, "Set Flag", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.flag_button.Bind(wx.EVT_BUTTON, self.set_flag)

        # ADD DELAUNAY BUTTON
        self.delaunay_button = wx.Button(self.tdv_left_panel, -1, "Grid", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.delaunay_button.Bind(wx.EVT_BUTTON, self.delaunay)

        # ADD PREDICTED DELAUNAY BUTTON
        self.predicted_delaunay_button = wx.Button(self.tdv_left_panel, -1, "Grid Predicted", size=(150, 20),
                                                   style=wx.ALIGN_CENTRE)
        self.predicted_delaunay_button.Bind(wx.EVT_BUTTON, self.render_predicted)

        # ADD DELETE SELECTED BUTTON
        self.delete_selected_button = wx.Button(self.tdv_left_panel, -1, "Delete", size=(150, 20),
                                                style=wx.ALIGN_CENTRE)
        self.delete_selected_button.Bind(wx.EVT_BUTTON, self.delete_selected)

        # ADD SAVE CM BUTTON
        self.save_cm_button = wx.Button(self.tdv_left_panel, -1, "Save .cm", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.save_cm_button.Bind(wx.EVT_BUTTON, self.save_cm)

        # ADD SAVE CM BUTTON
        self.toggle_button = wx.Button(self.tdv_left_panel, -1, "Toggle", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.toggle_button.Bind(wx.EVT_BUTTON, self.toggle)

        # PREDICTED MIN
        self.predicted_min_text = wx.StaticText(self.tdv_left_panel, -1, "Predicted Min", style=wx.ALIGN_CENTRE)
        self.predicted_min_color_slider = wx.Slider(self.tdv_left_panel, value=25, minValue=0,
                                                    maxValue=100, size=(150, 20),
                                                    style=wx.SL_HORIZONTAL)
        self.predicted_min_color_slider.Bind(wx.EVT_SLIDER, self.predicted_min)

        # PREDICTED MAX
        self.predicted_max_text = wx.StaticText(self.tdv_left_panel, -1, "Predicted Max", style=wx.ALIGN_CENTRE)
        self.predicted_max_color_slider = wx.Slider(self.tdv_left_panel, value=65, minValue=0,
                                                    maxValue=100, size=(150, 20), style=wx.SL_HORIZONTAL)
        self.predicted_max_color_slider.Bind(wx.EVT_SLIDER, self.predicted_max)

        # ADD BUTTONS ETC TO LEFT BOX
        self.left_box = wx.FlexGridSizer(cols=1, rows=20, hgap=5, vgap=5)
        self.left_box.AddMany([self.picker_button, self.x_scale_text, self.x_scale_slider, self.y_scale_text,
                               self.y_scale_slider, self.z_scale_text, self.z_scale_slider, self.size_text,
                               self.size_slider, self.flag_button, self.delaunay_button, self.predicted_delaunay_button,
                               self.delete_selected_button, self.save_cm_button, self.toggle_button,
                               self.predicted_min_text, self.predicted_min_color_slider, self.predicted_max_text,
                               self.predicted_max_color_slider])

        # INITIALIZE OBJECTS FOR LATER ---------------------------------------------------------------------------------
        self.cm = cm
        self.xyz = xyz
        self.xyz_cm_id = xyz_cm_id
        self.xyz_meta_data = xyz_meta_data
        self.xyz_cm_line_number = xyz_cm_line_number
        self.predicted_xyz = predicted_xyz
        self.diff_xyz = diff_xyz
        self.difference_xyz = difference_xyz
        self.score_xyz = score_xyz
        self.predicted_color_min = 0.25
        self.predicted_color_max = 0.65

        # RENDER THE .cm POINT DATA ------------------------------------------------------------------------------------
        self.do_point_render()

        # CREATE VTK PICKER OBJECTS ------------------------------------------------------------------------------------
        self.cell_picker = vtk.vtkCellPicker()
        self.node_picker = vtk.vtkPointPicker()
        self.cell_picker.SetTolerance(0.001)
        self.node_picker.SetTolerance(0.001)

        self.area_picker = vtk.vtkAreaPicker()  # vtkRenderedAreaPicker?
        self.rubber_band_style = vtk.vtkInteractorStyleRubberBandPick()

        # SET PICKER STYLE - SO LEFT MOUSE CLICK ALLOWS SELECTION OF A SINGLE POINT
        # self.picker_style = MouseInteractorHighLightActor(self.renderWindow, self.pointcloud)
        # self.picker_style.SetDefaultRenderer(self.renderer)
        # self.Interactor.SetInteractorStyle(self.picker_style)
        # self.Interactor.AddObserver("LeftButtonPressEvent", self.picker_style.leftButtonPressEvent)

        # PLACE BOX SIZERS IN CORRECT PANELS
        self.tdv_right_panel.SetSizerAndFit(self.box_top)
        self.tdv_left_panel.SetSizerAndFit(self.left_box)
        self.tdv_right_panel.SetSize(self.GetSize())
        self.tdv_left_panel.SetSize(self.GetSize())

        # INITIALIZE SWITCHES
        self.grid_created = 0

        # UPDATE AUI MANGER
        self.tdv_mgr.Update()

    def do_point_render(self):
        """
        RENDER 3D POINTS

        *** arg1 = XYZ NUMPY ARRAY
        """

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Render XYZ POINTS
        self.pointcloud = VtkPointCloud(self.xyz, self.difference_xyz, self.score_xyz)
        for k in range(len(self.xyz)):
            point = self.xyz[k]
            xyz_cm_id = self.xyz_cm_id[k]
            xyz_cm_line_number = self.xyz_cm_line_number[k]
            score_xyz = self.score_xyz[k]
            if self.difference_xyz is not None:
                difference_xyz = self.difference_xyz[k]
            else:
                difference_xyz = np.zeros_like(point)
            self.pointcloud.addPoint(point, xyz_cm_id, xyz_cm_line_number, difference_xyz, score_xyz)

        # ADD ACTOR TO RENDER
        self.renderer.AddActor(self.pointcloud.vtkActor)

        # SET POINT SIZE
        self.pointcloud.vtkActor.GetProperty().SetPointSize(4)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # Add 3D AXES WIDGET
        self.axesactor = vtk.vtkAxesActor()
        self.axes = vtk.vtkOrientationMarkerWidget()
        self.axes.SetOrientationMarker(self.axesactor)
        self.axes.SetInteractor(self.Interactor)
        self.axes.EnabledOn()
        self.axes.InteractiveOn()
        self.renderer.ResetCamera()

        # CREATE COLOR SCALE BAR
        self.cb_mapper = self.pointcloud.vtkActor.GetMapper()
        print(self.cb_mapper)
        self.cb_mapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
        self.sb = vtk.vtkScalarBarActor()
        self.sb.SetLookupTable(self.cb_mapper.GetLookupTable())
        self.renderer.AddActor(self.sb)
        self.sb.SetAnnotationTextScaling(100)
        self.sb.SetTitle("Depth (m)")
        self.sb.SetLabelFormat("%0.2f")
        self.sb.SetOrientationToHorizontal()
        self.sb.SetWidth(0.3)
        self.sb.SetHeight(0.05)
        self.sb.GetPositionCoordinate().SetValue(0.7, 0.05)

        #  % CREATE XYZ OUTLINE AXES GRID
        self.outlineMapper = self.pointcloud.vtkActor.GetMapper()
        self.outlineActor = vtk.vtkCubeAxesActor()
        self.outlineActor.SetBounds(self.xyz[:, 0].min()*self.x_scale, self.xyz[:, 0].max()*self.x_scale,
                                    self.xyz[:, 1].min()*self.y_scale, self.xyz[:, 1].max()*self.y_scale,
                                    self.xyz[:, 2].min()*self.z_scale, self.xyz[:, 2].max()*self.z_scale)

        self.outlineActor.SetCamera(self.renderer.GetActiveCamera())
        self.outlineActor.SetMapper(self.outlineMapper)
        self.outlineActor.DrawXGridlinesOn()
        self.outlineActor.DrawYGridlinesOn()
        self.outlineActor.DrawZGridlinesOn()
        self.renderer.AddActor(self.outlineActor)

        # TODO - CREATE BALLOON INFO WIDGET  THIS WILL ALLOW INFO OF THE POINT TO BE SHOWN WHEN HOVERED OVER WITH MOUSE
        # self.balloonRep = vtk.vtkBalloonRepresentation()
        # self.balloonRep.SetBalloonLayoutToImageRight()
        # self.balloonWidget = vtk.vtkBalloonWidget()
        # self.balloonWidget.SetInteractor(self.Interactor)
        # self.balloonWidget.SetRepresentation(self.balloonRep)
        # self.balloonWidget.AddBalloon(self.pointcloud.vtkActor, self.pointcloud.cm_poly_data.GetPoints().GetPoint())

    def delaunay(self, event):
        """CREATE 3D GRID"""
        if self.grid_created == 1:
            if self.meshActor.GetVisibility() == 1:
                self.meshActor.SetVisibility(False)
            else:
                self.meshActor.SetVisibility(True)
            self.renderWindow.Render()
            print("meshActor exists")
        else:
            self.grid_created = 1
            self.cell_array = vtk.vtkCellArray()
            self.boundary = self.pointcloud.cm_poly_data
            self.boundary.SetPoints(self.pointcloud.cm_poly_data.GetPoints())
            self.boundary.SetPolys(self.cell_array)

            self.delaunay = vtk.vtkDelaunay2D()

            self.delaunay.SetInputData(self.pointcloud.cm_poly_data)
            self.delaunay.SetSourceData(self.boundary)

            self.delaunay.Update()

            self.meshMapper = vtk.vtkPolyDataMapper()
            self.meshMapper.SetInputData(self.pointcloud.cm_poly_data)
            self.meshMapper.SetColorModeToDefault()
            self.meshMapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
            self.meshMapper.SetScalarVisibility(1)
            self.meshMapper.SetInputConnection(self.delaunay.GetOutputPort())
            self.meshActor = vtk.vtkActor()
            self.meshActor.SetMapper(self.meshMapper)
            # self.meshActor.GetProperty().SetEdgeColor(0, 0, 1)
            self.meshActor.GetProperty().SetInterpolationToFlat()
            # self.meshActor.GetProperty().SetRepresentationToWireframe()

            self.renderer.AddActor(self.meshActor)
            self.renderWindow.Render()

    def render_predicted(self, event):
        print("self.predicted_xyz ==")
        print(self.predicted_xyz)
        try:
            print("rendering predicted")
            #Render XYZ POINTS
            self.predicted_pointcloud = VtkPointCloudPredicted(self.predicted_xyz)
            print("ADDING POINTS")
            for k in range(len(self.predicted_xyz)):
                point = self.predicted_xyz[k]
                self.predicted_pointcloud.addPoint(point)
            print("ADDING ACTOR TO RENDER")
            # ADD ACTOR TO RENDER
            self.renderer.AddActor(self.predicted_pointcloud.vtkActor)
            self.predicted_pointcloud.vtkActor.GetProperty().SetPointSize(1)
            # HIDE
            self.predicted_pointcloud.vtkActor.SetVisibility(False)

            print("DOING delaunay_predicted")
            self.delaunay_predicted()

            self.renderWindow.Render()

            print("DONE")
        except AttributeError:
            print("ERROR FAILED TO RENDER predicted_xyz")

    def delaunay_predicted(self):
        """CREATE GRID OF PREDICTED BATHYMETRY"""
        try:
            if self.predicted_meshActor.GetVisibility() == 1:
                self.predicted_meshActor.SetVisibility(False)
            else:
                self.predicted_meshActor.SetVisibility(True)
            self.renderWindow.Render()
            print("predicted_meshActor exists")
        except AttributeError:
            try:
                print("CREATING PREDICTED GRID")
                self.cell_array = vtk.vtkCellArray()
                self.predicted_boundary = self.predicted_pointcloud.poly_data
                self.predicted_boundary.SetPoints(self.predicted_pointcloud.poly_data.GetPoints())
                self.predicted_boundary.SetPolys(self.cell_array)

                self.predicted_delaunay = vtk.vtkDelaunay2D()
                if vtk.VTK_MAJOR_VERSION <= 5:
                    self.predicted_delaunay.SetInput(self.predicted_pointcloud.poly_data.GetOutput())
                    self.predicted_delaunay.SetSource(self.predicted_boundary)
                else:
                    self.predicted_delaunay.SetInputData(self.predicted_pointcloud.poly_data)
                    self.predicted_delaunay.SetSourceData(self.predicted_boundary)

                self.predicted_delaunay.Update()

                print("MAKING MAPPER")
                self.predicted_meshMapper = vtk.vtkPolyDataMapper()
                self.predicted_meshMapper.SetInputData(self.predicted_pointcloud.poly_data)

                print("MAKING LUT")
                # CREATE COLOR LOOK UP TABLE
                self.predicted_lut = self.make_lookup_table()
                self.predicted_meshMapper.SetLookupTable(self.predicted_lut)

                print("SET MAPPER INPUTS")
                # SET MAPPER INPUTS
                self.predicted_meshMapper.SetScalarRange(self.predicted_xyz[:, 2].min(), self.predicted_xyz[:, 2].max())
                self.predicted_meshMapper.SetScalarVisibility(1)
                self.predicted_meshMapper.SetInputConnection(self.predicted_delaunay.GetOutputPort())

                # CREATE ACTOR
                self.predicted_meshActor = vtk.vtkActor()
                self.predicted_meshActor.SetMapper(self.predicted_meshMapper)
                self.predicted_meshActor.GetProperty().SetInterpolationToFlat()

                # ADD MESH TO RENDER
                self.renderer.AddActor(self.predicted_meshActor)
                self.renderWindow.Render()
            except AttributeError:
                print("FAILED ON CREATING PREDICTED")

    def make_lookup_table(self):
        """
        Make a color lookup table using vtkColorSeries.
        :return: An indexed lookup table.
        """
        # SET UPPER AND LOWER VALUES
        a = self.xyz[:, 2].min()
        b = self.xyz[:, 2].max()

        # CREATE LUT
        lut = vtk.vtkColorTransferFunction()

        #% SET COLOR BANDS (GREYSCALE)
        # % NB. FORMAT:: VALUE THEN RGB CODE (THREE NUMBERS)
        lut.AddRGBPoint(a, self.predicted_color_min, self.predicted_color_min, self.predicted_color_min)
        lut.AddRGBPoint(b, self.predicted_color_max, self.predicted_color_max, self.predicted_color_max)
        return lut

    def set_point_size(self, value):
        """SET THE SIZE OF THE DEPTH POINTS"""
        self.size = float(self.size_slider.GetValue())
        self.pointcloud.vtkActor.GetProperty().SetPointSize(self.size)
        self.pointcloud.vtkActor.Modified()
        self.renderWindow.Render()
        return

    def set_z_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        # GET THE NEW SCALE VALUE
        self.z_scale = float(self.z_scale_slider.GetValue())

        # REPLACE CURRENT RENDER WITH NEW DATA
        self.re_render()

        return

    def set_x_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        # GET THE NEW SCALE VALUE
        self.x_scale = float(self.x_scale_slider.GetValue())

        # REPLACE CURRENT RENDER WITH NEW DATA
        self.re_render()

        return

    def set_y_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        # GET THE NEW SCALE VALUE
        self.y_scale = float(self.y_scale_slider.GetValue())

        # REPLACE CURRENT RENDER WITH NEW DATA
        self.re_render()

        return

    def predicted_min(self, value):
        """RESCALE THE PREDICTED GRID COLOR SCALE"""
        try:
            #% GET THE NEW SCALE VALUE
            self.predicted_color_min = float(self.predicted_min_color_slider.GetValue())
            self.new_lut = self.make_lookup_table()

            self.predicted_meshMapper.SetLookupTable(self.new_lut)

            self.renderWindow.Render()
        except AttributeError:
            print("ERROR IN predicted_min")
            pass
        return

    def predicted_max(self, value):
        """RESCALE THE PREDICTED GRID COLOR SCALE"""
        try:
            #% GET THE NEW SCALE VALUE
            self.predicted_color_max = float(self.predicted_max_color_slider.GetValue())

            self.new_lut = self.make_lookup_table()

            self.predicted_meshMapper.SetLookupTable(self.new_lut)

            self.renderWindow.Render()
        except AttributeError:
            print("ERROR IN predicted_max")
            pass
        return

    def toggle(self, event):
        """Toggle Display (depth/difference/score)"""
        if self.pointcloud.cm_poly_data.GetPointData().GetScalars().GetName() == 'Z':
            print("WAS Z...")
            self.pointcloud.cm_poly_data.GetPointData().SetActiveScalars('DIFF')
            # print(self.difference_xyz[:, 2].min())
            # print(self.difference_xyz[:, 2].max())
            # print(np.mean(self.difference_xyz[:, 2]))
            # print(np.std(self.difference_xyz[:, 2]))
            self.pointcloud.mapper.SetScalarRange(self.difference_xyz[:, 2].min(), self.difference_xyz[:, 2].max())
            # self.pointcloud.mapper.SetScalarRange(0.0, 0.1)
            print("NOW SET AS DIFFERENCE")
        elif self.pointcloud.cm_poly_data.GetPointData().GetScalars().GetName() == 'DIFF':
            print("WAS DIFFERENCE...")
            self.pointcloud.cm_poly_data.GetPointData().SetActiveScalars('SCORE')
            self.pointcloud.mapper.SetScalarRange(self.score_xyz[:, 2].min(), self.score_xyz[:, 2].max())
            print("NOW SET AS SCORE")
        else:
            print("WAS SCORE...")
            self.pointcloud.cm_poly_data.GetPointData().SetActiveScalars('Z')
            self.pointcloud.mapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
            print("NOW SET AS Z")
        self.renderWindow.Render()

    def re_render(self):
        """
        # RE RENDER 3D POINTS AFTER REMOVING SELECTION
        """
        if self.current_style is 'base_style':
            # GET ACTIVE CAM POSITION
            # self.get_cam()

            print("re rendering")
            # REMOVE EXSISTING POINT CLOUD FROM THE RENDER AND MEMORY
            self.renderer.RemoveActor(self.pointcloud.vtkActor)
            del self.pointcloud.vtkActor
            del self.pointcloud

            # CREATE POINT DATA WITH NEW SCALING VALUES
            # self.xyz = np.divide(self.cm[:, 1:4], (self.x_scale, self.y_scale, self.z_scale))
            # self.difference_xyz = np.divide(self.diff_xyz, (self.x_scale, self.y_scale, self.z_scale))

            # CREATE THE POINT CLOUD VTK ACTOR
            self.pointcloud = VtkPointCloud(self.xyz, self.difference_xyz, self.score_xyz)
            for k in range(len(self.xyz)):
                point = self.xyz[k]
                xyz_cm_id = self.xyz_cm_id[k]
                xyz_cm_line_number = self.xyz_cm_line_number[k]
                score_xyz = self.score_xyz[k]
                if self.difference_xyz is not None:
                    difference_xyz = self.difference_xyz[k]
                else:
                    difference_xyz = np.zeros_like(point)
                self.pointcloud.addPoint(point, xyz_cm_id, xyz_cm_line_number, difference_xyz, score_xyz)

            # RENDER THE NEW POINT CLOUD
            self.renderer.AddActor(self.pointcloud.vtkActor)
            self.set_point_size(float(self.size_slider.GetValue()))

            # RESCALE THE AXIS OUTLINE
            self.outlineActor.SetBounds(self.xyz[:, 0].min() * self.x_scale, self.xyz[:, 0].max() * self.x_scale,
                                        self.xyz[:, 1].min() * self.y_scale, self.xyz[:, 1].max() * self.y_scale,
                                        self.xyz[:, 2].min() * self.z_scale, self.xyz[:, 2].max() * self.z_scale)
            # CHECK IF GRID ACTOR IS ON
            if self.grid_created == 1:
                self.grid_created = 0
                self.renderer.AddActor(self.meshActor)

            # SET ACTIVE CAM
            ## self.renderer.SetActiveCamera(self.cam)
            ## self.set_cam()

            # RE RENDER THE WINDOW
            self.pointcloud.vtkActor.Modified()
            # self.renderer.SetActiveCamera(self.cam)
            self.renderWindow.Render()
            # self.set_cam()
            # print("FINISHED")
            # self.Interactor.RemoveObservers('KeyPressEvent')
            # self.Interactor.RemoveObservers('CharEvent')

    def get_cam(self):
        print("!!!!!!!")
        print("get cam")
        print("!!!!!!!!")
        self.focal_point = self.cam.GetFocalPoint()
        self.positon = self.cam.GetPosition()
        self.view_up = self.cam.GetViewUp()
        self.view_angle = self.cam.GetViewAngle()
        self.parallel_projection = self.cam.GetParallelProjection()
        self.parallel_scale = self.cam.GetParallelScale()
        self.clip = self.cam.GetClippingRange()
        print(self.focal_point)
        print(self.positon)
        print(self.view_up)
        print(self.view_angle)
        print(self.parallel_projection)
        print(self.parallel_scale)
        print(self.clip)

    def set_cam(self):
        print("##########")
        print("set_cam")
        print("##########")
        print(self.focal_point)
        print(self.positon)
        print(self.view_up)
        print(self.view_angle)
        print(self.parallel_projection)
        print(self.parallel_scale)
        print(self.clip)
        self.cam.SetFocalPoint(self.focal_point)
        self.cam.SetPosition(self.positon)
        self.cam.SetViewUp(self.view_up)
        self.cam.SetViewAngle(self.view_angle)
        self.cam.SetParallelProjection(self.parallel_projection)
        self.cam.SetParallelScale(self.parallel_scale)
        self.cam.SetClippingRange(self.clip)
        return

    def delete_selected(self):
        """CREATES A NEW NUMPY ARRAY of the cm FILE WITH SELECTED NODES REMOVED"""
        print("Deleting")
        try:
            # DELETE SELECTED VALUES
            self.selected_cm_line_number = vtk_to_numpy(
                self.rubber_style.selected.GetPointData().GetArray("cm_line_number")).astype(int)
            self.new_cm = np.delete(self.cm, self.selected_cm_line_number, 0)
            self.cm = self.new_cm

            # REPLACE CURRENT RENDER WITH NEW DATA
            self.renderer.RemoveActor(self.rubber_style.selected_actor)
            self.re_render()

            # UPDATE RENDER
            self.renderWindow.Render()

        except AttributeError:
            print("attr error")
            pass

    def set_flag(self, event):
        """SETS FLAG FOR SELECTED NODES"""
        print("SETTING FLAG")
        try:
            # DELETE SELECTED VALUES
            self.selected_cm_line_number = vtk_to_numpy(
                self.rubber_style.selected.GetPointData().GetArray("cm_line_number")).astype(int)

            # CLONE CURRENT cm file
            self.new_cm = np.copy(self.cm)

            #SET FLAG AS 1 FOR ALL SELECTED NODES
            flag_column_index = np.shape(self.cm)[1]
            for x in range(len(self.selected_cm_line_number)):
                index = self.selected_cm_line_number[x]  # % GET INDEX VALUE
                self.new_cm[index, 4] = 1  # % INSERT FLAG IN COL 1

            # REMOVE SELECTED ACTOR
            self.renderer.RemoveActor(self.rubber_style.selected_actor)

            # DRAW FLAGGED ACTOR
            self.rubber_style.flagged_mapper = vtk.vtkDataSetMapper()
            self.rubber_style.flagged_actor = vtk.vtkActor()
            self.rubber_style.flagged_actor.SetMapper(self.rubber_style.flagged_mapper)
            self.rubber_style.flagged_mapper.SetInputData(self.rubber_style.selected)
            self.rubber_style.flagged_actor.GetMapper().ScalarVisibilityOff()
            self.rubber_style.flagged_actor.GetProperty().SetColor(0, 0, 0)  # (R, G, B)
            self.rubber_style.flagged_actor.GetProperty().SetPointSize(10)
            self.renderer.AddActor(self.rubber_style.flagged_actor)

            # REPLACE CURRENT RENDER WITH NEW DATA
            self.re_render()

            # UPDATE LIVE RENDER
            self.renderWindow.Render()

        except AttributeError:
            print("attr error")
            pass

    def save_cm(self, event):
        """# %SET OUTPUT FILE NAME AND DIR"""
        save_file_dialog = wx.FileDialog(self, "Save edited .cm file", "", "", ".cm file (*.cm)|*.cm",
                                         wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if save_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # %THE USER CHANGED THEIR MIND

        #SAVE TO DISC
        outputfile = save_file_dialog.GetPath()
        np.savetxt(outputfile, self.cm, delimiter=" ")

    def keyPressEvent(self, event, obj):
        key = self.Interactor.GetKeyCode()

        # ACTIVATE POINT PICKER
        if key == 'r':
            self.get_cam()
            self.toggle_mode(event)
            self.set_cam()
        # DELETE SELECTED NODE
        if key == 'd':
            self.get_cam()
            self.delete_selected()
            self.set_cam()

        # SET THE CAMERA BACK TO THE PREVIOUS POSITION
        if key == 'c':
            self.set_cam()

        # RERENDER THE VTK WINDOW
        self.re_render()

    def toggle_mode(self, event):
        """
        Turn on/off node picking mode
        :param event:
        :return: None
        """
        print("current style = %s" % self.current_style)
        if self.current_style is 'rubber_band':
            # REMOVE THE CURRENT HIGHLIGHT ACTOR (IF THERE IS ONE) FROM SCREEN
            if self.rubber_style.selected_actor:
                self.renderer.RemoveActor(self.rubber_style.selected_actor)
                del self.rubber_style.selected_actor

            del self.rubber_style
            print('setting style as base_style')
            self.Interactor.SetInteractorStyle(self.base_style)
            self.current_style = str('base_style')

            # self.renderer.Render()
            self.renderWindow.Render()
        else:
            print('setting style as rubber_band')
            # MAKE AREA PICKER ACTOR
            self.area_picker = vtk.vtkAreaPicker()

            # SET THE PICKING METHOD IN THE CURRENT VTK WINDOW
            self.Interactor.SetPicker(self.area_picker)

            # CREATE RUBBER BAND INTERACTOR STYLE
            self.rubber_style = RubberBand(self.renderWindow, self.renderer, self.pointcloud, self.Interactor,
                                           self.area_picker, self.cm)

            # SET INTERACTOR STYLE
            self.Interactor.SetInteractorStyle(self.rubber_style)
            self.current_style = str('rubber_band')

        # RERENDER THE VTK WINDOW
        self.re_render()
        return





