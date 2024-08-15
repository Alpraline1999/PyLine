import ctypes


class MouseSensitivitySet:
    def __init__(self):
        self.original_sensitivity = self.get_mouse_sensitivity()

    def set_mouse_sensitivity(self, sensitivity):
        SPI_SETMOUSESPEED = 0x0071
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, sensitivity, 0)

    def get_mouse_sensitivity(self):
        SPI_GETMOUSESPEED = 0x0070
        speed = ctypes.c_int()
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0
        )
        return speed.value

    def up_mouse_sensitivity(self):
        sensitivity = self.get_mouse_sensitivity()
        sensitivity = min(19, sensitivity)
        self.set_mouse_sensitivity(sensitivity + 1)

    def down_mouse_sensitivity(self):
        sensitivity = self.get_mouse_sensitivity()
        sensitivity = max(2, sensitivity)
        self.set_mouse_sensitivity(sensitivity - 1)

    def reset_mouse_sensitivity(self):
        self.set_mouse_sensitivity(self.original_sensitivity)
