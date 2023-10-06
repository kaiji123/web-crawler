import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget, QLineEdit

# Function to fetch and parse a web page
def crawl_page(url, depth, robot_parser, output_text):
    try:
        # Check if the URL is allowed by the site's robots.txt file
        if not robot_parser.can_fetch("*", url):
            output_text.append(f"Skipped (robots.txt disallowed): {url}")
            return

        # Send an HTTP GET request to the URL with a user-agent and headers
        headers = {'User-Agent': 'YourUserAgentString'}  # Replace with your user-agent
        response = requests.get(url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the page content with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract information or perform actions here
            # For example, print the page's title
            title = soup.title.string
            output_text.append(f"Title: {title}")

            # Find and process links on the page
            for link in soup.find_all('a', href=True):
                # Create an absolute URL by joining the base URL and the relative URL
                absolute_url = urljoin(url, link['href'])
                output_text.append(f"Link: {absolute_url}")

                # You can crawl more pages by recursively calling crawl_page with an incremented depth
                # crawl_page(absolute_url, depth + 1, robot_parser, output_text)

    except Exception as e:
        output_text.append(f"An error occurred: {str(e)}")

class WebCrawlerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Web Crawler GUI")
        self.setGeometry(100, 100, 800, 600)

        # Create widgets
        self.start_url_label = QLabel("Start URL:")
        self.start_url_entry = QLineEdit()
        self.max_depth_label = QLabel("Max Depth:")
        self.max_depth_entry = QLineEdit()
        self.crawl_button = QPushButton("Start Crawling")
        self.output_text = QTextEdit()
        self.page_limit_label = QLabel("Page Limit:")
        self.page_limit_entry = QLineEdit()
        self.crawled_results = []

                # Create pagination buttons
        self.prev_page_button = QPushButton("Previous Page")
        self.next_page_button = QPushButton("Next Page")
        self.current_page = 1  # Initialize current page to 1

        # Connect pagination button click events
        self.prev_page_button.clicked.connect(self.show_previous_page)
        self.next_page_button.clicked.connect(self.show_next_page)



        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.prev_page_button)
        layout.addWidget(self.next_page_button)
        layout.addWidget(self.start_url_label)
        layout.addWidget(self.start_url_entry)
        layout.addWidget(self.max_depth_label)
        layout.addWidget(self.max_depth_entry)
        layout.addWidget(self.page_limit_label)
        layout.addWidget(self.page_limit_entry)
        layout.addWidget(self.crawl_button)
        layout.addWidget(self.output_text)

        # Create central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Connect button click event to crawling function
        self.crawl_button.clicked.connect(self.start_crawling)

    def start_crawling(self):
        # Start URL for your web crawl
        start_url = self.start_url_entry.text()

        # Maximum depth for crawling
        max_depth = int(self.max_depth_entry.text())

        # Page limit
        page_limit = int(self.page_limit_entry.text())

        # Create a RobotFileParser and fetch the robots.txt file for the starting domain
        robot_parser = RobotFileParser()
        domain = start_url.split('/')[2]
        robot_parser.set_url(f"https://{domain}/robots.txt")
        robot_parser.read()

        # Clear the output text
        self.output_text.clear()

        # Create a queue for URL prioritization
        url_queue = [(start_url, 0)]  # Initialize with start URL and depth 0

        # Define the rate limit: Number of requests per second
        rate_limit = 1  # 1 request per second

        # Counter for the number of crawled pages
        crawled_pages = 0

        # Start crawling from the initial URL
        while url_queue and crawled_pages < page_limit:
            # Sort the queue based on priority (depth)
            url_queue.sort(key=lambda x: prioritize_url(x[0], x[1]))

            # Get the URL with the highest priority
            current_url, current_depth = url_queue.pop(0)

            # Crawl the page and display results in the GUI
            crawl_page(current_url, current_depth, robot_parser, self.crawled_results)

            # Increment the crawled pages counter
            crawled_pages += 1

            # Find and add links to the queue with an incremented depth, if within max depth
            if current_depth < max_depth:
                response = requests.get(current_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        absolute_url = urljoin(current_url, link['href'])
                        url_queue.append((absolute_url, current_depth + 1))

            # Implement rate limiting to respect website's policy
            time.sleep(1 / rate_limit)  # Sleep for the specified rate limit
        self.display_current_page()
    
    def show_previous_page(self):
        # Decrement current page number
        self.current_page -= 1
        if self.current_page < 1:
            self.current_page = 1
        self.display_current_page()

    def show_next_page(self):
        # Increment current page number
        self.current_page += 1
        self.display_current_page()

    def display_current_page(self):
        # Clear the output text
        self.output_text.clear()

        # Display the content for the current page
        page_start = (self.current_page - 1) * 10  # Change 10 to the desired number of pages per "pagination"
        page_end = page_start + 10

        # Display the content for the current page within the range [page_start, page_end)
        for i in range(page_start, min(page_end, len(self.crawled_results))):
            self.output_text.append(self.crawled_results[i])

def prioritize_url(url, depth):
    # Assign higher priority to URLs closer to the start URL (lower depth)
    return depth


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load and apply the CSS stylesheet
    with open('./styles.css', 'r') as stylesheet:
        app.setStyleSheet(stylesheet.read())

    window = WebCrawlerApp()
    window.show()
    sys.exit(app.exec_())