import pyautogui
import time
import json
import random
from pynput import mouse, keyboard
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

click_sequence = []
recording_in_progress = False
replay_stopped = False
recording_stopped = False

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

# --- UI Variables ---
click_count_var = tk.IntVar(value=5)
repeat_count_var = tk.IntVar(value=1)
min_delay_var = tk.DoubleVar(value=0.5)
max_delay_var = tk.DoubleVar(value=1.0)
infinite_recording_var = tk.BooleanVar(value=False)

# --- Button Panel ---
tk.Label(button_frame, text="Click Count:").pack()
tk.Spinbox(button_frame, from_=1, to=1000, textvariable=click_count_var, width=5).pack(pady=(0, 10))

tk.Checkbutton(button_frame, text="Infinite Recording", variable=infinite_recording_var).pack(pady=(0, 10))

tk.Label(button_frame, text="Repeat Count:").pack()
tk.Spinbox(button_frame, from_=1, to=100, textvariable=repeat_count_var, width=5).pack(pady=(0, 10))

delay_frame = tk.Frame(button_frame)
delay_frame.pack(pady=(0, 10))

tk.Label(delay_frame, text="Delay (Min / Max):").pack(side=tk.LEFT)
tk.Entry(delay_frame, textvariable=min_delay_var, width=5).pack(side=tk.LEFT, padx=2)
tk.Label(delay_frame, text="/").pack(side=tk.LEFT)
tk.Entry(delay_frame, textvariable=max_delay_var, width=5).pack(side=tk.LEFT, padx=2)

tk.Button(button_frame, text="Record Click Sequence", width=30, command=lambda: record_sequence(click_count_var.get())).pack(pady=5)
tk.Button(button_frame, text="Save Sequence to File", width=30, command=lambda: save_sequence()).pack(pady=5)
tk.Button(button_frame, text="Load Sequence from File", width=30, command=lambda: load_sequence()).pack(pady=5)
tk.Button(button_frame, text="Replay Sequence", width=30, command=lambda: replay_sequence(repeat_count_var.get())).pack(pady=5)
tk.Button(button_frame, text="Stop Replay / Recording (F12)", width=30, command=lambda: stop_replay()).pack(pady=5)
tk.Button(button_frame, text="Exit", width=30, command=root.quit).pack(pady=5)

# --- Status Panel ---
status_title = tk.Label(status_frame, text="Replay Status", font=("Arial", 12, "bold"))
status_title.pack(pady=5)

step_label = tk.Label(status_frame, text="Step: -", font=("Arial", 10))
step_label.pack()

countdown_label = tk.Label(status_frame, text="Next click in: -", font=("Consolas", 10))
countdown_label.pack()

total_time_label = tk.Label(status_frame, text="Total elapsed: 0.0s", font=("Consolas", 10))
total_time_label.pack()

loop_label = tk.Label(status_frame, text="Loop: -", font=("Arial", 10))
loop_label.pack()

time_remaining_label = tk.Label(status_frame, text="Est. remaining: -", font=("Arial", 10))
time_remaining_label.pack()

progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(status_frame, variable=progress_var, maximum=100, length=200)
progress_bar.pack(pady=(5, 10))

# --- Recorded Click Display ---
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

def record_sequence(num_clicks):
    global click_sequence, recording_in_progress, recording_stopped
    if recording_in_progress:
        return
    recording_in_progress = True
    recording_stopped = False
    click_sequence = []
    recorded_listbox.delete(0, tk.END)

    i = 0
    while (not recording_stopped) and (infinite_recording_var.get() or i < num_clicks):
        step_label.config(text=f"Recording Step: {i+1}/{'∞' if infinite_recording_var.get() else num_clicks}")
        countdown_label.config(text="Waiting for click...")
        root.update_idletasks()

        pos = wait_for_left_click()
        if recording_stopped:
            break

        delay = random.uniform(min_delay_var.get(), max_delay_var.get())
        click_sequence.append({"x": pos[0], "y": pos[1], "delay": delay})
        entry = f"{i + 1}:  x={pos[0]}  y={pos[1]}  delay={delay:.2f}s"
        recorded_listbox.insert(tk.END, entry)
        recorded_listbox.yview(tk.END)
        root.update_idletasks()
        i += 1

    reset_labels()
    recording_in_progress = False
    recording_stopped = False

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

def stop_replay():
    global replay_stopped, recording_stopped
    replay_stopped = True
    recording_stopped = True

def replay_sequence(repeat):
    global replay_stopped
    if not click_sequence:
        return

    replay_stopped = False
    step_counter = 1
    total_steps = len(click_sequence) * repeat
    total_elapsed_start = time.time()

    min_delay = min_delay_var.get()
    max_delay = max_delay_var.get()
    estimated_total_time = sum(step["delay"] + (min_delay + max_delay) / 2 for step in click_sequence) * repeat

    for i in range(repeat):
        loop_label.config(text=f"Loop: {i + 1} / {repeat}")
        for j, step in enumerate(click_sequence):
            if replay_stopped:
                reset_labels()
                return

            delay = step["delay"] + random.uniform(min_delay, max_delay)
            elapsed = 0.0
            while elapsed < delay:
                if replay_stopped:
                    reset_labels()
                    return

                remaining = delay - elapsed
                total_elapsed = time.time() - total_elapsed_start
                remaining_total = estimated_total_time - total_elapsed

                mins = int(total_elapsed) // 60
                secs = int(total_elapsed) % 60
                rmins = int(remaining_total) // 60
                rsecs = int(remaining_total) % 60

                step_label.config(text=f"Step: {step_counter} of {total_steps} (Loop {i+1}/{repeat})")
                countdown_label.config(text=f"Next click in: {remaining:.1f}s")
                total_time_label.config(text=f"Total elapsed: {mins}:{secs:02d} min")
                time_remaining_label.config(text=f"Est. remaining: {rmins}:{rsecs:02d} min")
                progress_percent = (step_counter - 1 + elapsed / delay) / total_steps * 100
                progress_var.set(progress_percent)

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

    reset_labels()

def reset_labels():
    step_label.config(text="Step: -")
    countdown_label.config(text="Next click in: -")
    total_time_label.config(text="Total elapsed: 0.0s")
    time_remaining_label.config(text="Est. remaining: -")
    loop_label.config(text="Loop: -")
    progress_var.set(0)

# Keyboard Shortcut Listener (F12)
def on_key_press(key):
    if key == keyboard.Key.f12:
        stop_replay()

keyboard.Listener(on_press=on_key_press).start()

# Start GUI loop
root.mainloop()
