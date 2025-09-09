import asyncio
import aiohttp
import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ComfyUIValidationService:
    """Service for validating ComfyUI workflows against the running ComfyUI instance"""
    
    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188"):
        self.comfyui_url = comfyui_url
        self.workflows_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workflows")
    
    async def validate_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Validate a workflow by checking:
        1. Workflow file exists and is valid JSON
        2. ComfyUI can load and validate the workflow
        3. All required nodes/models are available
        """
        try:
            # Load workflow file
            workflow_data = await self._load_workflow_file(workflow_name)
            if not workflow_data:
                return {
                    "valid": False,
                    "workflow_name": workflow_name,
                    "errors": [f"Workflow file '{workflow_name}.json' not found or invalid"],
                    "details": {}
                }
            
            # Validate against ComfyUI
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
    
    async def _load_workflow_file(self, workflow_name: str) -> Dict[str, Any]:
        """Load and parse workflow JSON file"""
        try:
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_name}.json")
            
            if not os.path.exists(workflow_path):
                logger.warning(f"Workflow file not found: {workflow_path}")
                return None
            
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            logger.info(f"Successfully loaded workflow: {workflow_name}")
            return workflow_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workflow {workflow_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_name}: {e}")
            return None
    
    async def _validate_with_comfyui(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow against ComfyUI API"""
        try:
            # Remove metadata before sending to ComfyUI
            clean_workflow = {k: v for k, v in workflow_data.items() if k != "workflow_metadata"}
            
            # Test basic connectivity first
            async with aiohttp.ClientSession() as session:
                # Check if ComfyUI is responding
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
                
                # Validate workflow structure with ComfyUI
                try:
                    # Use the /prompt endpoint to validate (without actually executing)
                    payload = {
                        "prompt": clean_workflow,
                        "client_id": "validation-service"
                    }
                    
                    async with session.post(
                        f"{self.comfyui_url}/prompt", 
                        json=payload,
                        timeout=10
                    ) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            # Successful validation
                            result = json.loads(response_text)
                            return {
                                "valid": True,
                                "errors": [],
                                "details": {
                                    "connectivity": True,
                                    "prompt_id": result.get("prompt_id"),
                                    "number": result.get("number"),
                                    "validation_method": "prompt_submission"
                                }
                            }
                        else:
                            # Parse error response
                            try:
                                error_data = json.loads(response_text)
                                error_details = error_data.get("error", {})
                                return {
                                    "valid": False,
                                    "errors": [
                                        f"ComfyUI validation failed: {error_details.get('message', response_text)}"
                                    ],
                                    "details": {
                                        "connectivity": True,
                                        "validation_method": "prompt_submission",
                                        "error_details": error_details
                                    }
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
                        "errors": [f"Workflow validation request failed: {str(e)}"],
                        "details": {"connectivity": True}
                    }
                    
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"ComfyUI validation failed: {str(e)}"],
                "details": {}
            }
    
    def _extract_required_models(self, workflow_data: Dict[str, Any]) -> List[str]:
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
    
    async def list_available_workflows(self) -> List[str]:
        """List all available workflow files"""
        try:
            if not os.path.exists(self.workflows_dir):
                return []
            
            workflows = []
            for filename in os.listdir(self.workflows_dir):
                if filename.endswith('.json'):
                    workflow_name = filename[:-5]  # Remove .json extension
                    workflows.append(workflow_name)
            
            return sorted(workflows)
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []