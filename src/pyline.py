# pyline.py
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, Menu, ttk
from PIL import Image
import mouseset
import drawphoto
from PIL import ImageTk
import base64
from io import BytesIO
import icon


class PyLine:
    def __init__(self, root):
        self._init_variables()

        self.root = root
        self.root.title("PyLine")
        self.root.geometry("1170x720")
        self.root.minsize(1170, 720)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.config(bg=self.root_color)

        # set icon
        icon_base64 = icon.icon_data().icon_base64
        icon_data = base64.b64decode(icon_base64)
        icon_image = Image.open(BytesIO(icon_data))
        icon_image = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(False, icon_image)

        self.mouse_set = mouseset.MouseSensitivitySet()

        self._create_frame()
        self._create_canvas()
        self._create_menu()
        self._creat_settings()
        self._creat_toolbar()
        self._creat_operations()
        self._bind_events()
        self._create_hotkeys()
        self._create_print_types()

    def _init_variables(self):
        # image file
        self.image_file = None

        #################################################
        # set colors
        #################################################
        self.root_color = "#F3E5F5"
        # self.root_color = ""
        self.label_color = "#E3F2FD"
        self.button_color = "#FFF3E0"
        self.text_color = "#E8F5E9"
        # self.frame_color = "#FFF3E0"
        self.frame_color = "lightgray"

        #################################################
        # set paddings
        #################################################
        self.frame_padx, self.frame_pady = 5, 3  # padding for frames
        self.toolbar_padx, self.toolbar_pady = 2, 0  # padding for toolbar widgets
        self.setting_padx, self.setting_pady = 5, 2  # padding for settings widgets
        self.operation_padx, self.operation_pady = (
            5,
            2,
        )  # padding for operation buttons

        #################################################
        # set default parameters
        #################################################
        self.default_line_color = 'black'  # default line color
        self.default_line_width = 2  # default line width
        self.default_point_scale = 1  # point_radius = point_scale * line_width
        self.default_point_interval = 7  # default point interval
        self.default_scale_factor = 2  # default scale factor

        #################################################
        # set main canvas size and zoom canvas size
        #################################################
        self.main_width = 800  # main canvas width
        self.main_height = 600  # main canvas height

        self.scale_factor = self.default_scale_factor  # scale factor for zoom
        self.zoom_size = 300  # zoom canvas size
        self.zoom_cursor_size = 12  # zoom cursor size

        # real axis and screen axis
        self.x1_real = self.x2_real = self.y1_real = self.y2_real = None
        self.x1_screen = self.x2_screen = self.y1_screen = self.y2_screen = None

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

        self.frame_toolbar.grid(
            row=0,
            column=0,
            columnspan=2,
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
        self.main.line.set_point_scale(self.default_point_scale)
        self.main.line.set_point_interval(self.default_point_interval)

        self.zoom.line.set_line_color(self.default_line_color)
        self.zoom.line.set_line_width(self.scale_factor * self.default_line_width)
        self.main.line.set_point_scale(self.default_point_scale)
        self.zoom.line.set_point_interval(
            self.scale_factor * self.default_point_interval
        )

    def _create_menu(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Files", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_main_image)
        file_menu.add_command(label="Export", command=self.save_main_line)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.on_closing)

        edit_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Redraw", command=self.redraw_lines)
        edit_menu.add_command(label="Undo", command=self.undo_last_action)
        edit_menu.add_command(label="Redo", command=self.redo_last_action)
        edit_menu.add_command(label="Clean", command=self.clear_all_linedatas)

        options_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=options_menu)
        options_menu.add_command(label="Line Color", command=self.set_line_color)
        options_menu.add_command(label="Line Width", command=self.set_line_width)
        options_menu.add_command(
            label="Point Interval", command=self.set_point_interval
        )
        options_menu.add_command(
            label="Point Scale Factor", command=self.set_point_scale
        )
        options_menu.add_command(
            label="Mouse Sensitivity",
            command=self.set_mouse_sensitivity,
        )
        options_menu.add_command(label="Zoom Scale Factor", command=self.set_zoom_scale)

        hotkeys_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Hotkeys (F1)", menu=hotkeys_menu)
        hotkeys_menu.add_command(label="HotKeys List", command=self.show_hotkeys)

    def _creat_toolbar(self):
        self.open_button = tk.Button(
            self.frame_toolbar,
            text="Open",
            command=self.open_main_image,
            bg=self.button_color,
        )
        self.open_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.save_button = tk.Button(
            self.frame_toolbar,
            text="Export",
            command=self.save_main_line,
            bg=self.button_color,
        )
        self.save_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.redraw_button = tk.Button(
            self.frame_toolbar,
            text="Redraw",
            command=self.redraw_lines,
            bg=self.button_color,
        )
        self.redraw_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.undo_button = tk.Button(
            self.frame_toolbar,
            text="Undo",
            command=self.undo_last_action,
            bg=self.button_color,
        )
        self.undo_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.redo_button = tk.Button(
            self.frame_toolbar,
            text="Redo",
            command=self.redo_last_action,
            bg=self.button_color,
        )
        self.redo_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.clean_button = tk.Button(
            self.frame_toolbar,
            text="Clean",
            command=self.clear_all_linedatas,
            bg=self.button_color,
        )
        self.clean_button.pack(
            side=tk.LEFT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.zoom_scale_button = tk.Button(
            self.frame_toolbar,
            text="Zoom Scale Factor",
            command=self.set_zoom_scale,
            bg=self.button_color,
        )
        self.zoom_scale_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.mouse_sensitivity_button = tk.Button(
            self.frame_toolbar,
            text="Mouse Sensitivity",
            command=self.set_mouse_sensitivity,
            bg=self.button_color,
        )
        self.mouse_sensitivity_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.point_scale_button = tk.Button(
            self.frame_toolbar,
            text="Point Scale Factor",
            command=self.set_point_scale,
            bg=self.button_color,
        )
        self.point_scale_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.point_interval_button = tk.Button(
            self.frame_toolbar,
            text="Point Interval",
            command=self.set_point_interval,
            bg=self.button_color,
        )
        self.point_interval_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.linewidth_button = tk.Button(
            self.frame_toolbar,
            text="Line Width",
            command=self.set_line_width,
            bg=self.button_color,
        )
        self.linewidth_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_pady
        )

        self.linecolor_button = tk.Button(
            self.frame_toolbar,
            text="Line Color",
            command=self.set_line_color,
            bg=self.button_color,
        )
        self.linecolor_button.pack(
            side=tk.RIGHT, padx=self.toolbar_padx, pady=self.toolbar_padx
        )

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
            sticky='E',
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
            sticky='E',
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
            sticky='E',
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
            sticky='E',
        )

        self.entry_x1 = tk.Entry(self.frame_settings, relief=tk.RAISED)
        self.entry_x1.grid(
            row=0, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_x2 = tk.Entry(
            self.frame_settings,
            relief=tk.RAISED,
        )
        self.entry_x2.grid(
            row=1, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_y1 = tk.Entry(
            self.frame_settings,
            relief=tk.RAISED,
        )
        self.entry_y1.grid(
            row=2, column=1, padx=self.setting_padx, pady=self.setting_pady
        )
        self.entry_y2 = tk.Entry(
            self.frame_settings,
            relief=tk.RAISED,
        )
        self.entry_y2.grid(
            row=3, column=1, padx=self.setting_padx, pady=self.setting_pady
        )

        self.button_x1 = tk.Button(
            self.frame_settings,
            text="Set X1",
            command=self.record_x1_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_x1.grid(
            row=0,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        self.button_x2 = tk.Button(
            self.frame_settings,
            text="Set X2",
            command=self.record_x2_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_x2.grid(
            row=1,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        self.button_y1 = tk.Button(
            self.frame_settings,
            text="Set Y1",
            command=self.record_y1_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_y1.grid(
            row=2,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
        )
        self.button_y2 = tk.Button(
            self.frame_settings,
            text="Set Y2",
            command=self.record_y2_screen,
            relief=tk.RAISED,
            bg=self.button_color,
        )
        self.button_y2.grid(
            row=3,
            column=2,
            padx=self.setting_padx,
            pady=self.setting_pady,
            sticky='W',
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
        # combobox for draw mode
        tk.Label(
            self.frame_operations,
            text="Draw Mode:",
            relief=tk.RAISED,
            bg=self.label_color,
        ).grid(
            row=0,
            column=0,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='E',
        )

        self.drawmode_option = tk.StringVar()
        self.drawmode_combobox = ttk.Combobox(
            self.frame_operations,
            textvariable=self.drawmode_option,
            state="readonly",
        )
        self.drawmode_combobox.grid(
            row=0,
            column=1,
            columnspan=2,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='W',
        )
        self.drawmode_combobox['values'] = ("Point", "Point-Line")
        self.drawmode_combobox.current(0)
        self.drawmode_combobox.bind("<<ComboboxSelected>>", self.set_drawmode)

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
            sticky='W',
        )

        self.pick_color_button = tk.Button(
            self.frame_operations,
            text="Pick Color",
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
            text="Assisted Pick Points",
            variable=self.assisted_option,
            command=self.set_assisted_point,
            relief=tk.RAISED,
        )
        self.assisted_checkbox.grid(
            row=1,
            column=2,
            padx=self.operation_padx,
            pady=self.operation_pady,
            sticky='E',
        )

    def set_assisted_point(self):
        self.main.if_assisted = self.assisted_option.get() == 1
        self._print("INFO", "Assisted Pick Points: " + str(self.main.if_assisted))

    def change_assisted_point(self):
        self.assisted_option.set(1 - self.assisted_option.get())
        self.set_assisted_point()

    def _pick_color(self):
        if not self.main.image:
            self._print("ERROR", "No Image Loaded!!!")
            return

        if self.main.line.last_point:
            self.main.assisted_point.set_ref_color(
                self.main.image, self.main.line.last_point
            )
            ref_color = self.rgb_to_hex(self.main.assisted_point.ref_color)
            self.ref_color_label.config(
                background=ref_color,
                foreground=self._comple_color(ref_color),
                text=ref_color,
            )
            self._print("INFO", "Reference Color: " + ref_color)
        else:
            self._print("ERROR", "No Point Picked!!!")

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
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")],
            title="Choose an image file",
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
            self._print("INFO", f"Image opened successfully: {self.image_file}")

            if self.main.line.line_segments:
                self.clear_all_linedatas()

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
            real_zoom_size = self.zoom_size // self.scale_factor
            half_real_zoom_size = self.zoom_size // (2 * self.scale_factor)
            if x - half_real_zoom_size < 0:
                dx = (x - half_real_zoom_size) * self.scale_factor
                self.zoom_left = 0
                self.zoom_right = self.zoom_left + real_zoom_size
            elif x + half_real_zoom_size > self.main.image.width:
                dx = (
                    x + half_real_zoom_size - self.main.image.width
                ) * self.scale_factor
                self.zoom_right = self.main.image.width
                self.zoom_left = self.zoom_right - real_zoom_size
            else:
                dx = 0
                self.zoom_left = x - half_real_zoom_size
                self.zoom_right = x + half_real_zoom_size

            if y - half_real_zoom_size < 0:
                dy = (y - half_real_zoom_size) * self.scale_factor
                self.zoom_upper = 0
                self.zoom_lower = self.zoom_upper + real_zoom_size
            elif y + half_real_zoom_size > self.main.image.height:
                dy = (
                    y + half_real_zoom_size - self.main.image.height
                ) * self.scale_factor
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
                        (px - self.zoom_left) * self.scale_factor,
                        (py - self.zoom_upper) * self.scale_factor,
                    )
                    for px, py in segment
                ]
                self.zoom.line.line_segments.append(zoom_segment)

        self.zoom.line.current_segment.clear()
        if self.main.line.current_segment:
            self.zoom.line.current_segment = [
                (
                    (px - self.zoom_left) * self.scale_factor,
                    (py - self.zoom_upper) * self.scale_factor,
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
        self.main.stop_draw_photoline(event)
        self.update_all_lines()

    def draw_line(self, event):
        # draw line in main image
        self.main.draw_photoline(event)
        self.update_all_lines()

    def save_main_line(self):
        if self.main.line.line_segments:
            output_file = filedialog.asksaveasfilename(
                defaultextension=".dat",
                filetypes=[("DAT files", "*.dat")],
                title="Save the line data to a file",
            )
            all_points = [
                point for segment in self.main.line.line_segments for point in segment
            ]

            if (
                self.x1_screen is None
                or self.x2_screen is None
                or self.x1_real is None
                or self.x2_real is None
                or self.y1_screen is None
                or self.y2_screen is None
                or self.y1_real is None
                or self.y2_real is None
            ):  # if not set coordinates, output all points without conversion
                self._print("WARNING", "Set the coordinates first ! ! !")
                converted_points = all_points
            else:  # if set coordinates, convert points to real coordinates
                x_scale = (self.x2_real - self.x1_real) / (
                    self.x2_screen - self.x1_screen
                )
                y_scale = (self.y2_real - self.y1_real) / (
                    self.y2_screen - self.y1_screen
                )

                x_offset = self.x1_real - self.x1_screen * x_scale
                y_offset = self.y1_real - self.y1_screen * y_scale

                converted_points = [
                    (x * x_scale + x_offset, y * y_scale + y_offset)
                    for x, y in all_points
                ]

            if output_file:
                with open(output_file, 'w') as f:
                    for point in converted_points:
                        f.write(f"{point[0]} {point[1]}\n")
                self._print("INFO", f"Line data has been saved: {output_file}")
        else:
            self._print("ERROR", "No lines to save ! ! !")

    def update_all_lines(self):
        self.update_zoom_line()
        self.main.update_photoline()
        self.zoom.update_photoline()
        self.update_zoom_cursor()

    def update_all_photos(self):
        status1 = self.main.update_photo()
        status2 = self.zoom.update_photo()
        # if status1 == 0 and status2 == 0:
        #     self._print("INFO", "Photos Updated")

    def clear_all_linedatas(self):
        status1 = self.main.clear_linedata()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", "Clear all line datas")
            self.update_all_photos()
        else:
            self._print("WARNING", "No lines to clear!")

    def undo_last_action(self):
        status1 = self.main.undo_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", "Undone")
        else:
            self._print("WARNING", "Already the oldest location!")

    def redo_last_action(self):
        status1 = self.main.redo_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", "Redone")
        else:
            self._print("WARNING", "Already the latest location!")

    def redraw_lines(self):
        status1 = self.main.redraw_photoline()
        self.update_all_lines()
        if status1 == 0:
            self._print("INFO", "Line Re-drawn")
        else:
            self._print("WARNING", "No lines to re-draw!")

    def record_x1_screen(self):
        if self.main.line.last_point:
            if self.entry_x1.get():
                self.x1_screen = self.main.line.last_point[0]
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.x1_real = float(self.entry_x1.get())
                self._print("INFO", f"X1: {self.x1_real}")
            else:
                self._print("ERROR", "Enter the coordinate values ​​first!")
        else:
            self._print("ERROR", "Pick a point first ! ! !")

    def record_x2_screen(self):
        if self.main.line.last_point:
            if self.entry_x2.get():
                self.x2_screen = self.main.line.last_point[0]
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.x2_real = float(self.entry_x2.get())
                self._print("INFO", f"X2: {self.x2_real}")
            else:
                self._print("ERROR", "Enter the coordinate values ​​first!")
        else:
            self._print("ERROR", "Pick a point first ! ! !")

    def record_y1_screen(self):
        if self.main.line.last_point:
            if self.entry_y1.get():
                self.y1_screen = self.main.line.last_point[1]
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.y1_real = float(self.entry_y1.get())
                self._print("INFO", f"Y1: {self.y1_real}")
            else:
                self._print("ERROR", "Enter the coordinate values ​​first!")
        else:
            self._print("ERROR", "Pick a point first ! ! !")

    def record_y2_screen(self):
        if self.main.line.last_point:
            if self.entry_y2.get():
                self.y2_screen = self.main.line.last_point[1]
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.y2_real = float(self.entry_y2.get())
                self._print("INFO", f"Y2: {self.y2_real}")
            else:
                self._print("ERROR", "Enter the coordinate values ​​first!")
        else:
            self._print("ERROR", "Pick a point first ! ! !")

    def set_drawmode(self, event):
        self.main.drawmode = self.drawmode_combobox.current()
        self.zoom.drawmode = self.drawmode_combobox.current()
        self.update_all_lines()
        self._print("INFO", f"Draw Mode: {self.drawmode_option.get()}")

    def set_line_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.main.line.set_line_color(color)
            self.zoom.line.set_line_color(color)
            self.update_all_lines()
            self._print("INFO", f"Line color: {color}")

    def set_line_width(self):
        width = simpledialog.askinteger(
            "Set Line Width",
            f"Input Line Width (1-10, default {self.default_line_width})：",
            minvalue=1,
            maxvalue=10,
        )
        if width:
            self.main.line.set_line_width(width)
            self.zoom.line.set_line_width(min(10, width * self.scale_factor))
            self.update_all_lines()
            self._print("INFO", f"Line width: {width}")

    def set_point_interval(self):
        interval = simpledialog.askinteger(
            "Set Point Interval",
            f"Input Point Interval (1-50, default {self.default_point_interval})：",
            minvalue=1,
            maxvalue=50,
        )
        if interval:
            self.main.line.set_point_interval(interval)
            self._print("INFO", f"Point interval: {interval}")

    def set_mouse_sensitivity(self):
        sensitivity = simpledialog.askinteger(
            "Set Mouse Sensitivity",
            "Input Mouse Sensitivity (1-20),\n or turn up/down by Ctrl+Shift+A/D：",
            minvalue=1,
            maxvalue=20,
        )
        if sensitivity:
            self.mouse_set.set_mouse_sensitivity(sensitivity)
            self._print("INFO", f"Mouse sensitivity: {sensitivity}")

    def set_zoom_scale(self):
        factor = simpledialog.askinteger(
            "Set Zoom Scale Factor",
            f"Input Zoom Scale Factor (1-10, default {self.default_scale_factor})：",
            minvalue=1,
            maxvalue=10,
        )
        if factor:
            self.scale_factor = factor
            self.zoom.line.set_line_width(
                min(10, self.zoom.line.line_width * self.scale_factor)
            )
            # self.update_zoom_image(event)
            self.update_all_lines()
            self._print("INFO", f"Zoom Scale factor: {factor}")

    def set_zoom_scale_by_mouse_wheel(self, event):
        if event.delta > 0:
            self.scale_factor += 1
        else:
            self.scale_factor -= 1
        self.scale_factor = max(1, min(self.scale_factor, 10))
        self.zoom.line.set_line_width(
            min(10, self.main.line.line_width * self.scale_factor)
        )
        self.update_zoom_image(event)
        self.update_all_lines()
        self._print("INFO", f"Zoom Scale factor: {self.scale_factor}")

    def set_point_scale(self):
        factor = simpledialog.askfloat(
            "Set Point Scale Factor",
            f"Input Point Scale Factor (0.1-10, default {self.default_point_scale})：",
            minvalue=0.1,
            maxvalue=10,
        )
        if factor:
            self.main.line.set_point_scale(factor)
            self.zoom.line.set_point_scale(factor)
            self.update_all_lines()
            self._print("INFO", f"Point scale Factor: {factor}")

    def up_mouse_sensitivity(self):
        self.mouse_set.up_mouse_sensitivity()
        self._print(
            "INFO", f"Mouse sensitivity: {self.mouse_set.get_mouse_sensitivity()}"
        )

    def down_mouse_sensitivity(self):
        self.mouse_set.down_mouse_sensitivity()
        self._print(
            "INFO", f"Mouse sensitivity: {self.mouse_set.get_mouse_sensitivity()}"
        )

    def reset_mouse_sensitivity(self):
        self.mouse_set.reset_mouse_sensitivity()
        self._print("INFO", f"Mouse sensitivity: {self.mouse_set.original_sensitivity}")

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
