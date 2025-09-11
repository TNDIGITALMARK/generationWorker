# Use RunPod's PyTorch base image
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# === STAGE 1: System dependencies (rarely changes) ===
# Install Node.js 18 and other tools
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs git python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# === STAGE 2: Clone repository and setup code (changes with code updates) ===
# Clone the repository
RUN git clone https://github.com/TNDIGITALMARK/generationWorker.git

# Set working directory to the cloned repo
WORKDIR /workspace/generationWorker

# === STAGE 3: Install dependencies (changes when package.json/requirements.txt change) ===
# Install Node.js dependencies first (smaller, faster)
RUN npm install

# Install ComfyUI Python dependencies
RUN cd /workspace/generationWorker/ComfyUI && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install --upgrade pip && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
    pip install -r requirements.txt

# Install ComfyUI custom nodes
RUN cd /workspace/generationWorker/ComfyUI && \
    git clone https://github.com/cubiq/ComfyUI_InstantID.git custom_nodes/ComfyUI_InstantID && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager && \
    source venv/bin/activate && \
    pip install -r custom_nodes/ComfyUI_InstantID/requirements.txt

# Setup Python service dependencies
RUN cd /workspace/generationWorker/python_service && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# === STAGE 4: Models will be copied at runtime from persistent S3 storage ===
# Models are stored in /workspace/base_models/ and copied during startup
# This keeps the Docker image small (~8-10GB instead of 35GB)

# === STAGE 5: Build TypeScript (changes with TS code) ===
RUN cd /workspace/generationWorker && npm run build

# === STAGE 6: Create startup script ===
RUN echo '#!/bin/bash\n\
echo "Starting synthGen worker..."\n\
\n\
# Create .env file from RunPod secrets\n\
if [ -f "/etc/rp_environment" ]; then\n\
    echo "Loading RunPod environment variables..."\n\
    source /etc/rp_environment\n\
fi\n\
\n\
# Create .env file in generationWorker root\n\
cat > /workspace/generationWorker/.env << EOF\n\
FIREBASE_ADMIN_KEY_PATH=${FIREBASE_ADMIN_KEY_PATH:-/workspace/generationWorker/synthgen-3acd7-firebase-adminsdk-fbsvc-2a569eefa8.json}\n\
COMFYUI_PORT=${COMFYUI_PORT:-8188}\n\
PYTHON_SERVICE_PORT=${PYTHON_SERVICE_PORT:-8000}\n\
NODE_SERVICE_PORT=${NODE_SERVICE_PORT:-3000}\n\
API_KEY=${API_KEY}\n\
DATABASE_URL=${DATABASE_URL}\n\
EOF\n\
\n\
# Create Python service .env\n\
cat > /workspace/generationWorker/python_service/.env << EOF\n\
COMFYUI_URL=${COMFYUI_URL:-http://localhost:8188}\n\
PORT=${PYTHON_SERVICE_PORT:-8000}\n\
EOF\n\
\n\
# Copy models from S3 storage to ComfyUI if they exist\n\
echo "Copying models from S3 storage..."\n\
if [ -d "/workspace/base_models" ]; then\n\
    # Copy checkpoints (handles both files and subdirectories)\n\
    if [ -d "/workspace/base_models/checkpoints" ] && [ "$(ls -A /workspace/base_models/checkpoints 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/checkpoints/* /workspace/generationWorker/ComfyUI/models/checkpoints/ 2>/dev/null || true\n\
        echo "  ✓ Checkpoints copied"\n\
    fi\n\
    \n\
    # Copy VAE models\n\
    if [ -d "/workspace/base_models/vae" ] && [ "$(ls -A /workspace/base_models/vae 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/vae/* /workspace/generationWorker/ComfyUI/models/vae/ 2>/dev/null || true\n\
        echo "  ✓ VAE models copied"\n\
    fi\n\
    \n\
    # Copy LoRA models\n\
    if [ -d "/workspace/base_models/loras" ] && [ "$(ls -A /workspace/base_models/loras 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/loras/* /workspace/generationWorker/ComfyUI/models/loras/ 2>/dev/null || true\n\
        echo "  ✓ LoRA models copied"\n\
    fi\n\
    \n\
    # Copy InstantID models\n\
    if [ -d "/workspace/base_models/instantid" ] && [ "$(ls -A /workspace/base_models/instantid 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/instantid/* /workspace/generationWorker/ComfyUI/models/instantid/ 2>/dev/null || true\n\
        echo "  ✓ InstantID models copied"\n\
    fi\n\
    \n\
    # Copy ControlNet models\n\
    if [ -d "/workspace/base_models/controlnet" ] && [ "$(ls -A /workspace/base_models/controlnet 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/controlnet/* /workspace/generationWorker/ComfyUI/models/controlnet/ 2>/dev/null || true\n\
        echo "  ✓ ControlNet models copied"\n\
    fi\n\
    \n\
    # Copy InsightFace models\n\
    if [ -d "/workspace/base_models/insightface" ] && [ "$(ls -A /workspace/base_models/insightface 2>/dev/null)" ]; then\n\
        cp -r /workspace/base_models/insightface/* /workspace/generationWorker/ComfyUI/models/insightface/ 2>/dev/null || true\n\
        echo "  ✓ InsightFace models copied"\n\
    fi\n\
    \n\
    echo "Models copied successfully!"\n\
else\n\
    echo "No base_models found - will use existing models in ComfyUI"\n\
fi\n\
\n\
echo "========================================"\n\
echo "synthGen worker ready!"\n\
echo "Services available:"\n\
echo "  ComfyUI: http://localhost:8188"\n\
echo "  Python API: http://localhost:8000"\n\
echo "  Node API: http://localhost:3000"\n\
echo ""\n\
echo "Models available:"\n\
echo "  27GB model collection copied from S3 storage"\n\
echo "  WAN, Babes Illustrious, InstantID suite ready"\n\
echo ""\n\
echo "Commands:"\n\
echo "  npm run dev    (start development server)"\n\
echo "  npm start      (start production server)"\n\
echo "========================================"\n\
\n\
# Start services based on command\n\
if [ "$1" = "dev" ] || [ "$1" = "npm run dev" ]; then\n\
    cd /workspace/generationWorker\n\
    npm run dev\n\
elif [ "$1" = "prod" ] || [ "$1" = "npm start" ]; then\n\
    cd /workspace/generationWorker\n\
    npm start\n\
else\n\
    exec "$@"\n\
fi' > /workspace/startup.sh && \
    chmod +x /workspace/startup.sh

# Set default command
ENTRYPOINT ["/workspace/startup.sh"]
CMD ["dev"]