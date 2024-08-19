from collections import deque
import math
import copy


class DrawLine:
    def __init__(self):
        self.tools = Tools()
        self.line_segments = deque()
        self.line_all_points = []
        max_len_of_undo_redo = 100
        self.redo_stack = deque(maxlen=max_len_of_undo_redo)
        self.undo_stack = deque(maxlen=max_len_of_undo_redo)
        self.current_segment = []
        self.last_point = []
        self.drawing = False

        self.line_color = "black"
        self.line_width = 2
        self.point_scale = 1  # point_radius = point_scale * line_width
        self.point_radius = 1
        self.point_interval = 2

    def start_draw_line(self, event):
        self.drawing = True
        self.current_segment.clear()
        x, y = event.x, event.y
        self.current_segment.append((x, y))

    def stop_draw_line(self, event):
        self.redo_stack.clear()  # clear redo_stack for undo/redo
        self._backup_line()

        if self.drawing:
            self.drawing = False
            if self.current_segment:
                self.line_segments.append(self.current_segment.copy())
                self.last_point = self.current_segment[-1]
        self.current_segment.clear()

    def update_allpoints(self):
        self.line_all_points = [
            point for segment in self.line_segments for point in segment
        ]

    def draw_line(self, event):
        if self.drawing:
            x, y = event.x, event.y
            if len(self.current_segment) == 0 or (
                self.tools.abs_r((x, y), self.current_segment[-1])
                >= self.point_interval
            ):
                self.current_segment.append((x, y))
                return 0
        return 1

    def _backup_line(self):
        # back up line_segments for undo/redo
        self.undo_stack.append(copy.deepcopy(self.line_segments))

    def clear_line(self):
        if self.line_segments:
            self.redo_stack.clear()
            self._backup_line()
            self.line_segments.clear()
            self.last_point = []
            return 0
        else:
            return 1

    def undo_line(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.line_segments))
            self.line_segments = self.undo_stack.pop()
            return 0
        else:
            return 1

    def redo_line(self):
        if self.redo_stack:
            self._backup_line()
            self.line_segments = self.redo_stack.pop()
            return 0
        else:
            return 1

    def redraw_line(self):
        if self.line_segments:
            all_points = [point for segment in self.line_segments for point in segment]
            sorted_points = sorted(all_points, key=lambda p: p[0])

            self.redo_stack.clear()
            self._backup_line()

            self.line_segments = self._split_into_segments(sorted_points)
            return 0
        else:
            return 1

    def _split_into_segments(self, points):
        if not points:
            return deque()
        segments = deque()
        current_segment = [points[0]]
        for p1, p2 in zip(points, points[1:]):
            if p1 == current_segment[-1]:
                current_segment.append(p2)
            else:
                segments.append(current_segment)
                current_segment = [p2]
        if current_segment:
            segments.append(current_segment)
        return segments

    def set_line_color(self, color):
        self.line_color = color

    def set_line_width(self, width):
        self.line_width = width
        self.update_point_radius()

    def set_point_scale(self, scale):
        self.point_scale = scale
        self.update_point_radius()

    def update_point_radius(self):
        self.point_radius = self.point_scale * self.line_width

    def set_point_interval(self, interval):
        self.point_interval = interval


class CheckRange:
    def __init__(self):
        self.tools = Tools()
        self.eccen = 0.98  # eccentricity of the ellipse
        self.x0, self.y0 = None, None
        self.a, self.b = None, None
        self.theta = None

    def set_range(self, p1, p2):
        self.x0, self.y0 = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        self.a = self.tools.abs_r(p1, p2) / 2
        self.b = self.a * (1 - self.eccen**2) ** 0.5
        self.theta = math.atan2(p2[1] - p1[1], p2[0] - p1[0])

    def check_range(self, point):
        dx, dy = point[0] - self.x0, point[1] - self.y0
        x_rot = dx * math.cos(self.theta) + dy * math.sin(self.theta)
        y_rot = -dx * math.sin(self.theta) + dy * math.cos(self.theta)
        return (
            x_rot**2 / self.a**2 + y_rot**2 / self.b**2 <= 1
        )  # check if the point is inside the ellipse


class Tools:
    def abs_r(self, p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
