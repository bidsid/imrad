import tkinter as tk
import random

# Function to change the color of the square (simulating a video feed)
def change_color():
    # Generate a random color (R, G, B)
    random_color = f'#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}'
    
    # Change the color of the square (the video area)
    video_label.config(bg=random_color)
    
    # Schedule the function to run again after a short delay (to simulate "video frames")
    video_label.after(1000, change_color)

# Function for "Like" button press
def like_button_press():
    print("You liked this color!")

# Function for "Share" button press
def share_button_press():
    print("You shared this color!")

# Set up the main window
root = tk.Tk()
root.title("TikTok-Like App")
root.geometry("400x700")

# Frame for the "video" (a color-changing square)
video_frame = tk.Frame(root, width=400, height=500)
video_frame.pack()

# Label to represent the video (color square)
video_label = tk.Label(video_frame, width=50, height=25)
video_label.pack()

# Frame for buttons (like, comment, share)
button_frame = tk.Frame(root, bg='black', height=100)
button_frame.pack(fill=tk.X, side=tk.BOTTOM)

# Buttons (Simulating Like, Comment, Share)
like_button = tk.Button(button_frame, text="❤️ Like", command=like_button_press)
like_button.pack(side=tk.LEFT, padx=10)

comment_button = tk.Button(button_frame, text="💬 Comment", command=lambda: print("You commented!"))
comment_button.pack(side=tk.LEFT, padx=10)

share_button = tk.Button(button_frame, text="📤 Share", command=share_button_press)
share_button.pack(side=tk.LEFT, padx=10)

# Start the color-changing simulation
change_color()

# Start the main loop of the Tkinter GUI
root.mainloop()

