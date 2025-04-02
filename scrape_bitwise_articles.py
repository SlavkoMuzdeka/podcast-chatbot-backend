import os
import json
import logging
import requests

from typing import List
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """
    Loads configuration settings from `config.json`.

    Returns:
        dict: Configuration dictionary containing base_url, folder_name, and debug flag.
    """
    with open("config.json", "r") as f:
        config = json.load(f)
        return config["bitwise_articles"]


def get_articles(base_url: str) -> List[str]:
    """
    Fetches article links from the `/cio-memos` page and returns a list of full URLs.

    Args:
        base_url (str): The base URL of the Bitwise website.

    Returns:
        List[str]: A list of full article URLs.
    """
    response = requests.get(base_url + "/cio-memos")
    soup = BeautifulSoup(response.content, "html.parser")
    article_links = [a["href"] for a in soup.find_all("a", href=True)]
    return [
        link if link.startswith("http") else f"{base_url}{link}"
        for link in article_links
    ]


def scrape_content(articles: List[str], folder_name: str, debug: bool = False) -> None:
    """
    Scrapes article content and saves it in the specified folder.

    Args:
        articles (List[str]): List of article URLs.
        folder_name (str): Folder to save articles.
        debug (bool, optional): If `True`, logs the number of new articles. Defaults to False.
    """
    os.makedirs(folder_name, exist_ok=True)

    num_existing_articles = len(os.listdir(folder_name))
    articles = articles[num_existing_articles:]

    if debug:
        logger.info(f"New articles -> {len(articles)}")

    for idx, article_link in enumerate(articles, start=num_existing_articles + 1):
        try:
            article_response = requests.get(article_link)
            article_soup = BeautifulSoup(article_response.content, "html.parser")

            # Extract title or assign default name
            title = (
                article_soup.find("h1").get_text(strip=True)
                if article_soup.find("h1")
                else f"Untitled_{idx}"
            )

            # Extract article content
            div_element = article_soup.find("div", class_="c-kVNxcv")
            if div_element:
                full_content = title
                for child in div_element.find_all(True):
                    text = child.get_text(strip=True)
                    if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        full_content += "\n\n" + text + "\n\n"
                    elif child.name == "p":
                        full_content += text

                # Save article to text file
                with open(
                    f"{folder_name}/article_{idx}.txt", "w", encoding="utf-8"
                ) as file:
                    file.write(full_content)

        except Exception as e:
            logger.info(f"Error processing {article_link}: {e}")


def main():
    """
    Runs the full scraping process by:
        1. Loading configuration.
        2. Fetching article links.
        3. Scraping and saving articles.
    """
    config = _load_config()
    articles = get_articles(config["base_url"])
    scrape_content(articles, config["folder_name"], config["debug"])


if __name__ == "__main__":
    main()
