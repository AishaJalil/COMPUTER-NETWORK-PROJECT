from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, urljoin
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests
import os
import base64
import re

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

        try:
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
        except Exception as e:
            self.send_error_page(500)
            self.log_message("500 Internal Server Error: %s - %s", path, str(e))

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            if path == '/submit':
                self.handle_form_submit()
            else:
                self.send_error_page(404)
                self.log_message("404 Not Found (POST): %s", path)
        except Exception as e:
            self.send_error_page(500)
            self.log_message("500 Internal Server Error (POST): %s - %s", path, str(e))

    def handle_fetch_external(self, query):
        if 'url' not in query:
            self.send_error_page(400, "Missing 'url' parameter")
            return

        external_url = query['url'][0]

        if external_url.startswith("data:"):
        # Example: data:image/png;base64,iVBORw0KGgoAAAANS...
            try:
                match = re.match(r'data:(.*?);base64,(.*)', external_url)
                if not match:
                    raise ValueError("Invalid data URI")

                mime_type, base64_data = match.groups()
                decoded_data = base64.b64decode(base64_data)

                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.end_headers()
                self.wfile.write(decoded_data)

                self.log_message("Served data URI: %s", mime_type)
            except Exception as e:
                self.send_error_page(400, f"Invalid data URI: {str(e)}")
                self.log_message("400 Bad Request - Invalid data URI: %s", str(e))
            return
        
        try:
            response = requests.get(external_url, headers={"User-Agent": "Mozilla/5.0"})
            content_type = response.headers.get('Content-Type', 'text/html')

            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                for tag in soup.find_all(['a', 'link', 'script', 'img']):
                    attr = 'href' if tag.name in ['a', 'link'] else 'src'
                    if tag.has_attr(attr):
                        original_url = tag[attr]
                        absolute_url = urljoin(external_url, original_url)
                        tag[attr] = f"/fetch?url={absolute_url}"

                modified_html = str(soup).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(modified_html)

            else:
                self.send_response(response.status_code)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(response.content)

            self.log_message("Fetched external URL: %s", external_url)

        except requests.exceptions.MissingSchema:
            self.send_error_page(400)
            self.log_message("400 Bad Request - Missing schema in URL: %s", external_url)
        except requests.exceptions.InvalidURL:
            self.send_error_page(400)
            self.log_message("400 Bad Request - Invalid URL: %s", external_url)
        except requests.exceptions.ConnectionError:
            self.send_error_page(400)
            self.log_message("400 Bad Request - Connection error for URL: %s", external_url)
        except Exception as e:
            self.send_error_page(500)
            self.log_message("500 Internal Server Error - %s", str(e))

    def handle_form_submit(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type')
        post_data = self.rfile.read(content_length)

        if not post_data:
            self.send_error_page(400, "Empty request body")
            return

        try:
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

        except Exception as e:
            self.send_error_page(400, f"Error parsing POST data: {str(e)}")

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
        elif filepath.endswith(".ico"):
            content_type = "image/x-icon"
        else:
            content_type = "application/octet-stream"
        self.serve_file(filepath, content_type)

    def send_error_page(self, code, message=None):
        page_map = {
            400: "templates/400.html",
            404: "templates/404.html",
            500: "templates/500.html"
        }

        file_path = page_map.get(code)
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                self.send_response(code)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        else:
            self.send_error(code, message if message else self.responses.get(code, ("Error",))[0])


if __name__ == "__main__":
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting HTTP Server at http://{server_address[0]}:{server_address[1]}")
    httpd.serve_forever()
<<<<<<< HEAD
=======

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
>>>>>>> 885103f (Delete flask_Server.log and server_flask.py)
