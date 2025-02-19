import math
import threading
from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk

screen_direction = [1, 1]

calculation = ""
ans: str = "0"

def get_taskbar_height() -> int:
	# from (https://stackoverflow.com/questions/4357258/how-to-get-the-height-of-windows-taskbar-using-python-pyqt-win32)
	monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
	monitor_area = monitor_info.get("Monitor")
	work_area = monitor_info.get("Work")
	taskbar_height = monitor_area[3]-work_area[3]
	return taskbar_height

taskbar_height = get_taskbar_height()



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

