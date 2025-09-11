# RunPod Deployment Guide

## 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-dockerhub-username/synthgen-worker:latest .

# Push to Docker Hub
docker push your-dockerhub-username/synthgen-worker:latest
```

## 2. RunPod Configuration

### Environment Variables (RunPod Secrets)
Set these in RunPod's Environment Variables section:

**Required:**
- `API_KEY` - Your API keys
- `DATABASE_URL` - Database connection string
- `FIREBASE_ADMIN_KEY_PATH` - Path to Firebase admin key (optional, defaults to built-in path)

**Optional (with defaults):**
- `COMFYUI_PORT` - ComfyUI port (default: 8188)
- `PYTHON_SERVICE_PORT` - Python service port (default: 8000) 
- `NODE_SERVICE_PORT` - Node service port (default: 3000)
- `COMFYUI_URL` - ComfyUI URL (default: http://localhost:8188)

### Pod Setup
1. Use custom Docker image: `your-dockerhub-username/synthgen-worker:latest`
2. Set environment variables above
3. Expose ports: 3000, 8000, 8188
4. Start pod

## 3. Usage

Once pod starts:
```bash
cd /workspace/generationWorker

# Everything is already installed and built!
# Just run:
npm run dev

# Or activate Python venv:
cd python_service
source venv/bin/activate
python main.py
```

## 4. Development

- Code is in `/workspace/generationWorker`
- Python venv: `cd python_service && source venv/bin/activate`
- Node deps already installed
- Built and ready to go
- `.env` files auto-created from RunPod secrets

## 5. Updating Code

To get latest code in running pod:
```bash
cd /workspace/generationWorker
git pull origin main
npm run build  # if needed
```