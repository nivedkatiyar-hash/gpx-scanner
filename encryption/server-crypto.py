from cryptography.fernet import Fernet
import json

# Generate a key for encryption and decryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

def encrypt_message(message):
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message

def decrypt_message(encrypted_message):
    decrypted_message = cipher_suite.decrypt(encrypted_message).decode()
    return decrypted_message

def send_message(source, action, message):
    message_data = {
        'source': source,
        'action': action,
        'message': encrypt_message(message)
    }
    return json.dumps(message_data)

def receive_message(encrypted_data):
    message_data = json.loads(encrypted_data)
    decrypted_message = decrypt_message(message_data['message'])
    return {
        'source': message_data['source'],
        'action': message_data['action'],
        'message': decrypted_message
    }

# Example usage
if __name__ == "__main__":
    source = "Server"
    action = "Notify"
    message = "This is a secret message."

    encrypted_data = send_message(source, action, message)
    print("Encrypted Data:", encrypted_data)

    received_data = receive_message(encrypted_data)
    print("Received Data:", received_data)
