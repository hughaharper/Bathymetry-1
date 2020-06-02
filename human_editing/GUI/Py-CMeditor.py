"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Description**

GUI application for viewing/editing bathymetry data.
Brook Tozer, SIO IGPP 2018-2020.

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Dependencies**

NumPy
Matplotlib
pylab
wxpython
VTK

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**References**

***

***

***

***

***
Icons where designed using the Free icon Maker.
https://freeiconmaker.com/
***

***
Documentation created using Sphinx.
***

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# IMPORT MODULES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# to-do vtk.vtkRadiusOutlierRemoval

import matplotlib as mpl
mpl.use('WXAgg')
from matplotlib import pyplot as plt
import wx
import wx.py as py
import wx.lib.agw.aui as aui
from wx.lib.buttons import GenBitmapButton
import numpy as np
import glob
import os
import webbrowser
import folium
import subprocess
from wx import html2
from three_dim_viewer import ThreeDimViewer
from folium import LayerControl
from folium.plugins import Draw
from folium.plugins import MousePosition
from folium.plugins import FastMarkerCluster
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PyCMeditor(wx.Frame):
    """
    Master class for program.
    Most functions are contained in this Class.
    Sets GUI display panels, sizer's and event bindings.
    Additional classes are used for "pop out" windows (Dialog boxes).
    Objects are passed between the master class and Dialog boxes.
    """

    # INITIALISE GUI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Py-CMeditor', size=(1800, 1050))

        # GET CURRENT WORKING DIR
        self.cwd = os.path.dirname(os.path.realpath(__file__))

        # DIR CONTAINING PROGRAM ICONS
        self.gui_icons_dir = self.cwd + '/icons/'

        # START AUI WINDOW MANAGER
        self.mgr = aui.AuiManager()

        # TELL AUI WHICH FRAME TO USE
        self.mgr.SetManagedWindow(self)

        # SET SPLITTER WINDOW TOGGLE IMAGES
        images = wx.ImageList(16, 16)
        top = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_MENU, (16, 16))
        bottom = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_MENU, (16, 16))
        images.Add(top)
        images.Add(bottom)

        # CREATE PANEL TO FILL WITH CONTROLS
        self.leftPanel = wx.SplitterWindow(self, wx.ID_ANY, size=(115, 1000), style=wx.SP_NOBORDER | wx.EXPAND)
        self.leftPanel.SetMinimumPaneSize(1)
        self.leftPanel.SetBackgroundColour('white')

        self.leftPanel_top = wx.Panel(self.leftPanel, -1, size=(115, 100), style=wx.ALIGN_RIGHT)
        self.leftPanel_bottom = wx.Panel(self.leftPanel, -1, size=(115, 900), style=wx.ALIGN_RIGHT)

        self.leftPanel.SplitHorizontally(self.leftPanel_top, self.leftPanel_bottom, 100)

        # CREATE PANEL TO FILL WITH INTERACTIVE MAP
        self.rightPanelbottom = wx.Panel(self, -1, size=(1700, 900), style=wx.ALIGN_RIGHT)
        self.rightPanelbottom.SetBackgroundColour('white')

        # CREATE PANEL FOR PYTHON CONSOLE (USED FOR DEBUGGING AND CUSTOM USAGES)
        self.ConsolePanel = wx.Panel(self, -1, size=(1700, 50), style=wx.ALIGN_LEFT | wx.BORDER_RAISED | wx.EXPAND)
        intro = "###############################################################\r" \
                "!USE import sys; then sys.Gmg.OBJECT TO ACCESS PROGRAM OBJECTS \r" \
                "ctrl+up FOR COMMAND HISTORY                                    \r" \
                "###############################################################"
        py_local = {'__app__': 'gmg Application'}
        sys.t = self
        self.win = py.shell.Shell(self.ConsolePanel, -1, size=(2200, 1100),
                                  locals=py_local, introText=intro)

        # ADD THE PANES TO THE AUI MANAGER
        self.mgr.AddPane(self.leftPanel, aui.AuiPaneInfo().Name('left').Left().Caption("Controls"))
        self.mgr.AddPane(self.rightPanelbottom, aui.AuiPaneInfo().Name('rightbottom').CenterPane())
        self.mgr.AddPane(self.ConsolePanel, aui.AuiPaneInfo().Name('console').Bottom().Caption("Console"))
        self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE BY DEFAULT
        self.mgr.Update()

        # CREATE PROGRAM MENUBAR & TOOLBAR (PLACED AT TOP OF FRAME)
        self.create_menu()
        self.create_toolbar()

        # CREATE STATUS BAR
        self.statusbar = self.CreateStatusBar(3, style=wx.NO_BORDER)
        self.controls_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'redock_2.png'),
                                               pos=(0, -5), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.show_controls, self.controls_button)

        # PYTHON CONSOLE
        self.console_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'python_16.png'),
                                              pos=(24, -5), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.show_console, self.console_button)

        # self.status_text = " || Current file: %s "
        # self.statusbar.SetStatusWidths([-1, -1, 1700])
        # self.statusbar.SetStatusText(self.status_text, 2)
        # self.statusbar.SetSize((1800, 24))

        # INITIALISE NAV FRAME
        self.draw_map_window()
        self.export_click_count = 0

        # SET PROGRAM STATUS
        self.bind_button_events()

        # BIND PROGRAM EXIT BUTTON WITH EXIT FUNCTION
        self.Bind(wx.EVT_CLOSE, self.on_close_button)

        # MAXIMIZE FRAME
        self.Maximize()

        # INITIALISE THREE DIMENSION VIEWER OBJECTS
        self.predicted_xyz = None
        self.difference_xyz = None

    def create_menu(self):
        """# CREATES GUI MENUBAR"""
        self.menubar = wx.MenuBar()  # MAIN MENUBAR

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # FILE MENU
        self.file = wx.Menu()  # CREATE MENUBAR ITEM

        m_open_cm_file = self.file.Append(-1, "Open \tCtrl-L", "Open")
        self.Bind(wx.EVT_MENU, self.open_cm_file, m_open_cm_file)

        self.file.AppendSeparator()

        m_exit = self.file.Append(-1, "Exit...\tCtrl-X", "Exit...")
        self.Bind(wx.EVT_MENU, self.exit, m_exit)

        self.file.AppendSeparator()

        self.menubar.Append(self.file, "&File")  # DRAW FILE MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # EDIT MENU
        self.edit = wx.Menu()  # CREATE MENUBAR ITEM

        self.menubar.Append(self.edit, "&Edit")  # DRAW EDIT MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # FIND MENU'  # CREATE MENUBAR ITEM
        self.find = wx.Menu()

        self.menubar.Append(self.find, "&Find")  # DRAW FIND MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # VIEW MENU'  # CREATE MENUBAR ITEM
        self.view = wx.Menu()

        self.menubar.Append(self.view, "&View")  # DRAW VIEW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # GO MENU'  # CREATE MENUBAR ITEM
        self.go = wx.Menu()

        self.menubar.Append(self.go, "&Go")  # DRAW GO MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # TOOLS MENU'  # CREATE MENUBAR ITEM
        self.tools = wx.Menu()

        self.menubar.Append(self.tools, "&Tools")  # DRAW TOOLS MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # WINDOW MENU'  # CREATE MENUBAR ITEM
        self.window = wx.Menu()

        self.menubar.Append(self.window, "&Window")  # DRAW WINDOW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # SET MENUBAR'
        self.SetMenuBar(self.menubar)

    def create_toolbar(self):
        """CREATE TOOLBAR"""
        # TOOLBAR - (THIS IS THE ICON BAR BELOW THE MENU BAR)
        self.toolbar = self.CreateToolBar()

        t_save_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'save_24.png'))
        # self.Bind(wx.EVT_TOOL, self.save_model, t_save_model)

        t_load_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'load_24.png'))
        # self.Bind(wx.EVT_TOOL, self.load_model, t_load_model)

        self.toolbar.Realize()
        self.toolbar.SetSize((1790, 36))

    def draw_map_window(self):
        """INITALISE FOLIUM INTERACTIVE MAP"""

        # CREATE MAP
        self.folium_map = folium.Map(location=[0.0, 0.0],
                                     zoom_start=2,
                                     attr='map',
                                     no_wrap=True,
                                     name='map',
                                     tiles=None)

        # ADD SRTM15+ TILES
        self.tiles = folium.TileLayer(tiles=self.cwd + '/../../../8-xyz-tiles/{z}/{x}/{y}.png',
                                      name='SRTM15+V2.1', attr='SRTM15+V2.1', control=False)
        self.tiles.add_to(self.folium_map)

        # self.V2tiles = folium.TileLayer(tiles=self.cwd + '/../../../SRTM15+V2-tiles/{z}/{x}/{y}.png',
        #                               name='SRTM15+V2.0', attr='SRTM15+V2.0', control=True)
        # self.V2tiles.add_to(self.folium_map)

        # LOAD DRAWING FUNCTIONALITY
        # importer=True,
        self.draw = Draw(filename='outpoint.geojson',
                         draw_options={'polyline': False, 'rectangle': False, 'circle': False, 'marker': False,
                                       'circlemarker': False},
                         edit_options={'poly': {'allowIntersection': False}})
        self.draw.add_to(self.folium_map)

        # MOUSE POSITION
        self.mouse_position = MousePosition()
        self.mouse_position.add_to(self.folium_map)

        # CREATE FOLIUM SCATTER PLOT OBJECT FOR THE .cm FILE
        self.bad_fg = folium.FeatureGroup(name="Bad")
        self.uncertain_fg = folium.FeatureGroup(name="Uncertain")
        self.good_fg = folium.FeatureGroup(name="Good", show=False)

        self.folium_map.add_child(self.bad_fg)
        self.folium_map.add_child(self.uncertain_fg)
        self.folium_map.add_child(self.good_fg)

        # HIDE/SHOW FUNCTIONALITY
        self.controls = LayerControl(position='bottomright', collapsed=False)
        self.controls.add_to(self.folium_map)

        # SAVE MAP AS HTML
        self.folium_map.save("my_map.html")

        # CREATE GUI HTML WINDOW
        # wx.html2.WebView.MSWSetEmulationLevel(wx.html2.WEBVIEWIE_EMU_IE11)
        self.browser = wx.html2.WebView.New(self.rightPanelbottom, -1)
        # self.browser.MSWSetEmulationLevel(level=wx.html2.WEBVIEWIE_EMU_IE11)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_export)
        # self.browser.Bind(wx.html2.EVT_HTML_LINK_CLICKED, self.on_import)
        # wx.html2.WebView.WEBVIEW_
        # LOAD FOLIUM MAP INTO HTML WINDOW
        self.browser.LoadURL(self.cwd + '/my_map.html')

        # SET MAIN MAP NAME
        self.main_map_url = str(self.browser.GetCurrentURL())
        print(self.main_map_url)

        # DRAW BUTTON WINDOW
        self.draw_button_and_list_frame()

        # UPDATE DISPLAY
        self.size_handler()

        # REFRESH SIZER POSITIONS
        self.Hide()
        self.Show()

    def on_import(self, event):
        """
        :param event:
        """
        self.browser.RunScript("document.write('Hello from wx.Widgets!')")

    def on_export(self, event):
        """
        FIRERS WHEN A NEW WINDOW IS OPENED IN THE wx.html2.WebView
        USE THIS CALLBACK TO EXPORT POLYGONS FROM THE MAP
        """
        print("export pressed")
        # self.export_click_count += 1
        # if self.browser.GetCurrentURL() == self.main_map_url:
        #     pass
        # else:
        #     text = self.browser.GetPageText()
        #     print(text)
        #     # self.browser.RunScript("document.write('Hello from wx.Widgets!')")
        #     self.browser.GoBack()

    def load_polygon(self, event, file_name):
        # https://stackoverflow.com/questions/58774249/python-how-to-extend-folium-functionality-such-as-measuring-distance-by-using
        # https: // github.com / Leaflet / Leaflet.draw / issues / 276
        # https: // stackoverflow.com / questions / 49097851 / wx - html2 - webview - form - get - doesnt - fill - in -url - parameters
        # https://stackoverflow.com/questions/50001220/open-wx-html-a-tag-in-default-browser
        javascript = ('var geojsonLayer = L.geoJson(geojsonFeature);'
                        'geojsonLayer.eachLayer('
                        'function(l){'
                        'drawnItems.addLayer(l)});')
        self.folium_map

    def draw_button_and_list_frame(self):
        """#% CREATE LEFT HAND BUTTON MENU"""

        # BUTTON ONE'
        self.button_one = wx.Button(self.leftPanel_top, -1, "Load .cm", style=wx.ALIGN_CENTER)

        # BUTTON TWO'
        self.button_two = wx.Button(self.leftPanel_top, -1, "Load .cm dir", style=wx.ALIGN_CENTER)

        # BUTTON THREE'
        self.button_three = wx.Button(self.leftPanel_top, -1, "Load predicted", style=wx.ALIGN_CENTER)

        # BUTTON FOUR'
        self.button_four = wx.Button(self.leftPanel_top, -1, "3D viewer", style=wx.ALIGN_CENTER)

        # BUTTON FIVE'
        self.button_five = wx.Button(self.leftPanel_top, -1, "Get predicted", style=wx.ALIGN_CENTER)

        self.file_list_ctrl = wx.ListCtrl(self.leftPanel_bottom, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_item_selected, self.file_list_ctrl)
        self.file_list_ctrl.InsertColumn(0, 'cm Files')

    def size_handler(self):
        """CREATE AND FIT SIZERS (DO THE GUI LAYOUT)"""

        # ADD MAIN COORDINATE MAP BOX
        self.box_right_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_bottom_sizer.Add(self.browser, 1, wx.ALL | wx.EXPAND, border=2)
        # self.box_right_bottom_sizer.Add(self.canvas, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        # CREATE LAYER BUTTON BOX
        self.left_box_top_sizer = wx.FlexGridSizer(cols=1, rows=5, hgap=8, vgap=8)
        self.left_box_top_sizer.AddMany([self.button_one, self.button_two, self.button_three, self.button_four,
                                         self.button_five])

        # CREATE FILE LIST BOX
        self.left_box_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_box_bottom_sizer.Add(self.file_list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # PLACE BOX SIZERS IN CORRECT PANELS
        self.leftPanel_top.SetSizerAndFit(self.left_box_top_sizer)
        self.leftPanel_bottom.SetSizerAndFit(self.left_box_bottom_sizer)

        self.rightPanelbottom.SetSizerAndFit(self.box_right_bottom_sizer)
        self.rightPanelbottom.SetSize(self.GetSize())

    def bind_button_events(self):
        """CONNECT MOUSE AND EVENT BINDINGS"""
        self.button_one.Bind(wx.EVT_BUTTON, self.open_cm_file)
        self.button_two.Bind(wx.EVT_BUTTON, self.open_cm_directory)
        self.button_three.Bind(wx.EVT_BUTTON, self.open_predicted_cm_file)
        self.button_four.Bind(wx.EVT_BUTTON, self.plot_three_dim)
        self.button_five.Bind(wx.EVT_BUTTON, self.get_predicted)

    # GUI INTERACTION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def color_score(self, value):
        """SET COLOR FOR POINT PLOTTING"""
        cmap = plt.cm.get_cmap('RdYlBu')
        norm = mpl.colors.Normalize(vmin=0.0, vmax=1.0)
        rgb = cmap(value)[:3]
        return (mpl.colors.rgb2hex(rgb))

    def color_depth(self, value):
        """SET COLOR FOR POINT PLOTTING"""
        cmap = plt.cm.get_cmap('RdYlBu')
        norm = mpl.colors.Normalize(vmin=-10000.0, vmax=0.0)
        rgb = cmap(value)[:3]
        return (mpl.colors.rgb2hex(rgb))

    def open_cm_file(self, event):
        """GET CM FILE TO LOAD"""

        # OPEN THE DIALOG BOX TO ENTER THE THRESHOLD VALUES
        open_cm_dialogbox = OpenCmDialog(self, -1, 'Open cm file')
        open_cm_dialogbox.ShowModal()

        # OPEN THE .cm FILE
        if open_cm_dialogbox.regular_load_button is True or open_cm_dialogbox.cluster_load_button is True:

            # 1. SET THE THRESHOLD VALUES
            bad_th = float(open_cm_dialogbox.bad_th_value)
            uncertain_th = float(open_cm_dialogbox.uncertain_th_value)

            # 2. OPEN THE FILE
            open_file_dialog = wx.FileDialog(self, "Open XY file", "", "", "All files (*.cm)|*.*", wx.FD_OPEN |
                                             wx.FD_FILE_MUST_EXIST)
            if open_file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # USER CHANGED THEIR MIND
            else:
                #  IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE
                try:
                    self.cm_plot
                except AttributeError:
                    pass
                else:
                    self.delete_cm_file()

                #  GET THE FILE NAME FROM FileDialog WINDOW
                self.cm_file = open_file_dialog.GetPath()
                self.cm_filename = open_file_dialog.Filename

                # SET THE CLUSTER ZOOM LEVEL TERMINATION
                if open_cm_dialogbox.regular_load_button is True:
                    self.zoom_level = 1
                else:
                    self.zoom_level = 6

                # LOAD THE DATA
                self.load_cm_file_as_cluster(bad_th, uncertain_th)

    def load_cm_file_as_cluster(self, bad_th, uncertain_th):
        """LOAD .cm FILE AND PLOT AS CLUSTERS"""
        try:
            # 1. LOAD .cm FILE USING NUMPY
            self.cm = np.genfromtxt(self.cm_file, delimiter=' ', filling_values=-9999)

            # 2. GENERATE COLORS
            colors = np.empty(shape=[self.cm.shape[0]], dtype=object)
            for i in range(0, self.cm.shape[0]):
                colors[i] = self.color_score(self.cm[i, 6])
            # ADD COLORS TO CM ARRAY
            self.cm = np.column_stack((self.cm, colors))

            # 3. DIVIDE RECORDS INTO BAD, UNCERTAIN, GOOD (BASED ON ML SCORE)
            # MAKE NUMPY ARRAY WITH BAD SCORES
            scored_bad = self.cm[self.cm[:, 6] <= bad_th]
            print(np.shape(scored_bad))
            # MAKE NUMPY ARRAY WITH UNCERTAIN SCORES
            scored_uncertain = self.cm[self.cm[:, 6] > bad_th]
            scored_uncertain = scored_uncertain[scored_uncertain[:, 6] <= uncertain_th]
            print(np.shape(scored_uncertain))
            # MAKE NUMPY ARRAY WITH GOOD SCORES
            scored_good = self.cm[self.cm[:, 6] > uncertain_th]
            print(np.shape(scored_good))

            # CUSTOM JAVA SCRIPT FOR CREATING CIRCLE MARKERS & COLORING WITH SCORE VALUE
            callback = ('function (input) {'
                        'var circle = L.circle(new L.LatLng(input[0], input[1]), '
                        '{color: input[2],  radius: 20,  opacity: 0.5});'
                        'return circle};')
            # CREATE CLUSTER OBJECTS
            self.bad_fg.add_child(FastMarkerCluster((scored_bad[:, (2, 1, 8)]).tolist(),
                                                    callback=callback, disableClusteringAtZoom=self.zoom_level))

            self.uncertain_fg.add_child(FastMarkerCluster((scored_uncertain[:, (2, 1, 8)]).tolist(),
                                                          callback=callback, disableClusteringAtZoom=self.zoom_level))

            self.good_fg.add_child(FastMarkerCluster((scored_good[:, (2, 1, 8)]).tolist(),
                                                     callback=callback, disableClusteringAtZoom=self.zoom_level))

            # SAVE AND DISPLAY THE NEW FOLIUM MAP (INCLUDING THE .cm FILE)
            self.folium_map.save("my_map.html")
            self.browser.Reload()

        except IndexError:
            error_message = "ERROR IN LOADING PROCESS - FILE MUST BE ASCII SPACE DELIMITED"
            wx.MessageDialog(self, -1, error_message, "Load Error")
            raise

    def delete_cm_file(self):
        """" # DELETE CURRENT .cm FILE SO THE NEWLY SELECTED .cm FILE CAN BE LOADED INTO THE VIEWERS"""

        #  REMOVE .cm DATA from MAP FRAME'
        del self.cm_file
        del self.cm
        self.cm_plot.set_visible(False)
        self.cm_plot.remove()
        del self.cm_plot

        #  REMOVE .cm DATA from MAP FRAME'
        del self.xyz
        del self.xyz_cm_id
        del self.xyz_width
        del self.xyz_meta_data
        del self.xyz_point_flags
        del self.xyz_cm_line_number

        self.draw()

    def open_cm_directory(self, event):
        """
        Update the listctrl with the file names in the passed in folder
        """
        dlg = wx.DirDialog(self, "Choose a directory:")
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
        self.active_dir = folder_path  # SET .cm DIR
        paths = glob.glob(folder_path + "/*.cm")  # GET ALL .cm file names
        for index, path in enumerate(paths):
            self.file_list_ctrl.InsertItem(index, os.path.basename(path))
        dlg.Destroy()

    def list_item_selected(self, event):
        """ACTIVATED WHEN A FILE FROM THE LIST CONTROL IS SELECTED"""

        file = event.GetText()
        self.selected_file = str(self.active_dir) + "/" + str(file)
        print(self.selected_file)

        #  IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
        try:
            self.cm_plot
        except AttributeError:
            pass
        else:
            self.delete_cm_file()

        # LOAD NEW .cm FILE DATA INTO VIEWERS'
        self.cm_file = self.selected_file
        self.load_cm_file()

    def open_predicted_cm_file(self, event):
        pass

    def get_predicted(self, event):
        msg = "Please wait while we process your request..."
        self.busyDlg = wx.BusyInfo(msg)

        try:
            #  SAVE CM AS INPUT XYZ FOR BASH SCRIPT'
            cm_file = self.cm[:, 1:4]
            np.savetxt('input.xyz', cm_file, delimiter=" ", fmt="%10.6f %10.6f %10.6f")

            # RUN BASH SCRIPT '
            subprocess.run(["bash", self.cwd + '/' + 'get_predicted.sh', self.cwd + '/' + self.cm_filename])

            # LOAD CURRENT GRID XYZ POINTS
            self.predicted_cm = np.genfromtxt('predicted.xyz', delimiter=' ', dtype=float, filling_values=-9999)

            # IVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X & Z
            self.predicted_xyz = np.divide(self.predicted_cm, (1.0, 1.0, 10000.0))

            # LOAD DIFFERENCE CM
            self.diff_xyz = np.genfromtxt('difference.xyz', delimiter=' ', dtype=float, filling_values=-9999)

            # DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X & Z
            self.difference_xyz = np.divide(self.diff_xyz, (1.0, 1.0, 10000.0))
        except AttributeError:
            print("ERROR: no .cm file loaded")
        self.busyDlg = None

    def button_three(self, event):
        """OPEN 3D VEIWER"""
        self.plot_three_dim()
        # self.SetTitle("STL File Viewer: " + self.p1.filename)
        # self.statusbar.SetStatusText("Use W,S,F,R keys and mouse to interact with the model ")

    def plot_three_dim(self, event):
        """
        PLOT 3D VIEW OF DATA
        """

        # OPEN A vtk 3D VIEWER WINDOW AND CREATE A RENDER'
        self.tdv = ThreeDimViewer(self, -1, 'Modify Current Model', self.cm, self.xyz, self.xyz_cm_id,
                                  self.xyz_meta_data, self.xyz_cm_line_number, self.predicted_xyz, self.diff_xyz,
                                  self.difference_xyz, self.score_xyz)
        self.tdv.Show(True)

    def reload_three_dim(self):
        """REMOVE 3D VIEWER AND REPLACE WITH NEWLY LOADED DATA"""
        self.tdv.Show(False)
        del self.tdv
        self.plot_three_dim(self)

    def show_controls(self, event):
        pass

    def show_console(self, event):
        """SHOW/HIDE PYTHON CONSOLE"""
        if self.mgr.GetPaneByName('console').Hide:
            self.mgr.GetPaneByName('console').Show()  # SHOW PYTHON CONSOLE
        else:
            self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE

    # DOCUMENTATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_documentation(self, event):
        """# OPENS DOCUMENTATION HTML"""
        new = 2
        doc_url = os.path.dirname(__file__) + '/docs/_build/html/manual.html'
        webbrowser.open(doc_url, new=new)

    def about_pycmeditor(self, event):
        """# SHOW SOFTWARE INFORMATION"""
        about = "About PyCMeditor"
        dlg = wx.MessageDialog(self, about, "About", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def legal(self, event):
        """# SHOW LICENCE"""
        licence = ["Copyright 2018 Brook Tozer \n\nRedistribution and use in source and binary forms, with or "
                   "without modification, are permitted provided that the following conditions are met: \n \n"
                   "1. Redistributions of source code must retain the above copyright notice, this list of conditions "
                   "and the following disclaimer. \n\n2. Redistributions in binary form must reproduce the above "
                   "copyright notice, this list of conditions and the following disclaimer in the documentation and/or "
                   "other materials provided with the distribution. \n\n3. Neither the name of the copyright holder "
                   "nor the names of its contributors may be used to endorse or promote products  derived from this "
                   "software without specific prior written permission. \n\nTHIS SOFTWARE IS PROVIDED BY THE "
                   "COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT "
                   "NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE "
                   "DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, "
                   "INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, "
                   "PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS "
                   "INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,"
                   " OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, "
                   "EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."]

        dlg = wx.MessageDialog(self, licence[0], "BSD-3-Clause Licence", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    # EXIT FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def exit(self, event):
        """# SHUTDOWN APP (FROM FILE MENU)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

    def on_close_button(self, event):
        """# SHUTDOWN APP (X BUTTON)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

# DIALOGS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class OpenCmDialog(wx.Dialog):
    """
    OPEN A CM FILE AND SET THE THRESHOLDS FOR THE SCORES

    **Paramaters**

    * User input : Wx.Dialog entries

    Returns:

        * x1 : float

    """

    def __init__(self, parent, id, title, m_x1=None, m_x2=None, m_z1=None, m_z2=None):
        """DIALOG BOX USED TO GATHER USER INPUT FOR CREATING A NEW MODEL"""
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.OK | wx.CANCEL
                                                          | wx.BORDER_RAISED)
        self.floating_panel = wx.Panel(self, -1)

        # SET BUTTON VALUES
        self.regular_load_button = False
        self.cluster_load_button = False

        # MAIN BOX SIZER
        self.main_box = wx.BoxSizer(wx.HORIZONTAL)

        # 1. ADD TEXT
        self.title_text = wx.StaticText(self.floating_panel, -1, "Set the score thresholds:",
                                        style=wx.ALIGN_CENTRE_HORIZONTAL)

        # 2. LINE SPACER
        self.line1 = (wx.StaticLine(self.floating_panel), 0, wx.ALL | wx.EXPAND, 5)

        # 3. THRESHOLD INPUTS
        self.scores_text = wx.StaticText(self.floating_panel, -1, "Thresholds:      ")
        self.bad_th_text = wx.TextCtrl(self.floating_panel, -1, "0", size=(100, -1))
        self.uncertain_th_text = wx.TextCtrl(self.floating_panel, -1, "0", size=(100, -1))

        # 4. LINE SPACER 2
        self.line2 = (wx.StaticLine(self.floating_panel), 0, wx.ALL | wx.EXPAND, 5)

        # 5. CREATE LOAD BUTTONS
        self.spacing = wx.StaticText(self.floating_panel, -1, "                           ")

        # 6. LOAD REGULAR BUTTON
        self.b_regular_button = wx.Button(self.floating_panel, -1, "Load regular")
        self.Bind(wx.EVT_BUTTON, self.open_regular_button, self.b_regular_button)

        # 7. LOAD CLUSTER BUTTON
        self.b_cluster_button = wx.Button(self.floating_panel, -1, "Load as cluster")
        self.Bind(wx.EVT_BUTTON, self.open_cluster_button, self.b_cluster_button)

        # 8. LINE SPACER 3
        self.line3 = (wx.StaticLine(self.floating_panel), 0, wx.ALL | wx.EXPAND, 5)

        # 9. ADD FOOTER TEXT
        self.footer_text = wx.StaticText(self.floating_panel, -1,
                                         "NB. Using Cluster mode is recommended for data sets that\n"
                                         "are geographically sparse and contain > 50,000 records.")

        self.sizer = wx.FlexGridSizer(cols=1, hgap=10, vgap=10)
        self.sizer.AddMany([self.title_text, self.line1, self.scores_text, self.bad_th_text, self.uncertain_th_text,
                            self.line2, self.spacing, self.b_regular_button, self.b_cluster_button, self.line3,
                            self.footer_text])

        self.main_box.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        self.floating_panel.SetSizerAndFit(self.main_box)
        self.main_box.Fit(self)

    def open_regular_button(self, event):
        """WHEN THE "Create Model" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.regular_load_button = True
        self.cluster_load_button = False
        self.EndModal(1)

    def open_cluster_button(self, event):
        """WHEN THE "Create Model" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.cluster_load_button = True
        self.regular_load_button = False
        self.EndModal(1)


class MessageDialog(wx.MessageDialog):
    """GENERIC MESSAGE DIALOG BOX"""

    def __init__(self, parent, id, message_text, title):
        wx.MessageDialog.__init__(self, parent, message_text, title)
        dlg = wx.MessageDialog(self, message_text, title, wx.OK)
        answer = dlg.ShowModal()
        dlg.Destroy()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# START SOFTWARE
if __name__ == "__main__":
    app = wx.App(False)
    fr = wx.Frame(None, title='Py-CMeditor')
    app.frame = PyCMeditor()
    app.frame.CenterOnScreen()
    app.frame.Show()
    app.MainLoop()
