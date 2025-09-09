from typing import Dict, Any
import logging
import os
import json
import sys

# Add utils path for ComfyUI utilities
utils_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)

from comfyUi.controllers.comfyUtilController import ComfyUtilController

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for handling workflow validation operations"""
    
    def __init__(self):
        self.comfy_util = ComfyUtilController()
        self.workflows_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workflows')
    
    async def validate_workflow_by_name(self, workflow_name: str) -> Dict[str, Any]:
        """Load and validate a workflow by name"""
        try:
            logger.info(f"Validating workflow: {workflow_name}")
            
            # Load workflow JSON
            workflow_data = await self._load_workflow(workflow_name)
            
            # Call ComfyUI validation utility
            validation_result = await self.comfy_util.validate_workflow(workflow_data)
            
            return {
                "valid": validation_result.get("valid", False),
                "workflow_name": workflow_name,
                "details": validation_result.get("details", {}),
                "errors": validation_result.get("errors", []),
                "comfy_response": validation_result.get("response", {})
            }
            
        except Exception as e:
            logger.error(f"Validation service failed for {workflow_name}: {e}")
            return {
                "valid": False,
                "workflow_name": workflow_name,
                "details": {},
                "errors": [str(e)],
                "comfy_response": {}
            }
    
    async def _load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Load workflow JSON from file"""
        try:
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            logger.info(f"Loaded workflow: {workflow_name}")
            return workflow_data
            
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_name}: {e}")
            raise e
    
    async def validate_workflow_json(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow JSON directly (without loading from file)"""
        try:
            # Call ComfyUI validation utility
            validation_result = await self.comfy_util.validate_workflow(workflow_data)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Direct JSON validation failed: {e}")
            return {
                "valid": False,
                "details": {},
                "errors": [str(e)],
                "comfy_response": {}
            }