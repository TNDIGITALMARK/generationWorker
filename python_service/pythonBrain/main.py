from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from .controllers.routingController import RoutingController

logger = logging.getLogger(__name__)

app = FastAPI(title="Python Brain - Internal Service Router", version="1.0.0")
router = RoutingController()

class ServiceRequest(BaseModel):
    service: str  # e.g., "text2Image"
    task: str     # e.g., "validateWorkflow", "generateImage"
    data: Dict[str, Any]  # Service-specific data

class WorkflowValidationRequest(BaseModel):
    service: str = "text2Image"
    task: str = "validateWorkflow"
    data: Dict[str, Any]  # Contains workflowName, etc.

@app.get("/")
async def root():
    return {"message": "Python Brain - Service Router", "status": "ready"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services_available": ["text2Image"],
        "tasks_available": ["validateWorkflow"]
    }

@app.post("/process")
async def process_request(request: ServiceRequest):
    """Main entry point for all service requests"""
    try:
        logger.info(f"Processing request - Service: {request.service}, Task: {request.task}")
        
        # Route request to appropriate handler
        result = await router.route_request(
            service=request.service,
            task=request.task, 
            data=request.data
        )
        
        return {
            "success": True,
            "service": request.service,
            "task": request.task,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Request processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text2image/validate")  
async def validate_text2image_workflow(request: WorkflowValidationRequest):
    """Convenience endpoint for text2image workflow validation"""
    try:
        # Ensure required fields are present
        if "workflowName" not in request.data:
            raise HTTPException(status_code=400, detail="workflowName is required")
        
        # Route through main processing system
        result = await router.route_request(
            service=request.service,
            task=request.task,
            data=request.data
        )
        
        return {
            "success": True,
            "workflow_name": request.data["workflowName"],
            "validation_result": result
        }
        
    except Exception as e:
        logger.error(f"Workflow validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))