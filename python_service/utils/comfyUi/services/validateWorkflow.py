from typing import Dict, Any
import logging
import requests
import asyncio
import json

logger = logging.getLogger(__name__)

class WorkflowValidationService:
    """Service for validating workflows with ComfyUI API"""
    
    def __init__(self, comfy_host: str = "localhost", comfy_port: int = 8188):
        self.comfy_url = f"http://{comfy_host}:{comfy_port}"
        self.prompt_endpoint = f"{self.comfy_url}/prompt"  # Use /prompt for validation
        self.timeout = 30  # 30 second timeout
    
    async def validate_with_comfyui(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow with ComfyUI validation endpoint"""
        try:
            logger.info(f"Validating workflow with ComfyUI at {self.prompt_endpoint}")
            
            # Prepare validation payload
            validation_payload = {
                "prompt": workflow_data
            }
            
            # Make async request to ComfyUI
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._make_validation_request, 
                validation_payload
            )
            
            return self._parse_validation_response(response)
            
        except Exception as e:
            logger.error(f"ComfyUI validation request failed: {e}")
            return {
                "valid": False,
                "details": {
                    "error": "ComfyUI API not available or validation failed",
                    "comfy_url": self.comfy_url
                },
                "errors": [str(e)],
                "response": {}
            }
    
    def _make_validation_request(self, payload: Dict[str, Any]) -> requests.Response:
        """Make synchronous validation request to ComfyUI"""
        try:
            response = requests.post(
                self.prompt_endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to ComfyUI at {self.comfy_url}: {e}")
            raise Exception(f"ComfyUI service unavailable at {self.comfy_url}")
        except requests.exceptions.Timeout as e:
            logger.error(f"ComfyUI validation timeout: {e}")
            raise Exception("ComfyUI validation timeout")
        except Exception as e:
            logger.error(f"ComfyUI request failed: {e}")
            raise e
    
    def _parse_validation_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse ComfyUI validation response"""
        try:
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                # Successful validation
                return {
                    "valid": True,
                    "details": {
                        "status_code": response.status_code,
                        "message": "Workflow validation successful"
                    },
                    "errors": [],
                    "response": response_data
                }
            else:
                # Validation failed
                return {
                    "valid": False,
                    "details": {
                        "status_code": response.status_code,
                        "message": "Workflow validation failed"
                    },
                    "errors": [response_data.get("error", "Unknown validation error")],
                    "response": response_data
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ComfyUI response: {e}")
            return {
                "valid": False,
                "details": {
                    "status_code": response.status_code,
                    "message": "Invalid JSON response from ComfyUI"
                },
                "errors": [f"JSON decode error: {str(e)}"],
                "response": {"raw_response": response.text}
            }
        except Exception as e:
            logger.error(f"Failed to process ComfyUI response: {e}")
            return {
                "valid": False,
                "details": {
                    "message": "Failed to process ComfyUI response"
                },
                "errors": [str(e)],
                "response": {}
            }