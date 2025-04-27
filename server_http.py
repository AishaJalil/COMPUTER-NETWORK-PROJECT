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
        
        if path == '/':
            self.serve_file('templates/index.html', 'text/html')
            self.log_message("GET %s", path)
        elif path.startswith('/static/'):
            filepath = path.lstrip('/')
            self.serve_static(filepath)
            self.log_message("GET %s", path)
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

            # Save form data
            with open(FORM_DATA_FILE, "a") as f:
                f.write(str(data) + "\n")

            # Respond
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "success", "received": data})
            self.wfile.write(response.encode('utf-8'))

        else:
            self.send_error_page(404)
            self.log_message("404 Not Found (POST): %s", path)

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
