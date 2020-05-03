import vtk

class VtkPointCloud:
    def __init__(self, xyz, xyz_difference, xyz_score, maxNumPoints=10e7):

        #INITIALISE POINT DATA
        self.xyz = xyz  # % THIS IS THE XYZ DATA
        self.xyz_difference = xyz_difference  # % THIS IS THE XYZ WITH Z = DIFFERENCE BETWEEN OBS && PREDICTED
        self.maxNumPoints = maxNumPoints
        #CREATE vtkPolyData OBJECT
        self.cm_poly_data = vtk.vtkPolyData()
        self.xyz_points = vtk.vtkPoints()
        self.cm_poly_data.SetPoints(self.xyz_points)

        #CREATE vtkPolyData VERTICES
        self.xyz_cells = vtk.vtkCellArray()
        self.cm_poly_data.SetVerts(self.xyz_cells)
        # self.xyz_cells.SetName('XYArray')

        #CREATE vtkPolyData SCALAR VALUES

        # SCALAR 1 = cm file line number - This is used for numpy array data manipulation
        self.cm_line_number = vtk.vtkDoubleArray()
        self.cm_line_number.SetName('cm_line_number')
        self.cm_poly_data.GetPointData().AddArray(self.cm_line_number)

        # SCALAR 2 = cm file id
        self.cm_id = vtk.vtkDoubleArray()
        self.cm_id.SetName('cm_id')
        self.cm_poly_data.GetPointData().AddArray(self.cm_id)

        # SCALAR 3 = DEPTH
        self.xyz_depth = vtk.vtkDoubleArray()
        self.xyz_depth.SetName('Z')
        self.cm_poly_data.GetPointData().AddArray(self.xyz_depth)
        self.cm_poly_data.GetPointData().SetScalars(self.xyz_depth)
        self.cm_poly_data.GetPointData().SetActiveScalars('Z')

        # SCALAR 4 = DIFFERENCE (PREDICTED-OBSERVED) DEPTHS
        self.diff = vtk.vtkDoubleArray()
        self.diff.SetName('DIFF')
        self.cm_poly_data.GetPointData().AddArray(self.diff)

        # SCALAR 5 = DIFFERENCE (PREDICTED-OBSERVED) DEPTHS
        self.score = vtk.vtkDoubleArray()
        self.score.SetName('SCORE')
        self.cm_poly_data.GetPointData().AddArray(self.score)

        # OLD METHOD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # SET COLOR MAPPER
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputData(self.cm_poly_data)
        self.mapper.SetColorModeToDefault()
        self.mapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
        self.mapper.SetScalarVisibility(1)
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(self.mapper)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # CREATE ACTOR TO BE ADDED TO RENDER
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(self.mapper)

    def addPoint(self, point, xyz_cm_id, xyz_cm_line_number, difference_xyz, score_xyz):

        if self.xyz_points.GetNumberOfPoints() < self.maxNumPoints:
            pointId = self.xyz_points.InsertNextPoint(point[:])
            self.xyz_depth.InsertNextValue(point[2])
            self.xyz_cells.InsertNextCell(1)
            self.xyz_cells.InsertCellPoint(pointId)
            self.cm_id.InsertNextValue(xyz_cm_id)
            self.cm_line_number.InsertNextValue(xyz_cm_line_number)
            self.diff.InsertNextValue(difference_xyz[2])
            self.score.InsertNextValue(score_xyz[2])
        else:
            print("ERROR: MORE THAN 10e6 POINTS IN FILE")
            return


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class VtkPointCloudPredicted:
    def __init__(self, xyz, maxNumPoints=10e7):
        print("STARTING  VtkPointCloudPredicted")
        #INITIALISE POINT DATA
        self.xyz = xyz  # % THIS IS THE XYZ DATA
        self.maxNumPoints = maxNumPoints

        print("CREATE vtkPolyData OBJECT")
        #CREATE vtkPolyData OBJECT
        self.poly_data = vtk.vtkPolyData()
        self.xyz_points = vtk.vtkPoints()
        self.poly_data.SetPoints(self.xyz_points)

        print("CREATE vtkPolyData VERTICES")
        #CREATE vtkPolyData VERTICES
        self.xyz_cells = vtk.vtkCellArray()
        self.poly_data.SetVerts(self.xyz_cells)

        # % NB. SCALAR VALUES ARE INITIALISED HERE AND THEN THE VALUES ARE ADDED in addPoint
        print("CREATE SCALAR")
        # SCALAR 1 = DEPTH
        self.xyz_depth = vtk.vtkDoubleArray()
        self.xyz_depth.SetName('Z')
        self.poly_data.GetPointData().AddArray(self.xyz_depth)
        self.poly_data.GetPointData().SetScalars(self.xyz_depth)
        self.poly_data.GetPointData().SetActiveScalars('Z')

        #  %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # % LUT TABLE
        print("CREATE LUT")
        self.lut = self.make_lookup_table()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetLookupTable(self.lut)
        self.mapper.SelectColorArray('Z')
        #  %~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        print("CREATE SET MAPPER STUFF")
        self.mapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
        self.mapper.SetInputData(self.poly_data)
        self.mapper.SetScalarModeToUsePointFieldData()

        # % CREATE ACTOR
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(self.mapper)

    def addPoint(self, point):
        if self.xyz_points.GetNumberOfPoints() < self.maxNumPoints:
            pointId = self.xyz_points.InsertNextPoint(point[:])
            self.xyz_depth.InsertNextValue(point[2])
            self.xyz_cells.InsertNextCell(1)
            self.xyz_cells.InsertCellPoint(pointId)
        else:
            print("ERROR: MORE THAN 10e8 POINTS IN FILE")
            return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def make_lookup_table(self):
        """
        Make a lookup table using vtkColorSeries.
        :return: An indexed lookup table.
        """
        # # Make the lookup table.
        # colorSeries = vtk.vtkColorSeries()
        # # # Select a color scheme.
        # colorSeriesEnum = colorSeries.BREWER_DIVERGING_BROWN_BLUE_GREEN_9
        # # # colorSeriesEnum = colorSeries.BREWER_DIVERGING_SPECTRAL_10
        # # # colorSeriesEnum = colorSeries.BREWER_DIVERGING_SPECTRAL_3
        # # # colorSeriesEnum = colorSeries.BREWER_DIVERGING_PURPLE_ORANGE_9
        # # colorSeriesEnum = colorSeries.BREWER_SEQUENTIAL_BLUE_PURPLE_9
        # # # colorSeriesEnum = colorSeries.BREWER_SEQUENTIAL_BLUE_GREEN_9
        # # # colorSeriesEnum = colorSeries.BREWER_QUALITATIVE_SET3
        # # # colorSeriesEnum = colorSeries.CITRUS
        # colorSeries.SetColorScheme(colorSeriesEnum)
        # lut = vtk.vtkLookupTable()
        # colorSeries.BuildLookupTable(lut)
        # lut.SetNanColor(1, 0, 0, 1)

        a = self.xyz[:, 2].min()
        b = self.xyz[:, 2].max()
        lut = vtk.vtkColorTransferFunction()
        # lut.AddRGBPoint(a, 0.0, 0.0, 1.0)
        # lut.AddRGBPoint(a + (b - a) / 4, 0.0, 0.5, 0.5)
        # lut.AddRGBPoint(a + (b - a) / 2, 0.0, 1.0, 0.0)
        # lut.AddRGBPoint(b - (b - a) / 4, 0.5, 0.5, 0.0)
        # lut.AddRGBPoint(b, 1.0, 0.0, 0.0)

        # % NB. FORMAT:: VALUE THEN RGB CODE (THREE NUMBERS)
        lut.AddRGBPoint(a, 0.25, 0.25, 0.25)
        lut.AddRGBPoint(b, 0.75, 0.75, 0.75)
        return lut