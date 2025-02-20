import math
import threading
from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk
from sympy import *

screen_direction = [1, 1]

prev_calculation = ""
text_calculation = ""
calculation_brackets: list[int] = []
Ans = symbols("Ans")


symbols_mem: dict[str, Symbol] = {}
relations_mem: dict = {}

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
	taskbar_height = monitor_area[3]-work_area[3]
	return taskbar_height

taskbar_height = get_taskbar_height()

def tokenise(string: str) -> list[str]:
	prev_type: str = ""
	curr: str = ""
	tokens: list[str] = []
	for char in string:
		curr_type: str
		if char.isdigit() or char == ".":
			curr_type = "num"
		elif char.isalpha():
			curr_type = "alpha"
		else:
			curr_type = "symbol"
		if curr_type == prev_type:
			curr += char
		elif prev_type != "":
			tokens.append(curr)
			curr = char
		prev_type = curr_type
	tokens.append(curr)
	return tokens

def solve(exact: bool = True) -> None:
	global prev_calculation
	global text_calculation
	idx: int = 0
	parsed: list[str] = []
	expression_type: str = "equation"
	has_ans: bool = False
	for token in tokenise(text_calculation):
		match token:
			case ":=":
				expression_type = "define"
			case "Ans":
				has_ans = True
		parsed.append(token)
		idx += len(token)
	
	match expression_type:
		case "equation":
			symbol_equation = sympify(text_calculation)
			if has_ans:
				symbol_equation = sympify(symbol_equation).subs(Ans, prev_calculation)
			if not exact:
				symbol_equation = symbol_equation.evalf()
			prev_calculation = symbol_equation
			text_calculation = str(prev_calculation)
			update_text_calculation()
		case "define":
			idx: int = 0
			name: str = ""
			fn_args: list[str] = []
			while parsed[idx] != "(":
				name += parsed[idx]
				idx += 1
			
			while parsed[idx] != ")" or parsed[idx] == ",)":
				if parsed[idx].strip() != ",":
					fn_args.append(parsed[idx])
					symbols_mem[parsed[idx]] = symbols(parsed[idx])
				idx += 1
			idx += 1
			
			relations_mem[name] = "".join(parsed[idx:])
			update_text_calculation("Done")

cursor_pos: int = 0

def add_to_calc(val: str | int) -> None:
	global text_calculation
	global cursor_pos
	global calculation_brackets
	prefix: str = ""
	suffix: str = ""
	val = str(val)
	
	if len(val) != 0:
		if val.isdigit() or val in exacts:
			if len(text_calculation) - 1 >= cursor_pos + 1 >= 0 and \
			(text_calculation[cursor_pos + 1].isdigit() or text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos + 1] == "("):
				suffix = "*"
			if len(text_calculation) - 1 >= cursor_pos - 1 >= 0 and \
			(text_calculation[cursor_pos - 1].isdigit() or text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos - 1] == ")"):
				prefix = "*"
		
		if val[len(val) - 1] == "(":
			calculation_brackets.append(cursor_pos + len(prefix) + len(val) - 1)
		elif val[len(val) - 1] == ")":
			idx: int = cursor_pos + len(prefix) + len(val) - 1
			for i in range(len(calculation_brackets)-1, -1, -1):
				if calculation_brackets[i] < idx:
					calculation_brackets.pop(i)
					break
	
	text_calculation = text_calculation[:cursor_pos] + prefix + val + suffix + text_calculation[cursor_pos:]
	update_text_calculation()
	cursor_pos += len(prefix) + len(val) + len(suffix)

def update_text_calculation(calc: str | None = None) -> None:
	global text_calculation
	calc = str(calc if calc is not None else text_calculation)
	text_area[1].delete(1.0, tk.END)
	text_area[1].insert(1.0, beautify_str(calc))
	brackets, left, right = get_brackets(text_calculation)
	for bracket in brackets:
		text_area[1].tag_add(rainbow[bracket[1]], f"1.{bracket[0]}", f"1.{bracket[0] + 1}")
	if left > 0:
		text_area[1].insert("1.end", "".join([")" for _i in range(left)]))
		text_area[1].tag_add(Overlay1, f"1.end-{left}c", "1.end")
	if right > 0:
		text_area[1].insert("1.0", "".join(["(" for _i in range(right)]))
		text_area[1].tag_add(Overlay1, f"1.0", f"1.{right}")

def clear_calc() -> None:
	global text_calculation
	text_calculation = ""
	text_area[1].delete(1.0, tk.END)


def mult(lhs: int, rhs: int) -> int:
	return lhs * rhs


def beautify_str(string: str) -> str:
	new_string: str = ""
	for char in string:
		added: bool = False
		for replace in repl:
			if replace[0] == char:
				new_string += replace[1]
				added = True
				break
		if not added:
			new_string += char
	
	return new_string

def get_brackets(string: str) -> tuple[list[tuple[int, int]], int, int]:
	brackets: int = 0
	unclosed_left_brackets: int = 0
	unclosed_right_brackets: int = 0
	brackets_list: list[tuple[int, int]] = []
	for i, char in enumerate(string):
		if char == "(":
			brackets_list.append((i, unclosed_left_brackets))
			brackets += 1
			unclosed_left_brackets += 1
		elif char == ")":
			brackets -= 1
			if unclosed_left_brackets > 0:
				unclosed_left_brackets -= 1
				brackets_list.append((i, unclosed_left_brackets))
			else:
				unclosed_right_brackets += 1
				brackets_list.append((i, -unclosed_right_brackets))
	return brackets_list, unclosed_left_brackets, unclosed_right_brackets
	

base = 10

repl = [
	("/", "÷"),
	("*", "×"),
	("E", "e")
]

modifiers = [
	"(",
	")",
]

functions = [
	"sin",
]

exacts = [
	"π",
	"Ans",
	"E"
]

dmas = [
	"/",
	"*",
	"+",
	"-"
]

commands = {
	"=": solve,
	"≈": lambda: solve(True),
	"C": clear_calc,
}

font: str = "Calibri"
font_size: int = 24
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

root = tk.Tk()
root.title("Calculator")
root.geometry(f"{70*base}x{378}")
root.minsize(70*base, 378)
root.configure(bg=Base)

screen_size = (root.winfo_screenwidth(), root.winfo_screenheight())

def move_window():
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
		self.lines = [tk.Text(self, height=1, width=16, font=(font, font_size), bg=Base, fg=Text, highlightthickness=0, borderwidth=0) for _i in range(3)]
		for line in self.lines:
			line.pack(expand=True, fill="both")
			for colour in rainbow:
				line.tag_config(colour, foreground=colour)
			line.tag_config(Overlay1, foreground=Overlay1)
	
	def __getitem__(self, item):
		return self.lines[item]
			

text_area = TextArea(root, bg=Base)
text_area.pack(expand=True, fill="both")
button_area = tk.Frame(root, bg=Base)
button_area.pack()
btns: list[tk.Button] = []

class HoverButton(tk.Button):
	def __init__(self, master, **kwargs):
		tk.Button.__init__(self,master=master, font=(font, font_size),width=4, bg=Surface0, activeforeground=Mantle, borderwidth=0, **kwargs)
		self.bind("<Enter>", self.on_enter)
		self.bind("<Leave>", self.on_leave)
	
	def on_enter(self, e):
		self['background'] = Overlay0
	
	def on_leave(self, e):
		self['background'] = Surface0

for i in range(base):
	btn = HoverButton(button_area, text=str(i), command=lambda i=i: add_to_calc(i))
	btn.grid(row=0, column=i)
	btns.append(btn)

for i, modifier in enumerate(dmas + modifiers + exacts):
	btn = HoverButton(button_area, text=beautify_str(modifier), command=lambda modifier=modifier: add_to_calc(modifier))
	btn.grid(row=1, column=i)
	btns.append(btn)

for i, modifier in enumerate(functions):
	btn = HoverButton(button_area, text=beautify_str(modifier), command=lambda modifier=modifier: add_to_calc(modifier + "("))
	btn.grid(row=2, column=i)
	btns.append(btn)

for i, command in enumerate(commands):
	btn = HoverButton(button_area, text=command, command=(commands[command]))
	btn.grid(row=3, column=i)
	btns.append(btn)

for i, btn in enumerate(btns):
	btn.configure(
		fg=rainbow[i % len(rainbow)],
		activebackground=rainbow[i % len(rainbow)],
	)

# move_window()
root.mainloop()

