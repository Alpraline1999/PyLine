# pyline.py
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, Menu, ttk
from PIL import Image, ImageTk
import sys
import mouseset
import drawphoto


class PyLine:
    def __init__(self, root):
        self.root = root
        self.root.title("PyLine")
        self.root.geometry("1170x750")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.mouse_set = mouseset.MouseSensitivitySet()

        self._init_variables()
        self._create_frame()
        self._create_canvas()
        self._create_menu()
        self._creat_settings()
        self._creat_operations()
        self._bind_events()
        self._create_hotkeys()

    def _init_variables(self):
        # image file
        self.image_file = None

        #################################################
        # set paddings
        #################################################
        self.padx_frames, self.pady_frames = 5, 3  # padding for frames
        self.padx_settings, self.pady_settings = 5, 2  # padding for settings widgets
        self.padx_operations, self.pady_operations = (
            15,
            2,
        )  # padding for operation buttons
        self.button_width = 10  # button width

        #################################################
        # set default parameters
        #################################################
        self.default_line_color = 'black'  # default line color
        self.default_line_width = 2  # default line width
        self.default_point_scale = 1  # point_radius = point_scale * line_width
        self.default_point_interval = 5  # default point interval
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
        self.frame_settings = tk.Frame(self.root)
        self.frame_operations = tk.Frame(self.root)
        self.frame_zoom = tk.Frame(self.root, bg='lightgray')
        self.frame_main = tk.Frame(self.root, bg='lightgray')

        self.frame_zoom.grid(
            row=0, column=0, sticky='NSEW', padx=self.padx_frames, pady=self.pady_frames
        )
        self.frame_operations.grid(
            row=1, column=0, sticky='NSEW', padx=self.padx_frames, pady=self.pady_frames
        )
        self.frame_settings.grid(
            row=2, column=0, sticky='NSEW', padx=self.padx_frames, pady=self.pady_frames
        )
        self.frame_main.grid(
            row=0,
            column=1,
            sticky='NSEW',
            rowspan=3,
            padx=self.padx_frames,
            pady=self.pady_frames,
        )

    def _create_canvas(self):
        self.zoom_cursor = [
            self.zoom_size // 2,
            self.zoom_size // 2,
        ]
        self.zoom_position = [0, 0]
        self.zoom_last_position = self.zoom_position

        self.main = drawphoto.DrawPhoto(self.root)
        self.main.canvas.config(
            width=self.main_width, height=self.main_height, bg='White'
        )
        self.main.canvas.pack(
            in_=self.frame_main,
            padx=self.padx_frames,
            pady=self.pady_frames,
            expand=True,
        )

        self.zoom = drawphoto.DrawPhoto(self.root)
        self.zoom.canvas.config(width=self.zoom_size, height=self.zoom_size, bg='White')
        self.zoom.canvas.pack(
            in_=self.frame_zoom,
            fill=tk.BOTH,
            padx=self.padx_frames,
            pady=self.pady_frames,
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
            label="Mouse Sensitivity",
            command=self.set_mouse_sensitivity,
        )
        options_menu.add_command(label="Zoom Scale Factor", command=self.set_zoom_scale)
        options_menu.add_command(
            label="Point Scale Factor", command=self.set_point_scale
        )

        hotkeys_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Hotkeys", menu=hotkeys_menu)
        hotkeys_menu.add_command(label="HotKeys List", command=self.show_hotkeys)

    def _creat_settings(self):  # create axis settings
        tk.Label(self.frame_settings, text="X1:").grid(
            row=0,
            column=0,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='E',
        )
        tk.Label(self.frame_settings, text="X2:").grid(
            row=1,
            column=0,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='E',
        )
        tk.Label(self.frame_settings, text="Y1:").grid(
            row=2,
            column=0,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='E',
        )
        tk.Label(self.frame_settings, text="Y2:").grid(
            row=3,
            column=0,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='E',
        )

        self.entry_x1 = tk.Entry(self.frame_settings)
        self.entry_x1.grid(
            row=0, column=1, padx=self.padx_settings, pady=self.pady_settings
        )
        self.entry_x2 = tk.Entry(self.frame_settings)
        self.entry_x2.grid(
            row=1, column=1, padx=self.padx_settings, pady=self.pady_settings
        )
        self.entry_y1 = tk.Entry(self.frame_settings)
        self.entry_y1.grid(
            row=2, column=1, padx=self.padx_settings, pady=self.pady_settings
        )
        self.entry_y2 = tk.Entry(self.frame_settings)
        self.entry_y2.grid(
            row=3, column=1, padx=self.padx_settings, pady=self.pady_settings
        )

        self.button_x1 = tk.Button(
            self.frame_settings, text="Set X1", command=self.record_x1_screen
        )
        self.button_x1.grid(
            row=0,
            column=2,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='W',
        )
        self.button_x2 = tk.Button(
            self.frame_settings, text="Set X2", command=self.record_x2_screen
        )
        self.button_x2.grid(
            row=1,
            column=2,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='W',
        )
        self.button_y1 = tk.Button(
            self.frame_settings, text="Set Y1", command=self.record_y1_screen
        )
        self.button_y1.grid(
            row=2,
            column=2,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='W',
        )
        self.button_y2 = tk.Button(
            self.frame_settings, text="Set Y2", command=self.record_y2_screen
        )
        self.button_y2.grid(
            row=3,
            column=2,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='W',
        )

        self.output_text = tk.Text(
            self.frame_settings, height=10, width=45, state=tk.NORMAL
        )
        self.output_text.grid(
            row=4,
            column=0,
            columnspan=3,
            padx=self.padx_settings,
            pady=self.pady_settings,
            sticky='EW',
        )

        # redirect standard output to the custom text widget
        self.original_stdout = sys.stdout
        sys.stdout = self

    def _creat_operations(self):  # create operation buttons
        self.open_button = tk.Button(
            self.frame_operations,
            text="Open",
            command=self.open_main_image,
            width=self.button_width,
        )
        self.open_button.grid(
            row=1,
            column=0,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='EW',
        )

        self.redraw_button = tk.Button(
            self.frame_operations,
            text="Re-draw",
            command=self.redraw_lines,
            width=self.button_width,
        )
        self.redraw_button.grid(
            row=1,
            column=1,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='EW',
        )

        self.save_button = tk.Button(
            self.frame_operations,
            text="Export",
            command=self.save_main_line,
            width=self.button_width,
        )
        self.save_button.grid(
            row=1,
            column=2,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='E',
        )

        self.undo_button = tk.Button(
            self.frame_operations,
            text="Undo",
            command=self.undo_last_action,
            width=self.button_width,
        )
        self.undo_button.grid(
            row=2,
            column=0,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='EW',
        )

        self.undo_button = tk.Button(
            self.frame_operations,
            text="Redo",
            command=self.redo_last_action,
            width=self.button_width,
        )
        self.undo_button.grid(
            row=2,
            column=1,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='EW',
        )

        self.clear_button = tk.Button(
            self.frame_operations,
            text="Clean",
            command=self.clear_all_linedatas,
            width=self.button_width,
        )
        self.clear_button.grid(
            row=2,
            column=2,
            padx=self.padx_operations,
            pady=self.pady_operations,
            sticky='E',
        )

        # combobox for draw mode
        tk.Label(self.frame_operations, text="Draw Mode:").grid(
            row=0,
            column=0,
            padx=self.padx_operations,
            pady=self.padx_operations,
            sticky='E',
        )

        self.drawmode_option = tk.StringVar()
        self.drawmode_combobox = ttk.Combobox(
            self.frame_operations, textvariable=self.drawmode_option
        )
        self.drawmode_combobox.grid(
            row=0,
            column=1,
            columnspan=2,
            padx=self.padx_operations,
            pady=self.padx_operations,
            sticky='E',
        )
        self.drawmode_combobox['values'] = ("Point", "Point-Line")
        self.drawmode_combobox.current(1)
        self.drawmode_combobox.bind("<<ComboboxSelected>>", self.set_drawmode)

    def _bind_events(self):
        self.main.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.main.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.main.canvas.bind("<Motion>", self.update_zoom_image)
        self.main.canvas.bind("<Motion>", self.draw_line, add='+')

    def _create_hotkeys(self):
        self.root.bind('<Control-h>', lambda event: self.show_hotkeys())
        self.root.bind("<Control-o>", lambda event: self.open_main_image())
        self.root.bind("<Control-s>", lambda event: self.save_main_line())
        self.root.bind("<Control-q>", lambda event: self.on_closing())
        self.root.bind("<Control-r>", lambda event: self.redraw_lines())
        self.root.bind("<Control-z>", lambda event: self.undo_last_action())
        self.root.bind("<Control-y>", lambda event: self.redo_last_action())
        self.root.bind("<Control-d>", lambda event: self.clear_all_linedatas())

        self.root.bind("<Control-Shift-Key-C>", lambda event: self.set_line_color())
        self.root.bind("<Control-Shift-Key-W>", lambda event: self.set_line_width())
        self.root.bind("<Control-Shift-Key-A>", lambda event: self.set_point_interval())
        self.root.bind("<Control-Shift-Key-Z>", lambda event: self.set_zoom_scale())
        self.root.bind("<Control-Shift-Key-D>", lambda event: self.set_point_scale())
        self.root.bind(
            "<Control-Shift-Key-S>", lambda event: self.set_mouse_sensitivity()
        )

        self.root.bind("<Control-Key-1>", lambda event: self.down_mouse_sensitivity())
        self.root.bind("<Control-Key-2>", lambda event: self.up_mouse_sensitivity())
        self.root.bind("<Control-Key-3>", lambda event: self.reset_mouse_sensitivity())

    def show_hotkeys(self):
        self.output_text.delete(1.0, tk.END)
        self.write("Hotkeys List:               Ctrl + H\n")
        self.write("Open image:                 Ctrl + O\n")
        self.write("Export line data:           Ctrl + S\n")
        self.write("Quit:                       Ctrl + Q\n")
        self.write("Redraw:                     Ctrl + R\n")
        self.write("Undo:                       Ctrl + Z\n")
        self.write("Redo:                       Ctrl + Y\n")
        self.write("Clean:                      Ctrl + D\n")
        self.write("Set line color:             Ctrl + Shift + C\n")
        self.write("Set line width:             Ctrl + Shift + W\n")
        self.write("Set point interval:         Ctrl + Shift + A\n")
        self.write("Set zoom scale:             Ctrl + Shift + Z\n")
        self.write("Set point scale:            Ctrl + Shift + D\n")
        self.write("Set mouse sensitivity:      Ctrl + Shift + S\n")
        self.write("Decrease mouse sensitivity: Ctrl + 1\n")
        self.write("Increase mouse sensitivity: Ctrl + 2\n")
        self.write("Reset mouse sensitivity:    Ctrl + 3\n")

    def write(self, message):
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)

    def flush(self):
        pass

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
            print(">>> Image opened successfully")

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
                left = 0
                right = left + real_zoom_size
            elif x + half_real_zoom_size > self.main.image.width:
                dx = (
                    x + half_real_zoom_size - self.main.image.width
                ) * self.scale_factor
                right = self.main.image.width
                left = right - real_zoom_size
            else:
                dx = 0
                left = x - half_real_zoom_size
                right = x + half_real_zoom_size

            if y - half_real_zoom_size < 0:
                dy = (y - half_real_zoom_size) * self.scale_factor
                upper = 0
                lower = upper + real_zoom_size
            elif y + half_real_zoom_size > self.main.image.height:
                dy = (
                    y + half_real_zoom_size - self.main.image.height
                ) * self.scale_factor
                lower = self.main.image.height
                upper = lower - real_zoom_size
            else:
                dy = 0
                upper = y - half_real_zoom_size
                lower = y + half_real_zoom_size

            self.zoom_last_position = self.zoom_position
            if dx == 0:
                self.zoom_position = [x, self.zoom_position[1]]
            if dy == 0:
                self.zoom_position = [self.zoom_position[0], y]

            # update zoom image
            cropped_image = self.main.image.crop((left, upper, right, lower))
            resized_image = cropped_image.resize((self.zoom_size, self.zoom_size))
            self.zoom.set_photoimage(resized_image)

            self.zoom_cursor[0] = dx + self.zoom_size // 2
            self.zoom_cursor[1] = dy + self.zoom_size // 2

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
        # start draw line in main image
        self.main.start_draw_photoline(event)

        # start draw line in zoom image
        x, y = self.zoom_cursor[0], self.zoom_cursor[1]
        event.x, event.y = x, y
        self.zoom.start_draw_photoline(event)

    def stop_draw(self, event):
        # stop draw line in main image
        self.main.stop_draw_photoline(event)

        # stop draw line in zoom image
        self.zoom.stop_draw_photoline(event)

    def draw_line(self, event):
        # draw line in main image
        status = self.main.draw_photoline(event)

        # draw line in zoom image
        if self.zoom.photo:
            x, y = event.x, event.y
            if (
                x < 0
                or y < 0
                or x > self.main.image.width
                or y > self.main.image.height
            ):
                return

            dx, dy = (
                self.zoom_last_position[0] - self.zoom_position[0],
                self.zoom_last_position[1] - self.zoom_position[1],
            )
            dx, dy = dx * self.scale_factor, dy * self.scale_factor

            # update line data based on cursor position in zoom image
            self.zoom.line.current_segment = [
                (px + dx, py + dy) for px, py in self.zoom.line.current_segment
            ]
            self.zoom.line.line_segments = [
                [(px + dx, py + dy) for px, py in segment]
                for segment in self.zoom.line.line_segments
            ]
            # append cursor position in zoom image to line data
            if status == 0:
                x, y = self.zoom_cursor[0], self.zoom_cursor[1]
                self.zoom.line.current_segment.append((x, y))

        # update lines
        self.update_all_lines()

    def save_main_line(self):
        if self.main.line.line_segments:
            if (
                self.x1_screen is None
                or self.x2_screen is None
                or self.x1_real is None
                or self.x2_real is None
                or self.y1_screen is None
                or self.y2_screen is None
                or self.y1_real is None
                or self.y2_real is None
            ):
                print(">>> ERROR <<< Set the coordinates first ! ! !")
                return

            x_scale = (self.x2_real - self.x1_real) / (self.x2_screen - self.x1_screen)
            y_scale = (self.y2_real - self.y1_real) / (self.y2_screen - self.y1_screen)

            x_offset = self.x1_real - self.x1_screen * x_scale
            y_offset = self.y1_real - self.y1_screen * y_scale

            all_points = [
                point for segment in self.main.line.line_segments for point in segment
            ]
            converted_points = [
                (x * x_scale + x_offset, y * y_scale + y_offset) for x, y in all_points
            ]

            output_file = filedialog.asksaveasfilename(
                defaultextension=".dat",
                filetypes=[("DAT files", "*.dat")],
                title="Save the line data to a file",
            )
            if output_file:
                with open(output_file, 'W') as f:
                    for point in converted_points:
                        f.write(f"{point[0]} {point[1]}\n")
                print(f">>> Line data has been saved to {output_file}")
        else:
            print(">>> ERROR <<< No lines to save ! ! !")

    def clear_all_linedatas(self):
        status1 = self.main.clear_linedata()
        status2 = self.zoom.clear_linedata()
        if status1 == 0 and status2 == 0:
            print(">>> Clear all line datas")
            self.update_all_photos()

    def update_all_lines(self):
        self.main.update_photoline()
        self.zoom.update_photoline()
        self.update_zoom_cursor()

    def update_all_photos(self):
        status1 = self.main.update_photo()
        status2 = self.zoom.update_photo()
        # if status1 == 0 and status2 == 0:
        #     print(">>> Photos Updated")

    def redraw_lines(self):

        status1 = self.main.redraw_photoline()
        status2 = self.zoom.redraw_photoline()
        if status1 == 0 and status2 == 0:
            print(">>> Line Re-drawn")

    def undo_last_action(self):
        status1 = self.main.undo_photoline()
        status2 = self.zoom.undo_photoline()
        if status1 == 0 and status2 == 0:
            print(">>> Undone")

    def redo_last_action(self):
        status1 = self.main.redo_photoline()
        status2 = self.zoom.redo_photoline()
        if status1 == 0 and status2 == 0:
            print(">>> Redone")

    def record_x1_screen(self):
        if self.main.line.last_point:
            if self.entry_x1.get():
                self.x1_screen = self.main.line.last_point[0]
                print(f">>> X1_screen: {self.x1_screen}")
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.x1_real = float(self.entry_x1.get())
            else:
                print(">>> ERROR <<< Set coordinate first ! ! !")
        else:
            print(">>> ERROR <<< Pick a point first ! ! !")

    def record_x2_screen(self):
        if self.main.line.last_point:
            if self.entry_x2.get():
                self.x2_screen = self.main.line.last_point[0]
                print(f">>> X2_screen: {self.x2_screen}")
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.x2_real = float(self.entry_x2.get())
            else:
                print(">>> ERROR <<< Set coordinate first ! ! !")
        else:
            print(">>> ERROR <<< Pick a point first ! ! !")

    def record_y1_screen(self):
        if self.main.line.last_point:
            if self.entry_y1.get():
                self.y1_screen = self.main.line.last_point[1]
                print(f">>> Y1_screen: {self.y1_screen}")
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.y1_real = float(self.entry_y1.get())
            else:
                print(">>> ERROR <<< Set coordinate first ! ! !")
        else:
            print(">>> ERROR <<< Pick a point first ! ! !")

    def record_y2_screen(self):
        if self.main.line.last_point:
            if self.entry_y2.get():
                self.y2_screen = self.main.line.last_point[1]
                print(f">>> Y2_screen: {self.y2_screen}")
                self.clear_all_linedatas()
                self.main.line.last_point = []
                self.y2_real = float(self.entry_y2.get())
            else:
                print(">>> ERROR <<< Set coordinate first ! ! !")
        else:
            print(">>> ERROR <<< Pick a point first ! ! !")

    def set_drawmode(self, event):
        self.main.drawmode = self.drawmode_combobox.current()
        self.zoom.drawmode = self.drawmode_combobox.current()
        self.update_all_lines()
        print(f">>> Draw Mode: {self.drawmode_option.get()}")

    def set_line_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.main.line.set_line_color(color)
            self.zoom.line.set_line_color(color)
            self.update_all_lines()
            print(f">>> Line color: {color}")

    def set_line_width(self):
        width = simpledialog.askinteger(
            "Set Line Width",
            f"Input Line Width (1-10, default {self.default_line_width})：",
            minvalue=1,
            maxvalue=10,
        )
        if width:
            self.main.line.set_line_width(width)
            self.zoom.line.set_line_width(width * self.scale_factor)
            self.update_all_lines()
            print(f">>> Line width: {width}")

    def set_point_interval(self):
        interval = simpledialog.askinteger(
            "Set Point Interval",
            f"Input Point Interval (1-50, default {self.default_point_interval})：",
            minvalue=1,
            maxvalue=50,
        )
        if interval:
            self.main.line.set_point_interval(interval)
            self.zoom.line.set_point_interval(interval * self.scale_factor)
            print(f">>> Point interval: {interval}")

    def set_mouse_sensitivity(self):
        sensitivity = simpledialog.askinteger(
            "Set Mouse Sensitivity",
            "Input Mouse Sensitivity (1-20),\n or turn up/down by Ctrl+Shift+A/D：",
            minvalue=1,
            maxvalue=20,
        )
        if sensitivity:
            self.mouse_set.set_mouse_sensitivity(sensitivity)
            print(f">>> Mouse sensitivity: {sensitivity}")

    def set_zoom_scale(self):
        factor = simpledialog.askinteger(
            "Set Zoom Scale Factor",
            f"Input Zoom Scale Factor (1-10, default {self.default_scale_factor})：",
            minvalue=1,
            maxvalue=10,
        )
        if factor:
            self.scale_factor = factor
            self.update_all_lines()
            print(f">>> Zoom Scale factor: {factor}")

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
            print(f">>> Point scale Factor: {factor}")

    def up_mouse_sensitivity(self):
        self.mouse_set.up_mouse_sensitivity()
        print(f">>> Mouse sensitivity: {self.mouse_set.get_mouse_sensitivity()}")

    def down_mouse_sensitivity(self):
        self.mouse_set.down_mouse_sensitivity()
        print(f">>> Mouse sensitivity: {self.mouse_set.get_mouse_sensitivity()}")

    def reset_mouse_sensitivity(self):
        self.mouse_set.reset_mouse_sensitivity()
        print(f">>> Mouse sensitivity: {self.mouse_set.original_sensitivity}")

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
