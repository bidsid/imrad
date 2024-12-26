import tkinter as tk

# Sample list of scraped abstracts (replace this with your actual scraped data)
abstracts = [
    "Abstract 1: This study investigates the impact of climate change on marine ecosystems, showing a significant shift in biodiversity.",
    "Abstract 2: We explore quantum entanglement and its implications for future computing technologies in this comprehensive research.",
    "Abstract 3: This paper examines the role of AI in drug discovery, highlighting potential benefits and ethical challenges.",
    "Abstract 4: A novel approach to gene editing was introduced, demonstrating high accuracy and efficiency in CRISPR techniques.",
    "Abstract 5: The article discusses the latest findings in dark matter research, providing new insights into the composition of the universe.",
    "Abstract 6: This research focuses on the effects of microplastic pollution on freshwater ecosystems.",
    "Abstract 7: An in-depth analysis of gravitational waves and their impact on modern astrophysics.",
    "Abstract 8: The study presents new findings on renewable energy storage systems, emphasizing sustainability.",
    "Abstract 9: We delve into the relationship between biodiversity and ecosystem services in tropical rainforests.",
    "Abstract 10: A detailed review of the latest advancements in cancer immunotherapy and their clinical applications."
]

# Function to display a new abstract based on the current index
def display_abstract(index):
    # Get the abstract for the current scroll
    abstract_text = abstracts[index]
    
    # Update the label to display the abstract text
    abstract_label.config(text=abstract_text)

# Function to scroll to the next or previous abstract
def on_scroll(event):
    global current_abstract_index
    
    if event.num == 5 or event.delta < 0:  # Scroll down (next abstract)
        if current_abstract_index < len(abstracts) - 1:
            current_abstract_index += 1
    elif event.num == 4 or event.delta > 0:  # Scroll up (previous abstract)
        if current_abstract_index > 0:
            current_abstract_index -= 1
    
    # Display the new abstract
    display_abstract(current_abstract_index)

# Set up the main window
root = tk.Tk()
root.title("TikTok-Like App with Nature Article Abstracts")
root.geometry("400x700")

# Create a label to represent the abstract area
abstract_label = tk.Label(root, width=50, height=20, wraplength=380, justify="left", anchor="n")
abstract_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# Frame for buttons (like, comment, share)
button_frame = tk.Frame(root, bg='black', height=100)
button_frame.pack(fill=tk.X, side=tk.BOTTOM)

like_button = tk.Button(button_frame, text="❤️ Like", command=lambda: print("Liked!"))
like_button.pack(side=tk.LEFT, padx=10)

comment_button = tk.Button(button_frame, text="💬 Comment", command=lambda: print("Commented!"))
comment_button.pack(side=tk.LEFT, padx=10)

share_button = tk.Button(button_frame, text="📤 Share", command=lambda: print("Shared!"))
share_button.pack(side=tk.LEFT, padx=10)

# Initial abstract index
current_abstract_index = 0

# Display the first abstract
display_abstract(current_abstract_index)

# Bind the scroll events to move between abstracts
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

