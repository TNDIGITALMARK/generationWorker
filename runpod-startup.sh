#!/bin/bash

# Clone your project
cd /workspace
git clone https://github.com/your-username/synthGen.git
cd synthGen/generationWorker

# Install/update dependencies
pip install -r python_service/requirements.txt
npm install

# Build if needed
npm run build

echo "Setup complete! Ready to work."