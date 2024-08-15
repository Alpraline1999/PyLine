import tkinter as tk
from PIL import ImageTk
import drawline


class DrawPhoto:
    def __init__(self, root):
        self.canvas = tk.Canvas(root)
        self.image = None
        self.photo = None
        self.line = drawline.DrawLine()
        self.drawmode = 1  # 0:Point 1:Point-Line

    def set_photoimage(self, image):
        self.image = image
        self.photo = ImageTk.PhotoImage(self.image)
        self.update_photo()

    def start_draw_photoline(self, event):
        if self.photo:
            self.line.start_draw_line(event)
            self.draw_segment_point(self.line.current_segment[-1:])

    def stop_draw_photoline(self, event):
        if self.photo:
            self.line.stop_draw_line(event)

    def draw_photoline(self, event):
        if self.photo:
            status = self.line.draw_line(event)
            if self.line.current_segment:
                self.draw_segment_point(self.line.current_segment[-1:])
            if len(self.line.current_segment) > 1:
                self.draw_segment_line(self.line.current_segment[-2:])
            return status

    def update_photoline(self):
        self.update_photo()
        self.line.update_allpoints()
        self.draw_segment_point(self.line.line_all_points)
        self.draw_segment_line(self.line.line_all_points)

        self.draw_segment_point(self.line.current_segment)
        self.draw_segment_line(self.line.current_segment)

    def draw_segment_line(self, segment):
        if self.drawmode == 0:
            return
        if len(segment) > 1:
            for i in range(1, len(segment)):
                self.canvas.create_line(
                    segment[i - 1],
                    segment[i],
                    fill=self.line.line_color,
                    width=self.line.line_width,
                )

    def draw_segment_point(self, segment):
        if segment:
            for i in range(0, len(segment)):
                x, y = segment[i][0], segment[i][1]
                self.canvas.create_oval(
                    x - self.line.point_radius,
                    y - self.line.point_radius,
                    x + self.line.point_radius,
                    y + self.line.point_radius,
                    fill=self.line.line_color,
                )

    def update_photo(self):
        self.canvas.delete("all")
        if self.photo:
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
            return 0
        else:
            return 1

    def clear_linedata(self):
        status = self.line.clear_line()
        if status == 0:
            self.update_photo()
            return 0
        else:
            return 1

    def undo_photoline(self):
        status = self.line.undo_line()
        if status == 0:
            self.update_photoline()
            return 0
        else:
            return 1

    def redo_photoline(self):
        status = self.line.redo_line()
        if status == 0:
            self.update_photoline()
            return 0
        else:
            return 1

    def redraw_photoline(self):
        status = self.line.redraw_line()
        if status == 0:
            self.update_photoline()
            return 0
        else:
            return 1
