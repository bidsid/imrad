import tkinter as tk
import threading
import time

# Function that runs in a background thread
def background_task():
    global stop_thread
    count = 0
    while not stop_thread:
        count += 1
        print(f"Background task running: {count}")
        time.sleep(1)  # Simulate some work being done

# Function to update the label every second using Tkinter's after()
def update_label():
    global label_text, root
    
    current_text = label_text.get()
    label_text.set(current_text + ".")  # Append a dot to the label text
    
    root.after(1000, update_label)  # Schedule the function to run again in 1 second

# Start the background thread when button is clicked
def start_thread():
    global stop_thread, background_thread
    stop_thread = False
    background_thread = threading.Thread(target=background_task)
    background_thread.start()

# Stop the background thread when button is clicked
def stop_thread_func():
    global stop_thread
    stop_thread = True

# Create the Tkinter GUI
root = tk.Tk()
root.title("Tkinter after() and Threading Test")
root.geometry("300x200")

# Create a label that will be updated periodically
label_text = tk.StringVar()
label_text.set("Waiting")
label = tk.Label(root, textvariable=label_text, font=("Helvetica", 16))
label.pack(pady=20)

# Create buttons to start and stop the background thread
start_button = tk.Button(root, text="Start Task", command=start_thread)
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Task", command=stop_thread_func)
stop_button.pack(pady=5)

# Start the label updater using Tkinter's after() function
root.after(1000, update_label)  # Schedule the first update in 1 second

# Global variables for the thread and control flag
stop_thread = False
background_thread = None

# Start the Tkinter event loop
root.mainloop()

# Wait for the background thread to finish before exiting
if background_thread is not None:
    background_thread.join()

