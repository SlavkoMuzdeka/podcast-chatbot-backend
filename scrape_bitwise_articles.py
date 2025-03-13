import os
import requests

from bs4 import BeautifulSoup

# Base URL to start scraping
BITWISE_FOLDER = "bitwise_articles"
BASE_URL = "https://experts.bitwiseinvestments.com"

# Step 1: Fetch the main page content
response = requests.get(BASE_URL + "/cio-memos")
soup = BeautifulSoup(response.content, "html.parser")

# Step 2: Find all <a> tags with href that contains weekly articles (you can refine this based on actual link structure)
article_links = [a["href"] for a in soup.find_all("a", href=True)]
article_links = [
    link if link.startswith("http") else f"https://experts.bitwiseinvestments.com{link}"
    for link in article_links
]

# Step 3: Create a folder to save article content
os.makedirs(BITWISE_FOLDER, exist_ok=True)

# Step 4: Loop through each article link, scrape content and save to txt
for idx, link in enumerate(article_links, start=1):
    try:
        # Fetch article page content
        article_response = requests.get(link)
        article_soup = BeautifulSoup(article_response.content, "html.parser")

        # Extract article text (you can adjust this selector based on the actual HTML structure)
        title = (
            article_soup.find("h1").get_text(strip=True)
            if article_soup.find("h1")
            else "Untitled"
        )
        # c-kVNxcv
        div_element = article_soup.find("div", class_="c-kVNxcv")

        if div_element:
            full_content = title
            for child in div_element.find_all(True):
                text = child.get_text(strip=True)
                if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    full_content += "\n\n" + text + "\n\n"
                elif child.name == "p":
                    full_content += text

            with open(
                f"{BITWISE_FOLDER}/article_{idx}.txt", "w", encoding="utf-8"
            ) as file:
                file.write(full_content)
    except Exception as e:
        print(f"Error processing {link}: {e}")
