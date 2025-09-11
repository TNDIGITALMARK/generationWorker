from typing import Dict, Any, List
import logging
import os
import json
import sys

# Add the img2vid path for imports
current_dir = os.path.dirname(__file__)
img2vid_root = os.path.dirname(current_dir)
services_path = os.path.join(img2vid_root, 'services')
if services_path not in sys.path:
    sys.path.insert(0, services_path)

from callValidation import ValidationService
from startImg2VidJob import StartImg2VidJobService

logger = logging.getLogger(__name__)

class Img2VidController:
    """Controller for img2vid service business logic"""
    
    def __init__(self):
        self.validation_service = ValidationService()
        self.start_job_service = StartImg2VidJobService()
        self.workflows_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workflows')
    
    async def validate_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Validate a specific workflow by name"""
        try:
            logger.info(f"Controller validating workflow: {workflow_name}")
            
            # Call validation service
            result = await self.validation_service.validate_workflow_by_name(workflow_name)
            
            return {
                "valid": result.get("valid", False),
                "workflow_name": workflow_name,
                "details": result.get("details", {}),
                "errors": result.get("errors", [])
            }
            
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return {
                "valid": False,
                "workflow_name": workflow_name,
                "details": {},
                "errors": [str(e)]
            }
    
    async def list_workflows(self) -> List[str]:
        """List all available workflows"""
        try:
            if not os.path.exists(self.workflows_dir):
                logger.warning(f"Workflows directory not found: {self.workflows_dir}")
                return []
            
            workflows = []
            for file in os.listdir(self.workflows_dir):
                if file.endswith('.json'):
                    workflow_name = file[:-5]  # Remove .json extension
                    workflows.append(workflow_name)
            
            logger.info(f"Found {len(workflows)} workflows")
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    async def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get information about a specific workflow"""
        try:
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                raise FileNotFoundError(f"Workflow not found: {workflow_name}")
            
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            # Extract metadata if available
            metadata = workflow_data.get("workflow_metadata", {})
            
            return {
                "name": workflow_name,
                "description": metadata.get("description", "No description available"),
                "version": metadata.get("version", "1.0"),
                "parameters": metadata.get("parameters", {}),
                "node_count": len([k for k in workflow_data.keys() if k.isdigit()])
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow info for {workflow_name}: {e}")
            raise e
    
    async def start_job(self, file_name: str, prompt: str, uid: str = None) -> Dict[str, Any]:
        """Start img2vid job"""
        try:
            logger.info(f"Starting img2vid job: file={file_name}, uid={uid}")
            
            # Call start job service
            result = await self.start_job_service.start_job(file_name, prompt, uid)
            
            return {
                "job_id": result.get("job_id"),
                "status": result.get("status", "pending"),
                "file_name": file_name,
                "prompt": prompt,
                "uid": uid
            }
            
        except Exception as e:
            logger.error(f"Start job failed: {e}")
            return {
                "job_id": None,
                "status": "failed",
                "error": str(e)
            }