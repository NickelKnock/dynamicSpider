from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests

# Function to download files from a given URL
def download_file(file_url, save_directory):
    if not file_url.startswith('http'):
        file_url = 'https://www.armourarchive.org' + file_url
    try:
        response = requests.get(file_url, stream=True)
        file_name = file_url.split('/')[-1].split('?')[0]
        file_path = os.path.join(save_directory, file_name)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {file_path}")
        else:
            print(f"Failed to download {file_url}")
    except requests.RequestException as e:
        print(f"Error downloading {file_url}: {e}")

# Initialize the Chrome WebDriver
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 10)

def main(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url  # Ensure the URL includes the scheme
    driver.get(url)
    save_directory = 'F:\\SpiderHaul'
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    try:
        # Collect all link URLs before navigating
        links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
        urls = [link.get_attribute('href') for link in links]  # Store URLs instead of web elements

        for url in urls:
            driver.get(url)
            print(f"Processing URL: {url}")
            # Here, add logic based on what you want to download from each page
            file_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf'], img[src$='.svg'], img[src*='.jpg'], img[src*='.png']")
            for file_link in file_links:
                file_url = file_link.get_attribute('href') or file_link.get_attribute('src')
                download_file(file_url, save_directory)
            driver.back()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

# Request user input for the URL
input_url = input("Please enter the URL to start scraping: ")
main(input_url)
