import tkinter as tk
import math
import re

# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#111114"
DISP_BG   = "#0d0d10"
SEP       = "#1e1e24"

C_NUM     = ("#1c1c21", "#26262d", "#2e2e38", "#eeeef5")
C_OP      = ("#171720", "#20202c", "#2a2a38", "#60a5fa")
C_FN      = ("#141418", "#1e1e24", "#28282f", "#7c8db0")
C_EQ      = ("#1d4ed8", "#2563eb", "#1e40af", "#ffffff")
C_CLR     = ("#1a1014", "#241418", "#2e1a1a", "#ef4444")
C_MODE    = ("#141418", "#1e1e24", "#28282f", "#44444e")

FONT_MAIN = ("Consolas", 38, "bold")
FONT_EXPR = ("Consolas", 11)
FONT_INFO = ("Consolas", 10)
FONT_NUM  = ("Consolas", 14, "bold")
FONT_OP   = ("Consolas", 15, "bold")
FONT_FN   = ("Consolas", 11, "bold")
FONT_EQ   = ("Consolas", 15, "bold")


class Btn(tk.Label):
    def __init__(self, parent, text, colors, font, cmd, **kw):
        bg, hov, press, fg = colors
        super().__init__(parent, text=text, font=font,
                         bg=bg, fg=fg, cursor="hand2",
                         padx=0, pady=0, **kw)
        self._bg = bg; self._hov = hov; self._press = press
        self.bind("<Enter>",           lambda e: self.configure(bg=hov))
        self.bind("<Leave>",           lambda e: self.configure(bg=bg))
        self.bind("<ButtonPress-1>",   lambda e: self.configure(bg=press))
        self.bind("<ButtonRelease-1>", lambda e: (self.configure(bg=hov), cmd()))


class EngCalc(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ENG CALC")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.expr        = ""
        self.current     = "0"
        self.just_evaled = False
        self.error       = False
        self.memory      = 0.0
        self.deg_mode    = True
        self.inv_mode    = False

        self._build()
        self._bind_keys()
        self._update()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Display ──────────────────────────────────────────────────────────
        disp = tk.Frame(self, bg=DISP_BG, padx=20, pady=14)
        disp.pack(fill="x")

        info = tk.Frame(disp, bg=DISP_BG)
        info.pack(fill="x")
        self.mem_var  = tk.StringVar(value="")
        self.inv_var  = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="DEG")
        tk.Label(info, textvariable=self.mem_var,  font=FONT_INFO,
                 bg=DISP_BG, fg="#34d399", anchor="w").pack(side="left")
        tk.Label(info, textvariable=self.inv_var,  font=FONT_INFO,
                 bg=DISP_BG, fg="#60a5fa", anchor="w").pack(side="left", padx=6)
        tk.Label(info, textvariable=self.mode_var, font=FONT_INFO,
                 bg=DISP_BG, fg="#44444e", anchor="e").pack(side="right")

        self.expr_var = tk.StringVar(value="")
        tk.Label(disp, textvariable=self.expr_var, font=FONT_EXPR,
                 bg=DISP_BG, fg="#44444e", anchor="e",
                 justify="right", width=26).pack(fill="x", pady=(5, 0))

        self.main_var = tk.StringVar(value="0")
        tk.Label(disp, textvariable=self.main_var, font=FONT_MAIN,
                 bg=DISP_BG, fg="#eeeef5", anchor="e",
                 justify="right", width=26).pack(fill="x")

        tk.Frame(self, bg=SEP, height=1).pack(fill="x")

        # ── Button grid ───────────────────────────────────────────────────────
        g = tk.Frame(self, bg=BG, padx=10, pady=10)
        g.pack(fill="both")

        # uniform row/col sizing
        for i in range(8):
            g.rowconfigure(i, minsize=50, weight=1)
        for j in range(6):
            g.columnconfigure(j, minsize=64, weight=1)

        P = dict(padx=3, pady=3, sticky="nsew")

        def nb(text, cmd):   return Btn(g, text, C_NUM,  FONT_NUM, cmd)
        def ob(text, cmd):   return Btn(g, text, C_OP,   FONT_OP,  cmd)
        def fb(text, cmd):   return Btn(g, text, C_FN,   FONT_FN,  cmd)
        def eb(text, cmd):   return Btn(g, text, C_EQ,   FONT_EQ,  cmd)
        def cb(text, cmd):   return Btn(g, text, C_CLR,  FONT_FN,  cmd)
        def mb(text, cmd):   return Btn(g, text, C_MODE, FONT_FN,  cmd)

        # Row 0 — memory & mode
        fb("MC",  self._mc)       .grid(row=0, column=0, **P)
        fb("MR",  self._mr)       .grid(row=0, column=1, **P)
        fb("M+",  self._mplus)    .grid(row=0, column=2, **P)
        fb("M−",  self._mminus)   .grid(row=0, column=3, **P)
        mb("DEG", self._toggle_deg).grid(row=0, column=4, **P)
        self._inv_btn = mb("INV", self._toggle_inv)
        self._inv_btn.grid(row=0, column=5, **P)

        # Row 1 — trig / log
        fb("sin", lambda: self._fn("sin")) .grid(row=1, column=0, **P)
        fb("cos", lambda: self._fn("cos")) .grid(row=1, column=1, **P)
        fb("tan", lambda: self._fn("tan")) .grid(row=1, column=2, **P)
        fb("ln",  lambda: self._fn("ln"))  .grid(row=1, column=3, **P)
        fb("log", lambda: self._fn("log")) .grid(row=1, column=4, **P)
        fb("√",   lambda: self._fn("sqrt")).grid(row=1, column=5, **P)

        # Row 2 — power / const / paren
        fb("x²",  lambda: self._fn("sq"))          .grid(row=2, column=0, **P)
        fb("xʸ",  lambda: self._append_op("**"))   .grid(row=2, column=1, **P)
        fb("π",   lambda: self._constant(math.pi)) .grid(row=2, column=2, **P)
        fb("e",   lambda: self._constant(math.e))  .grid(row=2, column=3, **P)
        fb("(",   lambda: self._paren("("))         .grid(row=2, column=4, **P)
        fb(")",   lambda: self._paren(")"))         .grid(row=2, column=5, **P)

        # Row 3
        cb("C",   self._clear)              .grid(row=3, column=0, **P)
        cb("⌫",   self._backspace)          .grid(row=3, column=1, **P)
        ob("%",   lambda: self._append_op("%")).grid(row=3, column=2, **P)
        ob("÷",   lambda: self._append_op("/")).grid(row=3, column=3, **P)

        # Row 4
        nb("7",   lambda: self._digit("7")) .grid(row=4, column=0, **P)
        nb("8",   lambda: self._digit("8")) .grid(row=4, column=1, **P)
        nb("9",   lambda: self._digit("9")) .grid(row=4, column=2, **P)
        ob("×",   lambda: self._append_op("*")).grid(row=4, column=3, **P)

        # Row 5
        nb("4",   lambda: self._digit("4")) .grid(row=5, column=0, **P)
        nb("5",   lambda: self._digit("5")) .grid(row=5, column=1, **P)
        nb("6",   lambda: self._digit("6")) .grid(row=5, column=2, **P)
        ob("−",   lambda: self._append_op("-")).grid(row=5, column=3, **P)

        # Row 6
        nb("1",   lambda: self._digit("1")) .grid(row=6, column=0, **P)
        nb("2",   lambda: self._digit("2")) .grid(row=6, column=1, **P)
        nb("3",   lambda: self._digit("3")) .grid(row=6, column=2, **P)
        ob("+",   lambda: self._append_op("+")).grid(row=6, column=3, **P)

        # = spans rows 6-7, col 4-5
        eq_btn = eb("=", self._evaluate)
        eq_btn.grid(row=6, column=4, columnspan=2, rowspan=2, **P)

        # Row 7
        nb("±",   self._negate)             .grid(row=7, column=0, **P)
        nb("0",   lambda: self._digit("0")) .grid(row=7, column=1, **P)
        nb(".",   self._dot)                .grid(row=7, column=2, **P)
        fb("1/x", lambda: self._fn("inv"))  .grid(row=7, column=3, **P)

    # ── Key bindings ───────────────────────────────────────────────────────────

    def _bind_keys(self):
        for d in "0123456789":
            self.bind(d, lambda e, x=d: self._digit(x))
        self.bind(".", lambda e: self._dot())
        self.bind("+", lambda e: self._append_op("+"))
        self.bind("-", lambda e: self._append_op("-"))
        self.bind("*", lambda e: self._append_op("*"))
        self.bind("/", lambda e: self._append_op("/"))
        self.bind("^", lambda e: self._append_op("**"))
        self.bind("%", lambda e: self._append_op("%"))
        self.bind("(", lambda e: self._paren("("))
        self.bind(")", lambda e: self._paren(")"))
        self.bind("<Return>",    lambda e: self._evaluate())
        self.bind("<KP_Enter>",  lambda e: self._evaluate())
        self.bind("<BackSpace>", lambda e: self._backspace())
        self.bind("<Escape>",    lambda e: self._clear())

    # ── Display ────────────────────────────────────────────────────────────────

    def _update(self):
        self.main_var.set(self.current)
        self.expr_var.set(self._pretty(self.expr))
        self.mem_var.set(f"M  {self._fmt(self.memory)}" if self.memory != 0 else "")
        self.mode_var.set("DEG" if self.deg_mode else "RAD")
        self.inv_var.set("INV" if self.inv_mode else "")
        if self._inv_btn:
            self._inv_btn.configure(fg="#60a5fa" if self.inv_mode else "#44444e")

    def _pretty(self, s):
        return s.replace("**","^").replace("*","×").replace("/","÷").replace("-","−")

    def _fmt(self, v):
        if isinstance(v, float) and v == int(v) and abs(v) < 1e13:
            return str(int(v))
        return f"{v:.10g}"

    # ── Input ──────────────────────────────────────────────────────────────────

    def _digit(self, d):
        if self.error: self._clear(); return
        if self.just_evaled:
            self.current = d; self.expr = ""; self.just_evaled = False
        elif self.current == "0":
            self.current = d
        elif len(self.current) < 16:
            self.current += d
        self._update()

    def _dot(self):
        if self.error: self._clear(); return
        if self.just_evaled:
            self.current = "0."; self.expr = ""; self.just_evaled = False
        elif "." not in self.current:
            self.current += "."
        self._update()

    def _append_op(self, op):
        if self.error: return
        self.just_evaled = False
        tail = self.expr[-2:] if len(self.expr) >= 2 else self.expr[-1:]
        if tail == "**" or (tail and tail[-1] in "+-*/%"):
            self.expr = self.expr[:-len(tail)] + op
        else:
            self.expr += self.current + op
            self.current = "0"
        self._update()

    def _paren(self, p):
        if self.error: return
        self.just_evaled = False
        if p == "(":
            prefix = "" if self.current == "0" else self.current + "*"
            self.expr += prefix + "("
            self.current = "0"
        else:
            self.expr += self.current + ")"
            self.current = "0"
        self._update()

    def _fn(self, name):
        if self.error: return
        try:
            v = float(self.current)
            inv = self.inv_mode
            r2d = math.radians if self.deg_mode else (lambda x: x)
            d2r = math.degrees if self.deg_mode else (lambda x: x)
            result = {
                "sin":  lambda: d2r(math.asin(v)) if inv else math.sin(r2d(v)),
                "cos":  lambda: d2r(math.acos(v)) if inv else math.cos(r2d(v)),
                "tan":  lambda: d2r(math.atan(v)) if inv else math.tan(r2d(v)),
                "ln":   lambda: math.exp(v)        if inv else math.log(v),
                "log":  lambda: 10**v              if inv else math.log10(v),
                "sqrt": lambda: v**2               if inv else math.sqrt(v),
                "sq":   lambda: math.sqrt(v)       if inv else v**2,
                "inv":  lambda: 1 / v,
            }[name]()
            self.current = self._fmt(result)
            self.just_evaled = True; self.error = False
        except ZeroDivisionError:
            self.current = "÷0 Error"; self.error = True
        except Exception:
            self.current = "Error"; self.error = True
        self._update()

    def _constant(self, val):
        if self.just_evaled: self.expr = ""
        self.current = self._fmt(val)
        self.just_evaled = True
        self._update()

    def _negate(self):
        if self.error: return
        if self.current not in ("0", ""):
            self.current = self.current[1:] if self.current.startswith("-") else "-" + self.current
        self._update()

    def _clear(self):
        self.current = "0"; self.expr = ""
        self.just_evaled = False; self.error = False
        self._update()

    def _backspace(self):
        if self.error or self.just_evaled: self._clear(); return
        self.current = self.current[:-1] or "0"
        self._update()

    def _evaluate(self):
        if self.error: self._clear(); return
        full = self.expr + self.current
        if not full: return
        self.expr_var.set(self._pretty(full) + "  =")
        try:
            safe = re.sub(r'[^0-9+\-*/.%()eE ]', '', full)
            result = eval(safe)  # nosec — sanitized
            self.current = self._fmt(result)
            self.expr = ""; self.just_evaled = True; self.error = False
        except ZeroDivisionError:
            self.current = "÷0 Error"; self.expr = ""; self.error = True
        except Exception:
            self.current = "Error"; self.expr = ""; self.error = True
        self._update()

    # ── Memory ─────────────────────────────────────────────────────────────────

    def _mc(self):
        self.memory = 0.0; self._update()

    def _mr(self):
        self.current = self._fmt(self.memory)
        self.just_evaled = True; self._update()

    def _mplus(self):
        try: self.memory += float(self.current)
        except: pass
        self._update()

    def _mminus(self):
        try: self.memory -= float(self.current)
        except: pass
        self._update()

    # ── Modes ──────────────────────────────────────────────────────────────────

    def _toggle_deg(self):
        self.deg_mode = not self.deg_mode
        self._update()

    def _toggle_inv(self):
        self.inv_mode = not self.inv_mode
        self._update()


if __name__ == "__main__":
    app = EngCalc()
    app.mainloop()
