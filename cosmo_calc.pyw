"""Cosmo Calc — калькулятор с темами «Космос» и «Китти».

Запуск: двойной клик по файлу или команда `py cosmo_calc.pyw`.
"""
import ast
import ctypes
import json
import math
import operator
import os
import random
import re
import sys
import tkinter as tk

# ---------- Размеры и файлы ----------
W, H = 400, 660
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Внутри собранного .exe файлы лежат во временной папке sys._MEIPASS
ICON_PATH = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "icon.ico")
SETTINGS_PATH = os.path.join(os.environ.get("APPDATA", APP_DIR), "CosmoCalc", "settings.json")

# ---------- Темы ----------
# Стили кнопок: (заливка, рамка, текст, заливка при наведении, рамка при наведении)
THEMES = {
    "space": {
        "label": "✦ космос",
        "bg": "#05030f",
        "buttons": {
            "num":  ("#12163a", "#3a4a9a", "#dfe6ff", "#1c2356", "#7aa2ff"),
            "op":   ("#1d0f3d", "#9b5cff", "#d6b8ff", "#2a1658", "#c79bff"),
            "func": ("#0d2a33", "#2fd3c9", "#9ff5ee", "#123b47", "#7ffff4"),
            "eq":   ("#ff6b35", "#ffc46b", "#1a0b00", "#ff8a4f", "#ffe2a8"),
        },
        "panel_glow": ["#141a40", "#23306e", "#3f5bd6"],
        "panel_fill": "#080b22",
        "panel_outline": "#5f7dff",
        "title": "✦ COSMO CALC",
        "title_color": "#5f6aa8",
        "accent": "#8fa6ff",
        "small_color": "#8a93c9",
        "big_color": "#eaf0ff",
        "font": "Segoe UI",
        "big_font": "Segoe UI Semilight",
    },
    "kitty": {
        "label": "♥ китти",
        "bg": "#ffe4ef",
        "buttons": {
            "num":  ("#ffffff", "#ffb6cf", "#7a3b55", "#fff0f6", "#ff7aa8"),
            "op":   ("#ffd1e3", "#ff7aa8", "#c2185b", "#ffbcd6", "#ff4f8f"),
            "func": ("#fff6d6", "#ffcf5c", "#a86b00", "#ffefb0", "#ffb300"),
            "eq":   ("#ff4f8f", "#ff9cc2", "#ffffff", "#ff6fa3", "#ff2d78"),
        },
        "panel_glow": ["#ffd6e6", "#ffc2da", "#ff9cc2"],
        "panel_fill": "#ffffff",
        "panel_outline": "#ff9cc2",
        "title": "♥ KITTY CALC",
        "title_color": "#ff7aa8",
        "accent": "#ff4f8f",
        "small_color": "#c57a98",
        "big_color": "#6b2a45",
        "font": "Comic Sans MS",
        "big_font": "Comic Sans MS",
    },
}
THEME_ORDER = list(THEMES)

# Раскладка кнопок: (надпись, стиль)
LAYOUT = [
    [("C", "func"), ("⌫", "func"), ("%", "func"), ("÷", "op")],
    [("7", "num"), ("8", "num"), ("9", "num"), ("×", "op")],
    [("4", "num"), ("5", "num"), ("6", "num"), ("−", "op")],
    [("1", "num"), ("2", "num"), ("3", "num"), ("+", "op")],
    [("±", "func"), ("0", "num"), (".", "num"), ("=", "eq")],
]

# Красивый символ на кнопке -> символ для вычислений
OP_SYMBOLS = {"+": "+", "−": "-", "×": "*", "÷": "/"}


# ---------- Настройки (тема сохраняется между запусками) ----------
def load_settings():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # не смогли сохранить — не страшно, калькулятор работает дальше


# ---------- Безопасное вычисление выражения ----------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv}


def safe_eval(expr):
    """Считает выражение вроде '2+3*4', разрешая только числа и + - * /."""
    def ev(node):
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = ev(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("недопустимое выражение")
    return ev(ast.parse(expr, mode="eval").body)


def fmt(value):
    """Превращает число в аккуратную строку: 4.0 -> '4', 0.1+0.2 -> '0.3'."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise OverflowError
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.12g}"
    if abs(value) >= 10**15:
        return f"{float(value):.12g}"
    return str(value)


def pretty(expr):
    """Внутренняя запись -> то, что видит пользователь."""
    return expr.replace("*", "×").replace("/", "÷").replace("-", "−")


# ---------- Помощники для рисования ----------
def blend(c1, c2, t):
    """Смешивает два цвета: t=0 -> c1, t=1 -> c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def rounded_rect(x1, y1, x2, y2, r):
    """Точки для прямоугольника со скруглёнными углами (create_polygon smooth=True)."""
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def heart(cx, cy, size):
    """Точки сердечка шириной примерно 2*size."""
    pts = []
    for i in range(24):
        t = math.tau * i / 24
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts += [cx + x * size / 16, cy + y * size / 16]
    return pts


class CosmoCalc:
    def __init__(self, root):
        self.root = root
        self.c = tk.Canvas(root, width=W, height=H, highlightthickness=0)
        self.c.pack()

        self.settings = load_settings()
        self.theme_key = self.settings.get("theme")
        if self.theme_key not in THEMES:
            self.theme_key = THEME_ORDER[0]

        self.expr = ""            # текущее выражение, например "12+3*4"
        self.history = ""         # прошлое вычисление, например "12+3 ="
        self.just_evaluated = False
        self.t = 0.0

        self.build()
        root.bind("<Key>", self.on_key)
        self.animate()
        self.root.after(1500, self.special_loop)

    # ---------- Темы ----------
    def build(self):
        """Полностью перерисовывает окно в текущей теме."""
        self.th = THEMES[self.theme_key]
        self.c.delete("all")
        self.c.config(bg=self.th["bg"], cursor="")
        self.root.configure(bg=self.th["bg"])
        self.buttons = {}
        self.hovered = None
        self.particles = []

        getattr(self, f"draw_bg_{self.theme_key}")()
        # Невидимая отметка: всё, что ниже неё, — фон (звёзды, кометы, сердечки)
        self.layer_mark = self.c.create_line(0, 0, 0, 0, state="hidden")
        getattr(self, f"draw_deco_{self.theme_key}")()
        self.draw_panel()
        self.draw_buttons()
        self.update_display()

    def next_theme(self):
        i = THEME_ORDER.index(self.theme_key)
        self.theme_key = THEME_ORDER[(i + 1) % len(THEME_ORDER)]
        self.settings["theme"] = self.theme_key
        save_settings(self.settings)
        self.build()

    # ---------- Тема «Космос» ----------
    def draw_bg_space(self):
        bg = self.th["bg"]
        # Туманности: много вложенных овалов с плавным переходом цвета
        for cx, cy, rx, ry, color in [(60, 470, 230, 170, "#3b1466"),
                                      (360, 330, 200, 150, "#0f3a55"),
                                      (200, 640, 220, 90, "#4a1640")]:
            steps = 28
            for i in range(steps):
                k = 1 - i / steps
                col = blend(bg, color, (i / steps) ** 1.6 * 0.55)
                self.c.create_oval(cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k,
                                   fill=col, outline="")
        # Звёзды
        palette = ["#ffffff", "#cfe0ff", "#ffe9c4", "#d9c8ff"]
        for _ in range(170):
            size = random.choice([1, 1, 1, 1.5, 2, 2.5])
            x, y = random.uniform(0, W), random.uniform(0, H)
            self.particles.append({
                "id": self.c.create_oval(x, y, x + size, y + size, outline=""),
                "x": x, "y": y, "size": size,
                "color": random.choice(palette),
                "speed": 0.08 + size * 0.12,          # крупные звёзды «ближе» и летят быстрее
                "phase": random.uniform(0, math.tau),
                "twinkle": random.uniform(1.0, 3.5),
            })

    def draw_deco_space(self):
        cx, cy, r = 352, 22, 62
        # Задняя половина кольца (за планетой)
        self.c.create_arc(cx - 110, cy - 22, cx + 110, cy + 22, start=0, extent=180,
                          style="arc", outline="#b59cff", width=3)
        # Планета с объёмом: круги, сдвигающиеся к освещённой стороне
        steps = 22
        for i in range(steps):
            t = i / steps
            rr = r * (1 - t * 0.8)
            ox = oy = -t * r * 0.32
            self.c.create_oval(cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr,
                               fill=blend("#1e0b3a", "#c77dff", t ** 1.3), outline="")
        # Передняя половина кольца
        self.c.create_arc(cx - 110, cy - 22, cx + 110, cy + 22, start=180, extent=180,
                          style="arc", outline="#e0d2ff", width=3)
        # Маленькая луна
        self.c.create_oval(30, 28, 46, 44, fill="#8d93ad", outline="")
        self.c.create_oval(30, 28, 41, 39, fill="#c7cbe0", outline="")

    def step_space(self):
        """Звёзды медленно плывут и мерцают."""
        bg = self.th["bg"]
        for s in self.particles:
            s["y"] += s["speed"]
            s["x"] -= s["speed"] * 0.25
            if s["y"] > H or s["x"] < -3:
                s["y"], s["x"] = -3, random.uniform(0, W + 60)
            glow = 0.55 + 0.45 * math.sin(s["phase"] + self.t * s["twinkle"])
            self.c.coords(s["id"], s["x"], s["y"], s["x"] + s["size"], s["y"] + s["size"])
            self.c.itemconfig(s["id"], fill=blend(bg, s["color"], glow))

    def special_space(self):
        """Падающая звезда: светлая голова и тускнеющий хвост."""
        x, y = random.uniform(W * 0.3, W + 40), random.uniform(-20, H * 0.45)
        ux, uy = -0.87, 0.5                     # направление полёта
        parts = []
        for length, color, width in [(110, "#2c3160", 1), (60, "#7d86c4", 1.5), (22, "#ffffff", 2)]:
            item = self.c.create_line(x, y, x - ux * length, y - uy * length,
                                      fill=color, width=width, capstyle="round")
            self.c.tag_lower(item, self.layer_mark)   # комета пролетает за кнопками
            parts.append(item)

        def fly(frame=0):
            if frame > 40 or not self.c.type(parts[0]):   # долетела или тему сменили
                for p in parts:
                    self.c.delete(p)
                return
            for p in parts:
                self.c.move(p, ux * 12, uy * 12)
            self.root.after(30, fly, frame + 1)

        fly()

    # ---------- Тема «Китти» ----------
    def draw_bg_kitty(self):
        # Обои в горошек
        for row, y in enumerate(range(10, H + 20, 40)):
            for x in range(10 + (row % 2) * 22, W + 20, 44):
                self.c.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#ffd0e2", outline="")
        # Сердечки, которые всплывают вверх
        colors = ["#ff8fb8", "#ffb3cf", "#ff6fa3", "#ffffff", "#ffc4dc"]
        for _ in range(24):
            x, y, size = random.uniform(0, W), random.uniform(0, H), random.uniform(5, 12)
            self.particles.append({
                "id": self.c.create_polygon(heart(x, y, size), smooth=True, outline="",
                                            fill=random.choice(colors)),
                "x": x, "y": y,
                "speed": 0.25 + size * 0.05,
                "phase": random.uniform(0, math.tau),
            })

    def draw_deco_kitty(self):
        ink = "#3a2a30"
        # Цветочек слева
        fx, fy = 40, 38
        for i in range(5):
            a = math.tau * i / 5 - math.pi / 2
            px, py = fx + 9 * math.cos(a), fy + 9 * math.sin(a)
            self.c.create_oval(px - 7, py - 7, px + 7, py + 7, fill="#ffffff", outline="#ffb6cf")
        self.c.create_oval(fx - 5, fy - 5, fx + 5, fy + 5, fill="#ffcc33", outline="")

        # Кошечка выглядывает из-за экрана
        cx, cy = 338, 40
        for side in (-1, 1):
            self.c.create_polygon(cx + side * 38, cy - 6, cx + side * 30, cy - 40, cx + side * 8, cy - 24,
                                  fill="#ffffff", outline=ink, width=2)
        self.c.create_oval(cx - 46, cy - 26, cx + 46, cy + 32, fill="#ffffff", outline=ink, width=2)
        self.c.create_oval(cx - 20, cy - 2, cx - 13, cy + 8, fill=ink, outline="")
        self.c.create_oval(cx + 13, cy - 2, cx + 20, cy + 8, fill=ink, outline="")
        self.c.create_oval(cx - 5, cy + 8, cx + 5, cy + 14, fill="#ffcc33", outline=ink)
        for side in (-1, 1):
            for k in range(3):
                self.c.create_line(cx + side * 30, cy + 4 + k * 6, cx + side * 58, cy + k * 10,
                                   fill=ink, width=2, capstyle="round")
        # Бантик на ушке
        bx, by = cx + 28, cy - 26
        for side in (-1, 1):
            self.c.create_polygon(bx, by, bx + side * 22, by - 14, bx + side * 24, by + 12,
                                  smooth=True, fill="#ff3b7f", outline=ink, width=2)
        self.c.create_oval(bx - 7, by - 7, bx + 7, by + 7, fill="#ff3b7f", outline=ink, width=2)

    def step_kitty(self):
        """Сердечки всплывают, слегка покачиваясь."""
        for p in self.particles:
            dx = math.sin(self.t * 1.5 + p["phase"]) * 0.4
            dy = -p["speed"]
            if p["y"] < -25:                       # улетело наверх — возвращаем вниз
                nx = random.uniform(0, W)
                dx, dy = nx - p["x"], H + 25 - p["y"]
            self.c.move(p["id"], dx, dy)
            p["x"] += dx
            p["y"] += dy

    def special_kitty(self):
        """Искорка: вспыхивает и тает."""
        x, y = random.uniform(20, W - 20), random.uniform(20, H - 20)
        color = random.choice(["#ff4f8f", "#ffb300", "#ff7aa8"])
        item = self.c.create_text(x, y, text="✦", fill=color, font=("Segoe UI", 6))
        self.c.tag_lower(item, self.layer_mark)

        def sparkle(frame=0):
            if frame > 24 or not self.c.type(item):
                self.c.delete(item)
                return
            grow = frame if frame < 12 else 24 - frame
            fade = max(0, frame - 12) / 12
            self.c.itemconfig(item, font=("Segoe UI", 6 + grow * 2),
                              fill=blend(color, self.th["bg"], fade))
            self.root.after(40, sparkle, frame + 1)

        sparkle()

    # ---------- Экран ----------
    def draw_panel(self):
        th = self.th
        x1, y1, x2, y2 = 24, 70, W - 24, 214
        for i, col in enumerate(th["panel_glow"]):
            pad = 6 - i * 3
            self.c.create_polygon(rounded_rect(x1 - pad, y1 - pad, x2 + pad, y2 + pad, 24),
                                  smooth=True, fill="", outline=col, width=2)
        self.c.create_polygon(rounded_rect(x1, y1, x2, y2, 22), smooth=True,
                              fill=th["panel_fill"], outline=th["panel_outline"], width=1)
        self.c.create_text(x1 + 18, y1 + 19, text=th["title"], anchor="w",
                           fill=th["title_color"], font=(th["font"], 9, "bold"))
        self.small_text = self.c.create_text(x2 - 20, y1 + 54, anchor="e",
                                             fill=th["small_color"], font=("Consolas", 14))
        self.big_text = self.c.create_text(x2 - 20, y1 + 106, anchor="e", fill=th["big_color"])
        self.draw_theme_switch(x2 - 16, y1 + 19)

    def draw_theme_switch(self, right, cy):
        """Кнопка-«таблетка» в углу экрана: показывает тему и переключает её."""
        th, tag = self.th, "theme_switch"
        text = self.c.create_text(right - 12, cy, anchor="e", text=th["label"] + "  ▸",
                                  fill=th["accent"], font=(th["font"], 9, "bold"), tags=tag)
        x1, _, _, _ = self.c.bbox(text)
        pill = self.c.create_polygon(rounded_rect(x1 - 12, cy - 11, right, cy + 11, 11),
                                     smooth=True, fill=th["panel_fill"], outline=th["accent"],
                                     width=1, tags=tag)
        self.c.tag_lower(pill, text)
        hover_fill = blend(th["panel_fill"], th["accent"], 0.18)
        self.c.tag_bind(tag, "<Enter>", lambda e: (self.c.itemconfig(pill, fill=hover_fill),
                                                    self.c.config(cursor="hand2")))
        self.c.tag_bind(tag, "<Leave>", lambda e: (self.c.itemconfig(pill, fill=th["panel_fill"]),
                                                    self.c.config(cursor="")))
        self.c.tag_bind(tag, "<Button-1>", lambda e: self.next_theme())

    def update_display(self):
        big = pretty(self.expr) or "0"
        size = 40 if len(big) <= 11 else max(16, int(40 * 11 / len(big)))
        self.c.itemconfig(self.big_text, text=big, font=(self.th["big_font"], size))

        small = self.history if self.just_evaluated else self.preview()
        self.c.itemconfig(self.small_text, text=small)

    def preview(self):
        """Подсказка с результатом прямо во время ввода."""
        e = self.expr.rstrip("+-*/")
        if not re.search(r"\d[+\-*/]", e):
            return ""
        try:
            return "= " + fmt(safe_eval(e))
        except Exception:
            return ""

    # ---------- Кнопки ----------
    def draw_buttons(self):
        bw, bh, gap = 76, 70, 12
        left = (W - (4 * bw + 3 * gap)) / 2
        top = 240
        for row_i, row in enumerate(LAYOUT):
            for col_i, (label, style) in enumerate(row):
                x1 = left + col_i * (bw + gap)
                y1 = top + row_i * (bh + gap)
                self.make_button(label, style, x1, y1, x1 + bw, y1 + bh)

    def make_button(self, label, style, x1, y1, x2, y2):
        fill, outline, text_col, _, hover_outline = self.th["buttons"][style]
        tag = f"btn_{len(self.buttons)}"
        glow = self.c.create_polygon(rounded_rect(x1 - 4, y1 - 4, x2 + 4, y2 + 4, 22),
                                     smooth=True, fill="", width=3, state="hidden",
                                     outline=blend(self.th["bg"], hover_outline, 0.45), tags=tag)
        body = self.c.create_polygon(rounded_rect(x1, y1, x2, y2, 20), smooth=True,
                                     fill=fill, outline=outline, width=2, tags=tag)
        self.c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=text_col,
                           font=(self.th["font"], 20, "bold" if style != "num" else "normal"),
                           tags=tag)
        self.buttons[label] = {"glow": glow, "body": body, "style": style}
        self.c.tag_bind(tag, "<Enter>", lambda e: self.set_hover(label))
        self.c.tag_bind(tag, "<Leave>", lambda e: self.set_hover(None))
        self.c.tag_bind(tag, "<Button-1>", lambda e: self.press(label))
        self.c.tag_bind(tag, "<Enter>", lambda e: self.c.config(cursor="hand2"), add="+")
        self.c.tag_bind(tag, "<Leave>", lambda e: self.c.config(cursor=""), add="+")

    def paint_button(self, label, state):
        b = self.buttons.get(label)
        if not b:
            return
        fill, outline, _, h_fill, h_outline = self.th["buttons"][b["style"]]
        if state == "normal":
            self.c.itemconfig(b["body"], fill=fill, outline=outline)
            self.c.itemconfig(b["glow"], state="hidden")
        elif state == "hover":
            self.c.itemconfig(b["body"], fill=h_fill, outline=h_outline)
            self.c.itemconfig(b["glow"], state="normal")
        elif state == "pressed":
            self.c.itemconfig(b["body"], fill=blend(h_fill, h_outline, 0.5), outline="#ffffff")
            self.c.itemconfig(b["glow"], state="normal")

    def set_hover(self, label):
        if self.hovered:
            self.paint_button(self.hovered, "normal")
        self.hovered = label
        if label:
            self.paint_button(label, "hover")

    def press(self, label):
        """Нажатие кнопки: вспышка + действие."""
        self.paint_button(label, "pressed")
        self.root.after(110, lambda: self.paint_button(
            label, "hover" if self.hovered == label else "normal"))
        self.handle(label)
        self.update_display()

    # ---------- Логика калькулятора ----------
    def handle(self, label):
        if label.isdigit():
            self.input_digit(label)
        elif label == ".":
            self.input_dot()
        elif label in OP_SYMBOLS:
            self.input_operator(OP_SYMBOLS[label])
        elif label == "=":
            self.evaluate()
            return
        elif label == "C":
            self.expr = ""
        elif label == "⌫":
            self.expr = "" if self.just_evaluated else self.expr[:-1]
        elif label == "%":
            self.replace_last_number(lambda n: fmt(float(n) / 100))
        elif label == "±":
            self.toggle_sign()
        self.just_evaluated = False

    def last_number(self):
        return re.search(r"(\d+\.?\d*|\.\d+)$", self.expr)

    def input_digit(self, d):
        if self.just_evaluated:
            self.expr = ""
        if len(self.expr) >= 40:
            return
        m = self.last_number()
        if m and m.group() == "0":          # не даём писать "007"
            self.expr = self.expr[:-1]
        self.expr += d

    def input_dot(self):
        if self.just_evaluated:
            self.expr = ""
        m = self.last_number()
        if m and "." in m.group():
            return
        self.expr += "." if m else "0."

    def input_operator(self, op):
        if not self.expr or self.expr == "-":
            self.expr = "-" if op == "-" else self.expr
            return
        if self.expr[-1] in "+-*/":
            if op == "-" and self.expr[-1] in "*/":
                self.expr += op               # разрешаем 5 × −3
                return
            self.expr = self.expr.rstrip("+-*/")
        self.expr += op

    def replace_last_number(self, func):
        m = self.last_number()
        if m:
            self.expr = self.expr[:m.start()] + func(m.group())

    def toggle_sign(self):
        m = self.last_number()
        if not m:
            return
        s, i = self.expr, m.start()
        if i >= 1 and s[i - 1] == "-" and (i == 1 or s[i - 2] in "+-*/"):
            self.expr = s[:i - 1] + s[i:]            # убираем унарный минус
        elif i >= 1 and s[i - 1] in "+-":
            self.expr = s[:i - 1] + ("+" if s[i - 1] == "-" else "-") + s[i:]
        else:
            self.expr = s[:i] + "-" + s[i:]

    def evaluate(self):
        e = self.expr.rstrip("+-*/")
        if not e or e == "-":
            return
        try:
            result = fmt(safe_eval(e))
            self.history = pretty(e) + " ="
            self.expr = result
        except ZeroDivisionError:
            self.history = "∞ чёрная дыра! на ноль делить нельзя"
            self.expr = ""
        except Exception:
            self.history = "ошибка в выражении"
            self.expr = ""
        self.just_evaluated = True

    # ---------- Клавиатура ----------
    def on_key(self, event):
        key, sym = event.char, event.keysym
        label = None
        if key.isdigit():
            label = key
        elif key in "+-*/":
            label = {"+": "+", "-": "−", "*": "×", "/": "÷"}[key]
        elif key in ".,":
            label = "."
        elif key == "%":
            label = "%"
        elif key == "=" or sym in ("Return", "KP_Enter"):
            label = "="
        elif sym == "BackSpace":
            label = "⌫"
        elif sym in ("Escape", "Delete"):
            label = "C"
        elif sym == "F2":
            self.next_theme()
        if label:
            self.press(label)

    # ---------- Анимация ----------
    def animate(self):
        self.t += 0.033
        getattr(self, f"step_{self.theme_key}")()
        self.root.after(33, self.animate)

    def special_loop(self):
        """Время от времени — особый эффект темы (комета или искорка)."""
        getattr(self, f"special_{self.theme_key}")()
        delay = (2500, 7000) if self.theme_key == "space" else (600, 1600)
        self.root.after(random.randint(*delay), self.special_loop)


def main():
    # Своё «имя» приложения, чтобы Windows показывала нашу иконку в панели задач, а не иконку Python
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CosmoCalc.Calculator")
    except (AttributeError, OSError):
        pass

    root = tk.Tk()
    root.title("Cosmo Calc")
    root.resizable(False, False)
    if os.path.exists(ICON_PATH):
        root.iconbitmap(default=ICON_PATH)
    x = (root.winfo_screenwidth() - W) // 2
    y = max(0, (root.winfo_screenheight() - H) // 2 - 30)
    root.geometry(f"{W}x{H}+{x}+{y}")
    CosmoCalc(root)
    root.mainloop()


if __name__ == "__main__":
    main()
