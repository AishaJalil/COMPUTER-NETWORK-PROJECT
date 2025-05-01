from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import json
import os

"""
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import json
import os

LOG_FILE = "server.log"
FORM_DATA_FILE = "form_data.txt"

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        with open(LOG_FILE, "a") as log_file:
            log_file.write("%s - %s\n" % (datetime.now(), format % args))

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == '/':
            self.serve_file('templates/index.html', 'text/html')
            self.log_message("GET %s", path)
        elif path.startswith('/static/'):
            filepath = path.lstrip('/')
            self.serve_static(filepath)
            self.log_message("GET %s", path)
        elif path == '/fetch':
            self.handle_fetch_external(query)
        else:
            self.send_error_page(404)
            self.log_message("404 Not Found: %s", path)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            content_type = self.headers.get('Content-Type')

            post_data = self.rfile.read(content_length)

            if content_type == "application/json":
                data = json.loads(post_data.decode('utf-8'))
                message = f"JSON Received: {data}"
            else:
                data = parse_qs(post_data.decode('utf-8'))
                message = f"Form Data Received: {data}"

            self.log_message("POST %s - %s", path, message)

            with open(FORM_DATA_FILE, "a") as f:
                f.write(str(data) + "\n")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "success", "received": data})
            self.wfile.write(response.encode('utf-8'))

        else:
            self.send_error_page(404)
            self.log_message("404 Not Found (POST): %s", path)

    def handle_fetch_external(self, query):
        if 'url' not in query:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'url' parameter")
            return
        
        external_url = query['url'][0]

        # Set custom headers to simulate a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        try:
            # Use requests to fetch the URL with proper headers and follow redirects
            response = requests.get(external_url, headers=headers, allow_redirects=True)
            
            if response.status_code == 200:
                # Send back the HTML content
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(response.content)
                self.log_message("Fetched external URL: %s", external_url)
            else:
                self.send_response(response.status_code)
                self.end_headers()
                self.wfile.write(f"Error fetching URL: {response.status_code}".encode('utf-8'))
                self.log_message(f"Failed fetching external URL: {external_url}, Status Code: {response.status_code}")

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Failed to fetch URL: {e}".encode('utf-8'))
            self.log_message("Failed fetching external URL: %s", external_url)

    def serve_file(self, filepath, content_type):
        try:
            with open(filepath, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error_page(404)

    def serve_static(self, filepath):
        if filepath.endswith(".css"):
            content_type = "text/css"
        elif filepath.endswith(".js"):
            content_type = "application/javascript"
        elif filepath.endswith(".png"):
            content_type = "image/png"
        elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
            content_type = "image/jpeg"
        else:
            content_type = "application/octet-stream"
        self.serve_file(filepath, content_type)

    def send_error_page(self, code):
        if code == 404:
            try:
                with open('templates/404.html', 'rb') as file:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, "404 Page Not Found")


if __name__ == "__main__":
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting HTTP Server at http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()

"""


LOG_FILE = "server.log"
FORM_DATA_FILE = "form_data.txt"

import requests  # Make sure this is at the top

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        with open(LOG_FILE, "a") as log_file:
            log_file.write("%s - %s\n" % (datetime.now(), format % args))

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == '/':
            self.serve_file('templates/index.html', 'text/html')
            self.log_message("GET %s", path)
        elif path.startswith('/static/'):
            filepath = path.lstrip('/')
            self.serve_static(filepath)
            self.log_message("GET %s", path)
        elif path == '/fetch':
            self.handle_fetch_external(query)
        else:
            self.send_error_page(404)
            self.log_message("404 Not Found: %s", path)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == '/submit':
            self.handle_form_submit()
        else:
            self.send_error_page(404)
            self.log_message("404 Not Found (POST): %s", path)

    def handle_fetch_external(self, query):
        if 'url' not in query:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'url' parameter")
            return
        
        external_url = query['url'][0]
        try:
            response = requests.get(external_url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            self.send_response(response.status_code)
            self.send_header('Content-Type', response.headers.get('Content-Type', 'text/html'))
            self.end_headers()
            self.wfile.write(response.content)
            self.log_message("Fetched external URL: %s", external_url)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error fetching external URL: {str(e)}".encode())

    def handle_form_submit(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type')

        post_data = self.rfile.read(content_length)

        if content_type == "application/json":
            data = json.loads(post_data.decode('utf-8'))
            message = f"JSON Received: {data}"
        else:
            data = parse_qs(post_data.decode('utf-8'))
            message = f"Form Data Received: {data}"

        self.log_message("POST /submit - %s", message)

        with open(FORM_DATA_FILE, "a") as f:
            f.write(str(data) + "\n")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "success", "received": data})
        self.wfile.write(response.encode('utf-8'))

    def serve_file(self, filepath, content_type):
        try:
            with open(filepath, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error_page(404)

    def serve_static(self, filepath):
        if filepath.endswith(".css"):
            content_type = "text/css"
        elif filepath.endswith(".js"):
            content_type = "application/javascript"
        elif filepath.endswith(".png"):
            content_type = "image/png"
        elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
            content_type = "image/jpeg"
        else:
            content_type = "application/octet-stream"
        self.serve_file(filepath, content_type)

    def send_error_page(self, code):
        if code == 404:
            try:
                with open('templates/404.html', 'rb') as file:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, "404 Page Not Found")



if __name__ == "__main__":
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting HTTP Server at http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()



