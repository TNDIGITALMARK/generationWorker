from typing import Dict, Any, List
import logging
import sys
import os

# Import the proper Text2ImageController
python_service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(python_service_root, 'text2image'))

from controllers.text2ImageController import Text2ImageController

logger = logging.getLogger(__name__)

class Text2ImageHandler:
    """Handler for text2Image service requests"""
    
    def __init__(self):
        self.controller = Text2ImageController()
        self.available_tasks = [
            "validateWorkflow",
            "generateImage", 
            "listWorkflows"
        ]
    
    async def handle_request(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text2Image requests and route to appropriate controller method"""
        try:
            logger.info(f"Text2Image handler processing task: {task}")
            
            if task == "validateWorkflow":
                return await self._handle_validate_workflow(data)
            elif task == "generateImage":
                return await self._handle_generate_image(data)
            elif task == "listWorkflows":
                return await self._handle_list_workflows(data)
            else:
                raise ValueError(f"Unknown task: {task}")
                
        except Exception as e:
            logger.error(f"Text2Image handler failed for task {task}: {e}")
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
    
    async def _handle_generate_image(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image generation request"""
        # TODO: Implement when ready
        return {
            "task": "generateImage", 
            "status": "not_implemented",
            "message": "Image generation not yet implemented"
        }
    
    async def _handle_list_workflows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list workflows request"""
        workflows = await self.controller.list_workflows()
        
        return {
            "task": "listWorkflows",
            "workflows": workflows
        }
    
    def get_available_tasks(self) -> list:
        """Get list of available tasks for this handler"""
        return self.available_tasks