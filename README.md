# imrad
Like Tiktok but for research abstracts. Abstracts are pulled from the Nature database's 

Features: Infinite scrolling, an algorithm that provides better videos with usage, quick load times.

Some details about how I made this app: Initially I planned to code this whole application by hand, but after asking chatGPT to provide the UI framework I wanted to see how far I could work with it to implement what I had in mind. I thought about the features I wanted and how I'd implement those and then gave chatGPT specific commands to do it how I'd do it if I were to do it by hand. The recommender system was the hardest part because I didn't know much about them: for that, I learned the basics from the resources of an online UCSD course and then came up with one (content-based based on cosine similarity of tf-idf of abstract texts) for the situation at hand. ChatGPT worked well but towards the end it became less helpful as it started forgetting some of the details of older code it had come up with. This was around the point where I finished the recommender system and was trying to preload and queue articles to make infinite scrolling work. For the latter it just wasn't helping so I implemented it myself. 

For each new improvement I made a new file because I don't appreciate the usefulness of version control apparently. Those files are all included here along with the transcript of the chatGPT conversation.
