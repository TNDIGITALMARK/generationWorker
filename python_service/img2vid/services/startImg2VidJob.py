from typing import Dict, Any
import logging
import sys
import os

# Add startImg2 path for imports
services_dir = os.path.dirname(__file__)
startimg2_path = os.path.join(services_dir, 'startImg2')
if startimg2_path not in sys.path:
    sys.path.insert(0, startimg2_path)

from jobInitiatedLogging import JobInitiatedLoggingService
from updateWorkflow import UpdateWorkflowService
from startImg2.callComfyJobHandler import CallComfyJobHandlerService
from callValidation import ValidationService

logger = logging.getLogger(__name__)

class StartImg2VidJobService:
    """Service for starting img2vid job workflow"""
    
    def __init__(self):
        self.logging_service = JobInitiatedLoggingService()
        self.workflow_service = UpdateWorkflowService()
        self.comfy_service = CallComfyJobHandlerService()
        self.validation_service = ValidationService()
    
    async def start_job(self, file_name: str, prompt: str, uid: str = None) -> Dict[str, Any]:
        """Start the complete img2vid job workflow"""
        try:
            logger.info(f"Starting img2vid job workflow: file={file_name}, uid={uid}")
            
            # Step 1: Create job logging document in Firestore
            job_id = await self.logging_service.create_job_document(
                file_name=file_name,
                prompt=prompt,
                uid=uid
            )
            
            logger.info(f"Job document created with ID: {job_id}")
            
            # Step 2: Update workflow with user parameters
            updated_workflow = await self.workflow_service.update_workflow_with_params(
                job_id=job_id,
                file_name=file_name,
                prompt=prompt
            )
            
            logger.info(f"Workflow updated for job: {job_id}")
            
            # Step 3: Validate updated workflow
            validation_result = await self.validation_service.validate_workflow_json(updated_workflow)
            
            if not validation_result.get("valid", False):
                logger.error(f"Workflow validation failed for job {job_id}: {validation_result.get('errors', [])}")
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": "Workflow validation failed",
                    "validation_errors": validation_result.get("errors", []),
                    "workflow_updated": True,
                    "workflow_validated": False,
                    "comfy_submitted": False
                }
            
            logger.info(f"Workflow validated successfully for job: {job_id}")
            
            # Step 4: Submit job to ComfyUI
            comfy_result = await self.comfy_service.submit_job(
                job_id=job_id,
                workflow_data=updated_workflow
            )
            
            logger.info(f"Job submitted to ComfyUI: {job_id}")
            
            return {
                "job_id": job_id,
                "status": "pending",
                "workflow_updated": True,
                "workflow_validated": True,
                "comfy_submitted": True,
                "validation_details": validation_result.get("details", {})
            }
            
        except Exception as e:
            logger.error(f"Start job workflow failed: {e}")
            return {
                "job_id": None,
                "status": "failed",
                "error": str(e),
                "workflow_updated": False,
                "workflow_validated": False,
                "comfy_submitted": False
            }