from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def fetch_website_contents_rp(url):
    """
    Return the title and contents of the website using Selenium.
    Truncate to 2,000 characters.
    """

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        # Get the fully rendered HTML
        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string if soup.title else "No title found"

        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()

            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""

        return (title + "\n\n" + text)[:2000]

    finally:
        driver.quit()