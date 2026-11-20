

import math
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import messagebox, ttk


# ABSTRACTION: the abstract base class
class Shape(ABC):
    """Abstract base class. Every shape must implement these methods."""

    # Names of the values the user must type in (subclasses override).
    fields: tuple[str, ...] = ()

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    @abstractmethod
    def area(self) -> float:
        """Return the area of the shape."""

    @abstractmethod
    def perimeter(self) -> float:
        """Return the perimeter (circumference) of the shape."""

    @abstractmethod
    def draw(self, canvas: tk.Canvas, cx: float, cy: float, scale: float) -> None:
        """Draw the shape centered at (cx, cy) on the canvas."""

    @abstractmethod
    def size(self) -> float:
        """Largest dimension, used to scale the drawing to fit the canvas."""

    # A normal (concrete) method that all subclasses inherit for free.
    def describe(self) -> str:
        return (f"{self.name}: area = {self.area():.2f}, "
                f"perimeter = {self.perimeter():.2f}")

    def __str__(self) -> str:
        return self.describe()



# INHERITANCE: concrete subclasses
class Circle(Shape):
    fields = ("Radius",)

    def __init__(self, radius: float):
        super().__init__("Circle", "#4e79a7")
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius

    def size(self) -> float:
        return 2 * self.radius

    def draw(self, canvas, cx, cy, scale):
        r = self.radius * scale
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           fill=self.color, outline="black", width=2)


class Rectangle(Shape):
    fields = ("Width", "Height")

    def __init__(self, width: float, height: float):
        super().__init__("Rectangle", "#f28e2b")
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

    def size(self) -> float:
        return max(self.width, self.height)

    def draw(self, canvas, cx, cy, scale):
        w, h = self.width * scale / 2, self.height * scale / 2
        canvas.create_rectangle(cx - w, cy - h, cx + w, cy + h,
                                fill=self.color, outline="black", width=2)


class Square(Rectangle):
    """Multi-level inheritance: Shape -> Rectangle -> Square.
    Square reuses Rectangle's area, perimeter and draw methods."""
    fields = ("Side",)

    def __init__(self, side: float):
        super().__init__(side, side)
        self.name = "Square"
        self.color = "#59a14f"


class Triangle(Shape):
    fields = ("Side A", "Side B", "Side C")

    def __init__(self, a: float, b: float, c: float):
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError("Those sides can't form a triangle "
                             "(each side must be shorter than the other two combined).")
        super().__init__("Triangle", "#e15759")
        self.a, self.b, self.c = a, b, c

    def area(self) -> float:
        s = self.perimeter() / 2  # Heron's formula
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self) -> float:
        return self.a + self.b + self.c

    def size(self) -> float:
        return max(self.a, self.b, self.c)

    def draw(self, canvas, cx, cy, scale):
        # Place side c on the bottom, then find the top point.
        a, b, c = self.a, self.b, self.c
        x = (b ** 2 + c ** 2 - a ** 2) / (2 * c)
        y = math.sqrt(max(b ** 2 - x ** 2, 0))
        pts = [(0, 0), (c, 0), (x, y)]
        # Center the triangle on (cx, cy).
        mid_x = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        mid_y = y / 2
        coords = []
        for px, py in pts:
            coords += [cx + (px - mid_x) * scale, cy - (py - mid_y) * scale]
        canvas.create_polygon(coords, fill=self.color, outline="black", width=2)


# Map dropdown names to classes. Adding a new shape only means writing a
# new subclass and adding one line here - the GUI code doesn't change.
SHAPES: dict[str, type[Shape]] = {
    "Circle": Circle,
    "Rectangle": Rectangle,
    "Square": Square,
    "Triangle": Triangle,
}


# GUI

class ShapeApp(tk.Tk):
    CANVAS_SIZE = 320

    def __init__(self):
        super().__init__()
        self.title("Shape Calculator - OOP Demo")
        self.resizable(False, False)
        self.entries: list[ttk.Entry] = []
        self.shapes: list[Shape] = []  # every shape the user has made

        self._build_controls()
        self._build_output()
        self._on_shape_change()

    # layout 
    def _build_controls(self):
        left = ttk.Frame(self, padding=12)
        left.grid(row=0, column=0, sticky="n")

        ttk.Label(left, text="Choose a shape:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.shape_var = tk.StringVar(value="Circle")
        combo = ttk.Combobox(left, textvariable=self.shape_var,
                             values=list(SHAPES), state="readonly", width=18)
        combo.pack(anchor="w", pady=(2, 10))
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_shape_change())

        self.fields_frame = ttk.Frame(left)
        self.fields_frame.pack(anchor="w", fill="x")

        btns = ttk.Frame(left)
        btns.pack(anchor="w", pady=10)
        ttk.Button(btns, text="Calculate", command=self.calculate).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear).pack(side="left", padx=6)

        self.result_var = tk.StringVar(value="Enter dimensions and press Calculate.")
        ttk.Label(left, textvariable=self.result_var, wraplength=220,
                  justify="left").pack(anchor="w", pady=(0, 10))

        ttk.Label(left, text="History:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.history = tk.Listbox(left, width=40, height=8)
        self.history.pack(anchor="w")
        ttk.Label(left, text="Total area of all shapes:").pack(anchor="w", pady=(6, 0))
        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(left, textvariable=self.total_var).pack(anchor="w")

    def _build_output(self):
        self.canvas = tk.Canvas(self, width=self.CANVAS_SIZE, height=self.CANVAS_SIZE,
                                bg="white", highlightthickness=1,
                                highlightbackground="#999")
        self.canvas.grid(row=0, column=1, padx=12, pady=12)

    # behaviour 
    def _on_shape_change(self):
        """Rebuild the input fields for the chosen shape class."""
        for child in self.fields_frame.winfo_children():
            child.destroy()
        self.entries.clear()

        shape_class = SHAPES[self.shape_var.get()]
        for row, label in enumerate(shape_class.fields):
            ttk.Label(self.fields_frame, text=f"{label}:").grid(row=row, column=0,
                                                                 sticky="w", pady=2)
            entry = ttk.Entry(self.fields_frame, width=12)
            entry.grid(row=row, column=1, padx=6, pady=2)
            entry.bind("<Return>", lambda e: self.calculate())
            self.entries.append(entry)
        if self.entries:
            self.entries[0].focus_set()

    def calculate(self):
        try:
            values = [float(e.get()) for e in self.entries]
            if any(v <= 0 for v in values):
                raise ValueError("All dimensions must be positive numbers.")
            shape = SHAPES[self.shape_var.get()](*values)
        except ValueError as err:
            msg = str(err)
            if "could not convert" in msg:
                msg = "Please enter numbers in every field."
            messagebox.showerror("Invalid input", msg)
            return

        self.shapes.append(shape)
        self.show(shape)

    def show(self, shape: Shape):
        """POLYMORPHISM: works for any Shape subclass without checking its type."""
        self.result_var.set(f"{shape.name}\n"
                            f"Area: {shape.area():.2f}\n"
                            f"Perimeter: {shape.perimeter():.2f}")
        self.history.insert(tk.END, shape.describe())
        self.total_var.set(f"{sum(s.area() for s in self.shapes):.2f}")

        self.canvas.delete("all")
        margin = 40
        scale = (self.CANVAS_SIZE - 2 * margin) / shape.size()
        center = self.CANVAS_SIZE / 2
        shape.draw(self.canvas, center, center, scale)
        self.canvas.create_text(center, 16, text=shape.name, font=("Arial", 12, "bold"))

    def clear(self):
        for e in self.entries:
            e.delete(0, tk.END)
        self.shapes.clear()
        self.history.delete(0, tk.END)
        self.canvas.delete("all")
        self.total_var.set("0.00")
        self.result_var.set("Enter dimensions and press Calculate.")


if __name__ == "__main__":
    ShapeApp().mainloop()
