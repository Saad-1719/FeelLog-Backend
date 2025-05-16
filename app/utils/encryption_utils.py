from cryptography.fernet import Fernet
from app.core.config import FERNET_KEY

if not FERNET_KEY:
    raise ValueError("FERNET_KEY not found in .env file")

# Initialize Fernet cipher
try:
    cipher = Fernet(FERNET_KEY.encode())
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY: {str(e)}")


def encrypt_data(data: str) -> str:
    """
    Encrypts the input string using the Fernet key.

    Args:
        data (str): The plaintext data to encrypt.

    Returns:
        str: The encrypted data as a base64-encoded string.

    Raises:
        ValueError: If encryption fails or input is invalid.
    """
    if not isinstance(data, str):
        raise ValueError("Input data must be a string")
    if not data:
        raise ValueError("Input data cannot be empty")
    try:
        encrypted_data = cipher.encrypt(data.encode())
        return encrypted_data.decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts the input encrypted string using the Fernet key.

    Args:
        encrypted_data (str): The encrypted data as a base64-encoded string.

    Returns:
        str: The decrypted plaintext data.

    Raises:
        ValueError: If decryption fails or input is invalid.
    """
    if not isinstance(encrypted_data, str):
        raise ValueError("Encrypted data must be a string")
    if not encrypted_data:
        raise ValueError("Encrypted data cannot be empty")
    try:
        decrypted_data = cipher.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
