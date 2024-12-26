import tkinter as tk
import random

# Function to generate random hex color
def generate_random_color():
    return f'#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}'

# Function to display a new square based on the current index
def display_square(index):
    # Get the color for the current square
    color = square_colors[index]
    
    # Update the color of the main display square
    square_label.config(bg=color)

# Function to scroll to the next or previous square
def on_scroll(event):
    global current_square_index
    
    if event.num == 5 or event.delta < 0:  # Scroll down (next square)
        if current_square_index < len(square_colors) - 1:
            current_square_index += 1
    elif event.num == 4 or event.delta > 0:  # Scroll up (previous square)
        if current_square_index > 0:
            current_square_index -= 1
    
    # Display the new square
    display_square(current_square_index)

# Set up the main window
root = tk.Tk()
root.title("TikTok-Like App with Scrolling Squares")
root.geometry("400x700")

# List of random colors for the squares
num_squares = 10  # Adjust the number of squares as needed
square_colors = [generate_random_color() for _ in range(num_squares)]

# Create a label to represent the square (color-changing area)
square_label = tk.Label(root, width=400, height=500)
square_label.pack(fill=tk.BOTH, expand=True)

# Frame for buttons (like, comment, share)
button_frame = tk.Frame(root, bg='black', height=100)
button_frame.pack(fill=tk.X, side=tk.BOTTOM)

like_button = tk.Button(button_frame, text="❤️ Like", command=lambda: print("Liked!"))
like_button.pack(side=tk.LEFT, padx=10)

comment_button = tk.Button(button_frame, text="💬 Comment", command=lambda: print("Commented!"))
comment_button.pack(side=tk.LEFT, padx=10)

share_button = tk.Button(button_frame, text="📤 Share", command=lambda: print("Shared!"))
share_button.pack(side=tk.LEFT, padx=10)

# Initial square index
current_square_index = 0

# Display the first square
display_square(current_square_index)

# Bind the scroll events to move between squares
def bind_scroll_events():
    if root.tk.call('tk', 'windowingsystem') == 'aqua':  # macOS
        root.bind("<MouseWheel>", on_scroll)
    else:  # Windows and Linux
        root.bind("<Button-4>", on_scroll)  # Scroll up
        root.bind("<Button-5>", on_scroll)  # Scroll down
        root.bind("<MouseWheel>", on_scroll)

bind_scroll_events()

# Start the main loop of the Tkinter GUI
root.mainloop()

