from typing import Dict, Any, Optional
import logging
import uuid
import sys
import os
from datetime import datetime

# Import Firebase using same path as main.py
python_service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if python_service_root not in sys.path:
    sys.path.insert(0, python_service_root)

from firebase.firebaseAdmin import get_db

logger = logging.getLogger(__name__)

class JobInitiatedLoggingService:
    """Service for creating and managing job documents in Firestore"""
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Get Firestore database instance"""
        if not self.db:
            try:
                self.db = get_db()
            except Exception as e:
                logger.error(f"Failed to get Firebase database: {e}")
                raise e
        return self.db
    
    async def create_job_document(self, file_name: str, prompt: str, uid: Optional[str] = None) -> str:
        """Create job document in Firestore and return job_id"""
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            logger.info(f"Creating job document: {job_id}")
            
            # Prepare job document
            job_doc = {
                "job_id": job_id,
                "file_name": file_name,
                "prompt": prompt,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "comfy_client_id": job_id,  # Use job_id as ComfyUI client_id
            }
            
            # Add uid if provided
            if uid:
                job_doc["uid"] = uid
                logger.info(f"Job associated with user: {uid}")
            
            # Save to Firestore
            db = self._get_db()
            db.collection('jobs').document(job_id).set(job_doc)
            
            logger.info(f"Job document created successfully: {job_id}")
            logger.info(f"Job details - file: {file_name}, uid: {uid}, status: pending")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job document: {e}")
            raise e
    
    async def update_job_status(self, job_id: str, status: str, **kwargs) -> bool:
        """Update job status in Firestore"""
        try:
            logger.info(f"Updating job status: {job_id} -> {status}")
            
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            # Add any additional fields
            update_data.update(kwargs)
            
            # Update Firestore document
            db = self._get_db()
            db.collection('jobs').document(job_id).update(update_data)
            
            logger.info(f"Job status updated successfully: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            return False