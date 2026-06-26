import math
import legoeducation as le

class colorSensor(le.ColorSensor):
    def __init__(self):
        super().__init__()

    def _safe(self, val):
        try:
            if math.isnan(val):
                return None
        except TypeError:
            pass
        return val

    # ── Color detection ─────────────────────────────────────────
    def detect_color(self):
        color_number = self.sensor.color
        if isinstance(color_number, float) and math.isnan(color_number):
            return 'No color'
        mapping = {
            0:  'no color',
            1:  'red',
            2:  'yellow',
            3:  'blue',
            4:  'teal',
            5:  'green',
            6:  'purple',
            7:  'white',
            8:  'magenta',
            9:  'orange',
            10: 'azure',
        }
        return mapping.get(int(color_number), 'No color')

    def detect_rgb(self):
        """Returns (red, green, blue) as raw 16-bit integers, or None if not ready."""
        r = self._safe(self.sensor.rawRed)
        g = self._safe(self.sensor.rawGreen)
        b = self._safe(self.sensor.rawBlue)
        if r is None or g is None or b is None:
            return None
        return (int(r), int(g), int(b))

    def detect_hue(self):
        """Returns hue 0–360, or None if not ready."""
        v = self._safe(self.sensor.hue)
        return int(v) if v is not None else None

    def detect_saturation(self):
        """Returns saturation 0–100, or None if not ready."""
        v = self._safe(self.sensor.saturation)
        return int(v) if v is not None else None

    def detect_reflection(self):
        """Returns reflection 0–100, or None if not ready."""
        v = self._safe(self.sensor.reflection)
        return int(v) if v is not None else None