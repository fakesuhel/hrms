#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.auth import create_access_token
from datetime import timedelta

# Generate a new token for testing
token_data = {'sub': 'admin'}
access_token = create_access_token(data=token_data, expires_delta=timedelta(hours=8))
print(access_token)
