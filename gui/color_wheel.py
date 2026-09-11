import math
import colorsys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk


def hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def hex_to_hsv(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


class ColorWheel(ctk.CTkFrame):
    """HSV kruh (odstín/sytost) + slider jasu.

    on_change se volá průběžně během tažení (živý náhled ve swatch),
    on_commit teprve ~250ms po posledním pohybu - až tehdy má smysl
    přebarvit celou appku (viz SettingsView._on_color_commit).
    """

    def __init__(self, master, initial_hex="#8B5CF6", size=170, wheel_bg="#1a1a22",
                 on_change=None, on_commit=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.radius = size / 2
        self.on_change = on_change
        self.on_commit = on_commit
        self._commit_job = None
        self._hue, self._sat, self._val = hex_to_hsv(initial_hex)

        self._wheel_photo = ImageTk.PhotoImage(self._render_wheel(wheel_bg))
        self.canvas = tk.Canvas(self, width=size, height=size, highlightthickness=0, bg=wheel_bg)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self._wheel_photo)
        self._cursor = self.canvas.create_oval(0, 0, 12, 12, outline="white", width=2)
        self._place_cursor()

        self.canvas.bind("<Button-1>", self._on_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        self.value_slider = ctk.CTkSlider(self, from_=0.25, to=1.0, command=self._on_value_drag)
        self.value_slider.set(self._val)
        self.value_slider.pack(fill="x", pady=(14, 0))

    def _render_wheel(self, bg_hex: str) -> Image.Image:
        size = self.size
        img = Image.new("RGB", (size, size), _hex_to_rgb(bg_hex))
        cx = cy = size / 2
        r = size / 2
        px = img.load()
        for x in range(size):
            for y in range(size):
                dx, dy = x - cx, y - cy
                dist = math.hypot(dx, dy)
                if dist <= r:
                    hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                    sat = min(dist / r, 1.0)
                    rgb = colorsys.hsv_to_rgb(hue, sat, 1.0)
                    px[x, y] = tuple(int(c * 255) for c in rgb)
        return img

    def _place_cursor(self):
        angle_rad = self._hue * 2 * math.pi - math.pi
        dist = self._sat * self.radius
        x = self.radius + math.cos(angle_rad) * dist
        y = self.radius + math.sin(angle_rad) * dist
        self.canvas.coords(self._cursor, x - 6, y - 6, x + 6, y + 6)

    def _on_drag(self, event):
        dx, dy = event.x - self.radius, event.y - self.radius
        dist = min(math.hypot(dx, dy), self.radius)
        self._hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
        self._sat = dist / self.radius if self.radius else 0
        self._place_cursor()
        self._changed()

    def _on_value_drag(self, val):
        self._val = float(val)
        self._changed()

    def _changed(self):
        hexc = self.hex_color
        if self.on_change:
            self.on_change(hexc)
        if self.on_commit:
            if self._commit_job:
                self.after_cancel(self._commit_job)
            self._commit_job = self.after(250, lambda: self.on_commit(hexc))

    @property
    def hex_color(self) -> str:
        return hsv_to_hex(self._hue, self._sat, self._val)
