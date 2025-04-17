from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import logging

PORT = 8000

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        logging.info(f"GET request: Path={self.path}")
        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = parse_qs(post_data.decode())
        
        # Save form data
        with open("form_data.txt", "a") as f:
            f.write(str(data) + "\n")

        logging.info(f"POST request: Path={self.path}, Data={data}")

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h2>Data Received!</h2></body></html>")

    def log_message(self, format, *args):
        logging.info("%s - - [%s] %s" %
                     (self.client_address[0],
                      self.log_date_time_string(),
                      format % args))

if __name__ == "__main__":
    logging.basicConfig(filename="http_server.log", level=logging.INFO)
    server = HTTPServer(('', PORT), MyHandler)
    print(f"Serving on port {PORT}...")
    server.serve_forever()
