from collections import deque


class DrawLine:
    def __init__(self):
        self.line_segments = deque()
        self.line_all_points = []
        self.redo_stack = deque()
        self.current_segment = []
        self.last_point = [0, 0]
        self.drawing = False

        self.line_color = None
        self.line_width = 1
        self.point_scale = 1  # point_radius = point_scale * line_width
        self.point_radius = 1
        self.point_interval = 1

        self.set_line_color("black")
        self.set_line_width(2)
        self.set_point_scale(1)
        self.set_point_interval(2)

    def start_draw_line(self, event):
        self.drawing = True
        self.current_segment.clear()
        x, y = event.x, event.y
        self.current_segment.append((x, y))

    def stop_draw_line(self, event):
        if self.drawing:
            self.drawing = False
            if self.current_segment:
                self.line_segments.append(self.current_segment.copy())
                self.redo_stack.clear()
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
                self.abs_r(
                    x - self.current_segment[-1][0], y - self.current_segment[-1][1]
                )
                >= self.point_interval
            ):
                self.current_segment.append((x, y))
                return 0
        return 1

    def clear_line(self):
        if self.line_segments or self.redo_stack:
            self.line_segments.clear()
            self.redo_stack.clear()
            self.last_point = [0, 0]
            return 0
        else:
            return 1

    def undo_line(self):
        if self.line_segments:
            self.redo_stack.append(self.line_segments.pop())
            return 0
        else:
            return 1

    def redo_line(self):
        if self.redo_stack:
            self.line_segments.append(self.redo_stack.pop())
            return 0
        else:
            return 1

    def redraw_line(self):
        if self.line_segments:
            all_points = [point for segment in self.line_segments for point in segment]
            sorted_points = sorted(all_points, key=lambda p: p[0])

            self.line_segments = self._split_into_segments(sorted_points)
            return 0
        else:
            return 1

    def _split_into_segments(self, points):
        if not points:
            return []
        segments = []
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

    def abs_r(self, x, y):
        return (x**2 + y**2) ** 0.5
