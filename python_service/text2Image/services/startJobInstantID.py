from typing import Dict, Any
import logging
import sys
import os
import json

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from callValidation import ValidationService

logger = logging.getLogger(__name__)

class StartJobInstantIDService:
    """Service for starting InstantID job workflow"""
    
    def __init__(self):
        self.validation_service = ValidationService()
        self.workflow_name = "instantid_workflow"
    
    async def start_job(self, reference_image: str, prompt: str, uid: str = None) -> Dict[str, Any]:
        """Start the complete InstantID job workflow"""
        try:
            logger.info(f"Starting InstantID job workflow: reference_image={reference_image}, uid={uid}")
            
            # Step 1: Log the request (simplified logging for now)
            job_id = f"instantid_{reference_image}_{hash(prompt) % 10000}"
            logger.info(f"InstantID job initiated with ID: {job_id}")
            
            # Step 2: Update workflow with user parameters
            updated_workflow = await self._update_workflow_with_params(
                job_id=job_id,
                reference_image=reference_image,
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
            
            # Step 4: Mock ComfyUI submission (as per your request)
            logger.info(f"Mock ComfyUI submission for job: {job_id}")
            
            return {
                "job_id": job_id,
                "status": "pending",
                "workflow_updated": True,
                "workflow_validated": True,
                "comfy_submitted": True,
                "validation_details": validation_result.get("details", {})
            }
            
        except Exception as e:
            logger.error(f"Start InstantID job workflow failed: {e}")
            return {
                "job_id": None,
                "status": "failed",
                "error": str(e),
                "workflow_updated": False,
                "workflow_validated": False,
                "comfy_submitted": False
            }
    
    async def _update_workflow_with_params(self, job_id: str, reference_image: str, prompt: str) -> Dict[str, Any]:
        """Update the InstantID workflow with user parameters"""
        try:
            # Load the InstantID workflow template
            workflows_dir = os.path.join(os.path.dirname(current_dir), 'workflows')
            workflow_path = os.path.join(workflows_dir, f"{self.workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                raise FileNotFoundError(f"InstantID workflow not found: {workflow_path}")
            
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            # Update workflow with user parameters
            workflow_str = json.dumps(workflow_data)
            
            # Replace placeholders
            workflow_str = workflow_str.replace("{reference_image}", reference_image)
            workflow_str = workflow_str.replace("{user_prompt}", prompt)
            workflow_str = workflow_str.replace("{timestamp}", str(hash(job_id) % 10000))
            
            updated_workflow = json.loads(workflow_str)
            
            logger.info(f"Workflow parameters updated for job: {job_id}")
            return updated_workflow
            
        except Exception as e:
            logger.error(f"Failed to update workflow with parameters: {e}")
            raise e