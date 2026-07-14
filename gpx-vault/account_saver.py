import sqlite3
import secrets
import hashlib
import time

def setup_db():
    """Creates a mock database with a user table."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            reset_token_hash TEXT,
            reset_expiry INTEGER
        )
    """)
    # Insert a dummy user
    cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                   ("user@example.com", "old_hashed_password"))
    conn.commit()
    return conn

def request_password_reset(conn, email):
    """Step 1: User requests a reset link."""
    cursor = conn.cursor()
    
    # 1. Generate a cryptographically secure token
    raw_token = secrets.token_urlsafe(32)
    
    # 2. Hash the token for storage (SHA-256 is fine for short-lived tokens)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # 3. Set expiration for 15 minutes (900 seconds) from now
    expiry_time = int(time.time()) + 900
    
    # 4. Save to database securely using parameterized queries
    cursor.execute("""
        UPDATE users 
        SET reset_token_hash = ?, reset_expiry = ? 
        WHERE email = ?
    """, (token_hash, expiry_time, email))
    
    if cursor.rowcount > 0:
        conn.commit()
        # In a real app, you would email this raw_token as a link:
        # https://yourwebsite.com/reset?email=user@example.com&token=raw_token
        print(f"📧 [EMAIL SENT TO {email}]: Your reset token is: {raw_token}")
    else:
        # Security Note: Never tell the user if the email exists or not, 
        # otherwise hackers can use the reset form to enumerate registered users.
        print(f"📧 [EMAIL SENT]: If that account exists, a reset link was sent.")

def execute_password_reset(conn, email, submitted_token, new_password):
    """Step 2: User submits the token to create a new password."""
    cursor = conn.cursor()
    
    # 1. Hash the submitted token so we can compare it to the database
    submitted_hash = hashlib.sha256(submitted_token.encode()).hexdigest()
    current_time = int(time.time())
    
    # 2. Look up the user's token and expiration
    cursor.execute("""
        SELECT reset_token_hash, reset_expiry 
        FROM users WHERE email = ?
    """, (email,))
    
    row = cursor.fetchone()
    
    if not row:
        print("❌ Reset failed: Invalid request.")
        return
        
    db_token_hash, expiry = row
    
    # 3. Verify token matches AND is not expired
    if db_token_hash != submitted_hash:
        print("❌ Reset failed: Invalid token.")
        return
        
    if current_time > expiry:
        print("❌ Reset failed: Token has expired. Please request a new one.")
        return
        
    # 4. Success! Hash the new password (in reality, use bcrypt or Argon2 here)
    new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # 5. Update password AND wipe the reset token so it can't be reused
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?, reset_token_hash = NULL, reset_expiry = NULL 
        WHERE email = ?
    """, (new_password_hash, email))
    conn.commit()
    
    print("✅ Password successfully reset!")

# --- RUN THE SIMULATION ---
if __name__ == "__main__":
    db = setup_db()
    
    print("--- 1. User Forgets Password ---")
    request_password_reset(db, "user@example.com")
    
    print("\n--- 2. Hacker tries to guess the token ---")
    execute_password_reset(db, "user@example.com", "fake_guessed_token_123", "hackers_password")
    
    print("\n--- 3. User uses the correct token ---")
    # Simulating the user copying the token from their email
    cursor = db.cursor()
    cursor.execute("SELECT reset_token_hash FROM users WHERE email = 'user@example.com'")
    # Note: We can't get the raw token from the DB! We have to pretend the user pasted it.
    print("(Paste the token from the email output above to test it in a real scenario)")
    
    # For simulation purposes, run this script and copy the token printed in step 1 
    # to pass it to execute_password_reset.
