import tkinter as tk
import threading
import requests
from bs4 import BeautifulSoup
import webbrowser
import random
import time
import re
import math
from collections import Counter
import atexit
import os
from datetime import datetime
import string

# Function to preprocess text
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


# Function to compute TF-IDF for the abstracts
def compute_tfidf(abstracts):
    print("Computing TF-IDF scores...")
    
    # Tokenize the abstracts
    tokenized_abstracts = [preprocess_text(abstract['abstract']).lower().split() for abstract in abstracts]
    
    # Calculate IDF for each term
    num_docs = len(tokenized_abstracts)
    term_doc_counts = Counter()
    
    for tokens in tokenized_abstracts:
        unique_terms = set(tokens)
        for term in unique_terms:
            term_doc_counts[term] += 1

    idf = {term: math.log(num_docs / (1 + count)) for term, count in term_doc_counts.items()}  # Smooth denominator
    
    # Compute TF-IDF for each abstract
    for abstract, tokens in zip(abstracts, tokenized_abstracts):
        tf = Counter(tokens)  # Term frequency for this abstract
        tfidf_scores = {term: tf[term] * idf[term] for term in tf}  # Combine TF and IDF
        
        # Save the TF-IDF score to the abstract dictionary
        abstract['tfidf'] = tfidf_scores
    
    print("TF-IDF computation complete.")

# Function to scrape a single random article from a given page
def scrape_random_article_from_page(page_number):
    try:
        print(f"Scraping a random article from page {page_number}...")
        url = f"https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={page_number}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Check if request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all articles on the page
        articles = soup.find_all('article', class_='u-full-height c-card c-card--flush')
        if not articles:
            print(f"No articles found on page {page_number}.")
            return None

        # Randomly select one article from the page
        article = random.choice(articles)
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

            # Remove reference numbers (e.g., [1], [10])
            #abstract_text = re.sub(r'\[\d+\]', '', abstract_text)
            abstract_text = re.sub(r'(\w)(\d+(,\d+)*)', r'\1', abstract_text)
            print(f"Abstract cleaned for: {title}")
        else:
            abstract_text = "Abstract not available."

        # Return the scraped article data
        return {"title": title, "abstract": abstract_text, "url": article_url}

    except (requests.RequestException, Exception) as e:
        print(f"Error scraping article from page {page_number}: {e}")
        return None

# Function to scrape a random sample of 20 articles from the first 1000 pages
def scrape_random_sample():
    print("Starting random sample scrape...")
    scraped_articles = []
    random_pages = random.sample(range(1, 1001), 20)  # Randomly select 20 unique page numbers

    for page_number in random_pages:
        article = scrape_random_article_from_page(page_number)
        if article:
            scraped_articles.append(article)
            article['score'] = 0 # added

        # Stop if we already have 20 articles
        if len(scraped_articles) == 20:
            break

    print(f"Scraped {len(scraped_articles)} articles.")
    return scraped_articles

# Function to display a new abstract based on the current index
def display_abstract(index):
    global last_scroll_time # added
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
        
        # added to give articles score based on how long on them
        time_spent = time.time() - last_scroll_time
        points = min(10, int(time_spent // 5))
        abstracts[index]['score'] += points
        last_scroll_time = last_scroll_time + time_spent

# added like button functionality
def like_article():
    global current_abstract_index
    abstracts[current_abstract_index]['score'] += 10

# Function to open the article link in the browser
def open_article(event):
    abstract_data = abstracts[current_abstract_index]
    webbrowser.open(abstract_data['url'])
    print(f"Opened article URL: {abstract_data['url']}")

# Function to scroll to the next or previous abstract
def on_scroll(event):
    global current_abstract_index

    if event.num == 5 or event.delta < 0:  # Scroll down (next abstract)
        if current_abstract_index < len(abstracts) - 1:
            current_abstract_index += 1
        else:
            print("No more articles to display.")

    elif event.num == 4 or event.delta > 0:  # Scroll up (previous abstract)
        if current_abstract_index > 0:
            current_abstract_index -= 1

    # Display the new abstract
    display_abstract(current_abstract_index)

# Background thread function to scrape abstracts
def background_task():
    global abstracts
    print("Starting background scrape task...")
    abstracts = scrape_random_sample()
    if abstracts:
        print("Abstracts scraped successfully! Computing TF-IDF...")
        compute_tfidf(abstracts)
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
    global loading
    loading = True
    print("Starting loading spinner and background scraping...")
    threading.Thread(target=background_task, daemon=True).start()  # Start in the background

# Function to print abstracts and scores and save top abstracts to a file
def print_abstracts_and_scores():
    print("\nFinal Abstracts and Scores:")
    top_abstracts = []

    for i, article in enumerate(abstracts):
        print(f"Article {i + 1}:")
        print(f"Title: {article['title']}")
        print(f"Score: {article['score']}")
        print(f"Abstract: {article['abstract']}\n")
        print(f"URL: {article['url']}")
        print("-" * 80)

        # Check if the article has a score of 15 or higher
        if article['score'] >= 15:
            top_abstracts.append(article)

    # Create a directory to store the save files
    save_dir = "abstracts_saves"
    os.makedirs(save_dir, exist_ok=True)

    # Generate a unique filename based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"top_abstracts_{timestamp}.txt")

    # Save up to 10 top abstracts to the new file
    if top_abstracts:
        with open(filename, "w", encoding="utf-8") as file:
            for idx, article in enumerate(top_abstracts[:10]):
                file.write(f"Article {idx + 1}:\n")
                file.write(f"Title: {article['title']}\n")
                file.write(f"Score: {article['score']}\n")
                file.write(f"Abstract: {article['abstract']}\n")
                file.write(f"URL: {article['url']}\n")
                file.write("-" * 80 + "\n")
        print(f"\nTop abstracts saved to '{filename}'.")
    else:
        print("\nNo abstracts scored 15 or higher to save.")

# Register the function to run when the program exits
atexit.register(print_abstracts_and_scores)

# Initialize variables at the top of the script
current_abstract_index = 0
abstracts = []
last_scroll_time = time.time()
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

button_frame = tk.Frame(root, bg='black', height=100)
button_frame.pack(fill=tk.X, side=tk.BOTTOM)
like_button = tk.Button(button_frame, text="❤️ Like", command=like_article)
like_button.pack(padx=10)

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
