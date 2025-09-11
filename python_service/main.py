from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
import sys
import os

# Add parent directory to path to import firebase config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comfy_integration import comfy_manager
from firebase.firebaseAdmin import initialize_firebase, test_firebase_connection, get_db
from pythonBrain.controllers.routingController import RoutingController

app = FastAPI(title="Image Worker Python Service", version="1.0.0")
router = RoutingController()

@app.on_event("startup")
async def startup_event():
    """Initialize ComfyUI and Firebase on startup"""
    try:
        await comfy_manager.initialize()
    except Exception as e:
        print(f"Warning: ComfyUI initialization failed: {e}")
        print("Service will start but ComfyUI features will be unavailable")
    
    try:
        initialize_firebase()
        print("Firebase initialized in Python service")
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")
        print("Service will start but Firebase features will be unavailable")

class Text2ImageValidationRequest(BaseModel):
    workflowName: str

class Img2VidValidationRequest(BaseModel):
    workflowName: str

class Img2VidStartJobRequest(BaseModel):
    fileName: str
    prompt: str
    uid: Optional[str] = None

class InstantIDStartJobRequest(BaseModel):
    referenceImage: str
    prompt: str
    uid: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Image Worker Python Service", "status": "ready"}

@app.get("/health")
async def health():
    comfy_health = await comfy_manager.health_check()
    firebase_health = await test_firebase_connection()
    
    return {
        "status": "healthy",
        "models_loaded": comfy_health.get("initialized", False),
        "comfyui": comfy_health,
        "firebase": firebase_health
    }

@app.post("/text2image/validate")
async def validate_text2image_workflow(request: Text2ImageValidationRequest):
    """Validate text2image workflow"""
    try:
        # Route through pythonBrain
        result = await router.route_request(
            service="text2Image",
            task="validateWorkflow",
            data={"workflowName": request.workflowName}
        )
        
        return {
            "success": True,
            "workflow_name": request.workflowName,
            "validation_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/img2vid/validate")
async def validate_img2vid_workflow(request: Img2VidValidationRequest):
    """Validate img2vid workflow"""
    try:
        # Route through pythonBrain
        result = await router.route_request(
            service="img2vid",
            task="validateWorkflow",
            data={"workflowName": request.workflowName}
        )
        
        return {
            "success": True,
            "workflow_name": request.workflowName,
            "validation_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/img2vid/start-job")
async def start_img2vid_job(request: Img2VidStartJobRequest):
    """Start img2vid job"""
    try:
        # Route through pythonBrain
        result = await router.route_request(
            service="img2vid",
            task="startJob",
            data={
                "fileName": request.fileName,
                "prompt": request.prompt,
                "uid": request.uid
            }
        )
        
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "status": "pending",
            "message": "Job started successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text2image/start-job-instantId")
async def start_instantid_job(request: InstantIDStartJobRequest):
    """Start InstantID job"""
    try:
        # Route through pythonBrain
        result = await router.route_request(
            service="text2Image",
            task="startJobInstantID",
            data={
                "referenceImage": request.referenceImage,
                "prompt": request.prompt,
                "uid": request.uid
            }
        )
        
        return {
            "success": True,
            "job_id": result.get("job_id"),
            "status": "pending",
            "message": "InstantID job started successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# Trigger restart - path fix applied

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)