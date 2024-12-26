import tkinter as tk
import threading
import requests
from bs4 import BeautifulSoup
import webbrowser
import random
import time

# Function to scrape abstracts from Nature's research articles with pagination
def scrape_nature_abstracts(page_number):
    try:
        print(f"Scraping abstracts from page {page_number}...")
        url = f"https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={page_number}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Check if request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the section containing the research articles
        articles = soup.find_all('article', class_='u-full-height c-card c-card--flush')
        if not articles:
            print(f"No articles found on page {page_number}.")

        scraped_abstracts = []

        # Iterate over the articles and extract abstracts
        for article in articles:
            title = article.find('h3', class_='c-card__title').get_text(strip=True)
            article_url = "https://www.nature.com" + article.find('a')['href']
            print(f"Scraping article: {title}")

            # Get the article page to extract the abstract
            article_response = requests.get(article_url, timeout=10)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            # Attempt to extract the abstract
            abstract_section = article_soup.find('div', {'class': 'c-article-section__content'})
            if abstract_section:
                abstract_text = abstract_section.get_text(strip=True)
                print(f"Abstract found for: {title}")
            else:
                abstract_text = "Abstract not available."
                print(f"No abstract available for: {title}")

            # Store title, abstract, and link
            scraped_abstracts.append({"title": title, "abstract": abstract_text, "url": article_url})

        return scraped_abstracts

    except (requests.RequestException, Exception) as e:
        print(f"Error fetching page {page_number}: {e}")
        return []

# Function to display a new abstract based on the current index
def display_abstract(index):
    if index < len(abstracts):
        abstract_data = abstracts[index]
        # Clear existing text
        abstract_label.config(state=tk.NORMAL)
        abstract_label.delete(1.0, tk.END)
        
        # Insert title in bold
        abstract_label.insert(tk.END, abstract_data['title'] + "\n\n", 'title')
        
        # Insert the abstract text
        abstract_label.insert(tk.END, abstract_data['abstract'])
        abstract_label.config(state=tk.DISABLED)
        print(f"Displayed abstract: {abstract_data['title']}")

# Function to open the article link in the browser
def open_article(event):
    abstract_data = abstracts[current_abstract_index]
    webbrowser.open(abstract_data['url'])
    print(f"Opened article URL: {abstract_data['url']}")

# Function to scroll to the next or previous abstract
def on_scroll(event):
    global current_abstract_index, current_page_number
    
    if event.num == 5 or event.delta < 0:  # Scroll down (next abstract)
        if current_abstract_index < len(abstracts) - 1:
            current_abstract_index += 1
        else:
            # Reached the end of current abstracts, load more
            current_page_number += 1
            print(f"Loading more abstracts from page {current_page_number}...")
            load_more_abstracts(current_page_number)

    elif event.num == 4 or event.delta > 0:  # Scroll up (previous abstract)
        if current_abstract_index > 0:
            current_abstract_index -= 1
    
    # Display the new abstract
    display_abstract(current_abstract_index)

# Function to load more abstracts when reaching the end
def load_more_abstracts(page_number):
    print(f"Loading more abstracts from page {page_number}...")
    new_abstracts = scrape_nature_abstracts(page_number)
    
    if new_abstracts:
        abstracts.extend(new_abstracts)  # Add new abstracts to the list
        current_abstract_index += 1      # Move to the next abstract
        display_abstract(current_abstract_index)
    else:
        print(f"No more abstracts to load or an error occurred on page {page_number}.")

# Background thread function to scrape abstracts
def background_task():
    global abstracts, current_page_number
    print(f"Starting background task to scrape abstracts from page {current_page_number}...")
    abstracts = scrape_nature_abstracts(current_page_number)
    if abstracts:
        print("Abstracts scraped successfully!")
    else:
        print("Failed to scrape abstracts.")

    # Update the UI after fetching abstracts
    root.after(0, on_loading_complete)

# Function to handle loading completion
def on_loading_complete():
    global loading
    loading = False
    print("Loading complete. Displaying first abstract...")
    display_abstract(current_abstract_index)  # Display the first abstract
    loading_label.pack_forget()  # Remove the loading label
    abstract_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # Show the abstract label

# Function to update the loading spinner
def update_loading_spinner():
    global loading_text
    current_text = loading_text.get()
    if current_text.endswith("...."):
        loading_text.set("Loading")
    else:
        loading_text.set(current_text + ".")
    
    # If loading is still active, schedule the next update
    if loading:
        root.after(500, update_loading_spinner)

# Start the background task
def start_loading():
    global loading, current_page_number
    loading = True
    current_page_number = random.randint(1, 100)  # Start from a random page number
    print(f"Starting loading spinner and background scraping from page {current_page_number}...")
    threading.Thread(target=background_task, daemon=True).start()  # Start in the background

# Initialize variables at the top of the script
current_abstract_index = 0
abstracts = []
loading = False

# Set up the main window
root = tk.Tk()
root.title("TikTok-Like App with Nature Article Abstracts")
root.geometry("400x700")

# Create a label for the loading text
loading_text = tk.StringVar()
loading_text.set("Loading")
loading_label = tk.Label(root, textvariable=loading_text, font=("Helvetica", 16))
loading_label.pack(pady=20)

# Create a text widget to represent the abstract area (hidden at start)
abstract_label = tk.Text(root, width=50, height=20, wrap=tk.WORD, bg='white', cursor="hand2", state=tk.DISABLED)
abstract_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
abstract_label.pack_forget()  # Hide the abstract label during loading

# Make the title bold
abstract_label.tag_configure('title', font=('Helvetica', 14, 'bold'))

# Frame for buttons (like, comment, share)
button_frame = tk.Frame(root, bg='black', height=100)
button_frame.pack(fill=tk.X, side=tk.BOTTOM)

like_button = tk.Button(button_frame, text="❤️ Like", command=lambda: print("Liked!"))
like_button.pack(side=tk.LEFT, padx=10)

comment_button = tk.Button(button_frame, text="💬 Comment", command=lambda: print("Commented!"))
comment_button.pack(side=tk.LEFT, padx=10)

share_button = tk.Button(button_frame, text="📤 Share", command=lambda: print("Shared!"))
share_button.pack(side=tk.LEFT, padx=10)

# Bind the scroll events to move between abstracts
def bind_scroll_events():
    if root.tk.call('tk', 'windowingsystem') == 'aqua':  # macOS
        root.bind("<MouseWheel>", on_scroll)
    else:  # Windows and Linux
        root.bind("<Button-4>", on_scroll)  # Scroll up
        root.bind("<Button-5>", on_scroll)  # Scroll down
        root.bind("<MouseWheel>", on_scroll)

# Bind the click event to open the article in the browser
abstract_label.bind("<Button-1>", open_article)

bind_scroll_events()

# Start the loading spinner and background task
update_loading_spinner()  # Start spinner animation
start_loading()           # Start the background loading

# Start the main loop of the Tkinter GUI
root.mainloop()

