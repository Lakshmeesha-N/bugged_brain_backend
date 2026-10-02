#!/usr/bin/env python3
"""
Developer helper script to obtain a Firebase ID Token using email and password.

Usage:
    python scripts/get_token.py <email> <password> <firebase_web_api_key>

Example:
    python scripts/get_token.py user@example.com mypassword AIzaSyD...
"""

import sys
import httpx


def get_token(email: str, password: str, api_key: str) -> None:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = httpx.post(url, json=payload)
        data = response.json()
        if response.status_code == 200:
            print(data.get("idToken", ""))
        else:
            error_message = data.get("error", {}).get("message", response.text)
            print(f"Error: {error_message}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/get_token.py <email> <password> <firebase_web_api_key>", file=sys.stderr)
        sys.exit(1)

    email_arg = sys.argv[1]
    password_arg = sys.argv[2]
    api_key_arg = sys.argv[3]

    get_token(email_arg, password_arg, api_key_arg)
