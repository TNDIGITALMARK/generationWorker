from typing import Dict, Any, List
import logging
import sys
import os

# Import the proper Img2VidController using absolute import
python_service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
img2vid_controllers_path = os.path.join(python_service_root, 'img2vid', 'controllers')
sys.path.insert(0, img2vid_controllers_path)

from img2vidController import Img2VidController

logger = logging.getLogger(__name__)

class Img2VidHandler:
    """Handler for img2vid service requests"""
    
    def __init__(self):
        self.controller = Img2VidController()
        self.available_tasks = [
            "validateWorkflow",
            "generateVideo", 
            "listWorkflows",
            "startJob"
        ]
    
    async def handle_request(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle img2vid requests and route to appropriate controller method"""
        try:
            logger.info(f"Img2Vid handler processing task: {task}")
            
            if task == "validateWorkflow":
                return await self._handle_validate_workflow(data)
            elif task == "generateVideo":
                return await self._handle_generate_video(data)
            elif task == "listWorkflows":
                return await self._handle_list_workflows(data)
            elif task == "startJob":
                return await self._handle_start_job(data)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Img2Vid handler failed for task {task}: {e}")
            raise e
    
    async def _handle_validate_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow validation request"""
        if "workflowName" not in data:
            raise ValueError("workflowName is required for validateWorkflow task")
        
        workflow_name = data["workflowName"]
        logger.info(f"Validating workflow: {workflow_name}")
        
        # Pass to controller - using proper enterprise pattern
        result = await self.controller.validate_workflow(workflow_name)
        
        return {
            "task": "validateWorkflow",
            "workflowName": workflow_name,
            "validation": result
        }
    
    async def _handle_generate_video(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle video generation request"""
        # TODO: Implement when ready
        return {
            "task": "generateVideo", 
            "status": "not_implemented",
            "message": "Video generation not yet implemented"
        }
    
    async def _handle_list_workflows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list workflows request"""
        workflows = await self.controller.list_workflows()
        
        return {
            "task": "listWorkflows",
            "workflows": workflows
        }
    
    async def _handle_start_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start job request"""
        required_fields = ["fileName", "prompt"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"{field} is required for startJob task")
        
        file_name = data["fileName"]
        prompt = data["prompt"]
        uid = data.get("uid")  # Optional field
        
        logger.info(f"Starting img2vid job: file={file_name}, uid={uid}")
        
        # Pass to controller
        result = await self.controller.start_job(file_name, prompt, uid)
        
        return {
            "task": "startJob",
            "job_id": result.get("job_id"),
            "status": result.get("status", "pending"),
            "fileName": file_name,
            "prompt": prompt
        }
    
    def get_available_tasks(self) -> list:
        """Get list of available tasks for this handler"""
        return self.available_tasks