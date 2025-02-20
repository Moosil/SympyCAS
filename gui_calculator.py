import threading

from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk
from sympy import *
from io import BytesIO
from PIL import Image, ImageTk

init_printing(full_prec=False)

screen_direction = [1, 1]

prev_calculation = ""
text_calculation = ""
Ans = symbols("Ans")


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
	global cursor_pos
	idx: int = 0
	parsed: list[str] = []
	expression_type: str = "equation"
	has_ans: bool = False
	
	# Add in brackets that are not closed
	brackets, left, right = get_brackets(text_calculation)
	if left > 0:
		text_calculation += "".join([")" for _i in range(left)])
	if right > 0:
		text_calculation = "".join(["(" for _i in range(right)]) + text_calculation
	
	for token in tokenise(text_calculation):
		match token:
			case ":=":
				expression_type = "define"
			case "Ans":
				has_ans = True
			case token if token.isalpha():
				symbols_mem[token] = symbols(token)
		parsed.append(token)
		idx += len(token)
	
	match expression_type:
		case "equation":
			symbol_equation = sympify(text_calculation)
			
			if has_ans:
				symbol_equation = sympify(symbol_equation).subs(Ans, prev_calculation)
			for fn_name, fn_symbolic in relations_mem:
				symbol_equation = sympify(symbol_equation).subs(fn_name, fn_symbolic)
			
			prev_calculation = symbol_equation
			obj = BytesIO()
			preview(symbol_equation, viewer='BytesIO', output='png', outputbuffer=obj, dvioptions=["-bd", "0", "-fg", f"RGB {hex_to_rgb(Text)}", "-bg", f"RGB {hex_to_rgb(Base)}", "-D", "240"])
			obj.seek(0)
			text_area[1].img = ImageTk.PhotoImage(Image.open(obj))
			text_area[1].config(image=text_area[1].img)
			
			if not exact:
				symbol_equation = symbol_equation.evalf().simplify().normal()
			
			text_calculation = str(symbol_equation)
			cursor_pos = len(text_calculation)
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
			
			relations_mem[name] = sympify("".join(parsed[idx:]))
			text_calculation = ""
			cursor_pos = 0
			update_text_calculation("Done")

cursor_pos: int = 0

def add_to_calc(val: str | int) -> None:
	global text_calculation
	global cursor_pos
	prefix: str = ""
	suffix: str = ""
	val = str(val)
	
	if len(val) != 0:
		if val in exacts:
			if len(text_calculation) - 1 >= cursor_pos + 1 >= 0 and \
			(text_calculation[cursor_pos + 1].isdigit() or text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos + 1] == "("):
				suffix = "*"
			if len(text_calculation) - 1 >= cursor_pos - 1 >= 0 and \
			(text_calculation[cursor_pos - 1].isdigit() or text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos - 1] == ")"):
				prefix = "*"
		elif val.isdigit():
			if len(text_calculation) - 1 >= cursor_pos + 1 >= 0 and \
					(text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos + 1] == "("):
				suffix = "*"
			if len(text_calculation) - 1 >= cursor_pos - 1 >= 0 and \
					(text_calculation[cursor_pos - 1] in exacts or text_calculation[cursor_pos - 1] == ")"):
				prefix = "*"
	
	text_calculation = text_calculation[:cursor_pos] + prefix + val + suffix + text_calculation[cursor_pos:]
	update_text_calculation()
	cursor_pos += len(prefix) + len(val) + len(suffix)

def update_text_calculation(calc: str | None = None) -> None:
	global text_calculation
	calc = str(calc if calc is not None else text_calculation)
	text_area[0].delete(1.0, tk.END)
	text_area[0].insert(1.0, beautify_str(calc))
	brackets, left, right = get_brackets(text_calculation)
	for bracket in brackets:
		text_area[0].tag_add(rainbow[bracket[1]], f"1.{bracket[0]}", f"1.{bracket[0] + 1}")
	if left > 0:
		text_area[0].insert("1.end", "".join([")" for _i in range(left)]))
		text_area[0].tag_add(Overlay1, f"1.end-{left}c", "1.end")
	if right > 0:
		text_area[0].insert("1.0", "".join(["(" for _i in range(right)]))
		text_area[0].tag_add(Overlay1, f"1.0", f"1.{right}")

def backspace_calc(calc: str | None = None) -> None:
	global text_calculation
	global cursor_pos
	text_calculation = text_calculation[:cursor_pos - 1] + text_calculation[cursor_pos:]
	cursor_pos -= 1
	update_text_calculation()

def clear_calc() -> None:
	global text_calculation
	text_calculation = ""
	text_area[0].delete(1.0, tk.END)

def beautify_str(string: str) -> str:
	new_string: str = ""
	i: int = 0
	while i <= len(string) - 1:
		added: bool = False
		for j in range(max_repl, 0, -1):
			if i+j <= len(string) and string[i:i+j] in repl:
				new_string += repl[string[i:i+j]]
				i += j - 1
				added = True
				break
		if not added:
			new_string += string[i]
		i += 1
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

repl = {
	"/": "÷",
	"*": "×",
	"E": "e",
	"**": "^",
}

max_repl = max([len(key) for key in repl.keys()])

modifiers = {
	"+": "+",
	"-": "-",
	"/": "÷",
	"*": "×",
	"**(": "⬚^",
	"**2)": "⬚²",
	"sqrt(": "√⬚",
	"(": "(",
	")": ")",
}

functions = {
	"sin(": "sin",
	"cos(": "cos",
	"tan(": "tan",
}

exacts = {
	"π": "π",
	"Ans": "Ans",
	"E": "e",
}

commands = {
	"=": solve,
	"≈": lambda: solve(False),
	"C": clear_calc,
	"⌫": backspace_calc,
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
rows: int = 5

root = tk.Tk()
root.title("Calculator")
root.geometry(f"{70*base}x{41*2+64*rows}")
root.minsize(70*base, 41*2+64*rows)
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
		self.lines: list[tk.Text | tk.Label] = [
			tk.Text(self, height=1, width=16, font=(font, font_size), bg=Base, fg=Text, highlightthickness=0, borderwidth=0),
			tk.Label(self, height=3, width=16, bg=Base, fg=Text, highlightthickness=0, borderwidth=0)
		]
		self.lines[0].grid(column=0, row=0, sticky=tk.EW)
		self.lines[1].grid(column=0, row=1, sticky=tk.NSEW)
		
		for colour in rainbow:
			self.lines[0].tag_config(colour, foreground=colour)
		self.lines[0].tag_config(Overlay1, foreground=Overlay1)
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=1)
	
	def __getitem__(self, item):
		return self.lines[item]
			

text_area = TextArea(root, bg=Base)
text_area.grid(column=0, row=0, sticky=tk.NSEW)
button_area = tk.Frame(root, bg=Base)
button_area.grid(column=0, row=1, sticky=tk.EW)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
btns: list[tk.Button] = []

class HoverButton(tk.Button):
	def __init__(self, master, **kwargs):
		tk.Button.__init__(self,master=master, font=(font, font_size),width=4, bg=Surface0, activeforeground=Mantle, borderwidth=0, **kwargs)
		self.bind("<Enter>", self.on_enter)
		self.bind("<Leave>", self.on_leave)
	
	def on_enter(self, _e):
		self['background'] = Overlay0
	
	def on_leave(self, _e):
		self['background'] = Surface0
  
for i in range(base):
	btn = HoverButton(button_area, text=str(i), command=lambda i=i: add_to_calc(i))
	btn.grid(row=0, column=i)
	btns.append(btn)

UI_order: list = \
[
	modifiers,
	exacts,
	functions,
]

for i, names in enumerate(UI_order):
	for j, (plain, fancy) in enumerate(names.items()):
		btn = HoverButton(button_area, text=fancy, command=lambda plain=plain: add_to_calc(plain))
		btn.grid(row=i+1, column=j)
		btns.append(btn)

for i, command in enumerate(commands):
	btn = HoverButton(button_area, text=command, command=(commands[command]))
	btn.grid(row=4, column=i)
	btns.append(btn)

for i, btn in enumerate(btns):
	btn.configure(
		fg=rainbow[i % len(rainbow)],
		activebackground=rainbow[i % len(rainbow)],
	)


# move_window()
root.mainloop()

