import requests
from bs4 import BeautifulSoup
import time
from datasets import Dataset  # Hugging Face datasets library

# Base URLs for English and Chinese versions
BASE_EN = "https://blogs.nvidia.com"
BASE_ZH = "https://blogs.nvidia.com.tw"

# Custom headers (helps to mimic a browser)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def get_article_content(url):
    """
    Fetches the content of an article given its URL.
    Returns a tuple: (title, content). 
    Adjust the parsing based on the site’s structure.
    """
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {url} (Status code: {response.status_code})")
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to extract the title (assuming it's in an <h1> tag)
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # Try to extract the main content.
        # Here we assume the content is inside a <div> with class "entry-content".
        content_div = soup.find("div", class_="entry-content")
        if content_div:
            content = content_div.get_text(separator="\n", strip=True)
        else:
            # Fallback: get all text
            content = soup.get_text(separator="\n", strip=True)
        return title, content

    except Exception as e:
        print(f"Exception occurred while fetching {url}: {e}")
        return None, None

def get_chinese_article_links(main_page_url, num_articles=20):
    """
    Scrapes the Chinese main page for article links.
    Only returns links that contain '/blog/'.
    """
    links = []
    try:
        response = requests.get(main_page_url, headers=headers)
        if response.status_code != 200:
            print("Failed to fetch main page", main_page_url)
            return links
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <a> tags with an href that contains '/blog/'
        for a in soup.find_all("a", href=True):
            href = a['href']
            if '/blog/' in href:
                # If it's a full URL, ensure it belongs to the Chinese site
                if href.startswith("http"):
                    if "blogs.nvidia.com.tw" in href and href not in links:
                        links.append(href)
                else:
                    full_link = BASE_ZH + href
                    if full_link not in links:
                        links.append(full_link)
            if len(links) >= num_articles:
                break

    except Exception as e:
        print("Exception occurred while fetching links: ", e)
    return links[:num_articles]

if __name__ == '__main__':
    # Number of article pairs you want
    num_articles = 1000

    # Step 1: Get Chinese article links
    zh_main = "https://blogs.nvidia.com.tw/"
    zh_links = get_chinese_article_links(zh_main, num_articles)
    print("Found Chinese article links:")
    for link in zh_links:
        print(link)
    
    article_pairs = []
    for zh_link in zh_links:
        # Step 2: Construct the corresponding English URL.
        # (Assuming the relative path is identical between sites.)
        try:
            relative_path = zh_link.split("blogs.nvidia.com.tw")[-1]
            en_link = BASE_EN + relative_path
        except Exception as e:
            print("Error extracting relative path from: ", zh_link)
            continue

        print("\nProcessing article pair:")
        print("English URL:", en_link)
        print("Chinese URL:", zh_link)

        # Step 3: Get contents from both versions
        en_title, en_content = get_article_content(en_link)
        zh_title, zh_content = get_article_content(zh_link)

        # If both pages were fetched successfully, save the pair
        if en_title and zh_title:
            article_pairs.append({
                'en_url': en_link,
                'en_title': en_title,
                'en_content': en_content,
                'zh_url': zh_link,
                'zh_title': zh_title,
                'zh_content': zh_content,
            })
        else:
            print("Skipping pair due to missing content.")

        # Be polite to the server
        time.sleep(1)

    print("\nCollected article pairs:", len(article_pairs))
    
    # ----- Saving in Hugging Face dataset format -----
    # Convert the list of dictionaries into a Hugging Face Dataset.
    hf_dataset = Dataset.from_list(article_pairs)
    
    # Save the dataset to disk (Hugging Face's native format)
    hf_dataset.save_to_disk("nvidia_blog_dataset")
    
    # Optionally, also save it as a JSON Lines file
    hf_dataset.to_json("nvidia_blog_dataset.jsonl", orient="records", force_ascii=False)
    
    print("Dataset saved in Hugging Face format (both as a disk folder and as a JSONL file).")

