# app/services/auth.py
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

load_dotenv()

def get_credentials():
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)

def get_subscription_id():
    return os.getenv("AZURE_SUBSCRIPTION_ID")
