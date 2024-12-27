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
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import glob
import logging

# File to store next articles to preload
PRELOAD_FILE = "next_articles.json"
FURTHEST_NATURE_DIRECTORY_PAGE = 1000
ABSTRACT_SAVE_CUTOFF_SCORE = 15
SAVE_DIRECTORY = "saved_abstracts"
NUM_FILES_TO_SAVE_TO_PRELOAD = 20
SIZE_OF_LOAD_BATCH = 5
MAX_UNSEEN_FILES_LOADED_IN = 50
MAX_SAVED_BEST_ABSTRACTS_PER_SESSION = 10
MAX_NUM_SAVED_BEST_FILES = 8
VIEW_POINT_HOW_OFTEN = 5    # in seconds
MAX_VIEW_POINTS = 10
LIKE_POINTS = 10
CLICK_POINTS = 20

# Function to preprocess text
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text

def load_saved_abstracts(directory="saved_abstracts"):
    saved_abstracts = []
    if os.path.exists(directory):
        for file_name in os.listdir(directory):
            with open(os.path.join(directory, file_name), "r") as file:
                data = json.load(file)
                saved_abstracts.append(data['abstract'])  # Assuming 'abstract' key in saved files
    return saved_abstracts

def rank_articles_by_similarity_with_saved_corpus(scraped_articles, saved_corpus):
    # Preprocess the saved corpus and scraped abstracts
    saved_corpus = [preprocess_text(abstract) for abstract in saved_corpus]
    scraped_texts = [preprocess_text(article['abstract']) for article in scraped_articles]

    # Check for empty corpus
    if not saved_corpus or all(len(text.strip()) == 0 for text in saved_corpus):
        logger.warning("Error: No valid abstracts in the saved corpus. Cannot compute similarity.")
        return [(article) for article in scraped_articles]

    if not scraped_texts or all(len(text.strip()) == 0 for text in scraped_texts):
        logger.warning("Error: No valid scraped articles for ranking. Returning original order.")
        return [(article) for article in scraped_articles]

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    try:
        corpus_tfidf = vectorizer.fit_transform(saved_corpus)  # Fit on the saved corpus
        articles_tfidf = vectorizer.transform(scraped_texts)  # Transform scraped abstracts
    except ValueError as e:
        logger.warning("Error computing TF-IDF: %s", e)
        return [(article) for article in scraped_articles]

    # Compute similarity between each scraped article and the saved corpus
    similarity_scores = cosine_similarity(articles_tfidf, corpus_tfidf).mean(axis=1)

    # Combine scraped articles with their similarity scores
    ranked_articles = sorted(
        zip(scraped_articles, similarity_scores),
        key=lambda x: x[1],
        reverse=True  # Sort by descending similarity
    )
       
    just_articles = []
    for item in ranked_articles:
        just_articles.append(item[0])
    return just_articles

# Function to scrape a single random article from a given page
def scrape_random_article_from_page(page_number):
    try:
        logger.info("Scraping a random article from page %s...", page_number)
        url = f"https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={page_number}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Check if request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all articles on the page
        articles = soup.find_all('article', class_='u-full-height c-card c-card--flush')
        if not articles:
            logger.info("No articles found on page %s.", page_number)
            return None

        # Randomly select one article from the page
        article = random.choice(articles)
        title = article.find('h3', class_='c-card__title').get_text(strip=True)
        article_url = "https://www.nature.com" + article.find('a')['href']
        logger.info("Scraping article: %s", title)

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
            logger.info("Abstract cleaned for: %s", title)
        else:
            abstract_text = "Abstract not available."

        # Return the scraped article data
        return {"title": title, "abstract": abstract_text, "url": article_url, "score": 0, "liked": False}

    except (requests.RequestException, Exception) as e:
        logger.warning("Error scraping article from page %s: %s", page_number, e)
        return None

# Function to scrape a random sample of articles from the first FURTHEST_NATURE_DIRECTORY_PAGE pages
def scrape_random_sample(sample_size=10):
    logger.info("Starting random sample scrape of size %s...", sample_size)
    scraped_articles = []
    random_pages = random.sample(range(1, FURTHEST_NATURE_DIRECTORY_PAGE + 1), sample_size)  # Randomly select unique page numbers

    for page_number in random_pages:
        article = scrape_random_article_from_page(page_number)
        if article:
            scraped_articles.append(article)

        # Stop if we already have 10 articles
        if len(scraped_articles) == sample_size:
            break

    logger.info("Scraped %s articles.", len(scraped_articles))
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
        logger.info("Displayed abstract: %s", abstract_data['title'])

        # added to give articles score based on how long on them
        time_spent = time.time() - last_scroll_time
        points = min(10, int(time_spent // 5))
        abstracts[index]['score'] += points
        last_scroll_time = last_scroll_time + time_spent
       
        if abstracts[current_abstract_index]['liked']:
            like_button.config(state=tk.DISABLED)
        else:
            like_button.config(state=tk.NORMAL)

# added like button functionality
def like_article():
    global current_abstract_index
    abstracts[current_abstract_index]['score'] += LIKE_POINTS
    abstracts[current_abstract_index]['liked'] = True
    like_button.config(state=tk.DISABLED)
   

# Function to open the article link in the browser
def open_article(event):
    abstract_data = abstracts[current_abstract_index]
    abstract_data['score'] += CLICK_POINTS
    webbrowser.open(abstract_data['url'])
    logger.info("Opened article URL: %s", abstract_data['url'])

# Modify the scroll function to trigger loading more articles
def on_scroll(event):
    global current_abstract_index, last_seen_index

    if event.num == 5 or event.delta < 0:  # Scroll down (next abstract)
        if current_abstract_index < len(abstracts) - 1:
            current_abstract_index += 1

            # Load more articles if scrolled 5 and number of unseen < 50
            num_unseen_abstracts = len(abstracts) - last_seen_index - 1
            if current_abstract_index % 5 == 0 and num_unseen_abstracts < MAX_UNSEEN_FILES_LOADED_IN:
                threading.Thread(target=load_more_articles_and_rank, daemon=True).start()

        else:
            logger.warning("No more articles to display.")

    elif event.num == 4 or event.delta > 0:  # Scroll up (previous abstract)
        if current_abstract_index > 0:
            current_abstract_index -= 1

    # Display the new abstract
    display_abstract(current_abstract_index)
    if current_abstract_index > last_seen_index:
        last_seen_index = current_abstract_index

# Background thread function to scrape abstracts
def background_task():
    global abstracts, saved_abstracts, loading_more_articles
    logger.info("Starting background scrape task...")
    loading_more_articles = True
    abstracts = scrape_random_sample()
    if abstracts:
        logger.info("Abstracts scraped successfully!")
    else:
        logger.warning("Failed to scrape abstracts.")
   
    loading_more_articles = False
    # Update the UI after fetching abstracts
    root.after(0, on_loading_complete)

# Function to handle loading completion
def on_loading_complete():
    global loading
    loading = False
    logger.info("Loading complete. Displaying first abstract...")
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
    logger.info("Starting loading spinner and background scraping...")
    threading.Thread(target=background_task, daemon=True).start()  # Start in the background
    update_loading_spinner()

# Function to dynamically load and rank more articles
def load_more_articles_and_rank(num_articles=10):
    global abstracts, saved_abstracts, seen_titles, loading_more_articles, current_abstract_index, last_seen_index
    if loading_more_articles:
        logger.warning("Already loading more articles, skipping new thread.")
        return

    loading_more_articles = True  # Set the flag
    logger.info("Loading more articles...")
    try:
        new_articles = scrape_random_sample(num_articles)

        # Get unseen articles from the abstracts list after the current index
        unseen_existing_articles = abstracts[last_seen_index + 1:]
        '''
        unseen_existing_articles = [
            article for article in abstracts[last_seen_index + 1:]

            if article['title'] not in seen_titles
        ]
        '''
       
        # Filter out duplicates from the newly scraped articles
        unique_new_articles = [
            article for article in new_articles
            if article['title'] not in seen_titles
        ]

        # Combine unseen existing articles and unique new articles
        combined_articles = unseen_existing_articles + unique_new_articles

        if not combined_articles:
            logger.warning("No new unique articles found.")
            return

        # Add titles of combined articles to seen set
        for article in combined_articles:
            seen_titles.add(article['title'])

        # Rank the combined articles against the saved corpus
        ranked_articles = rank_articles_by_similarity_with_saved_corpus(combined_articles, saved_abstracts)

        # Replace abstracts list with seen articles up to the current index,

        # then add ranked unseen articles
        abstracts = abstracts[:last_seen_index + 1] + ranked_articles

        logger.info("Re-ranked %s articles, combining unseen and new.", len(ranked_articles))
    except Exception as e:
        raise(e)
        logger.warning("Error while loading and ranking more articles: %s", e)
    finally:
        loading_more_articles = False  # Reset the flag

def load_saved_abstracts_json(directory="saved_abstracts"):
    saved_abstracts = []
    if not os.path.exists(directory):
        return saved_abstracts  # Return empty list if no directory exists

    for file in os.listdir(directory):
        if file.endswith(".json"):
            with open(os.path.join(directory, file), 'r') as f:
                try:
                    data = json.load(f)
                    saved_abstracts.extend(preprocess_text(article["abstract"]) for article in data)
                except json.JSONDecodeError as e:
                    logger.warning("Error loading JSON file %s: %s", file, e)

    return saved_abstracts

def remove_oldest_file(directory):
    """
    Removes the oldest file from the specified directory.
    """
    try:
        # List all files in the directory
        files = glob.glob(os.path.join(directory, "*"))

        if not files:
            logger.info("No files to remove.")
            return

        # Find the file with the oldest modification time
        oldest_file = min(files, key=os.path.getmtime)
       
        # Remove the oldest file
        os.remove(oldest_file)
        logger.info("Removed the oldest file: %s", oldest_file)

    except Exception as e:
        logger.warning("Error while removing the oldest file: %s", e)

def save_top_abstracts_json(abstracts, directory="saved_abstracts"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(directory, f"top_abstracts_{timestamp}.json")
   
    top_abstracts = [
        {
            "title": abstract['title'],
            "abstract": preprocess_text(abstract['abstract']),
            "score": abstract['score'],
            "url": abstract['url']
        }
        for abstract in abstracts if abstract['score'] >= ABSTRACT_SAVE_CUTOFF_SCORE
    ]
   
    if top_abstracts:
        # Save only up to 10 top abstracts
        top_abstracts = sorted(top_abstracts, key=lambda x: x['score'], reverse=True)[:10]
       
        if len(os.listdir(directory)) >= MAX_NUM_SAVED_BEST_FILES:
            remove_oldest_file(directory)
            logger.info("Removed the oldest file in %s to make room for another.", directory)

        with open(save_path, 'w') as f:
            json.dump(top_abstracts, f, indent=4)

        logger.info("Saved %s abstracts to %s", len(top_abstracts), {save_path})
    else:
        logger.info("No articles with high enough score to save. Not saving.")

# Function to preload saved articles
def load_preloaded_articles():
    if os.path.exists(PRELOAD_FILE):
        try:
            with open(PRELOAD_FILE, "r") as file:
                preloaded_articles = json.load(file)
                logger.info("Loaded %s preloaded articles.", len(preloaded_articles))
                return preloaded_articles
        except Exception as e:
            logger.warning("Error loading preloaded articles: %s", e)
    return []

# Function to save next articles for preload
def save_next_articles(articles):
    try:
        with open(PRELOAD_FILE, "w") as file:
            json.dump(articles, file)
            logger.info("Saved %s articles for next preload.", len(articles))
    except Exception as e:
        logger.warning("Error saving preloaded articles: %s", e)
        raise(e)

# Modify the exit function to preload articles
def save_next_and_exit():
    global abstracts, current_abstract_index, last_seen_index
    while loading_more_articles:
        time.sleep(0.5)
    logger.debug("No longer loading more articles normally. Loading for preload now.")
    num_remaining_articles = len(abstracts) - last_seen_index - 1
    if (num_remaining_articles < NUM_FILES_TO_SAVE_TO_PRELOAD):
        logger.debug("Stats before:")
        logger.debug("Last seen index: %s", last_seen_index)
        logger.debug("length of abstracts list: %s", len(abstracts))
        logger.debug("Number of remaining articles: %s", num_remaining_articles)
        last_seen_index = len(abstracts) - 1 # to make load_more_articles_and_rank work
        load_more_articles_and_rank(NUM_FILES_TO_SAVE_TO_PRELOAD - num_remaining_articles)
        save_next_articles(abstracts[-NUM_FILES_TO_SAVE_TO_PRELOAD:])
    else:
        save_next_articles(abstracts[last_seen_index + 1: last_seen_index + NUM_FILES_TO_SAVE_TO_PRELOAD + 1])
    logger.debug("Stats after:")
    logger.debug("Last seen index: %s", last_seen_index)
    logger.debug("length of abstracts list: %s", len(abstracts))
    logger.debug("Number of remaining articles: %s", num_remaining_articles)
    logger.info("Program exiting.")

# Saves the top abstracts to a file for future comparison, saves unseen abstracts
# to preload for next time, and does some final logging
def cleanup():
    save_top_abstracts_json(abstracts)
    save_next_and_exit()
   
    print("\n")
    logger.info("Final Abstracts and Scores:")

    for i, article in enumerate(abstracts):
        logger.info("Article %s:", i + 1)
        logger.info("Title: %s", article['title'])
        logger.info("Score: %s", article['score'])
        logger.info("Abstract: %s", article['abstract'])
        logger.info("URL: %s", article['url'])
        print("-" * 80)

# Register the function to run when the program exits
atexit.register(cleanup)

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize variables at the top of the script
current_abstract_index = 0
last_seen_index = 0
abstracts = []
saved_abstracts = []
last_scroll_time = time.time()
loading = False
# Global flag to track if a scraping thread is running
loading_more_articles = False
seen_titles = set()

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
like_button.config(state=tk.DISABLED)

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


# Load preloaded articles and start the scraping process
abstracts = load_preloaded_articles()
saved_abstracts = load_saved_abstracts_json()
if not abstracts:
    logger.warning("No preloaded articles found. Starting fresh scrape...")
    threading.Thread(target=background_task, daemon=True).start()
else:
    logger.info("Preloaded articles ready. Starting background scrape for more...")
    on_loading_complete()

# Start the main loop of the Tkinter GUI
root.mainloop()
