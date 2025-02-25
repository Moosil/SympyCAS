import threading

from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk
from tkinter.font import Font
from sympy import *
import matplotlib
from typing import Union, Type
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')

init_printing(full_prec=False)

screen_direction = [1, 1]

class Token:
	def __init__(self, parent: 'ContainerToken', index: int = -1) -> None:
		self.index = index
		self.parent = parent
	
	def __str__(self):
		return "oops"
	
	def latex(self) -> str:
		return "oops"

class ContainerToken(Token):
	def __init__(self, parent: 'ContainerToken' = None, children: list[Token] = None, owner_token: Token = None) -> None:
		super().__init__(parent, -1)
		if children is None:
			children = []
		self.children = children
		self.owner_token = owner_token
	
	def __str__(self) -> str:
		if len(self.children) == 0:
			return "⬚"
		elif len(self.children) == 1:
			return str(self.children[0])
		elif self.parent is None:
			return "".join([str(c) for c in self.children])
		else:
			return "("+"".join([str(c) for c in self.children])+")"
	
	def latex(self) -> str:
		global cursor_pos
		global curr_token
		if len(self.children) == 0:
			return "|" if curr_token is self and cursor_pos == -1 else "⬚"
		elif len(self.children) == 1:
			if curr_token is self:
				return ("|" if cursor_pos == -1 else "") + self.children[0].latex() + ("|" if cursor_pos == 0 else "")
			else:
				return self.children[0].latex()
		elif self.parent is None:
			if curr_token is not self:
				return " ".join([c.latex() for c in self.children])
			else:
				rv = "|" if cursor_pos == -1 else ""
				for i, c in enumerate(self.children):
					rv += c.latex() + ("|" if i == cursor_pos else " ")
				return rv
		else:
			if curr_token is not self:
				return "("+" ".join([c.latex() for c in self.children])+")"
			else:
				rv = "(" + "|" if cursor_pos == -1 else ""
				for i, c in enumerate(self.children):
					rv += c.latex() + ("|" if i == cursor_pos else " ")
				return rv + ")"

class NumberToken(Token):
	def __init__(self, parent: ContainerToken, index: int = -1, val: int = 0) -> None:
		super().__init__(parent, index)
		self.val = val
	
	def add_to_end(self, digit: int) -> None:
		self.val *= 10
		self.val += digit
		
	def __str__(self) -> str:
		return str(self.val)
	
	def latex(self) -> str:
		return str(self.val)

class ExactToken(Token):
	def __init__(self, parent: ContainerToken, index: int = -1, val: str = "this needs to be filled") -> None:
		super().__init__(parent, index)
		self.val = val
	
	def __str__(self) -> str:
		return self.val
	
	def latex(self) -> str:
		match self.val:
			case "pi":
				return r"\pi"
			case "E":
				return "e"

class OperatorToken(Token):
	def __init__(self, parent: ContainerToken, index: int = -1, val: str = "this needs to be filled") -> None:
		super().__init__(parent, index)
		self.val = val
	
	def __str__(self) -> str:
		match self.val:
			case '+':
				return '+'
			case '-':
				return '-'
			case '*':
				return "*"
			case "/":
				return "*"
			case _:
				return "oops"
	
	def latex(self) -> str:
		match self.val:
			case '+':
				return '+'
			case '-':
				return '-'
			case '*':
				return r"\times"
			case "/":
				return r"\div"
			case _:
				return "oops"

class FractionToken(OperatorToken):
	def __init__(self, parent: ContainerToken, index: int = -1, top_children: list[Token] = None, bottom_children: list[Token] = None) -> None:
		super().__init__(parent, index, "⁄")
		if top_children is None:
			top_children = []
		if bottom_children is None:
			bottom_children = []
		self.top: ContainerToken = ContainerToken(parent, top_children, self)
		self.bottom: ContainerToken = ContainerToken(parent, bottom_children, self)
	
	def __str__(self) -> str:
		return f"({str(self.top)}) / ({str(self.bottom)})"
	
	def latex(self) -> str:
		if isinstance(self.parent.owner_token, SubSuperScript):
			return self.top.latex()+" / "+self.bottom.latex()
		else:
			return r"\dfrac{"+self.top.latex()+"}{"+self.bottom.latex()+"}"
	
	def enter_left(self) -> ContainerToken:
		return self.top
	
	def enter_right(self) -> ContainerToken:
		return self.top
	
	def get_up(self, curr_container: ContainerToken) -> ContainerToken:
		return self.top
	
	def get_down(self, curr_container: ContainerToken) -> ContainerToken:
		return self.bottom

class SubSuperScript(Token):
	def __init__(self, parent: ContainerToken, index: int = -1, inner_children: list[Token] = None, sub_children: list[Token] = None,
	             super_children: list[Token] = None) -> None:
		super().__init__(parent, index)
		if inner_children is None:
			inner_children = []
		if sub_children is None:
			sub_children = []
		if super_children is None:
			super_children = []
		self.inner: ContainerToken = ContainerToken(parent, inner_children, self)
		self.sub: ContainerToken = ContainerToken(parent, sub_children, self)
		self.super: ContainerToken = ContainerToken(parent, super_children, self)
		for i, child in enumerate(self.inner.children):
			child.parent = self.inner
			child.index = i
		for i, child in enumerate(self.sub.children):
			child.parent = self.sub
			child.index = i
		for i, child in enumerate(self.super.children):
			child.parent = self.super
			child.index = i
	
	def __str__(self) -> str:
		return f"({self.inner})_{{{self.sub}}}^{{{self.super}}}"
	
	def latex(self) -> str:
		return f"{self.inner.latex()}_{{{self.sub.latex()}}}^{{{self.super.latex()}}}"
	
	def enter_left(self) -> ContainerToken:
		return self.inner
	
	def enter_right(self) -> ContainerToken:
		global cursor_pos
		cursor_pos += 1
		return self.super
	
	def get_up(self, curr_container: ContainerToken) -> ContainerToken:
		if curr_container is self.sub:
			return self.inner
		else:
			return self.super
	
	def get_down(self, curr_container: ContainerToken) -> ContainerToken:
		if curr_container is self.super:
			return self.inner
		else:
			return self.sub

class PowerToken(SubSuperScript, OperatorToken):
	def __init__(self, parent: ContainerToken, index: int = -1, inner_children: list[Token] = None,
	             power_children: list[Token] = None) -> None:
		super().__init__(parent=parent, index=index, inner_children=inner_children, sub_children=None, super_children=power_children)
		del self.val
		del self.sub
	
	def __str__(self) -> str:
		return f"({self.inner})**({self.super})"
	
	def latex(self) -> str:
		return f"{self.inner.latex()}^{{{self.super.latex()}}}"
	
	def enter_left(self) -> ContainerToken:
		return self.inner
	
	def enter_right(self) -> ContainerToken:
		return self.super
	
	def get_up(self, curr_container: ContainerToken) -> ContainerToken:
		return self.super
	
	def get_down(self, curr_container: ContainerToken) -> ContainerToken:
		return self.inner

class RootToken(PowerToken):
	def __init__(self, parent: ContainerToken, index: int = -1, inner_children: list[Token] = None,
	             root_children: list[Token] = None) -> None:
		super().__init__(parent, index, inner_children, root_children)
		self.super.token_type = RootToken
	
	def __str__(self) -> str:
		return f"root({self.inner}, {self.super})"
	
	def latex(self) -> str:
		return fr"\sqrt[{self.super.latex()}]{{{self.inner.latex()}}}"
	
	def enter_left(self) -> ContainerToken:
		return self.super
	
	def enter_right(self) -> ContainerToken:
		return self.inner
	
	def get_up(self, curr_container: ContainerToken) -> ContainerToken:
		return self.super
	
	def get_down(self, curr_container: ContainerToken) -> ContainerToken:
		return self.inner

calculation: ContainerToken = ContainerToken()
curr_token: ContainerToken = calculation
cursor_pos: int = -1

Ans = symbols("Ans")

dvd_logo_toggle = False
def toggle_dvd_logo():
	global dvd_logo_toggle
	dvd_logo_toggle = not dvd_logo_toggle
	if dvd_logo_toggle:
		move_window()

symbols_mem: dict[str, Symbol] = {}
relations_mem: dict = {}

def hex_to_rgb(hex_str) -> str:
	hex_str = hex_str.lstrip('#')
	return f"{int(hex_str[0:2], 16)} {int(hex_str[2:4], 16)} {int(hex_str[4:6], 16)}"

def combine_hex_values(d):
	# from (https://stackoverflow.com/questions/61488790/how-can-i-proportionally-mix-colors-in-python)
	d_items = sorted(d.items())
	tot_weight = sum(d.values())
	red = int(sum([int(k[:2], 16)*v for k, v in d_items])/tot_weight)
	green = int(sum([int(k[2:4], 16)*v for k, v in d_items])/tot_weight)
	blue = int(sum([int(k[4:6], 16)*v for k, v in d_items])/tot_weight)
	zpad = lambda x: x if len(x)==2 else '0' + x
	return zpad(hex(red)[2:]) + zpad(hex(green)[2:]) + zpad(hex(blue)[2:])

def get_taskbar_height() -> int:
	# from (https://stackoverflow.com/questions/4357258/how-to-get-the-height-of-windows-taskbar-using-python-pyqt-win32)
	monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
	monitor_area = monitor_info.get("Monitor")
	work_area = monitor_info.get("Work")
	return monitor_area[3]-work_area[3]

taskbar_height = get_taskbar_height()

def solve(exact: bool = True) -> None:
	pass

# def token_to_latex_sympy() -> str:
# 	str_tokens: str = "".join([str(token) for token in calculation_tokens])
# 	transformations = parsing.sympy_parser.standard_transformations + (parsing.sympy_parser.implicit_multiplication, )
# 	expr = parse_expr(str_tokens, evaluate=False, transformations=transformations)
# 	return latex(expr, mul_symbol="times")

def add_to_calc(token_type: Type[Token], *token_args) -> None:
	global calculation
	global cursor_pos
	global curr_token
	if cursor_pos == -1:
		token: Token = token_type(curr_token, 0, *token_args)
		curr_token.children.insert(0, token)
		if isinstance(token, FractionToken):
			curr_token = token.top
			cursor_pos = -1
		elif isinstance(token, PowerToken):
			curr_token = token.inner
			cursor_pos = -1
		else:
			cursor_pos = 0
	else:
		prev_token = curr_token.children[cursor_pos]
		next_token = None if cursor_pos + 1 >= len(curr_token.children) else curr_token.children[cursor_pos+1]
		token: Token = token_type(curr_token, cursor_pos + 1, *token_args)
		if isinstance(token, NumberToken):
			if isinstance(prev_token, NumberToken):
				prev_token.val *= 10
				prev_token.val += token.val
			elif isinstance(prev_token, OperatorToken):
				curr_token.children.insert(cursor_pos + 1, token)
				cursor_pos += 1
		elif isinstance(token, OperatorToken):
			if isinstance(token, FractionToken):
				if isinstance(prev_token, NumberToken | FractionToken | PowerToken):
					token.top.children.append(prev_token)
					prev_token.parent = token.top
					token.index -= 1
					curr_token.children.pop(cursor_pos)
					curr_token.children.insert(cursor_pos, token)
					curr_token = token.bottom
				else:
					curr_token.children.insert(cursor_pos + 1, token)
					curr_token = token.top
				cursor_pos = -1
			elif isinstance(token, PowerToken):
				if isinstance(prev_token, NumberToken | FractionToken | PowerToken):
					token.inner.children.append(prev_token)
					prev_token.parent = token.inner
					token.index -= 1
					curr_token.children.pop(cursor_pos)
					curr_token.children.insert(cursor_pos, token)
					if len(token.super.children) == 0:
						curr_token = token.super
						cursor_pos = -1
					else:
						pass
				else:
					curr_token.children.insert(cursor_pos + 1, token)
					curr_token = token.inner
					cursor_pos = -1
			else:
				curr_token.children.insert(cursor_pos + 1, token)
				cursor_pos += 1
		
	
	latex_string = calculation.latex()
	text_area.display_latex(latex_string)

def move_cursor(x: int, y: int) -> None:
	global cursor_pos
	global curr_token
	global calculation
	x_sign: int = 1 if x > 0 else -1 if x < 0 else 0
	y_sign: int = 1 if y > 0 else -1 if y < 0 else 0
	while x != 0:
		if ((cursor_pos == -1) and x_sign == -1) or (cursor_pos == len(curr_token.children) - 1 and x_sign == 1):
			if curr_token is calculation:
				break
			else:
				cursor_pos = curr_token.owner_token.index + (-1 if x_sign == -1 else 0)
				curr_token = curr_token.parent
		else:
			start_token: Token = curr_token.children[cursor_pos]
			if cursor_pos != -1 and isinstance(start_token, FractionToken | SubSuperScript):
				if x_sign == -1:
					curr_token = start_token.enter_right()
					cursor_pos = len(curr_token.children) - 1
				else:
					cursor_pos += 1
			else:
				cursor_pos += x_sign
				enter_token: Token = curr_token.children[cursor_pos]
				if isinstance(enter_token, FractionToken | SubSuperScript):
					if x_sign == 1:
						curr_token = enter_token.enter_left()
						cursor_pos = -1
					
		x -= x_sign
	while y != 0 and curr_token is not None:
		if y_sign == 1:
			curr_token = curr_token.owner_token.get_up(curr_token)
		else:
			curr_token = curr_token.owner_token.get_down(curr_token)
		y -= y_sign
	
	latex_string = calculation.latex()
	text_area.display_latex(latex_string)

def backspace_calc() -> None:
	pass

def clear_calc() -> None:
	pass

repl = {
	"/": "÷",
	"*": "×",
	"E": "e",
	"**": "^",
	"sqrt": "√"
}

max_repl = max([len(key) for key in repl.keys()])

class ButtonConfig:
	pass

class AddButtonConfig(ButtonConfig):
	def __init__(self, text: str, token_type: Type[Token], *token_args, **kwargs) -> None:
		self.text = text
		self.token_type = token_type
		self.token_args = token_args
		self.kwargs = kwargs

class FunctionButtonConfig(ButtonConfig):
	def __init__(self, text: str, func: callable) -> None:
		self.text = text
		self.func = func

Rosewater="#f5e0dc"
Flamingo="#f2cdcd"
Pink="#f5c2e7"
Mauve="#cba6f7"
Red="#f38ba8"
Maroon="#eba0ac"
Peach="#fab387"
Yellow="#f9e2af"
Green="#a6e3a1"
Teal="#94e2d5"
Sky="#89dceb"
Sapphire="#74c7ec"
Blue="#89b4fa"
Lavender="#b4befe"
Text="#cdd6f4"
Subtext1="#bac2de"
Subtext0="#a6adc8"
Overlay2="#9399b2"
Overlay1="#7f849c"
Overlay0="#6c7086"
Surface2="#585b70"
Surface1="#45475a"
Surface0="#313244"
Base="#1e1e2e"
Mantle="#181825"
Crust="#11111b"
rainbow = [Red, Peach, Yellow, Green, Teal, Sky, Sapphire, Blue, Mauve, Lavender, Pink, Maroon]
rows: int = 5
columns: int = 10

root = tk.Tk()
root.title("Calculator")
root.geometry(f"{66*columns}x{41*3+64*rows}")
root.minsize(66*columns, 41*3+64*rows)
root.configure(bg=Base)

font = Font(family="Calibri", size=22)
small_font = Font(family="Calibri", size=10)
italic_font = Font(family="Calibri", size=22, slant="italic")

screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())

def move_window():
	global dvd_logo_toggle
	if not dvd_logo_toggle:
		return
	new_pos = (root.winfo_x() + screen_direction[0], root.winfo_y() + screen_direction[1])
	screen_width = screen_size[0] - root.winfo_width()
	screen_height = screen_size[1] - root.winfo_height() - taskbar_height
	
	if new_pos[0] < 0 or new_pos[0] > screen_width:
		screen_direction[0] *= -1
	if new_pos[1] < 0 or new_pos[1] > screen_height:
		screen_direction[1] *= -1
	
	root.geometry(f"+{new_pos[0]}+{new_pos[1]}")
	timer = threading.Timer(0.001, move_window)
	timer.start()

class TextArea(tk.Frame):
	def __init__(self, master = None, **kwargs):
		super().__init__(master, **kwargs)
		self.figure = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
		self.figure.patch.set_facecolor(Base)
		self.latex_input = self.figure.add_subplot(111)
		self.latex_input.patch.set_facecolor(Base)
		for dir in ["top", "bottom", "left", "right"]:
			self.latex_input.spines[dir].set_color(Base)
		self.line: tk.Label = tk.Label(self, height=3, width=16, bg=Base, fg=Text, highlightthickness=0, borderwidth=0)
		self.canvas = FigureCanvasTkAgg(self.figure, master=self.line)
		self.canvas._tkcanvas.configure(background=Base)
		self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		
		self.latex_input.get_xaxis().set_visible(False)
		self.latex_input.get_yaxis().set_visible(False)
		
		self.line.grid(column=0, row=1, sticky=tk.NSEW)
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)
		#TODO: Add typing with keyboard
		# def event(e: tk.Event):
		# 	if e.char.isprintable():
		# 		add_to_calc(e.char)
		# 	return "break"
		# self.line.bind("<Key>", event)
		latex_string = calculation.latex()
		self.display_latex(latex_string)
		
	
	def display_latex(self, latex_str: str) -> None:
		self.latex_input.clear()
		self.latex_input.text(0.2, 0.6, "$"+latex_str+"$", fontsize=24, color=Text, backgroundcolor=Base)
		self.latex_input.patch.set_facecolor(Base)
		self.canvas.draw()

text_area = TextArea(root, bg=Base)
text_area.grid(column=0, row=0, sticky=tk.NSEW)
main_button_area = tk.Frame(root, bg=Base)
main_button_area.grid(column=0, row=1, sticky=tk.EW)
function_button_area = tk.Frame(root, bg=Base)
function_button_area.grid(column=0, row=1, sticky=tk.EW)
function_button_area.grid_remove()
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
curr_window = main_button_area
btns: list[tk.Button] = []

def switch_to_window(window) -> None:
	global curr_window
	curr_window.grid_remove()
	window.grid()
	curr_window = window

ui: dict[tk.Frame, list[tuple[int, int, ButtonConfig]]] = {
	main_button_area: [
		(0, 0, AddButtonConfig("+", OperatorToken, "+")),
		(0, 1, AddButtonConfig("-", OperatorToken, "-")),
		(0, 2, AddButtonConfig("÷", OperatorToken, "/")),
		(0, 3, AddButtonConfig("×", OperatorToken, "*")),
		(0, 4, AddButtonConfig("⬚\n—\n⬚", FractionToken, font=small_font)),
		# (0, 5, AddButtonConfig(")")),
		(0, 6, AddButtonConfig("7", NumberToken, 7)),
		(0, 7, AddButtonConfig("8", NumberToken, 8)),
		(0, 8, AddButtonConfig("9", NumberToken, 9)),
		(1, 0, AddButtonConfig("⬚ⁿ", PowerToken)),
		(1, 1, AddButtonConfig("⬚²", PowerToken, None, [NumberToken(None, val=2)])),
		(1, 2, AddButtonConfig("²√⬚", RootToken, None, [NumberToken(None, val=2)])),
		(1, 3, AddButtonConfig("ⁿ√⬚", RootToken)),
		(1, 4, AddButtonConfig("(", OperatorToken, "(")),
		(1, 5, AddButtonConfig(")", OperatorToken, ")")),
		(1, 6, AddButtonConfig("4", NumberToken, 4)),
		(1, 7, AddButtonConfig("5", NumberToken, 5)),
		(1, 8, AddButtonConfig("6", NumberToken, 6)),
		
		
		(2, 6, AddButtonConfig("1", NumberToken, 1)),
		(2, 7, AddButtonConfig("2", NumberToken, 2)),
		(2, 8, AddButtonConfig("3", NumberToken, 3)),
		
		
		# (3, 0, AddButtonConfig("π", ExactToken, "pi")),
		# (3, 1, AddButtonConfig("e", ExactToken, "E")),
		(3, 1, FunctionButtonConfig("↑", lambda: move_cursor(0, 1))),
		
		(3, 6, FunctionButtonConfig("=", solve)),
		(3, 7, AddButtonConfig("0", NumberToken, 0)),
		(3, 8, AddButtonConfig("Ans", ExactToken, "Ans")),
		
		(4, 0, FunctionButtonConfig("←", lambda: move_cursor(-1, 0))),
		(4, 1, FunctionButtonConfig("↓", lambda: move_cursor(0, -1))),
		(4, 2, FunctionButtonConfig("→", lambda: move_cursor(1, 0))),
		(4, 6, FunctionButtonConfig("≈", lambda: solve(False))),
		(4, 7, FunctionButtonConfig("⌫", backspace_calc)),
		(4, 8, FunctionButtonConfig("C", clear_calc)),
		
		(4, 3, AddButtonConfig(":=", OperatorToken, ":=")),
		
		(0, 9, FunctionButtonConfig("🖩", lambda: switch_to_window(main_button_area))),
		(1, 9, FunctionButtonConfig("trig", lambda: switch_to_window(function_button_area))),
		(2, 9, FunctionButtonConfig("📀", toggle_dvd_logo)),
	],
	function_button_area: [
		(0, 0, AddButtonConfig("sin", "sin(")),
		(0, 1, AddButtonConfig("csc", "csc(")),
		(0, 2, AddButtonConfig("cos", "cos(")),
		(0, 3, AddButtonConfig("sec", "sec(")),
		(0, 4, AddButtonConfig("tan", "tan(")),
		(0, 5, AddButtonConfig("cot", "cot(")),
		(0, 6, AddButtonConfig("sinc", "sinc(")),
		(1, 0, AddButtonConfig("asin", "asin(")),
		(1, 1, AddButtonConfig("acsc", "acsc(")),
		(1, 2, AddButtonConfig("acos", "acos(")),
		(1, 3, AddButtonConfig("asec", "asec(")),
		(1, 4, AddButtonConfig("atan", "atan(")),
		(1, 5, AddButtonConfig("acot", "acot(")),
		(1, 6, AddButtonConfig("atan2", "atan2(")),
		(2, 0, AddButtonConfig("abs", "Abs(")),
		(2, 1, AddButtonConfig("sign", "sign(")),
		(2, 2, AddButtonConfig("Im", "im(")),
		(2, 3, AddButtonConfig("Re", "re(")),
		(2, 4, AddButtonConfig("Frac", "frac(")),
		(2, 5, AddButtonConfig("ceil", "ceiling(")),
		(2, 6, AddButtonConfig("floor", "floor(")),
		(2, 7, AddButtonConfig("min", "Min(")),
		(2, 8, AddButtonConfig("max", "Max(")),
		(3, 0, AddButtonConfig("log₂", "log2(")),
		(3, 1, AddButtonConfig("log₂", "log10(")),
		(3, 2, AddButtonConfig("logₑ", "log(")),
		(3, 3, AddButtonConfig("logₙ(", "log(")),
		(4, 0, AddButtonConfig("d/dx", "diff(")),
		(4, 1, AddButtonConfig("∫", "integrate(")),
		(4, 2, AddButtonConfig("lim", "limit(")),
		
		(0, 9, FunctionButtonConfig("🖩", lambda: switch_to_window(main_button_area))),
		(1, 9, FunctionButtonConfig("trig", lambda: switch_to_window(function_button_area))),
		(2, 9, FunctionButtonConfig("📀", toggle_dvd_logo)),
	]
}

class HoverButton(tk.Button):
	def __init__(self, master, **kwargs):
		if "font" not in kwargs:
			kwargs["font"] = font
		tk.Button.__init__(self,master=master, width=4, bg=Surface0, activeforeground=Mantle, borderwidth=0, **kwargs)
		self.bind("<Enter>", self.on_enter)
		self.bind("<Leave>", self.on_leave)
	
	def on_enter(self, _e):
		self['background'] = Overlay0
	
	def on_leave(self, _e):
		self['background'] = Surface0

for frame, ui_elements in ui.items():
	for i, (row, column, cfg) in enumerate(ui_elements):
		if isinstance(cfg, AddButtonConfig):
			fancy: str = cfg.text
			token_type: Type[Token] = cfg.token_type
			token_args = cfg.token_args
			kwargs = cfg.kwargs
			btn = HoverButton(frame, text=fancy, command=lambda token_type=token_type, token_args=token_args: add_to_calc(token_type, *token_args), **kwargs)
			btn.grid(row=row, column=column, sticky=tk.NSEW)
			btns.append(btn)
		elif isinstance(cfg, FunctionButtonConfig):
			fn_name: str = cfg.text
			fn_callable: str = cfg.func
			btn = HoverButton(frame, text=fn_name, command=lambda fn_callable=fn_callable: fn_callable())
			btn.grid(row=row, column=column)
			btns.append(btn)

for i, btn in enumerate(btns):
	btn.configure(
		fg=rainbow[i % len(rainbow)],
		activebackground=rainbow[i % len(rainbow)],
	)


move_window()
root.mainloop()

