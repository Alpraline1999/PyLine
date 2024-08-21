# pyline.py
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, Menu, ttk
from PIL import Image
from matplotlib import pyplot as plt
import mouseset
import drawphoto


class PyLine:
    def __init__(self, root):
        try:
            self.language
        except:
            self._init_variables()

        self.root = root
        self.root.title("PyLine")
        self.root.state("zoomed")
        self.root.minsize(self.root_min_width, self.root_min_height)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.config(bg=self.root_color)

        self._init_strings()

        self.mouse_set = mouseset.MouseSensitivitySet()

        self._create_frame()
        self._create_canvas()
        self._create_menu()
        self._create_datatree()
        self._creat_settings()
        self._creat_toolbar()
        self._creat_operations()
        self._bind_events()
        self._create_hotkeys()
        self._create_print_types()

    def _init_variables(self):
        # default language
        self.language = "zh"
        self.root_min_width = 1350
        self.root_min_height = 780

        # image file
        self.image_file = None

        #################################################
        # set colors
        #################################################
        self.root_color = "#F3E5F5"
        self.label_color = "#E3F2FD"
        self.button_color = "#FFF3E0"
        self.text_color = "#E8F5E9"
        self.frame_color = "lightgray"

        #################################################
        # set paddings
        #################################################
        self.frame_padx, self.frame_pady = 5, 3  # padding for frames
        self.toolbar_padx, self.toolbar_pady = 2, 0  # padding for toolbar widgets
        self.setting_padx, self.setting_pady = 5, 2  # padding for settings widgets
        self.operation_padx, self.operation_pady = (
            4,
            2,
        )  # padding for operation buttons

        #################################################
        # set default parameters
        #################################################
        self.default_line_color = 'black'  # default line color
        self.default_line_width = 2  # default line width
        self.default_point_scale_factor = 1  # point_radius = point_scale * line_width
        self.default_point_interval = 7  # default point interval
        self.default_zoom_scale_factor = 2  # default scale factor

        #################################################
        # set main canvas size and zoom canvas size
        #################################################
        self.main_width = 800  # main canvas width
        self.main_height = 600  # main canvas height

        self.zoom_scale_factor = self.default_zoom_scale_factor  # scale factor for zoom
        self.zoom_size = 320  # zoom canvas size
        self.zoom_cursor_size = 12  # zoom cursor size

        # real axis and screen axis
        self.x1_real = self.x2_real = self.y1_real = self.y2_real = None
        self.x1_screen = self.x2_screen = self.y1_screen = self.y2_screen = None

    def _change_language(self):
        self.language = simpledialog.askstring(
            self.str_language, self.str_select_language
        )
        self._init_strings()

        self.root.destroy()
        new_root = tk.Tk()
        self.__init__(new_root)
        new_root.mainloop()

    def _init_strings(self):
        if self.language == "zh":
            self.str_language = "Language"
            self.str_select_language = "Simplified Chinese/English (zh/en):"

            self.str_menu_file = "文件"
            self.str_menu_edit = "编辑"
            self.str_menu_settings = "设置"
            self.str_menu_hotkeys = "快捷键 (F1)"
            self.str_hotkeys_list = "快捷键列表"
            self.str_open = "打开"
            self.str_save = "导出"
            self.str_quit = "退出"
            self.str_redraw = "重绘"
            self.str_undo = "撤销"
            self.str_redo = "重做"
            self.str_clean = "清除"
            self.str_preview = "预览"
            self.str_line_color = "颜色"
            self.str_line_width = "线宽"
            self.str_point_interval = "点间距"
            self.str_point_scale = "点的尺寸系数"
            self.str_zoom_scale = "图片缩放系数"
            self.str_mouse_sensitivity = "鼠标灵敏度"
            self.str_draw_mode = "绘图模式"
            self.str_mode_point = "点"
            self.str_mode_point_line = "点-线"
            self.str_auto_mode = "识别模式"
            self.str_auto_mode_1 = "欧氏距离"
            self.str_auto_mode_2 = "CIE76"
            self.str_pick_color = "选取颜色"
            self.str_assisted_pick_points = "辅助取点"
            self.str_set = "设置"
            self.str_input = "输入"
            self.str_default = "默认为"

            self.str_no_image_loaded = "无加载图片"
            self.str_ref_color = "参考色"
            self.str_no_point_picked = "无选取点"
            self.str_image_files = "图片文件"
            self.str_open_image = "打开图片"
            self.str_data_file = "数据文件"
            self.str_save_data = "导出数据"

            self.str_set_coordinates_first = "未设置坐标"
            self.str_line_saved = "已保存曲线数据"
            self.str_no_line = "无曲线数据"
            self.str_clear_all = "已清除所有点"
            self.str_undone = "已撤销"
            self.str_redone = "已重做"
            self.str_oldest = "已位于最旧位置"
            self.str_latest = "已位于最新位置"
            self.str_redrawn = "已重绘曲线"
            self.str_set_ref_color_first = "未设置参考色"
            self.str_auto_draw = "自动取点"
            self.str_auto_drawing = "自动取点中..."
            self.str_auto_drawn = "已完成自动取点"
            self.str_erase_range = "橡皮大小"

        elif self.language == "en":
            self.str_language = "语言"
            self.str_select_language = "简体中文/英文 (zh/en): "

            self.str_menu_file = "Files"
            self.str_menu_edit = "Edit"
            self.str_menu_settings = "Settings"
            self.str_menu_hotkeys = "HotKeys (F1)"
            self.str_hotkeys_list = "HotKeys List"
            self.str_open = "Open"
            self.str_save = "Export"
            self.str_quit = "Quit"
            self.str_redraw = "Redraw"
            self.str_undo = "Undo"
            self.str_redo = "Redo"
            self.str_clean = "Clean"
            self.str_preview = "Preview"
            self.str_line_color = "Line Color"
            self.str_line_width = "Line Width"
            self.str_point_interval = "Point Interval"
            self.str_point_scale = "Point Scale Factor"
            self.str_zoom_scale = "Zoom Scale Factor"
            self.str_mouse_sensitivity = "Mouse Sensitivity"
            self.str_draw_mode = "Draw Mode"
            self.str_mode_point = "Point"
            self.str_mode_point_line = "Point_Line"
            self.str_auto_mode = "Auto Mode"
            self.str_auto_mode_1 = "Distance"
            self.str_auto_mode_2 = "CIE76"
            self.str_pick_color = "Pick Color"
            self.str_assisted_pick_points = "Assisted Pick Points"
            self.str_set = "Set "
            self.str_input = "Input "
            self.str_default = "default "

            self.str_no_image_loaded = "No Image Loaded"
            self.str_ref_color = "Reference Color"
            self.str_no_point_picked = "No Point Picked"
            self.str_image_files = "Image Files"
            self.str_open_image = "Open Image"
            self.str_data_file = "Data File"
            self.str_save_data = "Save Data"

            self.str_set_coordinates_first = "Set Coordinates First"
            self.str_line_saved = "Line data has been saved"
            self.str_no_line = "No lines"
            self.str_clear_all = "All line datas cleared"
            self.str_undone = "Undone"
            self.str_redone = "Redone"
            self.str_oldest = "Already the oldest location"
            self.str_latest = "Already the latest location"
            self.str_redrawn = "Line Re-drawn"
            self.str_set_ref_color_first = "Set Reference Color First"
            self.str_auto_draw = "Auto Draw"
            self.str_auto_drawing = "Auto Drawing ..."
            self.str_auto_drawn = "Auto Draw Finished"
            self.str_erase_range = "Eraser Size"

    def _create_frame(self):
        self.frame_toolbar = tk.Frame(
            self.root, bd=1, relief=tk.RAISED, bg=self.frame_color
        )
        self.frame_settings = tk.Frame(
            self.root, bd=1, relief=tk.RAISED, bg=self.frame_color
        )
        self.frame_operations = tk.Frame(
            self.root, bd=1, relief=tk.RAISED, bg=self.frame_color
        )
        self.frame_zoom = tk.Frame(
            self.root,
            width=self.zoom_size,
            height=self.zoom_size,
            bd=1,
            relief=tk.RAISED,
            bg=self.frame_color,
        )
        self.frame_main = tk.Frame(
            self.root,
            width=self.main_width,
            height=self.main_height,
            bd=1,
            relief=tk.RAISED,
            bg=self.frame_color,
        )
        self.frame_datatree = tk.Frame(
            self.root,
            bd=1,
            relief=tk.RAISED,
            bg=self.frame_color,
        )

        self.frame_toolbar.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky='NEW',
            padx=self.frame_padx,
            pady=self.frame_pady,
        )
        self.frame_zoom.grid(
            row=1, column=0, sticky='NSEW', padx=self.frame_padx, pady=self.frame_pady
        )
        self.frame_operations.grid(
            row=2, column=0, sticky='NSEW', padx=self.frame_padx, pady=self.frame_pady
        )
        self.frame_settings.grid(
            row=3, column=0, sticky='NSEW', padx=self.frame_padx, pady=self.frame_pady
        )
        self.frame_main.grid(
            row=1,
            column=1,
            sticky='NSEW',
            rowspan=3,
            padx=self.frame_padx,
            pady=self.frame_pady,
        )
        self.frame_datatree.grid(
            row=1,
            column=2,
            rowspan=3,
            sticky='NSEW',
            padx=self.frame_padx,
            pady=self.frame_pady,
        )

    def _create_canvas(self):
        self.zoom_cursor = [
            self.zoom_size // 2,
            self.zoom_size // 2,
        ]  # zoom cursor position

        self.main = drawphoto.DrawPhoto(self.root)
        self.main.canvas.config(
            width=self.main_width, height=self.main_height, bg=self.label_color
        )
        self.main.canvas.pack(
            in_=self.frame_main,
            padx=self.frame_padx,
            pady=self.frame_pady,
            expand=True,
        )

        self.zoom = drawphoto.DrawPhoto(self.root)
        self.zoom.canvas.config(
            width=self.zoom_size, height=self.zoom_size, bg=self.label_color
        )

        self.zoom.canvas.pack(
            in_=self.frame_zoom,
            fill=tk.BOTH,
            padx=self.frame_padx,
            pady=self.frame_pady,
        )

        # set color, width and point interval for lines
        self.main.line.set_line_color(self.default_line_color)
        self.main.line.set_line_width(self.default_line_width)
        self.main.line.set_point_scale(self.default_point_scale_factor)
        self.main.line.set_point_interval(self.default_point_interval)

        self.zoom.line.set_line_color(self.default_line_color)
        self.zoom.line.set_line_width(self.zoom_scale_factor * self.default_line_width)
        self.main.line.set_point_scale(self.default_point_scale_factor)
        self.zoom.line.set_point_interval(
            self.zoom_scale_factor * self.default_point_interval
        )

    def _create_menu(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.str_menu_file, menu=file_menu)
        file_menu.add_command(label=self.str_open, command=self.open_main_image)
        file_menu.add_command(label=self.str_save, command=self.save_main_line)
        file_menu.add_separator()
        file_menu.add_command(label=self.str_quit, command=self.on_closing)

        edit_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.str_menu_edit, menu=edit_menu)
        edit_menu.add_command(label=self.str_redraw, command=self.redraw_lines)
        edit_menu.add_command(label=self.str_undo, command=self.undo_last_action)
        edit_menu.add_command(label=self.str_redo, command=self.redo_last_action)
        edit_menu.add_command(label=self.str_clean, command=self.clear_all_linedatas)

        options_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.str_menu_settings, menu=options_menu)
        options_menu.add_command(label=self.str_line_color, command=self.set_line_color)
        options_menu.add_command(label=self.str_line_width, command=self.set_line_width)
        options_menu.add_command(
            label=self.str_point_interval, command=self.set_point_interval
        )
        options_menu.add_command(
            label=self.str_point_scale, command=self.set_point_scale
        )
        options_menu.add_command(
            label=self.str_mouse_sensitivity,
            command=self.set_mouse_sensitivity,
        )
        options_menu.add_command(label=self.str_zoom_scale, command=self.set_zoom_scale)

        hotkeys_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.str_menu_hotkeys, menu=hotkeys_menu)
        hotkeys_menu.add_command(label=self.str_hotkeys_list, command=self.show_hotkeys)

        language_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.str_language, menu=language_menu)
        language_menu.add_command(
            label=self.str_language, command=self._change_language
        )

    def _creat_toolbar(self):
        self.open_button = tk.Button(
            self.frame_toolbar,
            text=self.str_open,
            command=self.open_main_image,
            bg=self.button_color,
        )
        self.open_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.save_button = tk.Button(
            self.frame_toolbar,
            text=self.str_save,
            command=self.save_main_line,
            bg=self.button_color,
        )
        self.save_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.redraw_button = tk.Button(
            self.frame_toolbar,
            text=self.str_redraw,
            command=self.redraw_lines,
            bg=self.button_color,
        )
        self.redraw_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.undo_button = tk.Button(
            self.frame_toolbar,
            text=self.str_undo,
            command=self.undo_last_action,
            bg=self.button_color,
        )
        self.undo_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.redo_button = tk.Button(
            self.frame_toolbar,
            text=self.str_redo,
            command=self.redo_last_action,
            bg=self.button_color,
        )
        self.redo_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.clean_button = tk.Button(
            self.frame_toolbar,
            text=self.str_clean,
            command=self.clear_all_linedatas,
            bg=self.button_color,
        )
        self.clean_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.preview_button = tk.Button(
            self.frame_toolbar,
            text=self.str_preview,
            command=self.preview_line,
            bg=self.button_color,
        )
        self.preview_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.zoom_scale_button = tk.Button(
            self.frame_toolbar,
            text=self.str_zoom_scale,
            command=self.set_zoom_scale,
            bg=self.button_color,
        )
        self.zoom_scale_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.mouse_sensitivity_button = tk.Button(
            self.frame_toolbar,
            text=self.str_mouse_sensitivity,
            command=self.set_mouse_sensitivity,
            bg=self.button_color,
        )
        self.mouse_sensitivity_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.point_scale_button = tk.Button(
            self.frame_toolbar,
            text=self.str_point_scale,
            command=self.set_point_scale,
            bg=self.button_color,
        )
        self.point_scale_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.point_interval_button = tk.Button(
            self.frame_toolbar,
            text=self.str_point_interval,
            command=self.set_point_interval,
            bg=self.button_color,
        )
        self.point_interval_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.linewidth_button = tk.Button(
            self.frame_toolbar,
            text=self.str_line_width,
            command=self.set_line_width,
            bg=self.button_color,
        )
        self.linewidth_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.linecolor_button = tk.Button(
            self.frame_toolbar,
            text=self.str_line_color,
            command=self.set_line_color,
            bg=self.button_color,
        )
        self.linecolor_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_padx
        )

    def _create_datatree(self):
        datatree_width = 80
        self.datatree = ttk.Treeview(
            self.frame_datatree, columns=("X", "Y"), show="headings"
        )
        self.datatree.pack(side="left", fill=tk.BOTH, expand=True)
        self.datatree.heading("X", text="X")
        self.datatree.heading("Y", text="Y")
        self.datatree.column("#1", anchor='w', width=datatree_width)
        self.datatree.column("#2", anchor="w", width=datatree_width)

        self.datatree_vsp = tk.Scrollbar(
            self.frame_datatree, orient=tk.VERTICAL, command=self.datatree.yview
        )
        self.datatree_vsp.pack(side="right", fill=tk.Y)
        self.datatree.configure(yscrollcommand=self.datatree_vsp.set)

    def _creat_settings(self):  # create axis settings
        label_width = 7
        tk.Label(
            self.frame_settings,
            width=label_width,
            text="X1:",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=0,
            column=0,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        tk.Label(
            self.frame_settings,
            width=label_width,
            text="X2:",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=1,
            column=0,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        tk.Label(
            self.frame_settings,
            width=label_width,
            text="Y1:",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=2,
            column=0,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        tk.Label(
            self.frame_settings,
            width=label_width,
            text="Y2:",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=3,
            column=0,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )

        self.entry_x1 = tk.Entry(self.frame_settings, relief=tk.RAISED)
        self.entry_x1.grid(
            row=0, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_x2 = tk.Entry(self.frame_settings, relief=tk.RAISED)
        self.entry_x2.grid(
            row=1, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_y1 = tk.Entry(self.frame_settings, relief=tk.RAISED)
        self.entry_y1.grid(
            row=2, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_y2 = tk.Entry(self.frame_settings, relief=tk.RAISED)
        self.entry_y2.grid(
            row=3, column=1, padx=self.setting_padx, pady=self.setting_pady
        )

        self.button_x1 = tk.Button(
            self.frame_settings,
            text=self.str_set + "X1",
            command=self.record_x1_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_x1.grid(
            row=0,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='E',
        )
        self.button_x2 = tk.Button(
            self.frame_settings,
            text=self.str_set + "X2",
            command=self.record_x2_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_x2.grid(
            row=1,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='E',
        )
        self.button_y1 = tk.Button(
            self.frame_settings,
            text=self.str_set + "Y1",
            command=self.record_y1_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_y1.grid(
            row=2,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='E',
        )
        self.button_y2 = tk.Button(
            self.frame_settings,
            text=self.str_set + "Y2",
            command=self.record_y2_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_y2.grid(
            row=3,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='E',
        )

        self.output_text = tk.Text(
            self.frame_settings,
            height=10,
            width=45,
            relief=tk.RAISED,
            state=tk.DISABLED,
        )
        self.output_text.grid(
            row=4,
            column=0,
            columnspan=3,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='EW',
        )

    def _creat_operations(self):  # create operation buttons
        combo_width = 7
        # combobox for draw mode
        tk.Label(
            self.frame_operations,
            text=self.str_draw_mode + ": ",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=0,
            column=0,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.draw_mode_option = tk.StringVar()
        self.draw_mode_combobox = ttk.Combobox(
            self.frame_operations,
            textvariable=self.draw_mode_option,
            state="readonly",
            width=combo_width,
        )
        self.draw_mode_combobox.grid(
            row=0,
            column=1,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )
        self.draw_mode_combobox['values'] = (
            self.str_mode_point,
            self.str_mode_point_line,
        )
        self.draw_mode_combobox.current(0)
        self.draw_mode_combobox.bind("<<ComboboxSelected>>", self.set_draw_mode)

        # combobox for auto mode
        tk.Label(
            self.frame_operations,
            text=self.str_auto_mode + ": ",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=0,
            column=2,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.auto_mode_option = tk.StringVar()
        self.auto_mode_combobox = ttk.Combobox(
            self.frame_operations,
            textvariable=self.auto_mode_option,
            state="readonly",
            width=combo_width,
        )
        self.auto_mode_combobox.grid(
            row=0,
            column=3,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )
        self.auto_mode_combobox['values'] = (
            self.str_auto_mode_1,
            self.str_auto_mode_2,
        )
        self.auto_mode_combobox.current(0)
        self.auto_mode_combobox.bind("<<ComboboxSelected>>", self.set_auto_mode)

        # pick color
        self.ref_color_label = tk.Label(
            self.frame_operations,
            width=10,
            height=1,
            background="white",
            foreground="black",
            text="#FFFFFF",
            relief=tk.RAISED,
        )
        self.ref_color_label.grid(
            row=1,
            column=0,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.pick_color_button = tk.Button(
            self.frame_operations,
            text=self.str_pick_color,
            command=self._pick_color,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.pick_color_button.grid(
            row=1,
            column=1,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.assisted_option = tk.IntVar()
        self.assisted_checkbox = tk.Checkbutton(
            self.frame_operations,
            text=self.str_assisted_pick_points,
            variable=self.assisted_option,
            command=self.set_assisted_point,
            relief=tk.RAISED,
        )
        self.assisted_checkbox.grid(
            row=1,
            column=2,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.auto_draw_button = tk.Button(
            self.frame_operations,
            text=self.str_auto_draw,
            command=self.auto_draw,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.auto_draw_button.grid(
            row=1,
            column=3,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.erase_range_label = tk.Label(
            self.frame_operations,
            text=self.str_erase_range + ": ",
            relief=tk.RAISED,
            bg=self.label_color,
        )
        self.erase_range_label.grid(
            row=2,
            column=0,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

        self.erase_range_scale = tk.Scale(
            self.frame_operations,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            bg=self.button_color,
            command=self.set_erase_range,
        )
        self.erase_range_scale.set(
            self.main.assisted_point.erase_range
        )  # initiate the value of the erase range scale
        self.erase_range_scale.grid(
            row=2,
            column=1,
            columnspan=3,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='EW',
        )

    def set_assisted_point(self):
        self.main.if_assisted = self.assisted_option.get() == 1
        self._print(
            "INFO", self.str_assisted_pick_points + ": " + str(self.main.if_assisted)
        )

    def change_assisted_point(self):
        self.assisted_option.set(1 - self.assisted_option.get())
        self.set_assisted_point()

    def set_erase_range(self, value):
        self.main.assisted_point.set_erase_range(int(value))

    def _pick_color(self):
        if not self.main.image:
            self._print("ERROR", self.str_no_image_loaded)
            return

        if self.main.line.last_point:
            self.main.assisted_point.set_ref_color(
                self.main.image, self.main.line.last_point
            )
            # delete last point
            self.main.line.delete_last_point()
            self.update_all_lines()
            ref_color = self.rgb_to_hex(self.main.assisted_point.ref_color)
            self.ref_color_label.config(
                background=ref_color,
                foreground=self._comple_color(ref_color),
                text=ref_color,
            )
            self._print("INFO", self.str_ref_color + ": " + ref_color)
        else:
            self._print("ERROR", self.str_no_point_picked)

    def _comple_color(self, hex_color):
        rgb = self.hex_to_rgb(hex_color)
        perceived_brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        if perceived_brightness > 128:
            return '#000000'
        else:
            return '#FFFFFF'

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb_color):
        return '#%02x%02x%02x' % rgb_color

    def _bind_events(self):
        self.main.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.main.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.main.canvas.bind("<Motion>", self.update_zoom_image)
        self.main.canvas.bind("<Motion>", self.draw_line, add='+')
        self.main.canvas.bind("<B3-Motion>", self.update_zoom_image)
        self.main.canvas.bind("<B3-Motion>", self.draw_line, add='+')
        self.main.canvas.bind("<B3-Motion>", self.delete_points, add='+')
        self.main.canvas.bind("<ButtonPress-3>", self.start_delete)
        self.main.canvas.bind("<ButtonPress-3>", self.delete_points, add='+')
        self.main.canvas.bind("<ButtonRelease-3>", self.stop_delete)

    def _create_hotkeys(self):
        self.root.bind('<F1>', lambda event: self.show_hotkeys())
        self.root.bind("<Control-o>", lambda event: self.open_main_image())
        self.root.bind("<Control-s>", lambda event: self.save_main_line())
        self.root.bind("<Control-q>", lambda event: self.on_closing())
        self.root.bind("<Control-r>", lambda event: self.redraw_lines())
        self.root.bind("<Control-z>", lambda event: self.undo_last_action())
        self.root.bind("<Control-y>", lambda event: self.redo_last_action())
        self.root.bind("<Control-d>", lambda event: self.clear_all_linedatas())
        self.root.bind("<Control-p>", lambda event: self._pick_color())

        self.root.bind("<Control-Shift-Key-C>", lambda event: self.set_line_color())
        self.root.bind("<Control-Shift-Key-W>", lambda event: self.set_line_width())
        self.root.bind("<Control-Shift-Key-I>", lambda event: self.set_point_interval())
        self.root.bind("<Control-Shift-Key-Z>", lambda event: self.set_zoom_scale())
        self.root.bind("<Control-Shift-Key-P>", lambda event: self.set_point_scale())
        self.root.bind(
            "<Control-Shift-Key-M>", lambda event: self.set_mouse_sensitivity()
        )
        self.root.bind(
            "<Control-Shift-Key-A>", lambda event: self.change_assisted_point()
        )

        self.root.bind("<Control-Key-1>", lambda event: self.down_mouse_sensitivity())
        self.root.bind("<Control-Key-2>", lambda event: self.up_mouse_sensitivity())
        self.root.bind("<Control-Key-3>", lambda event: self.reset_mouse_sensitivity())
        self.root.bind("<Control-MouseWheel>", self.set_zoom_scale_by_mouse_wheel)

    def show_hotkeys(self):
        hotkeys_window = tk.Toplevel(self.root)
        hotkeys_window.title("Hotkeys")
        hotkeys_window.geometry("450x500")
        hotkeys_text = tk.Text(
            hotkeys_window, wrap=tk.WORD, state=tk.NORMAL, font=("Consolas", 11)
        )
        hotkeys_text.pack(expand=True, fill=tk.BOTH)
        hotkeys_text.insert(tk.END, "Hotkeys List:                  F1\n")
        hotkeys_text.insert(tk.END, "Open image:                    Ctrl + O\n")
        hotkeys_text.insert(tk.END, "Export line data:              Ctrl + S\n")
        hotkeys_text.insert(tk.END, "Quit:                          Ctrl + Q\n")
        hotkeys_text.insert(tk.END, "Redraw:                        Ctrl + R\n")
        hotkeys_text.insert(tk.END, "Undo:                          Ctrl + Z\n")
        hotkeys_text.insert(tk.END, "Redo:                          Ctrl + Y\n")
        hotkeys_text.insert(tk.END, "Clean:                         Ctrl + D\n")
        hotkeys_text.insert(tk.END, "Pick reference color:          Ctrl + P\n")
        hotkeys_text.insert(tk.END, "Set line color:                Ctrl + Shift + C\n")
        hotkeys_text.insert(tk.END, "Set line width:                Ctrl + Shift + W\n")
        hotkeys_text.insert(tk.END, "Set point interval:            Ctrl + Shift + I\n")
        hotkeys_text.insert(tk.END, "Set zoom scale:                Ctrl + Shift + Z\n")
        hotkeys_text.insert(tk.END, "Set point scale:               Ctrl + Shift + P\n")
        hotkeys_text.insert(tk.END, "Set mouse sensitivity:         Ctrl + Shift + M\n")
        hotkeys_text.insert(tk.END, "Change assisted state:         Ctrl + Shift + A\n")
        hotkeys_text.insert(tk.END, "Decrease mouse sensitivity:    Ctrl + 1\n")
        hotkeys_text.insert(tk.END, "Increase mouse sensitivity:    Ctrl + 2\n")
        hotkeys_text.insert(tk.END, "Reset mouse sensitivity:       Ctrl + 3\n")
        hotkeys_text.insert(
            tk.END, "Decrease/Increase zoom scale:  Ctrl + Mouse Wheel\n"
        )
        hotkeys_text.config(state=tk.DISABLED)

    def _create_print_types(self):
        font_type = 'Consolas'
        font_size = 10
        self.output_text.tag_configure(
            "INFO", foreground="black", font=(font_type, font_size)
        )
        self.output_text.tag_configure(
            "CORRECT", foreground="green", font=(font_type, font_size)
        )
        self.output_text.tag_configure(
            "WARNING", foreground="blue", font=(font_type, font_size)
        )
        self.output_text.tag_configure(
            "ERROR", foreground="red", font=(font_type, font_size, 'bold')
        )

    def _print(self, type, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, '> ' + type + ' < ' + message + '\n', type)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def open_main_image(self):
        self.image_file = filedialog.askopenfilename(
            filetypes=[(self.str_image_files, "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")],
            title=self.str_open_image,
        )
        if self.image_file:
            image = Image.open(self.image_file)
            image_ratio = image.width / image.height
            canvas_ratio = self.main_width / self.main_height

            if image_ratio > canvas_ratio:
                new_width = self.main_width
                new_height = int(self.main_width / image_ratio)
            else:
                new_height = self.main_height
                new_width = int(self.main_height * image_ratio)

            resized_image = image.resize((new_width, new_height))
            self.main.canvas.config(width=new_width, height=new_height)
            self.main.set_photoimage(resized_image)
            self._print("INFO", self.str_open_image + f": {self.image_file}")

            if self.main.line.line_segments:
                self.clear_all_linedatas()

            self.axis_setted = False  # if axis is setted

    def update_zoom_image(self, event):
        if self.main.image:
            x, y = event.x, event.y
            if (
                x < 0
                or y < 0
                or x > self.main.image.width
                or y > self.main.image.height
            ):
                return

            # Calculate the zoom size based on the main image size and the scale factor
            real_zoom_size = self.zoom_size // self.zoom_scale_factor
            half_real_zoom_size = self.zoom_size // (2 * self.zoom_scale_factor)
            if x - half_real_zoom_size < 0:
                dx = (x - half_real_zoom_size) * self.zoom_scale_factor
                self.zoom_left = 0
                self.zoom_right = self.zoom_left + real_zoom_size
            elif x + half_real_zoom_size > self.main.image.width:
                dx = (
                    x + half_real_zoom_size - self.main.image.width
                ) * self.zoom_scale_factor
                self.zoom_right = self.main.image.width
                self.zoom_left = self.zoom_right - real_zoom_size
            else:
                dx = 0
                self.zoom_left = x - half_real_zoom_size
                self.zoom_right = x + half_real_zoom_size

            if y - half_real_zoom_size < 0:
                dy = (y - half_real_zoom_size) * self.zoom_scale_factor
                self.zoom_upper = 0
                self.zoom_lower = self.zoom_upper + real_zoom_size
            elif y + half_real_zoom_size > self.main.image.height:
                dy = (
                    y + half_real_zoom_size - self.main.image.height
                ) * self.zoom_scale_factor
                self.zoom_lower = self.main.image.height
                self.zoom_upper = self.zoom_lower - real_zoom_size
            else:
                dy = 0
                self.zoom_upper = y - half_real_zoom_size
                self.zoom_lower = y + half_real_zoom_size

            # update zoom image
            cropped_image = self.main.image.crop(
                (self.zoom_left, self.zoom_upper, self.zoom_right, self.zoom_lower)
            )
            resized_image = cropped_image.resize((self.zoom_size, self.zoom_size))
            self.zoom.set_photoimage(resized_image)

            self.zoom_cursor[0] = dx + self.zoom_size // 2
            self.zoom_cursor[1] = dy + self.zoom_size // 2

    def update_zoom_line(self):
        self.zoom.line.line_segments.clear()
        if self.main.line.line_segments:
            for segment in self.main.line.line_segments:
                zoom_segment = [
                    (
                        (px - self.zoom_left) * self.zoom_scale_factor,
                        (py - self.zoom_upper) * self.zoom_scale_factor,
                    )
                    for px, py in segment
                ]
                self.zoom.line.line_segments.append(zoom_segment)

        self.zoom.line.current_segment.clear()
        if self.main.line.current_segment:
            self.zoom.line.current_segment = [
                (
                    (px - self.zoom_left) * self.zoom_scale_factor,
                    (py - self.zoom_upper) * self.zoom_scale_factor,
                )
                for px, py in self.main.line.current_segment
            ]

    def update_zoom_cursor(self):
        # draw cursor in zoom image
        self.zoom.canvas.create_line(
            self.zoom_cursor[0] - self.zoom_cursor_size,
            self.zoom_cursor[1],
            self.zoom_cursor[0] + self.zoom_cursor_size,
            self.zoom_cursor[1],
            fill=self.zoom.line.line_color,
            width=self.zoom.line.line_width,
        )
        self.zoom.canvas.create_line(
            self.zoom_cursor[0],
            self.zoom_cursor[1] - self.zoom_cursor_size,
            self.zoom_cursor[0],
            self.zoom_cursor[1] + self.zoom_cursor_size,
            fill=self.zoom.line.line_color,
            width=self.zoom.line.line_width,
        )

    def start_draw(self, event):
        # start draw line
        self.main.start_draw_photoline(event)
        self.update_all_lines()

    def stop_draw(self, event):
        # stop draw line and update lines
        status = self.main.stop_draw_photoline(event)
        if status == -1:  # if not set reference color, output warning
            self._print("WARNING", self.str_set_ref_color_first)

        self.update_all_lines()

    def auto_draw(self):
        if not self.main.image:
            self._print("ERROR", self.str_no_image_loaded)
            return

        self._print("INFO", self.str_auto_drawing)
        self.root.update_idletasks()

        # auto draw line
        status = self.main.auto_draw()
        if status < 0:  # if not set reference color, output warning
            self._print("WARNING", self.str_set_ref_color_first)
        else:
            self._print("INFO", self.str_auto_drawn)

        self.update_all_lines()

    def start_delete(self, event):
        self.deleted = -1
        self.main.line._backup_line()

    def stop_delete(self, event):
        if (
            self.deleted == 0
        ):  # if changed, clear redo stack and back up line_segments for undo/redo
            self.main.line.redo_stack.clear()
        else:  # if not changed, clear undo stack and cancel back up
            self.main.line.undo_stack.pop()
        self.update_all_lines()

    def delete_points(self, event):
        if self.main.image:
            self.deleted = self.deleted * self.main.erase_points(event)
            self.update_all_lines()
            self.update_erase(event)

    def update_erase(self, event):
        erase_range = self.main.assisted_point.erase_range
        self.main.canvas.create_line(
            event.x - erase_range,
            event.y - erase_range,
            event.x + erase_range,
            event.y - erase_range,
            fill=self.main.line.line_color,
            width=self.main.line.line_width,
        )
        self.main.canvas.create_line(
            event.x + erase_range,
            event.y - erase_range,
            event.x + erase_range,
            event.y + erase_range,
            fill=self.main.line.line_color,
            width=self.main.line.line_width,
        )
        self.main.canvas.create_line(
            event.x + erase_range,
            event.y + erase_range,
            event.x - erase_range,
            event.y + erase_range,
            fill=self.main.line.line_color,
            width=self.main.line.line_width,
        )
        self.main.canvas.create_line(
            event.x - erase_range,
            event.y + erase_range,
            event.x - erase_range,
            event.y - erase_range,
            fill=self.main.line.line_color,
            width=self.main.line.line_width,
        )

        zoom_erase_range = erase_range * self.zoom_scale_factor
        self.zoom.canvas.create_line(
            self.zoom_cursor[0] - zoom_erase_range,
            self.zoom_cursor[1] - zoom_erase_range,
            self.zoom_cursor[0] + zoom_erase_range,
            self.zoom_cursor[1] - zoom_erase_range,
            fill=self.zoom.line.line_color,
            width=self.main.line.line_width,
        )
        self.zoom.canvas.create_line(
            self.zoom_cursor[0] + zoom_erase_range,
            self.zoom_cursor[1] - zoom_erase_range,
            self.zoom_cursor[0] + zoom_erase_range,
            self.zoom_cursor[1] + zoom_erase_range,
            fill=self.zoom.line.line_color,
            width=self.main.line.line_width,
        )
        self.zoom.canvas.create_line(
            self.zoom_cursor[0] + zoom_erase_range,
            self.zoom_cursor[1] + zoom_erase_range,
            self.zoom_cursor[0] - zoom_erase_range,
            self.zoom_cursor[1] + zoom_erase_range,
            fill=self.zoom.line.line_color,
            width=self.main.line.line_width,
        )
        self.zoom.canvas.create_line(
            self.zoom_cursor[0] - zoom_erase_range,
            self.zoom_cursor[1] + zoom_erase_range,
            self.zoom_cursor[0] - zoom_erase_range,
            self.zoom_cursor[1] - zoom_erase_range,
            fill=self.zoom.line.line_color,
            width=self.main.line.line_width,
        )

    def draw_line(self, event):
        # draw line in main image
        self.main.draw_photoline(event)
        self.update_all_lines()

    def save_main_line(self):
        if self.main.line.line_segments:
            self.update_all_lines()
            if (
                not self.axis_setted
            ):  # if not set coordinates, output without conversion
                self._print("WARNING", self.str_set_coordinates_first)

            output_file = filedialog.asksaveasfilename(
                defaultextension=".dat",
                filetypes=[(self.str_data_file, "*.dat")],
                title=self.str_save_data,
            )
            if output_file:
                with open(output_file, 'w') as f:
                    for point in self.converted_points:
                        f.write(f"{point[0]} {point[1]}\n")
                self._print("INFO", self.str_line_saved + f": {output_file}")
        else:
            self._print("ERROR", self.str_no_line)

    def update_all_lines(self):
        if self.main.image:
            self.update_zoom_line()
            self.main.update_photoline()
            self.zoom.update_photoline()
            self.update_zoom_cursor()

            self.update_datatree()

    def update_datatree(self):
        self.datatree.delete(*self.datatree.get_children())
        if self.main.line.line_all_points:
            if (
                not self.axis_setted
            ):  # if not set coordinates, output without conversion
                self.converted_points = self.main.line.line_all_points
            else:  # if set coordinates, convert points to real coordinates
                x_scale = (self.x2_real - self.x1_real) / (
                    self.x2_screen - self.x1_screen
                )
                y_scale = (self.y2_real - self.y1_real) / (
                    self.y2_screen - self.y1_screen
                )

                x_offset = self.x1_real - self.x1_screen * x_scale
                y_offset = self.y1_real - self.y1_screen * y_scale

                self.converted_points = [
                    (x * x_scale + x_offset, y * y_scale + y_offset)
                    for x, y in self.main.line.line_all_points
                ]

            for point in self.converted_points:
                self.datatree.insert(
                    "",
                    "end",
                    values=(point[0], point[1]),
                )

    def update_all_photos(self):
        status1 = self.main.update_photo()
        status2 = self.zoom.update_photo()
        # if status1 == 0 and status2 == 0:
        #     self._print("INFO", "Photos Updated")

    def clear_all_linedatas(self):
        status1 = self.main.clear_linedata()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", self.str_clear_all)
            self.update_all_photos()
        else:
            self._print("WARNING", self.str_no_line)

    def undo_last_action(self):
        status1 = self.main.undo_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", self.str_undone)
        else:
            self._print("WARNING", self.str_oldest)

    def redo_last_action(self):
        status1 = self.main.redo_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", self.str_redone)
        else:
            self._print("WARNING", self.str_latest)

    def redraw_lines(self):
        status1 = self.main.redraw_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", self.str_redrawn)
        else:
            self._print("WARNING", self.str_no_line)

    def preview_line(self):
        if self.main.line.line_segments:
            if self.axis_setted:
                self.update_all_lines()
                x = [point[0] for point in self.converted_points]
                y = [point[1] for point in self.converted_points]
                plt.plot(x, y)
                plt.show()
            else:
                self._print("WARNING", self.str_set_coordinates_first)

        else:
            self._print("ERROR", self.str_no_line)

    def _check_axis(self):
        if self.main.image:
            if not (
                self.x1_screen is None
                or self.x2_screen is None
                or self.x1_real is None
                or self.x2_real is None
                or self.y1_screen is None
                or self.y2_screen is None
                or self.y1_real is None
                or self.y2_real is None
            ):  # if not set coordinates, output all points without conversion
                self.axis_setted = True

    def record_x1_screen(self):
        if self.main.line.last_point:
            if self.entry_x1.get():
                self.x1_screen = self.main.line.last_point[0]
                self.main.line.delete_last_point()
                self.update_all_lines()
                self.x1_real = float(self.entry_x1.get())
                self._print("INFO", f"X1: {self.x1_real}")
                self._check_axis()
            else:
                self._print("ERROR", self.str_set_coordinates_first)
        else:
            self._print("ERROR", self.str_no_point_picked)

    def record_x2_screen(self):
        if self.main.line.last_point:
            if self.entry_x2.get():
                self.x2_screen = self.main.line.last_point[0]
                self.main.line.delete_last_point()
                self.update_all_lines()
                self.x2_real = float(self.entry_x2.get())
                self._print("INFO", f"X2: {self.x2_real}")
                self._check_axis()
            else:
                self._print("ERROR", self.str_set_coordinates_first)

        else:
            self._print("ERROR", self.str_no_point_picked)

    def record_y1_screen(self):
        if self.main.line.last_point:
            if self.entry_y1.get():
                self.y1_screen = self.main.line.last_point[1]
                self.main.line.delete_last_point()
                self.update_all_lines()
                self.y1_real = float(self.entry_y1.get())
                self._print("INFO", f"Y1: {self.y1_real}")
                self._check_axis()
            else:
                self._print("ERROR", self.str_set_coordinates_first)
        else:
            self._print("ERROR", self.str_no_point_picked)

    def record_y2_screen(self):
        if self.main.line.last_point:
            if self.entry_y2.get():
                self.y2_screen = self.main.line.last_point[1]
                self.main.line.delete_last_point()
                self.update_all_lines()
                self.y2_real = float(self.entry_y2.get())
                self._print("INFO", f"Y2: {self.y2_real}")
                self._check_axis()
            else:
                self._print("ERROR", self.str_set_coordinates_first)
        else:
            self._print("ERROR", self.str_no_point_picked)

    def set_draw_mode(self, event):
        self.main.draw_mode = self.draw_mode_combobox.current()
        self.zoom.draw_mode = self.draw_mode_combobox.current()
        self.update_all_lines()
        self._print("INFO", self.str_draw_mode + f": {self.draw_mode_option.get()}")

    def set_auto_mode(self, event):
        self.main.assisted_point.auto_mode = self.auto_mode_combobox.current()
        self._print("INFO", self.str_auto_mode + f": {self.auto_mode_option.get()}")

    def set_line_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.main.line.set_line_color(color)
            self.zoom.line.set_line_color(color)
            self.update_all_lines()
            self._print("INFO", self.str_line_color + f": {color}")

    def set_line_width(self):
        width = simpledialog.askinteger(
            self.str_set + self.str_line_width,
            self.str_input
            + self.str_line_width
            + "(1-10, "
            + self.str_default
            + f"{self.default_line_width})：",
            minvalue=1,
            maxvalue=10,
        )
        if width:
            self.main.line.set_line_width(width)
            self.zoom.line.set_line_width(min(10, width * self.zoom_scale_factor))
            self.update_all_lines()
            self._print("INFO", self.str_line_width + f": {width}")

    def set_point_interval(self):
        interval = simpledialog.askinteger(
            self.str_set + self.str_point_interval,
            self.str_input
            + self.str_point_interval
            + "(1-50, "
            + self.str_default
            + f"{self.default_point_interval})：",
            minvalue=1,
            maxvalue=50,
        )
        if interval:
            self.main.line.set_point_interval(interval)
            self._print("INFO", self.str_point_interval + f": {interval}")

    def set_mouse_sensitivity(self):
        sensitivity = simpledialog.askinteger(
            self.str_set + self.str_mouse_sensitivity,
            self.str_input
            + self.str_mouse_sensitivity
            + "(1-20, "
            + self.str_default
            + f"{self.mouse_set.original_sensitivity})：",
            minvalue=1,
            maxvalue=20,
        )
        if sensitivity:
            self.mouse_set.set_mouse_sensitivity(sensitivity)
            self._print("INFO", self.str_mouse_sensitivity + f": {sensitivity}")

    def set_zoom_scale(self):
        factor = simpledialog.askinteger(
            self.str_set + self.str_zoom_scale,
            self.str_input
            + self.str_zoom_scale
            + "(1-10, "
            + self.str_default
            + f"{self.default_zoom_scale_factor})：",
            minvalue=1,
            maxvalue=10,
        )
        if factor:
            self.zoom_scale_factor = factor
            self.zoom.line.set_line_width(
                min(10, self.zoom.line.line_width * self.zoom_scale_factor)
            )
            # self.update_zoom_image(event)
            self.update_all_lines()
            self._print("INFO", self.str_zoom_scale + f": {factor}")

    def set_zoom_scale_by_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_scale_factor += 1
        else:
            self.zoom_scale_factor -= 1
        self.zoom_scale_factor = max(1, min(self.zoom_scale_factor, 10))
        self.zoom.line.set_line_width(
            min(10, self.main.line.line_width * self.zoom_scale_factor)
        )
        self.update_zoom_image(event)
        self.update_all_lines()
        self._print("INFO", self.str_zoom_scale + f": {self.zoom_scale_factor}")

    def set_point_scale(self):
        factor = simpledialog.askfloat(
            self.str_set + self.str_point_scale,
            self.str_input
            + self.str_point_scale
            + "(0.1-10, "
            + self.str_default
            + f"{self.default_point_scale_factor})：",
            minvalue=0.1,
            maxvalue=10,
        )
        if factor:
            self.main.line.set_point_scale(factor)
            self.zoom.line.set_point_scale(factor)
            self.update_all_lines()
            self._print("INFO", self.str_point_scale + f": {factor}")

    def up_mouse_sensitivity(self):
        self.mouse_set.up_mouse_sensitivity()
        self._print(
            "INFO",
            self.str_mouse_sensitivity + f": {self.mouse_set.get_mouse_sensitivity()}",
        )

    def down_mouse_sensitivity(self):
        self.mouse_set.down_mouse_sensitivity()
        self._print(
            "INFO",
            self.str_mouse_sensitivity + f": {self.mouse_set.get_mouse_sensitivity()}",
        )

    def reset_mouse_sensitivity(self):
        self.mouse_set.reset_mouse_sensitivity()
        self._print(
            "INFO",
            self.str_mouse_sensitivity + f": {self.mouse_set.original_sensitivity}",
        )

    def on_closing(self):
        self.mouse_set.reset_mouse_sensitivity()
        self.root.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PyLine(root)
    root.mainloop()


if __name__ == "__main__":
    main()
