import math
import threading
from win32api import GetMonitorInfo, MonitorFromPoint
from fractions import Fraction
from decimal import Decimal, getcontext
import tkinter as tk
from typing import Union

getcontext().prec = 6
screen_direction = [1, 1]

calculation = ""
ans: str = "0"


class NaN:
	def __init__(self):
		pass

class Function:
	def __init__(self, rule: callable, gives_exact):
		self.rule = rule
		self.gives_exact = gives_exact
	
	def get_value(self, *args: Union[list[Union[Fraction, 'Function', 'Symbol', 'Exact']], Fraction, 'Function', 'Symbol', 'Exact']) -> Union[Fraction, 'Exact']:
		is_exact = True
		for arg in args:
			if not isinstance(arg, Fraction):
				is_exact = False
				break
		if is_exact:
			return Fraction(Decimal(self.rule(args)))
		else:
			new_args: list[list[Fraction | 'Function' | 'Symbol' | 'Exact']] = []
			for arg in args:
				if isinstance(arg, list):
					new_args.append(arg)
				else:
					new_args.append([arg])
			return Exact(
				f"{self.__class__.__name__}({",".join([str(arg) for arg in args])})",
				[self, Symbol('(')] + new_args + [Symbol(')')]
			)

class Sin(Function):
	def __init__(self):
		super().__init__(math.sin, False)

class Symbol:
	def __init__(self, symbol: str):
		self.symbol = symbol
	
	def __repr__(self):
		return f"Symbol('{self.symbol}')"
	
	def __str__(self):
		return self.symbol

class Exact:
	def __init__(self, name: str, expr: list[Union[Fraction, Function, Symbol, 'Exact']] | float):
		self.name = name
		self.expr = expr
	
	def get_value(self) -> Fraction:
		if isinstance(self.expr, list):
			return _solve(self.expr)
		elif isinstance(self.expr, float):
			return Fraction(self.expr)
	
	def __repr__(self):
		if isinstance(self.expr, list):
			return f"Symbol('{self.name}'={"".join(self.expr)})"
		elif isinstance(self.expr, float):
			return f"Symbol('{self.name}'={self.expr})"
	
	def __str__(self):
		return self.get_value()

functions: dict = {
	"sin": Sin()
}

def get_function(name: str) -> Function:
	return functions[name]

def get_taskbar_height() -> int:
	# from (https://stackoverflow.com/questions/4357258/how-to-get-the-height-of-windows-taskbar-using-python-pyqt-win32)
	monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
	monitor_area = monitor_info.get("Monitor")
	work_area = monitor_info.get("Work")
	taskbar_height = monitor_area[3]-work_area[3]
	return taskbar_height

taskbar_height = get_taskbar_height()

def solve(is_decimal: bool = False) -> None:
	global calculation
	global ans
	parsed = parse_calculation(calculation)
	new_ans: list[Fraction | str] | NaN | str
	if isinstance(parsed, NaN):
		new_ans = NaN()
	else:
		new_ans = _solve(parsed)
	calculation = ""
	if isinstance(new_ans, NaN):
		ans = 0
		calculation = str('NaN')
		update_text_calculation()
		return
	
	if isinstance(new_ans, Fraction):
		ans = new_ans
		calculation = str(ans)
		if is_decimal:
			text_result.delete("1.0", tk.END)
			text_result.insert(1.0, "".join([beautify(c) for c in str(Decimal(float(ans)))]))
		else:
			update_text_calculation()
	else:
		TypeError(f"ans is not a Fraction (is {type(ans)}): {ans}")
		return


def parse_calculation(calc: str) -> list[Fraction | Symbol | Function | Exact] | NaN:
	if calc.find('NaN') != -1:
		return NaN()
	calc = calc.replace("Ans", "(" + str(ans) + ")")
	curr: str = ""
	parsed: list[Fraction | Symbol | Function | Exact] = []
	
	prev_type: str = ""
	for char in calc:
		curr_type: str
		if char.isdigit():
			curr_type = "number"
		elif char.isalpha():
			curr_type = "function"
		else:
			curr_type = "symbol"
			if prev_type == "symbol":
				if curr in exacts:
					parsed.append(Exact(exacts[curr]))
				else:
					parsed.append(Symbol(curr))
				if curr == ")":
					parsed.append(Symbol("*"))
				curr = ""
		
		if prev_type == curr_type or prev_type == "":
			curr += char
		else:
			if len(curr) != 0:
				match prev_type:
					case "number":
						parsed.append(Fraction(curr))
						if curr_type == "symbol" and char == "(":
							parsed.append(Symbol("*"))
					case "function":
						parsed.append(get_function(curr))
					case "symbol":
						if curr == "number" and parsed[len(parsed) - 1].symbol == "(":
							parsed.append(Symbol("*"))
						if curr in exacts:
							parsed.append(Exact(exacts[curr]))
						else:
							parsed.append(Symbol(curr))
			curr = char
		
		prev_type = curr_type
		
	if len(curr) != 0:
		match prev_type:
			case "number":
				parsed.append(Fraction(curr))
			case "function":
				parsed.append(get_function(curr))
			case "symbol":
				if curr == "number" and parsed[len(parsed) - 1].symbol == "(":
					parsed.append(Symbol("*"))
				if curr in exacts:
					parsed.append(Exact(exacts[curr]))
				else:
					parsed.append(Symbol(curr))
	return parsed


def _solve(calc: list[Fraction | Symbol | Function | Exact]) -> Fraction | Exact | NaN:
	n: int = len(calc)
	i: int
	brackets = (
		next((i for i in range(n) if isinstance(calc[i], Symbol) and calc[i].symbol == "("), -1),
		next((i for i in range(n) if isinstance(calc[i], Symbol) and calc[i].symbol == ")"), -1)
	)
	if brackets[0] != -1:
		if brackets[1] != -1:
			if brackets[0] != 0 and isinstance(calc[brackets[0] - 1], Function):
				fn: Function = calc[brackets[0] - 1]
				middle = _solve(calc[brackets[0] + 1:brackets[1]])
				if isinstance(middle, NaN):
					return NaN()
				elif isinstance(middle, Fraction):
					return _solve(calc[:brackets[0] - 1] + [fn.get_value(middle)] + calc[brackets[1] + 1:])
				else:
					ValueError("middle is not a valid data type")
			else:
				middle = _solve(calc[brackets[0] + 1:brackets[1]])
				if isinstance(middle, NaN):
					return NaN()
				elif isinstance(middle, Fraction):
					return _solve(calc[:brackets[0]] + [middle] + calc[brackets[1] + 1:])
				else:
					ValueError("middle is not a valid data type")
		else:
			if brackets[0] != 0 and isinstance(calc[brackets[0] - 1], Function):
				fn: Function = calc[brackets[0] - 1]
				right = _solve(calc[brackets[0] + 1:])
				if isinstance(right, NaN):
					return NaN()
				elif isinstance(right, Fraction):
					return _solve(calc[:brackets[0] - 1] + [fn.get_value(right)])
				else:
					ValueError("right is not a valid data type")
			else:
				right: Fraction | list[Fraction | str] | NaN = _solve(calc[brackets[0] + 1:])
				if isinstance(right, NaN):
					return NaN()
				elif isinstance(right, Fraction):
					return _solve(calc[:brackets[0]] + [right])
				else:
					ValueError("right is not a valid data type")
	
	div_mult = next((i for i in range(n) if isinstance(calc[i], Symbol) and calc[i].symbol == dmas[0]), -1)
	new = next((i for i in range(div_mult if div_mult != -1 else n) if isinstance(calc[i], Symbol) and calc[i].symbol == dmas[1]), -1)
	if new != -1:
		div_mult = new
	
	if div_mult != -1:
		middle: Fraction
		if calc[div_mult].symbol == dmas[0]:
			if calc[div_mult + 1] == 0:
				return NaN()
			else:
				middle = calc[div_mult - 1] / calc[div_mult + 1]
		else:
			middle = calc[div_mult - 1] * calc[div_mult + 1]
		return _solve(calc[:div_mult - 1] + [middle] + calc[div_mult + 2:])
	
	add_sub = next((i for i in range(n) if isinstance(calc[i], Symbol) and calc[i].symbol == dmas[2]), -1)
	new = next((i for i in range(add_sub if add_sub != -1 else n) if isinstance(calc[i], Symbol) and calc[i].symbol == dmas[3]), -1)
	negative = False
	if new == 0:
		new = next((i for i in range(1, add_sub if add_sub != -1 else n) if isinstance(calc[i], Symbol) and calc[i].symbol == dmas[3]), -1)
		negative = True
	if new != -1:
		add_sub = new
	
	if add_sub != -1:
		middle: Fraction
		if calc[add_sub].symbol == dmas[2]:
			middle = calc[add_sub - 1] + calc[add_sub + 1]
		else:
			middle = calc[add_sub - 1] - calc[add_sub + 1]
		return _solve(calc[:add_sub - 1 - (1 if negative else 0)] + [middle] + calc[add_sub + 2:])
	
	if len(calc) == 1:
		if isinstance(calc[0], Fraction):
			return calc[0]
		else:
			ValueError("calc is not a fraction")
	else:
		ValueError("calc is not fully solved")


def add_to_calc(val: str | int) -> None:
	global calculation
	prefix = ""
	if val == "(" and len(calculation) != 0 and calculation[len(calculation) - 1].isdigit():
		prefix = "*"
	calculation += prefix + str(val)
	update_text_calculation()


def update_text_calculation() -> None:
	text_result.delete(1.0, tk.END)
	text_result.insert(1.0, "".join([beautify(c) for c in calculation]))


def clear_calc() -> None:
	global calculation
	calculation = ""
	text_result.delete(1.0, tk.END)


def mult(lhs: int, rhs: int) -> int:
	return lhs * rhs


def beautify(symbol: str) -> str:
	for b in repl:
		if b[0] == symbol:
			return b[1]
	return symbol


base = 10

repl = [
	("/", "÷"),
	("*", "×"),
]

modifiers = [
	"(",
	")",
	"Ans",
	"sin(",
]

exacts = {
	"π": math.pi,
	"e": math.e
}

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
root.geometry(f"{70*base}x{272}")
root.minsize(70*base, 272)
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

text_result = tk.Text(root, height=2, width=16, font=(font, font_size), bg=Base, fg=Text, highlightthickness=0, borderwidth=0)
text_result.pack(expand=True, fill="both")
button_area = tk.Frame(root, bg=Base)
button_area.pack()
btns: list[tk.Button] = []

class HoverButton(tk.Button):
	def __init__(self, master, **kw):
		tk.Button.__init__(self,master=master, font=(font, font_size),width=4, bg=Surface0, activeforeground=Mantle, borderwidth=0, **kw)
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

for i, modifier in enumerate(dmas + modifiers + list(exacts.keys())):
	btn = HoverButton(button_area, text=beautify(modifier), command=lambda modifier=modifier: add_to_calc(modifier))
	btn.grid(row=1, column=i)
	btns.append(btn)

for i, command in enumerate(commands):
	btn = HoverButton(button_area, text=command, command=(commands[command]))
	btn.grid(row=2, column=i)
	btns.append(btn)

for i, btn in enumerate(btns):
	btn.configure(
		fg=rainbow[i % len(rainbow)],
		activebackground=rainbow[i % len(rainbow)],
	)

move_window()
root.mainloop()

