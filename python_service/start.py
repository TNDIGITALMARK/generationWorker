#!/usr/bin/env python3
import sys
import os

def start_python_service():
    print("Starting Image Worker Python Service...")
    
    # Import our service first (before adding ComfyUI to path)
    from main import app
    import uvicorn
    
    # Add ComfyUI to Python path after our imports
    comfy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ComfyUI")
    if comfy_path not in sys.path:
        sys.path.append(comfy_path)
    
    print(f"Added ComfyUI path: {comfy_path}")
    
    # Start the FastAPI service
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    start_python_service()