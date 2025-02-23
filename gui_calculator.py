import threading

from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk
from tkinter.font import Font
from sympy import *
import matplotlib
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')

init_printing(full_prec=False)

screen_direction = [1, 1]

class Token:
	def __init__(self, up: 'Token' = None, down: 'Token' = None, left: 'Token' = None, right: 'Token' = None):
		self.up = up
		self.down = down
		self.left = left
		self.right = right
	
	def __str__(self):
		return "oops"
	
	def get_up(self) -> list['Token']:
		if self.up is None:
			return [self]
		return [self] + self.up.get_up()
	
	def get_down(self) -> list['Token']:
		if self.down is None:
			return [self]
		return [self] + self.down.get_down()
	
	def get_left(self) -> list['Token']:
		if isinstance(self.left, StartToken):
			return [self]
		return [self] + self.left.get_left()
	
	def get_right(self) -> list['Token']:
		if isinstance(self.right, EndToken):
			return [self]
		return [self] + self.right.get_right()
	
	def latex(self) -> str:
		return "oops"

class StartToken(Token):
	def __str__(self):
		return ""
	
	def latex(self) -> str:
		return ""
	
class EndToken(Token):
	def __str__(self):
		return ""
	
	def latex(self) -> str:
		return ""

class FillableToken(Token):
	def __str__(self):
		return "⬚"
	
	def latex(self) -> str:
		return "⬚"
	
	def replace_with(self, token: Token) -> None:
		token.left = self.left
		token.right = self.right
		token.up = self.up
		token.down = self.down
		self.left.right = token
		self.right.left = token
		self.up.down = token
		self.down.up = token
		del self

class NumberToken(Token):
	def __init__(self, val: int, up: 'Token' = None, down: 'Token' = None, left: 'Token' = None, right: 'Token' = None):
		super().__init__(up, down, left, right)
		self.val = val
	
	def add_to_end(self, digit: int) -> None:
		self.val *= 10
		self.val += digit
		
	def __str__(self) -> str:
		return str(self.val)
	
	def latex(self) -> str:
		return str(self.val)

class ExactToken(Token):
	def __init__(self, val: str, up: 'Token' = None, down: 'Token' = None, left: 'Token' = None, right: 'Token' = None):
		super().__init__(up, down, left, right)
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
	def __init__(self, val: str,  up: 'Token' = None, down: 'Token' = None, left: 'Token' = None, right: 'Token' = None, take_previous: bool = False):
		super().__init__(up, down, left, right)
		self.val = val
		self.take_previous = take_previous
	
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
			case "⁄":
				return f"( ({"".join([str(t) for t in self.up.get_right()])}) / ({"".join([str(t) for t in self.down.get_right()])}) )"
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
			case "⁄":
				return r"\dfrac{"+token_to_latex(self.up.get_right())+"}{"+token_to_latex(self.up.get_right())+"}"
			case _:
				return "oops"

class FractionToken(OperatorToken):
	def __init__(self, up: 'Token' = None, down: 'Token' = None, left: 'Token' = None, right: 'Token' = None):
		if up is None:
			up = StartToken()
			up.right = FillableToken()
			up.right.right = EndToken()
			up.down = up
			up.left = left
		if down is None:
			down = StartToken()
			down.right = FillableToken()
			down.right.right = EndToken()
			down.up = up
			down.left = left
		super().__init__("⁄", up, down, left, right, True)

root_token: StartToken = StartToken()
root_token.right = EndToken()
root_token.right.left = root_token
cursor_pos: Token = root_token
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

def token_to_latex(token: StartToken) -> str:



def token_to_latex_sympy() -> str:
	str_tokens: str = "".join([str(token) for token in calculation_tokens])
	transformations = parsing.sympy_parser.standard_transformations + (parsing.sympy_parser.implicit_multiplication, )
	expr = parse_expr(str_tokens, evaluate=False, transformations=transformations)
	return latex(expr, mul_symbol="times")

def insert_token_between(token: Token, left: Token, right: Token) -> None:
	token.left = left
	token.right = right
	left.right = token
	right.left = token

def remove_token(token: Token) -> None:
	token.left.right = token.right
	token.right.left = token.left
	del token

def add_to_calc(token: Token) -> None:
	global cursor_pos
	
	if isinstance(token, NumberToken): # If token to add is a Number Token
		if isinstance(cursor_pos, NumberToken): # If previous token is Number Token, add onto it
			cursor_pos.val *= 10
			cursor_pos.val += token.val
		elif isinstance(cursor_pos, OperatorToken): # If previous token is Operator Token,
			pass
		elif isinstance(cursor_pos, StartToken): # If previous token is the start of the expression, add on to it
			token.left = cursor_pos
			cursor_pos.right = token
			cursor_pos = token
	elif isinstance(token, OperatorToken): # if val is an Operator Token
		if isinstance(token, FractionToken):
			if not isinstance(cursor_pos, StartToken):
				insert_token_between(token.up, cursor_pos.left, cursor_pos.right)
				token.down.left = cursor_pos.left
				cursor_pos.right = cursor_pos.right
				token.up.right.replace_with(cursor_pos)
			else:
				insert_token_between(token, cursor_pos, cursor_pos.right)
		else:
			insert_token_between(token, cursor_pos, cursor_pos.right)
	
	latex_string = token_to_latex()
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
	def __init__(self, text: str, token: Token, **kwargs) -> None:
		self.text = text
		self.token = token
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
		self.lines: list[tk.Text | tk.Label] = [
			tk.Text(self, height=1, width=16, font=font, bg=Base, fg=Text, highlightthickness=0, borderwidth=0, insertbackground=Text, insertborderwidth=0, insertwidth=4),
			tk.Label(self, height=3, width=16, bg=Base, fg=Text, highlightthickness=0, borderwidth=0)
		]
		self.canvas = FigureCanvasTkAgg(self.figure, master=self.lines[1])
		self.canvas._tkcanvas.configure(background=Base)
		self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		
		self.latex_input.get_xaxis().set_visible(False)
		self.latex_input.get_yaxis().set_visible(False)
		
		self.lines[0].grid(column=0, row=0, sticky=tk.EW)
		self.lines[1].grid(column=0, row=1, sticky=tk.NSEW)
		
		for colour in rainbow:
			self.lines[0].tag_config(colour, foreground=colour)
		self.lines[0].tag_config(Overlay1, foreground=Overlay1)
		self.lines[0].tag_config("italic", font=italic_font)
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)
		def event(e: tk.Event):
			if e.char.isprintable():
				add_to_calc(e.char)
			return "break"
		self.lines[0].bind("<Key>", event)
	
	def __getitem__(self, item):
		return self.lines[item]
	
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
		(0, 0, AddButtonConfig("+", OperatorToken("+"))),
		(0, 1, AddButtonConfig("-", OperatorToken("+"))),
		(0, 2, AddButtonConfig("÷", OperatorToken("/"))),
		(0, 3, AddButtonConfig("×", OperatorToken("*"))),
		(0, 4, AddButtonConfig("⬚\n—\n⬚", OperatorToken("⁄", take_previous=True), font=small_font)),
		# (0, 5, AddButtonConfig(")")),
		(0, 6, AddButtonConfig("7", NumberToken(7))),
		(0, 7, AddButtonConfig("8", NumberToken(8))),
		(0, 8, AddButtonConfig("9", NumberToken(9))),
		(1, 0, AddButtonConfig("⬚ⁿ", "**(")),
		(1, 1, AddButtonConfig("⬚²", "**2")),
		(1, 2, AddButtonConfig("²√⬚", "Sqrt(")),
		(1, 3, AddButtonConfig("ⁿ√⬚", "**(1/")),
		(1, 4, AddButtonConfig("(", OperatorToken("("))),
		(1, 5, AddButtonConfig(")", OperatorToken(")"))),
		(1, 6, AddButtonConfig("4", NumberToken(4))),
		(1, 7, AddButtonConfig("5", NumberToken(5))),
		(1, 8, AddButtonConfig("6", NumberToken(6))),
		
		
		(2, 6, AddButtonConfig("1", NumberToken(1))),
		(2, 7, AddButtonConfig("2", NumberToken(2))),
		(2, 8, AddButtonConfig("3", NumberToken(3))),
		
		
		# (3, 0, AddButtonConfig("π", ExactToken("pi"))),
		# (3, 1, AddButtonConfig("e", ExactToken("E"))),
		(3, 1, FunctionButtonConfig("↑", None)),
		
		(3, 6, FunctionButtonConfig("=", solve)),
		(3, 7, AddButtonConfig("0", NumberToken(0))),
		(3, 8, AddButtonConfig("Ans", ExactToken("Ans"))),
		
		(4, 0, FunctionButtonConfig("←", None)),
		(4, 1, FunctionButtonConfig("↓", None)),
		(4, 2, FunctionButtonConfig("→", None)),
		(4, 6, FunctionButtonConfig("≈", lambda: solve(False))),
		(4, 7, FunctionButtonConfig("⌫", backspace_calc)),
		(4, 8, FunctionButtonConfig("C", clear_calc)),
		
		(4, 3, AddButtonConfig(":=", OperatorToken(":="))),
		
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
			token: Token = cfg.token
			kwargs = cfg.kwargs
			btn = HoverButton(frame, text=fancy, command=lambda token=token: add_to_calc(token), **kwargs)
			btn.grid(row=row, column=column, sticky=tk.NSEW)
			btns.append(btn)
		elif isinstance(cfg, FunctionButtonConfig):
			fn_name: str = cfg.text
			fn_callable: str = cfg.func
			btn = HoverButton(frame, text=fn_name, command=fn_callable)
			btn.grid(row=row, column=column)
			btns.append(btn)

for i, btn in enumerate(btns):
	btn.configure(
		fg=rainbow[i % len(rainbow)],
		activebackground=rainbow[i % len(rainbow)],
	)


move_window()
root.mainloop()

