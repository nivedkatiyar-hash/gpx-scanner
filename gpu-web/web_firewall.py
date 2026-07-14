#!/usr/bin/env python3
"""
Lightweight Python WAF (Web Application Firewall)
Scans incoming HTTP requests for malicious payloads.
"""

import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- THREAT SIGNATURES ---
# These regular expressions catch the most common web vulnerabilities.
SIGNATURES = {
    "SQL_INJECTION": r"(?i)(UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|1=1|' OR '1'='1|--\s*$)",
    "XSS": r"(?i)(<script.*?>|javascript:|onerror=\s*|onload=\s*)",
    "PATH_TRAVERSAL": r"(?i)(\.\./|\.\.\\|/etc/passwd|windows\\system32)",
    "CMD_INJECTION": r"(?i)(;|\||`|\$|\n)\s*(ls|cat|whoami|echo|wget|curl|ping|nc\s+)",
    "BAD_BOT": r"(?i)(sqlmap|nikto|nmap|curl|wget)"
}

# Compile regex for performance
COMPILED_RULES = {name: re.compile(pattern) for name, pattern in SIGNATURES.items()}

# UI Colors for the terminal
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RESET = "\033[0m"

class SecureRequestHandler(BaseHTTPRequestHandler):
    
    def scan_payload(self, target_name, payload):
        """Scans a string against all compiled regex rules."""
        if not payload:
            return True
            
        decoded_payload = urllib.parse.unquote(payload)
        
        for attack_type, rule in COMPILED_RULES.items():
            if rule.search(decoded_payload):
                print(f"{C_RED}[!] MALICIOUS REQUEST BLOCKED{C_RESET}")
                print(f"    Target: {target_name}")
                print(f"    Threat: {attack_type}")
                print(f"    IP: {self.client_address[0]}")
                return False
        return True

    def is_request_safe(self):
        """Extracts and scans the URL, Headers, and Body."""
        # 1. Scan the URL and Query Parameters
        if not self.scan_payload("URL", self.path):
            return False
            
        # 2. Scan HTTP Headers (especially User-Agent and Cookies)
        for header, value in self.headers.items():
            if not self.scan_payload(f"Header ({header})", value):
                return False
                
        # 3. Scan the Body (for POST requests)
        if self.command == 'POST':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                # Read body and decode to string
                body = self.rfile.read(content_length).decode('utf-8', errors='ignore')
                if not self.scan_payload("POST Body", body):
                    return False
                    
        return True

    def reject_request(self):
        """Sends a 403 Forbidden response."""
        self.send_response(403)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>403 Forbidden</h1><p>Security violation detected.</p>")

    def process_safe_request(self):
        """Handles legitimate requests."""
        print(f"{C_GREEN}[+] Safe request allowed: {self.path}{C_RESET}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>200 OK</h1><p>Your request was clean and processed successfully.</p>")

    # --- HTTP METHODS ---
    
    def do_GET(self):
        if self.is_request_safe():
            self.process_safe_request()
        else:
            self.reject_request()

    def do_POST(self):
        if self.is_request_safe():
            self.process_safe_request()
        else:
            self.reject_request()

    def log_message(self, format, *args):
        """Overrides default logging to prevent terminal clutter."""
        pass

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), SecureRequestHandler)
    print(f"{C_YELLOW}🛡️  WAF Scanner running on http://localhost:{PORT}{C_RESET}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
