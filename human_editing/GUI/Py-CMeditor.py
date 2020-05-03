"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Description**

GUI application for hand editing Bathymetry data.
Brook Tozer, SIO IGPP 2018.

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
import sys
import matplotlib as mpl
mpl.use('WXAgg')
from matplotlib import pyplot as plt
import wx
import wx.py as py
import wx.lib.agw.aui as aui
from wx.lib.buttons import GenBitmapButton
import numpy as np
from numpy import size
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy
import glob
import os
import webbrowser
import folium
import subprocess
from wx import html2
from three_dim_viewer import ThreeDimViewer
from folium.plugins import Draw
from folium.plugins import MousePosition


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

    # INITALIZE GUI~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Py-CMeditor', size=(1800, 1050))

        ## GET CURRENT WORKING DIR
        self.cwd = os.path.dirname(os.path.realpath(__file__))

        ## DIR CONTAINING PROGRAM ICONS
        self.gui_icons_dir = self.cwd + '/icons/'

        '# %START AUI WINDOW MANAGER'
        self.mgr = aui.AuiManager()

        '# %TELL AUI WHICH FRAME TO USE'
        self.mgr.SetManagedWindow(self)

        '# %SET SPLITTER WINDOW TOGGLE IMAGES'
        images = wx.ImageList(16, 16)
        top = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_MENU, (16, 16))
        bottom = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_MENU, (16, 16))
        images.Add(top)
        images.Add(bottom)

        '# %CREATE PANEL TO FILL WITH CONTROLS'
        self.leftPanel = wx.SplitterWindow(self, wx.ID_ANY, size=(115, 1000), style=wx.SP_NOBORDER | wx.EXPAND)
        self.leftPanel.SetMinimumPaneSize(1)
        self.leftPanel.SetBackgroundColour('white')

        self.leftPanel_top = wx.Panel(self.leftPanel, -1, size=(115, 100), style=wx.ALIGN_RIGHT)
        self.leftPanel_bottom = wx.Panel(self.leftPanel, -1, size=(115, 900), style=wx.ALIGN_RIGHT)

        self.leftPanel.SplitHorizontally(self.leftPanel_top, self.leftPanel_bottom, 100)

        '# %CREATE PANEL TO FILL WITH COORDINATE INFORMATION'
        self.rightPaneltop = wx.Panel(self, -1, size=(1800, 50), style=wx.ALIGN_RIGHT)
        self.rightPaneltop.SetBackgroundColour('white')

        '# %CREATE PANEL TO FILL WITH MATPLOTLIB INTERACTIVE FIGURE (MAIN NAVIGATION FRAME)'
        self.rightPanelbottom = wx.Panel(self, -1, size=(1700, 900), style=wx.ALIGN_RIGHT)
        self.rightPanelbottom.SetBackgroundColour('white')

        '# %CREATE PANEL FOR PYTHON CONSOLE (USED FOR DEBUGGING AND CUSTOM USAGES)'
        self.ConsolePanel = wx.Panel(self, -1, size=(1800, 100), style=wx.ALIGN_LEFT | wx.BORDER_RAISED | wx.EXPAND)
        intro = "###############################################################\r" \
                "!USE import sys; then sys.Gmg.OBJECT TO ACCESS PROGRAM OBJECTS \r" \
                "ctrl+up FOR COMMAND HISTORY                                    \r" \
                "###############################################################"
        py_local = {'__app__': 'gmg Application'}
        sys.t = self
        self.win = py.shell.Shell(self.ConsolePanel, -1, size=(2200, 1100), locals=py_local, introText=intro)


        '# %ADD THE PANES TO THE AUI MANAGER'
        self.mgr.AddPane(self.leftPanel, aui.AuiPaneInfo().Name('left').Left().Caption("Controls"))
        self.mgr.AddPane(self.rightPaneltop, aui.AuiPaneInfo().Name('righttop').Top())
        self.mgr.AddPane(self.rightPanelbottom, aui.AuiPaneInfo().Name('rightbottom').CenterPane())
        self.mgr.AddPane(self.ConsolePanel, aui.AuiPaneInfo().Name('console').Bottom().Caption("Console"))
        # self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE BY DEFAULT
        self.mgr.Update()

        '# %CREATE PROGRAM MENUBAR & TOOLBAR (PLACED AT TOP OF FRAME)'
        self.create_menu()
        self.create_toolbar()

        '# %CREATE STATUS BAR'
        self.statusbar = self.CreateStatusBar(3, style=wx.NO_BORDER)
        self.controls_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'redock_2.png'),
                                               pos=(0, -5), style=wx.NO_BORDER)
        # self.Bind(wx.EVT_BUTTON, self.show_controls, self.controls_button)

        '# %PYTHON CONSOLE'
        self.console_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'python_16.png'),
                                              pos=(24, -5), style=wx.NO_BORDER)
        # self.Bind(wx.EVT_BUTTON, self.show_console, self.console_button)

        self.status_text = " || Current file: %s "
        self.statusbar.SetStatusWidths([-1, -1, 1700])
        self.statusbar.SetStatusText(self.status_text, 2)
        self.statusbar.SetSize((1800, 24))

        '# %INITALISE NAV FRAME'
        self.draw_navigation_window()

        '# %SET PROGRAM STATUS'
        self.connect_mpl_events()

        '# %SET PROGRAM STATUS'
        self.saved = False

        '# %BIND PROGRAM EXIT BUTTON WITH EXIT FUNCTION'
        self.Bind(wx.EVT_CLOSE, self.on_close_button)

        '# %MAXIMIZE FRAME'
        self.Maximize(True)

        '# % INITIALISE THREE DIMESION VERIWER OBJECTS'
        self.predicted_xyz = None
        self.difference_xyz = None

    def create_menu(self):
        """# %CREATES GUI MENUBAR"""
        self.menubar = wx.MenuBar()  # MAIN MENUBAR

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# % FILE MENU'
        self.file = wx.Menu()  # CREATE MENUBAR ITEM

        m_open_cm_file = self.file.Append(-1, "Open \tCtrl-L", "Open")
        self.Bind(wx.EVT_MENU, self.open_cm_file, m_open_cm_file)

        self.file.AppendSeparator()

        m_exit = self.file.Append(-1, "Exit...\tCtrl-X", "Exit...")
        self.Bind(wx.EVT_MENU, self.exit, m_exit)

        self.file.AppendSeparator()

        # m_3d = self.file.Append(-1, "plot\tCtrl-p", "Plot")
        # self.Bind(wx.EVT_MENU, self.plot_surface, m_3d)

        self.menubar.Append(self.file, "&File")  # %DRAW FILE MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %EDIT MENU'
        self.edit = wx.Menu()  # CREATE MENUBAR ITEM

        self.menubar.Append(self.edit, "&Edit")  # %DRAW EDIT MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %FIND MENU'  # CREATE MENUBAR ITEM
        self.find = wx.Menu()

        self.menubar.Append(self.find, "&Find")  # % DRAW FIND MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %VIEW MENU'  # CREATE MENUBAR ITEM
        self.view = wx.Menu()

        self.menubar.Append(self.view, "&View")  # % DRAW VIEW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %GO MENU'  # CREATE MENUBAR ITEM
        self.go = wx.Menu()

        self.menubar.Append(self.go, "&Go")  # % DRAW GO MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %TOOLS MENU'  # CREATE MENUBAR ITEM
        self.tools = wx.Menu()

        self.menubar.Append(self.tools, "&Tools")  # % DRAW TOOLS MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %WINDOW MENU'  # CREATE MENUBAR ITEM
        self.window = wx.Menu()

        self.menubar.Append(self.window, "&Window")  # % DRAW WINDOW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %SET MENUBAR'
        self.SetMenuBar(self.menubar)

    def create_toolbar(self):
        '# %TOOLBAR - (THIS IS THE ICON BAR BELOW THE MENU BAR)'
        self.toolbar = self.CreateToolBar()

        t_save_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'save_24.png'))
        # self.Bind(wx.EVT_TOOL, self.save_model, t_save_model)

        t_load_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'load_24.png'))
        # self.Bind(wx.EVT_TOOL, self.load_model, t_load_model)

        t_calc_model_bott = self.toolbar.AddTool(wx.ID_ANY, 'calculate-gravity',
                                                 wx.Bitmap(self.gui_icons_dir + 'G_24.png'))
        # self.Bind(wx.EVT_TOOL, self.calc_grav_switch, t_calc_model_bott)

        t_capture_coordinates = self.toolbar.AddTool(wx.ID_ANY, 't_capture_coordinates',
                                                     wx.Bitmap(self.gui_icons_dir + 'C_24.png'))
        # self.Bind(wx.EVT_TOOL, self.capture_coordinates, t_capture_coordinates)

        t_aspect_increase = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-up',
                                                 wx.Bitmap(self.gui_icons_dir + 'large_up_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_increase, t_aspect_increase)

        t_aspect_decrease = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-down',
                                                 wx.Bitmap(self.gui_icons_dir + 'large_down_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_decrease, t_aspect_decrease)

        t_aspect_increase2 = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-up-2',
                                                  wx.Bitmap(self.gui_icons_dir + 'small_up_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_increase2, t_aspect_increase2)

        t_aspect_decrease2 = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-down-2',
                                                  wx.Bitmap(self.gui_icons_dir + 'small_down_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_decrease2, t_aspect_decrease2)

        t_zoom = self.toolbar.AddTool(wx.ID_ANY, 'zoom',
                                      wx.Bitmap(self.gui_icons_dir + 'zoom_in_24.png'))
        self.Bind(wx.EVT_TOOL, self.zoom, t_zoom)

        t_zoom_out = self.toolbar.AddTool(wx.ID_ANY, 'zoom out',
                                          wx.Bitmap(self.gui_icons_dir + 'zoom_out_24.png'))
        self.Bind(wx.EVT_TOOL, self.zoom_out, t_zoom_out)

        t_full_extent = self.toolbar.AddTool(wx.ID_ANY, 'full_extent',
                                             wx.Bitmap(self.gui_icons_dir + 'full_extent_24.png'))
        self.Bind(wx.EVT_TOOL, self.full_extent, t_full_extent, id=604)

        t_pan = self.toolbar.AddTool(wx.ID_ANY, 'pan',
                                     wx.Bitmap(self.gui_icons_dir + 'pan_24.png'))
        self.Bind(wx.EVT_TOOL, self.pan, t_pan)
        #
        # t_transparency_down = self.toolbar.AddTool(wx.ID_ANY, 'transparency_down',
        #                                                 wx.Bitmap(self.gui_icons_dir + 'large_left_24.png'))
        # self.Bind(wx.EVT_TOOL, self.transparency_decrease, t_transparency_down)
        #
        # t_transparency_up = self.toolbar.AddTool(wx.ID_ANY, 'transparency_up',
        #                                               wx.Bitmap(self.gui_icons_dir + 'large_right_24.png'))
        # self.Bind(wx.EVT_TOOL, self.transparency_increase, t_transparency_up)
        #
        self.toolbar.Realize()
        self.toolbar.SetSize((1790, 36))

    def draw_navigation_window(self):
        """INITALISE FOLIUM INTERACTIVE MAP"""

        # CREATE MAP
        self.folium_map = folium.Map(location=[0.0, 0.0],
                                     zoom_start=2,
                                     tiles=self.cwd+'/8-xyz-tiles/{z}/{x}/{y}.png',
                                     attr='SRTM15+',
                                     no_wrap=True)

        # LOAD DRAWING FUNCTIONALITY
        self.draw = Draw(export=True,
                         filename='outpoint.geojson',
                         draw_options={'polyline': False, 'rectangle': False, 'circle': False, 'marker': False,
                                       'circlemarker': False},
                         edit_options={'poly': {'allowIntersection': False}})
        self.draw.add_to(self.folium_map)

        # MOUSE POSITION
        self.mouse_position = MousePosition()
        self.mouse_position.add_to(self.folium_map)

        # SAVE MAP AS HTML
        self.folium_map.save("my_map.html")

        # CREATE GUI HTML WINDOW
        self.browser = wx.html2.WebView.New(self.rightPanelbottom, -1)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, self.on_export)

        # LOAD FOLIUM MAP INTO HTML WINDOW
        self.browser.LoadURL(self.cwd + '/my_map.html')


        # DRAW MAIN PROGRAM WINDOW
        self.draw_main_frame()

        # DRAW BUTTON WINDOW
        self.draw_button_and_list_frame()

        # UPDATE DISPLAY
        self.size_handler()

        # REFRESH SIZER POSITIONS
        self.Hide()
        self.Show()

    def on_export(self, event):
        """FIRERS WHEN A NEW WINDOW IS OPENED IN THE WEBVIEWER"""
        print("fired")

    def draw_main_frame(self):
        """DRAW THE PROGRAM CANVASES"""

        # CURRENT COORDINATES'
        self.window_font = wx.Font(16, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)  # SET FONT

        # SET LONGITUDE
        self.longitude_text = wx.StaticText(self.rightPaneltop, -1, "Longitude (x):", style=wx.ALIGN_CENTER)
        self.longitude_text.SetFont(self.window_font)
        self.longitude = wx.TextCtrl(self.rightPaneltop, -1)

        '#  % SET LATITUDE'
        self.latitude_text = wx.StaticText(self.rightPaneltop, -1, "Latitude (y):")
        self.latitude_text.SetFont(self.window_font)
        self.latitude = wx.TextCtrl(self.rightPaneltop, -1)

        '#  % SET T VALUE'
        self.T_text = wx.StaticText(self.rightPaneltop, -1, "t:")
        self.T_text.SetFont(self.window_font)

        self.T = wx.TextCtrl(self.rightPaneltop, -1)

        '#%NAV CANVAS'
        # self.nav_canvas = plt.subplot2grid((20, 20), (2, 2), rowspan=17, colspan=17)
        # self.nav_canvas.set_xlabel("Longitude (dec. Degrees)")
        # self.nav_canvas.set_ylabel("Latitude (dec. Degrees)")
        # self.nav_canvas.set_xlim(-180., 180.)  # % SET X LIMITS
        # self.nav_canvas.set_ylim(-90, 90.)  # % SET Y LIMITS
        # self.nav_canvas.grid()
        # self.fig.subplots_adjust(top=1.05, left=-0.045, right=1.02, bottom=0.02,
        #                          hspace=0.5)
        # self.error = 0.
        # self.last_layer = 0

        '#% UPDATE INFO BAR'
        # self.display_info()

        '#%DRAW MAIN'
        # self.draw()

    def draw_button_and_list_frame(self):
        """#% CREATE LEFT HAND BUTTON MENU"""

        '# %BUTTON ONE'
        self.button_one = wx.Button(self.leftPanel_top, -1, "Load .cm", style=wx.ALIGN_CENTER)

        '# %BUTTON TWO'
        self.button_two = wx.Button(self.leftPanel_top, -1, "Load .cm dir", style=wx.ALIGN_CENTER)

        '# %BUTTON THREE'
        self.button_three = wx.Button(self.leftPanel_top, -1, "Load predicted", style=wx.ALIGN_CENTER)

        '# %BUTTON FOUR'
        self.button_four = wx.Button(self.leftPanel_top, -1, "3D viewer", style=wx.ALIGN_CENTER)

        '# %BUTTON FIVE'
        self.button_five = wx.Button(self.leftPanel_top, -1, "Get predicted", style=wx.ALIGN_CENTER)

        self.file_list_ctrl = wx.ListCtrl(self.leftPanel_bottom, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_item_selected, self.file_list_ctrl)
        self.file_list_ctrl.InsertColumn(0, 'cm Files')

    def size_handler(self):
        """# %CREATE AND FIT BOX SIZERS (GUI LAYOUT)"""

        '# %ADD CURRENT COORDINATE BOXES'
        self.coordinate_box_sizer = wx.FlexGridSizer(cols=6, hgap=7, vgap=1)
        self.coordinate_box_sizer.AddMany([self.longitude_text, self.longitude, self.latitude_text, self.latitude,
                                           self.T_text, self.T])

        '# %ADD LIVE COORDINATE DATA BOX'
        self.box_right_top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_top_sizer.Add(self.coordinate_box_sizer, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        '# %ADD MAIN COORDINATE MAP BOX'
        self.box_right_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_bottom_sizer.Add(self.browser, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)
        # self.box_right_bottom_sizer.Add(self.canvas, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        '# %CREATE LAYER BUTTON BOX'
        self.left_box_top_sizer = wx.FlexGridSizer(cols=1, rows=5, hgap=8, vgap=8)
        self.left_box_top_sizer.AddMany([self.button_one, self.button_two, self.button_three, self.button_four,
                                         self.button_five])

        '# %CREATE FILE LIST BOX'
        self.left_box_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_box_bottom_sizer.Add(self.file_list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        '# %CREATE LEFT SPLITTER PANEL SIZE (POPULATED WITH BUTTON BOX AND FILE LIST BOX)'
        self.splitter_left_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.splitter_left_panel_sizer.Add(self.leftPanel, 1, wx.EXPAND)

        '# %PLACE BOX SIZERS IN CORRECT PANELS'
        self.leftPanel_top.SetSizerAndFit(self.left_box_top_sizer)
        self.leftPanel_bottom.SetSizerAndFit(self.left_box_bottom_sizer)
        self.leftPanel.SetSizer(self.splitter_left_panel_sizer)
        self.rightPaneltop.SetSizerAndFit(self.box_right_top_sizer)
        self.rightPanelbottom.SetSizerAndFit(self.box_right_bottom_sizer)
        self.rightPaneltop.SetSize(self.GetSize())
        self.rightPanelbottom.SetSize(self.GetSize())

    def connect_mpl_events(self):
        """
        CONNECT MOUSE AND EVENT BINDINGS
        """
        self.button_one.Bind(wx.EVT_BUTTON, self.open_cm_file)
        self.button_two.Bind(wx.EVT_BUTTON, self.open_cm_directory)
        self.button_three.Bind(wx.EVT_BUTTON, self.open_predicted_cm_file)
        self.button_four.Bind(wx.EVT_BUTTON, self.plot_threed)
        self.button_five.Bind(wx.EVT_BUTTON, self.get_predicted)

    # FIGURE DISPLAY FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def zoom(self, event):
        self.nav_toolbar.zoom()
        self.draw()

    def zoom_out(self, event):
        self.nav_toolbar.back()
        self.draw()

    def full_extent(self, event):
        """# %REDRAW MODEL FRAME WITH FULL EXTENT"""
        '#% SET CANVAS LIMITS'
        self.nav_canvas.set_xlim(self.cm[:, 1].min() - 0.2, self.cm[:, 1].max() + 0.2)
        self.nav_canvas.set_ylim(self.cm[:, 2].min() - 0.2, self.cm[:, 2].max() + 0.2)
        self.draw()

    def pan(self, event):
        """# %PAN MODEL VIEW USING MOUSE DRAG"""
        self.nav_toolbar.pan()
        self.draw()

    def aspect_increase(self, event):
        if self.aspect >= 1:
            self.aspect = self.aspect + 1
            self.set_nav_aspect()
            self.draw()
        elif 1.0 > self.aspect >= 0.1:
            self.aspect = self.aspect + 0.1
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def aspect_decrease(self, event):
        if self.aspect >= 2:
            self.aspect = self.aspect - 1
            self.set_nav_aspect()
            self.draw()
        elif 1.0 >= self.aspect >= 0.2:
            self.aspect = self.aspect - 0.1
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def aspect_increase2(self, event):
        self.aspect = self.aspect + 2
        self.set_nav_aspect()
        self.draw()

    def aspect_decrease2(self, event):
        if self.aspect >= 3:
            self.aspect = self.aspect - 2
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def set_nav_aspect(self):
        self.nav_canvas.set_aspect(self.aspect)

    # GUI INTERACTION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_cm_file(self, event):
        """# %GET CM FILE TO LOAD"""
        open_file_dialog = wx.FileDialog(self, "Open XY file", "", "", "All files (*.cm)|*.*", wx.FD_OPEN |
                                         wx.FD_FILE_MUST_EXIST)
        if open_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # %THE USER CHANGED THEIR MIND
        else:
            '# % IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
            try:
                self.cm_plot
            except AttributeError:
                pass
            else:
                self.delete_cm_file()

            '# % GET THE FILE NAME FROM FileDialog WINDOW'
            self.cm_file = open_file_dialog.GetPath()
            self.cm_filename = open_file_dialog.Filename  # % ASSIGN FILE

            '# % NOW LOAD THE DATA'
            self.load_cm_file()

    def color(self, input_elev):
        """SET COLOR FOR POINT PLOTTING"""
        color_input = -(float(input_elev) / 10000.)
        cmap = plt.cm.get_cmap('RdYlBu')
        norm = mpl.colors.Normalize(vmin=-10000.0, vmax=0.0)
        rgb = cmap(color_input)[:3]
        return (mpl.colors.rgb2hex(rgb))

    def load_cm_file(self):
        """LOAD .cm FILE DATA INTO PROGRAM"""
        try:
            ## MAKE COLOR SACLE
            self.colorbar = plt.cm.get_cmap('RdYlBu')

            ## LOAD .cm FILE USNING NUMPY
            self.cm = np.genfromtxt(self.cm_file, delimiter=' ', dtype=float, filling_values=-9999)  # % LOAD FILE

            ## CREATE FOLIUM SCATTER PLOT OBJECT FOR THE .cm FILE
            fg = folium.FeatureGroup(name="cm_file")
            # for lat, lon, elev, name in zip(self.cm[:, 2], self.cm[:, 1], self.cm[:, 3], self.cm[:, 4]):
            #     folium.CircleMarker(location=[lat, lon], radius=1, popup=None, fill=True,
            #                         color=self.color(elev)).add_to(fg)
            for lat, lon, elev in zip(self.cm[:, 2], self.cm[:, 1], self.cm[:, 3]):
                folium.CircleMarker(location=[lat, lon], radius=1, popup=None, fill=True,
                                    color=self.color(elev)).add_to(fg)
            self.folium_map.add_child(fg)

            ## SAVE AND DISPLAY THE NEW FOLIUM MAP (INCLUDING THE .cm FILE)
            self.folium_map.save("my_map.html")
            self.browser.LoadURL(self.cwd + '/my_map.html')
            # self.browser.LoadURL(self.cwd + '/tiles-dir/leaflet.html')


            # '# % SET WINDOW DIMENSIONS TO FIT CURRENT SURVEY'
            # self.nav_canvas.set_xlim(self.cm[:, 1].min()-0.2, self.cm[:, 1].max()+0.2)
            # self.nav_canvas.set_ylim(self.cm[:, 2].min()-0.2, self.cm[:, 2].max()+0.2)

        except IndexError:
            error_message = "ERROR IN LOADING PROCESS - FILE MUST BE ASCII SPACE DELIMITED"
            wx.MessageDialog(self, -1, error_message, "Load Error")
            raise

        '# %GET DATA AS cm FILE DATA AS NUMPY ARRAYS'
        self.xyz = self.cm[:, 1:4]
        self.xyz = np.divide(self.xyz, (1.0, 1.0, 10000.0))  # % DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X&Z
        self.xyz_cm_id = self.cm[:, 0].astype(int)  # % GET CM FILE IDs
        self.xyz_width = self.cm.shape[1]
        self.xyz_meta_data = self.cm[:, 4:self.xyz_width]
        self.xyz_point_flags = np.zeros(shape=(1, len(self.xyz)))
        self.xyz_cm_line_number = np.linspace(0, len(self.xyz), (len(self.xyz) + 1))
        self.score_xyz = self.cm[:, [1, 2, 6]]

        # GET THE PREDICTED DEPTH GRID
        # self.get_predicted(None)

        '# % If THREE DIMENSIONAL VIEWER IS OPEN, THEN CLOSE IT AND REOPEN WITH NEW .cm FILE'
        try:
            self.tdv
        except AttributeError:
            pass
        else:
            self.reload_threed()

        '# %UPDATE MPL CANVAS'
        # self.draw()

    def delete_cm_file(self):
        """" # %DELETE CURRENT .cm FILE SO THE NEWLY SELECTED .cm FILE CAN BE LOADED INTO THE VIEWERS"""

        '# % REMOVE .cm DATA from MAP FRAME'
        del self.cm_file
        del self.cm
        self.cm_plot.set_visible(False)
        self.cm_plot.remove()
        del self.cm_plot

        '# % REMOVE .cm DATA from MAP FRAME'
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
        self.active_dir = folder_path  # % SET .cm DIR
        paths = glob.glob(folder_path + "/*.cm")  # % GET ALL .cm file names
        for index, path in enumerate(paths):
            self.file_list_ctrl.InsertItem(index, os.path.basename(path))
        dlg.Destroy()

    def list_item_selected(self, event):
        """ACTIVATED WHEN A FILE FROM THE LIST CONTROL IS SELECTED"""

        file = event.GetText()
        self.selected_file = str(self.active_dir) + "/" + str(file)
        print(self.selected_file)

        '# % IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
        try:
            self.cm_plot
        except AttributeError:
            pass
        else:
            self.delete_cm_file()

        '# %LOAD NEW .cm FILE DATA INTO VIEWERS'
        self.cm_file = self.selected_file
        self.load_cm_file()

    def open_predicted_cm_file(self, event):
        pass

    def get_predicted(self, event):
        msg = "Please wait while we process your request..."
        self.busyDlg = wx.BusyInfo(msg)

        try:
            '# % SAVE CM AS INPUT XYZ FOR BASH SCRIPT'
            cm_file = self.cm[:, 1:4]
            np.savetxt('input.xyz', cm_file, delimiter=" ", fmt="%10.6f %10.6f %10.6f")

            '# %RUN BASH SCRIPT '
            subprocess.run(["bash", self.cwd + '/' + 'get_predicted.sh', self.cwd + '/' + self.cm_filename])

            '# %LOAD PREDICTED CM'
            self.predicted_cm = np.genfromtxt('predicted.xyz', delimiter=' ', dtype=float, filling_values=-9999)

            '# %MAKE PREDICTED DATA A NUMPY ARRAY - DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X & Z'
            self.predicted_xyz = np.divide(self.predicted_cm, (1.0, 1.0, 10000.0))

            '# %LOAD DIFFERENCE CM'
            self.diff_xyz = np.genfromtxt('difference.xyz', delimiter=' ', dtype=float, filling_values=-9999)

            '# %MAKE DIFFERENCE DATA A NUMPY ARRAY - DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X & Z'
            self.difference_xyz = np.divide(self.diff_xyz, (1.0, 1.0, 10000.0))
        except AttributeError:
            print("ERROR: no .cm file loaded")
        self.busyDlg = None

    def button_three(self, event):
        self.plot_threed()
        # self.SetTitle("STL File Viewer: " + self.p1.filename)
        # self.statusbar.SetStatusText("Use W,S,F,R keys and mouse to interact with the model ")

    def plot_threed(self, event):
        """
        PLOT 3D VIEW OF DATA
        """

        '# %OPEN A vtk 3D VIEWER WINDOW AND CREATE A RENDER'
        self.tdv = ThreeDimViewer(self, -1, 'Modify Current Model', self.cm, self.xyz, self.xyz_cm_id,
                                  self.xyz_meta_data, self.xyz_point_flags, self.xyz_cm_line_number,
                                  self.predicted_xyz, self.diff_xyz, self.difference_xyz, self.score_xyz)
        self.tdv.Show(True)

    def reload_threed(self):
        """REMOVE 3D VIEWER AND REPLACE WITH NEWLY LOADED DATA"""
        self.tdv.Show(False)
        del self.tdv
        self.plot_threed(self)

    # DOCUMENTATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_documentation(self, event):
        """# %OPENS DOCUMENTATION HTML"""
        new = 2
        doc_url = os.path.dirname(__file__) + '/docs/_build/html/manual.html'
        webbrowser.open(doc_url, new=new)

    def about_pycmeditor(self, event):
        """# %SHOW SOFTWARE INFORMATION"""
        about = "About PyCMeditor"
        dlg = wx.MessageDialog(self, about, "About", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def legal(self, event):
        """# %SHOW LICENCE"""
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
        """# %SHUTDOWN APP (FROM FILE MENU)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

    def on_close_button(self, event):
        """# %SHUTDOWN APP (X BUTTON)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''# %START SOFTWARE'''
if __name__ == "__main__":
    app = wx.App(False)
    fr = wx.Frame(None, title='Py-CMeditor')
    app.frame = PyCMeditor()
    app.frame.CenterOnScreen()
    app.frame.Show()
    app.MainLoop()
