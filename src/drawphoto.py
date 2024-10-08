import numpy as np
import tkinter as tk
from PIL import ImageTk
import drawline


class DrawPhoto:
    def __init__(self, root):
        self.canvas = tk.Canvas(root)
        self.image = None
        self.photo = None
        self.line = drawline.DrawLine()
        self.draw_mode = 0  # 0:Point 1:Point-Line
        self.assisted_point = AssistedPoint()
        self.if_assisted = False
        self.if_erase = True

    def set_photoimage(self, image):
        self.image = image
        self.photo = ImageTk.PhotoImage(self.image)
        self.update_photo()

    def start_draw_photoline(self, event):
        if self.photo:
            self.line.start_draw_line(event)

    def stop_draw_photoline(self, event):
        if self.photo:
            self.line.stop_draw_line(event)
            return self.assisted_draw()

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
        if self.draw_mode == 0:
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
        return status

    def redo_photoline(self):
        status = self.line.redo_line()
        return status

    def redraw_photoline(self):
        status = self.line.redraw_line()
        return status

    def erase_points(self, event):
        if self.if_erase:
            if self.line.line_segments:
                changed = -1
                for i in range(len(self.line.line_segments) - 1, -1, -1):
                    for j in range(len(self.line.line_segments[i]) - 1, -1, -1):
                        if self.assisted_point.check_erase_range(
                            event, self.line.line_segments[i][j]
                        ):
                            changed = 0
                            self.line.line_segments[i].pop(j)
                    if self.line.line_segments[i] == []:
                        self.line.line_segments.pop(i)
                return changed
            else:
                return 1
        else:
            return 1

    def assisted_draw(self):
        if self.if_assisted:
            self.line.update_allpoints()
            if len(self.line.line_all_points) > 1:
                if not self.assisted_point.ref_color is None:
                    # get assisted points
                    p1 = self.line.line_all_points[-2]
                    p2 = self.line.line_all_points[-1]
                    assited_points = self.assisted_point.ergodic_range(
                        self.image, p1, p2
                    )

                    if len(assited_points) > 0:
                        # clear redo stack and back up line_segments for undo/redo
                        self.line.redo_stack.clear()
                        self.line._backup_line()

                        points_to_remove = 2
                        while points_to_remove > 0 and self.line.line_segments:
                            last_segment = self.line.line_segments[-1]

                            num_points = len(last_segment)
                            points_to_remove_now = min(points_to_remove, num_points)

                            last_segment = last_segment[:-points_to_remove_now]

                            if last_segment:
                                self.line.line_segments[-1] = last_segment
                            else:
                                self.line.line_segments.pop()

                            points_to_remove -= points_to_remove_now

                        # organize assisted points according to point-interval
                        assited_points_sorted = sorted(
                            [point for point in assited_points], key=lambda p: p[0]
                        )
                        assited_points = [p1]
                        temp_point = p1
                        for i in range(0, len(assited_points_sorted)):
                            if (
                                self.line.tools.abs_r(assited_points_sorted[i], p1)
                                >= self.line.point_interval
                                and self.line.tools.abs_r(assited_points_sorted[i], p2)
                                >= self.line.point_interval
                            ) and (
                                self.line.tools.abs_r(
                                    assited_points_sorted[i], temp_point
                                )
                                >= self.line.point_interval
                                or i == len(assited_points_sorted) - 1
                            ):
                                assited_points.append(assited_points_sorted[i])
                                temp_point = assited_points_sorted[i]
                        assited_points.append(p2)

                        # add the assisted points
                        self.line.line_segments.append(assited_points)
                        return 0
                    else:
                        return 1
                else:
                    return -1  # if ref_color is not set, return -1
            else:
                return 1
        else:
            return 1

    def auto_draw(self):
        if not self.assisted_point.ref_color is None:
            # get assisted points
            assited_points = self.assisted_point.ergodic_all_range(self.image)

            if len(assited_points) > 0:
                # clear redo stack and back up line_segments for undo/redo
                self.line.redo_stack.clear()
                self.line._backup_line()
                self.clear_linedata()

                # organize assisted points according to point-interval
                assited_points_sorted = sorted(
                    [point for point in assited_points], key=lambda p: p[0]
                )
                assited_points = assited_points_sorted[0:1]
                temp_point = assited_points[0]
                for i in range(0, len(assited_points_sorted)):
                    if (
                        self.line.tools.abs_r(assited_points_sorted[i], temp_point)
                        >= self.line.point_interval
                        or i == len(assited_points_sorted) - 1
                    ):
                        assited_points.append(assited_points_sorted[i])
                        temp_point = assited_points_sorted[i]

                # add the assisted points
                self.line.line_segments.append(assited_points)
                return 0
            else:
                return 1
        else:
            return -1


class AssistedPoint:
    def __init__(self):
        self.recog_range = 1.0  # the initial range of the recognition
        self.erase_range = 15  # the initial range of the eraser
        self.checkrange = drawline.CheckRange()
        self.ref_color = None  # the reference color
        self.auto_mode = 0  # 0: Distance 1: CIE76

    def set_recog_range(self, range):
        self.recog_range = range

    def set_erase_range(self, range):
        self.erase_range = range

    def check_erase_range(self, event, point):
        if (
            point[0] < event.x - self.erase_range
            or point[0] > event.x + self.erase_range
            or point[1] < event.y - self.erase_range
            or point[1] > event.y + self.erase_range
        ):
            return False
        else:
            return True

    def set_ref_color(self, image, point):
        self.ref_color = self.get_color(image, point)

    def get_color(self, image, point):
        return image.getpixel(point)[0:3]

    def ergodic_range(self, image, p1, p2):
        self.checkrange.set_range(p1, p2)
        p1, p2 = (min(p1[0], p2[0]), min(p1[1], p2[1])), (
            max(p1[0], p2[0]),
            max(p1[1], p2[1]),
        )
        output = []
        for x in range(p1[0], p2[0] + 1):
            temp = []
            for y in range(
                p1[1] - int(self.checkrange.b), p2[1] + 1 + int(self.checkrange.b)
            ):
                if x == p1[0] and y == p1[1]:
                    continue
                elif x == p2[0] and y == p2[1]:
                    continue
                if self.checkrange.check_range((x, y)):
                    point_color = self.get_color(image, (x, y))
                    if self.if_color_close(point_color, self.ref_color, self.auto_mode):
                        temp.append(y)
            if len(temp) > 0:
                y_average = int(np.average(temp))
                output.append((x, y_average))
        return output

    def ergodic_all_range(self, image):
        output = []
        for x in range(0, image.width):
            for y in range(0, image.height):
                point_color = self.get_color(image, (x, y))
                """
                methods used for judging color close:
                0: distance
                1: ciede2000
                2: cie76
                3: hsv
                """
                if self.if_color_close(point_color, self.ref_color, self.auto_mode):
                    output.append((x, y))
        return output

    def if_color_close(self, color1, color2, type=0):
        if type == 0:
            threshold = 30 * self.recog_range
            return self.if_color_close_distance(color1, color2, threshold)
        elif type == 1:
            threshold = 3.33 * self.recog_range
            return self.if_color_close_cie76(color1, color2, threshold)
        elif type == 2:
            return self.if_color_close_hsv(color1, color2)
        elif type == 3:
            return self.if_color_close_ciede2000(color1, color2)

    def if_color_close_distance(self, color1, color2, threshold=30):
        """
        judge if two colors are close using distance

        :param color1: the RGB value of the first color, in the format (R, G, B)
        :param color2: the RGB value of the second color, in the format (R, G, B)
        :param threshold: the value used for judging color close or not, generally 30
        :return: if color close return True, else return False
        """
        # calculate the distance between two colors
        distance = (
            (color1[0] - color2[0]) ** 2
            + (color1[1] - color2[1]) ** 2
            + (color1[2] - color2[2]) ** 2
        ) ** 0.5

        return distance < threshold

    def if_color_close_cie76(self, color1, color2, threshold=3.3):
        import colorspacious as cs

        """
        jude if two colors are close using CIE76

        :param color1: the RGB value of the first color, in the format (R, G, B)
        :param color2: the RGB value of the second color, in the format (R, G, B)
        :param threshold: the value used for judging color close or not, generally 2.3
        :return: if color close return True, else return False
        """
        # normalize RGB color to [0, 1]
        rgb_renormalized_1 = np.array(color1) / 255.0
        rgb_renormalized_2 = np.array(color2) / 255.0
        # transfer RGB color to XYZ color space
        xyz_1 = cs.cspace_convert(rgb_renormalized_1, "sRGB1", "XYZ1")
        xyz_2 = cs.cspace_convert(rgb_renormalized_2, "sRGB1", "XYZ1")
        # transfer XYZ color to CIE Lab color space
        lab1 = cs.cspace_convert(xyz_1, "XYZ1", "CIELab")
        lab2 = cs.cspace_convert(xyz_2, "XYZ1", "CIELab")
        # calculate the Euclidian distance between two LAB colors
        delta_e = np.linalg.norm(lab1 - lab2)

        return delta_e < threshold

    def if_color_close_hsv(
        self, color1, color2, hue_threshold=0.1, brightness_threshold=0.1
    ):
        from colorsys import rgb_to_hsv

        """
        jugde if two colors are close using HSV

        :param color1: the RGB value of the first color, in the format (R, G, B)
        :param color2: the RGB value of the second color, in the format (R, G, B)
        :param hue_threshold: the value used for judging color close or not, generally 0.1
        :param brightness_threshold: the value used for judging color close or not, generally 0.1
        :return: if color close return True, else return False
        """
        # transfer RGB color to HSV color space
        hsv1 = rgb_to_hsv(color1[0] / 255.0, color1[1] / 255.0, color1[2] / 255.0)
        hsv2 = rgb_to_hsv(color2[0] / 255.0, color2[1] / 255.0, color2[2] / 255.0)

        # compare the color phase and brightness
        hue_diff = abs(hsv1[0] - hsv2[0])
        brightness_diff = abs(hsv1[2] - hsv2[2])

        return hue_diff < hue_threshold and brightness_diff < brightness_threshold

    def if_color_close_ciede2000(self, color1, color2, threshold=2.3):
        from colormath.color_objects import sRGBColor, LabColor
        from colormath.color_conversions import convert_color
        from colormath.color_diff import delta_e_cie2000

        """
        judge if two colors are close using CIEDE2000

        :param color1: the RGB value of the first color, in the format (R, G, B)
        :param color2: the RGB value of the second color, in the format (R, G, B)
        :param threshold: the value used for judging color close or not, generally 2.3
        :return: if color close return True, else return False
        """
        # transfer RGB color to CIELab color space
        color1_lab = convert_color(
            sRGBColor(color1[0], color1[1], color1[2], is_upscaled=True), LabColor
        )
        color2_lab = convert_color(
            sRGBColor(color2[0], color2[1], color2[2], is_upscaled=True), LabColor
        )

        # calculate CIEDE2000
        delta_e = delta_e_cie2000(color1_lab, color2_lab)

        return delta_e < threshold
