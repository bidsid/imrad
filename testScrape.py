import tkinter as tk
import requests
from bs4 import BeautifulSoup

# Function to scrape abstracts from Nature's most recent research articles
def scrape_nature_abstracts():
    url = "https://www.nature.com/nature/research-articles"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the section containing the most recent research articles
    articles = soup.find_all('article', class_='u-full-height c-card c-card--flush')

    abstracts = []

    # Iterate over the articles and extract abstracts
    for article in articles[:10]:  # Get only the 10 most recent articles
        title = article.find('h3', class_='c-card__title').get_text(strip=True)
        article_url = "https://www.nature.com" + article.find('a')['href']
        
        # Get the article page to extract the abstract
        article_response = requests.get(article_url)
        article_soup = BeautifulSoup(article_response.text, 'html.parser')

        # Attempt to extract the abstract
        abstract_section = article_soup.find('div', {'class': 'c-article-section__content'})
        if abstract_section:
            abstract_text = abstract_section.get_text(strip=True)
        else:
            abstract_text = "Abstract not available."

        # Store title and abstract
        abstracts.append(f"{title}: {abstract_text}")
    
    return abstracts

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

# Scrape the Nature articles and get the abstracts
abstracts = scrape_nature_abstracts()

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

