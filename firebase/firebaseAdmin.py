import os
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_app: Optional[firebase_admin.App] = None
_db: Optional[firestore.Client] = None

def initialize_firebase() -> tuple[firebase_admin.App, firestore.Client]:
    """Initialize Firebase Admin SDK for Python service"""
    global _app, _db
    
    if _app:
        return _app, _db
    
    try:
        # Create credentials dictionary from environment variables
        cred_dict = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
        }
        
        # Initialize Firebase with credentials
        cred = credentials.Certificate(cred_dict)
        _app = firebase_admin.initialize_app(cred)
        _db = firestore.client()
        
        logger.info("Firebase Admin initialized successfully in Python service")
        return _app, _db
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise e

async def test_firebase_connection() -> bool:
    """Test Firebase connection"""
    try:
        if not _db:
            raise Exception("Firebase not initialized")
        
        # Test connection with a simple read
        doc_ref = _db.collection('health').document('test')
        doc_ref.get()
        return True
        
    except Exception as e:
        logger.error(f"Firebase connection test failed: {e}")
        return False

def get_db() -> firestore.Client:
    """Get Firestore database instance"""
    if not _db:
        raise Exception("Firebase not initialized. Call initialize_firebase() first.")
    return _db

def get_app() -> firebase_admin.App:
    """Get Firebase app instance"""
    if not _app:
        raise Exception("Firebase not initialized. Call initialize_firebase() first.")
    return _app