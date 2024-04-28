import sys
import os
import requests
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


class WebScraperGUI(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.driver = None
        self.init_ui()
        self.show()

    def init_ui(self):
        # Layout setup
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # URL input
        self.url_input = qtw.QLineEdit(self)
        self.url_input.setPlaceholderText('Enter URL here...')
        layout.addWidget(self.url_input)

        # File type selection
        self.file_types = {'PDF': '.pdf', 'SVG': '.svg', 'JPG': '.jpg', 'PNG': '.png'}
        self.checkboxes = {}
        for name, ext in self.file_types.items():
            cb = qtw.QCheckBox(f'Download {name} files', self)
            cb.setChecked(True)
            self.checkboxes[ext] = cb
            layout.addWidget(cb)

        # Save directory chooser
        self.save_dir_input = qtw.QLineEdit(self)
        self.save_dir_input.setPlaceholderText('Specify save directory...')
        self.browse_button = qtw.QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.set_save_directory)
        dir_layout = qtw.QHBoxLayout()
        dir_layout.addWidget(self.save_dir_input)
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout)

        # Start button
        self.start_button = qtw.QPushButton('Start Scraping', self)
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        # Terminal output box
        self.output_terminal = qtw.QTextEdit(self)
        self.output_terminal.setReadOnly(True)
        layout.addWidget(self.output_terminal)

        # Hide Browser Checkbox
        self.hide_browser_cb = qtw.QCheckBox('Hide Browser', self)
        layout.addWidget(self.hide_browser_cb)

    def set_save_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.save_dir_input.setText(dir_path)

    def start_scraping(self):
        url = self.url_input.text()
        save_directory = self.save_dir_input.text()
        file_types = {ext: cb.isChecked() for ext, cb in self.checkboxes.items()}
        self.output_terminal.append(f"Starting scraping at {url}")
        self.init_webdriver()
        self.main(url, save_directory, file_types)
        self.driver.quit()

    def init_webdriver(self):
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        if self.hide_browser_cb.isChecked():
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def main(self, url, save_directory, file_types):
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        self.driver.get(url)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        try:
            links = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
            urls = [link.get_attribute('href') for link in links]

            for url in urls:
                self.driver.get(url)
                self.output_terminal.append(f"Processing URL: {url}")
                try:
                    file_links = self.driver.find_elements(By.CSS_SELECTOR, ",".join(
                        [f"a[href$='{ext}'], img[src$='{ext}']" for ext, checked in file_types.items() if checked]
                    ))
                    for file_link in file_links:
                        try:
                            file_url = file_link.get_attribute('href') or file_link.get_attribute('src')
                            self.download_file(file_url, save_directory)
                        except StaleElementReferenceException:
                            self.output_terminal.append(f"Skipped stale element at URL: {url}")
                            continue
                except Exception as e:
                    self.output_terminal.append(f"An error occurred while processing URL: {url}, Error: {e}")
                self.driver.back()


        except Exception as e:
            self.output_terminal.append(f"An error occurred: {e}")

    def download_file(self, file_url, save_directory):
        try:
            response = requests.get(file_url, stream=True)
            file_name = file_url.split('/')[-1].split('?')[0]
            file_path = os.path.join(save_directory, file_name)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.output_terminal.append(f"Downloaded: {file_path}")
            else:
                self.output_terminal.append(f"Failed to download {file_url}")
        except requests.RequestException as e:
            self.output_terminal.append(f"Error downloading {file_url}: {e}")

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    ex = WebScraperGUI()
    sys.exit(app.exec_())
