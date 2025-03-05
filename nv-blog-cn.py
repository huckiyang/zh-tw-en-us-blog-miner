import requests
from bs4 import BeautifulSoup
import time
from datasets import Dataset

# Base URLs for English and Chinese versions
BASE_EN = "https://developer.nvidia.com/blog"
BASE_ZH = "https://developer.nvidia.com/zh-cn/blog"

# Custom headers (helps to mimic a browser)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
}

def get_article_content(url):
    """
    Fetches the content of an article given its URL.
    Returns a tuple: (title, content). 
    """
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {url} (Status code: {response.status_code})")
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the title - in developer blog it's usually in h1
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # Find the main content
        # Note: You might need to adjust these selectors based on the actual page structure
        content_div = soup.find("div", class_="post-content")  # Adjust class name as needed
        if content_div:
            # Remove any script and style elements
            for element in content_div.find_all(['script', 'style']):
                element.decompose()
            content = content_div.get_text(separator="\n", strip=True)
        else:
            content = "No content found"
            
        return title, content

    except Exception as e:
        print(f"Exception occurred while fetching {url}: {e}")
        return None, None

def get_article_links(main_page_url, num_articles=20):
    """
    Scrapes the blog page for article links.
    """
    links = []
    try:
        response = requests.get(main_page_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch main page {main_page_url}")
            return links

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all article links
        # Adjust these selectors based on the actual page structure
        for article in soup.find_all("article"):
            link_tag = article.find("a", href=True)
            if link_tag:
                href = link_tag['href']
                if href.startswith('/'):
                    href = f"https://developer.nvidia.com{href}"
                if href not in links:
                    links.append(href)
            if len(links) >= num_articles:
                break

    except Exception as e:
        print(f"Exception occurred while fetching links: {e}")
    return links[:num_articles]

def get_corresponding_url(url, from_lang='zh-cn', to_lang='en-us'):
    """
    Convert URL between languages
    """
    if from_lang == 'zh-cn':
        return url.replace('/zh-cn/', '/blog/')
    else:
        return url.replace('/blog/', '/zh-cn/')

if __name__ == '__main__':
    num_articles = 100  # Adjust as needed

    # Get Chinese article links
    zh_links = get_article_links(BASE_ZH, num_articles)
    print(f"Found {len(zh_links)} Chinese article links")
    
    article_pairs = []
    for zh_link in zh_links:
        print(f"\nProcessing: {zh_link}")
        
        # Get corresponding English URL
        en_link = get_corresponding_url(zh_link)
        
        print(f"English version: {en_link}")

        # Get contents from both versions
        zh_title, zh_content = get_article_content(zh_link)
        en_title, en_content = get_article_content(en_link)

        # If both pages were fetched successfully, save the pair
        if zh_title and en_title and zh_content and en_content:
            article_pairs.append({
                'en_url': en_link,
                'en_title': en_title,
                'en_content': en_content,
                'zh_url': zh_link,
                'zh_title': zh_title,
                'zh_content': zh_content,
            })
            print(f"Successfully paired: {zh_title}")
        else:
            print("Skipping pair due to missing content")

        # Be polite to the server
        time.sleep(2)

    print(f"\nCollected {len(article_pairs)} article pairs")
    
    # Create and save dataset
    if article_pairs:
        hf_dataset = Dataset.from_list(article_pairs)
        
        # Save as Hugging Face dataset
        hf_dataset.save_to_disk("nvidia_dev_blog_dataset")
        
        # Save as JSONL
        hf_dataset.to_json("nvidia_zh_cn_en_us_dev_blog_dataset.jsonl", orient="records", force_ascii=False)
        
        print("Dataset saved successfully")
    else:
        print("No article pairs collected")

