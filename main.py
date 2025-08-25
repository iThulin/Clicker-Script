import pyautogui
import time
import json
import random
from pynput import mouse
import tkinter as tk
from tkinter import filedialog, messagebox

click_sequence = []
recording_in_progress = False

# GUI Setup
root = tk.Tk()
root.title("Click Automator")
root.attributes("-topmost", True)

main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

button_frame = tk.Frame(main_frame)
button_frame.pack(side=tk.LEFT, padx=10)

status_frame = tk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
status_frame.pack(side=tk.RIGHT, padx=10)

# --- UI Elements ---
click_count_var = tk.IntVar(value=5)
repeat_count_var = tk.IntVar(value=1)

tk.Label(button_frame, text="Click Count:").pack()
tk.Spinbox(button_frame, from_=1, to=100, textvariable=click_count_var, width=5).pack(pady=(0, 10))

tk.Label(button_frame, text="Repeat Count:").pack()
tk.Spinbox(button_frame, from_=1, to=100, textvariable=repeat_count_var, width=5).pack(pady=(0, 10))

tk.Button(button_frame, text="Record Click Sequence", width=30, command=lambda: record_sequence(click_count_var.get())).pack(pady=5)
tk.Button(button_frame, text="Save Sequence to File", width=30, command=lambda: save_sequence()).pack(pady=5)
tk.Button(button_frame, text="Load Sequence from File", width=30, command=lambda: load_sequence()).pack(pady=5)
tk.Button(button_frame, text="Replay Sequence", width=30, command=lambda: replay_sequence(repeat_count_var.get())).pack(pady=5)
tk.Button(button_frame, text="Exit", width=30, command=root.quit).pack(pady=5)

status_title = tk.Label(status_frame, text="Replay Status", font=("Arial", 12, "bold"))
status_title.pack(pady=5)
step_label = tk.Label(status_frame, text="Step: -", font=("Arial", 10))
step_label.pack()
countdown_label = tk.Label(status_frame, text="Next click in: -", font=("Consolas", 10))
countdown_label.pack()
total_time_label = tk.Label(status_frame, text="Total elapsed: 0m 0.0s", font=("Consolas", 10))
total_time_label.pack()

recorded_label = tk.Label(status_frame, text="Recorded Clicks", font=("Arial", 10, "bold"))
recorded_label.pack(pady=(10, 0))
recorded_frame = tk.Frame(status_frame)
recorded_frame.pack(fill=tk.BOTH, expand=True)
recorded_scrollbar = tk.Scrollbar(recorded_frame)
recorded_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
recorded_listbox = tk.Listbox(recorded_frame, height=10, width=35, yscrollcommand=recorded_scrollbar.set)
recorded_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
recorded_scrollbar.config(command=recorded_listbox.yview)

# --- Core Functions ---
def wait_for_left_click():
    position = None
    def on_click(x, y, button, pressed):
        nonlocal position
        if pressed and button == mouse.Button.left:
            position = (x, y)
            return False
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    return position

def show_click_marker(x, y, size=20, duration=500):
    marker = tk.Toplevel()
    marker.overrideredirect(True)
    marker.attributes("-topmost", True)
    marker.lift()
    marker.geometry(f"{size}x{size}+{x - size // 2}+{y - size // 2}")
    transparent_color = "pink"
    marker.configure(bg=transparent_color)
    try:
        marker.wm_attributes("-transparentcolor", transparent_color)
    except:
        pass
    canvas = tk.Canvas(marker, width=size, height=size, highlightthickness=0, bg=transparent_color)
    canvas.pack()
    canvas.create_oval(2, 2, size - 2, size - 2, fill="red", outline="black")
    marker.after(duration, marker.destroy)

def record_sequence(num_clicks):
    global click_sequence, recording_in_progress
    if recording_in_progress:
        return
    recording_in_progress = True
    click_sequence = []
    recorded_listbox.delete(0, tk.END)

    last_time = None
    for i in range(num_clicks):
        step_label.config(text=f"Recording Step: {i+1}/{num_clicks}")
        countdown_label.config(text="Waiting for click...")
        root.update_idletasks()

        pos = wait_for_left_click()
        current_time = time.time()
        delay = current_time - last_time if last_time else 2.5
        last_time = current_time

        show_click_marker(pos[0], pos[1])
        click_sequence.append({"x": pos[0], "y": pos[1], "delay": delay})
        entry = f"{i + 1}:  x={pos[0]}  y={pos[1]}  delay={delay:.2f}s"
        recorded_listbox.insert(tk.END, entry)
        recorded_listbox.yview(tk.END)
        root.update_idletasks()

    step_label.config(text="Step: -")
    countdown_label.config(text="Next click in: -")
    recording_in_progress = False

def save_sequence():
    if not click_sequence:
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return
    with open(file_path, "w") as f:
        json.dump(click_sequence, f, indent=4)

def load_sequence():
    global click_sequence
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return
    with open(file_path, "r") as f:
        click_sequence = json.load(f)
    recorded_listbox.delete(0, tk.END)
    for i, step in enumerate(click_sequence):
        entry = f"{i + 1}:  x={step['x']}  y={step['y']}  delay={step['delay']:.2f}s"
        recorded_listbox.insert(tk.END, entry)

def replay_sequence(repeat):
    if not click_sequence:
        return
    total_steps = len(click_sequence) * repeat
    step_counter = 1
    total_elapsed_start = time.time()

    for i in range(repeat):
        for step in click_sequence:
            delay = step["delay"] + random.uniform(0.5, 1.0)
            elapsed = 0.0
            while elapsed < delay:
                remaining = delay - elapsed
                total_elapsed = time.time() - total_elapsed_start
                minutes = int(total_elapsed // 60)
                seconds = total_elapsed % 60
                step_label.config(text=f"Step: {step_counter} of {total_steps} (Loop {i+1}/{repeat})")
                countdown_label.config(text=f"Next click in: {remaining:.1f}s")
                total_time_label.config(text=f"Total elapsed: {minutes}m {seconds:.1f}s")
                root.update_idletasks()
                time.sleep(0.1)
                elapsed += 0.1

            drift_x = random.randint(-3, 3)
            drift_y = random.randint(-3, 3)
            x = step["x"] + drift_x
            y = step["y"] + drift_y

            pyautogui.moveTo(x, y)
            pyautogui.click()
            step_counter += 1

    step_label.config(text="Step: -")
    countdown_label.config(text="Next click in: -")
    total_time_label.config(text="Total elapsed: 0m 0.0s")

root.mainloop()
