from typing import Dict, Any, List
import logging
import sys
import os

# Use absolute path approach to import the controller
import importlib.util

python_service_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
controller_path = os.path.join(python_service_root, 'text2image', 'controllers', 'text2ImageController.py')

# Simple direct ComfyUI integration
import aiohttp
import json

class Text2ImageController:
    def __init__(self):
        self.comfyui_url = "http://127.0.0.1:8188"
        self.workflows_dir = os.path.join(python_service_root, 'text2image', 'workflows')
    
    async def validate_workflow(self, workflow_name: str):
        """Validate workflow against ComfyUI API directly"""
        try:
            # Load workflow file
            workflow_data = await self._load_workflow_file(workflow_name)
            if not workflow_data:
                return {
                    "valid": False,
                    "workflow_name": workflow_name,
                    "errors": [f"Workflow file '{workflow_name}.json' not found"],
                    "details": {}
                }
            
            # Test ComfyUI connectivity and validate workflow
            validation_result = await self._validate_with_comfyui(workflow_data)
            
            return {
                "valid": validation_result["valid"],
                "workflow_name": workflow_name,
                "details": {
                    "workflow_metadata": workflow_data.get("workflow_metadata", {}),
                    "node_count": len([k for k in workflow_data.keys() if k != "workflow_metadata"]),
                    "comfyui_validation": validation_result.get("details", {}),
                    "required_models": self._extract_required_models(workflow_data)
                },
                "errors": validation_result.get("errors", [])
            }
        except Exception as e:
            logger.error(f"Workflow validation failed for {workflow_name}: {e}")
            return {
                "valid": False,
                "workflow_name": workflow_name,
                "errors": [f"Validation error: {str(e)}"],
                "details": {}
            }
    
    async def _load_workflow_file(self, workflow_name: str):
        """Load workflow JSON file"""
        try:
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                logger.error(f"Workflow file not found at: {workflow_path}")
                return None
            
            with open(workflow_path, 'r') as f:
                logger.info(f"Successfully loaded workflow: {workflow_name}")
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_name}: {e}")
            return None
    
    async def _validate_with_comfyui(self, workflow_data: Dict[str, Any]):
        """Validate workflow against ComfyUI API"""
        try:
            # Remove metadata before sending to ComfyUI
            clean_workflow = {k: v for k, v in workflow_data.items() if k != "workflow_metadata"}
            
            async with aiohttp.ClientSession() as session:
                # Test connectivity first
                try:
                    async with session.get(f"{self.comfyui_url}/system_stats", timeout=5) as response:
                        if response.status != 200:
                            return {
                                "valid": False,
                                "errors": [f"ComfyUI not responding (status: {response.status})"],
                                "details": {"connectivity": False}
                            }
                except Exception as e:
                    return {
                        "valid": False,
                        "errors": [f"Cannot connect to ComfyUI: {str(e)}"],
                        "details": {"connectivity": False}
                    }
                
                # Submit workflow to ComfyUI for validation
                try:
                    payload = {"prompt": clean_workflow, "client_id": "validation-service"}
                    async with session.post(f"{self.comfyui_url}/prompt", json=payload, timeout=10) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            result = json.loads(response_text)
                            return {
                                "valid": True,
                                "errors": [],
                                "details": {
                                    "connectivity": True,
                                    "prompt_id": result.get("prompt_id"),
                                    "validation_method": "comfyui_prompt_submission"
                                }
                            }
                        else:
                            try:
                                error_data = json.loads(response_text)
                                return {
                                    "valid": False,
                                    "errors": [f"ComfyUI validation failed: {error_data.get('error', {}).get('message', response_text)}"],
                                    "details": {"connectivity": True, "error_details": error_data}
                                }
                            except:
                                return {
                                    "valid": False,
                                    "errors": [f"ComfyUI error (status {response.status}): {response_text[:200]}"],
                                    "details": {"connectivity": True}
                                }
                except Exception as e:
                    return {
                        "valid": False,
                        "errors": [f"Validation request failed: {str(e)}"],
                        "details": {"connectivity": True}
                    }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"ComfyUI validation failed: {str(e)}"],
                "details": {}
            }
    
    def _extract_required_models(self, workflow_data: Dict[str, Any]):
        """Extract required model files from workflow"""
        required_models = []
        for node_id, node_data in workflow_data.items():
            if node_id == "workflow_metadata":
                continue
            if node_data.get("class_type") == "CheckpointLoaderSimple":
                ckpt_name = node_data.get("inputs", {}).get("ckpt_name")
                if ckpt_name:
                    required_models.append(ckpt_name)
        return required_models
    
    async def list_workflows(self):
        """List all available workflow files"""
        try:
            if not os.path.exists(self.workflows_dir):
                return []
            workflows = []
            for filename in os.listdir(self.workflows_dir):
                if filename.endswith('.json'):
                    workflows.append(filename[:-5])  # Remove .json extension
            return sorted(workflows)
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []

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
        
        # Pass to controller
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