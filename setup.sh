#!/bin/bash

# Advanced Video Automation System - Quick Start Script

echo "🚀 Advanced Video Automation System - Quick Start Setup"
echo "=========================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Some operations may require sudo privileges"
fi

# Check Python installation
echo "📋 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check pip installation
echo "📋 Checking pip installation..."
if command -v pip3 &> /dev/null; then
    echo "✅ pip found"
else
    echo "❌ pip not found. Installing pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Check FFmpeg installation
echo "📋 Checking FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo "✅ FFmpeg found: $FFMPEG_VERSION"
else
    echo "❌ FFmpeg not found. Installing FFmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
fi

# Check for uv (primary package manager)
echo "📋 Checking for uv (primary package manager)..."
if command -v uv &> /dev/null; then
    echo "✅ uv found - using uv for package management"
    UV_FOUND=true
else
    echo "ℹ️  uv not found. You can install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    UV_FOUND=false
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ "$UV_FOUND" = true ]; then
    uv pip install -r requirements.txt
else
    pip3 install -r requirements.txt
fi

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p output/-1003737951848/pending_photos
mkdir -p logs

echo "✅ Directory structure created"

# Check for client.json
echo "🔐 Checking YouTube API credentials..."
if [ -f "client.json" ]; then
    echo "✅ client.json found"
else
    echo "⚠️  client.json not found!"
    echo "   Please follow these steps:"
    echo "   1. Go to https://console.cloud.google.com/"
    echo "   2. Create a project and enable YouTube Data API v3"
    echo "   3. Create OAuth 2.0 credentials"
    echo "   4. Download the client secrets JSON file"
    echo "   5. Save it as 'client.json' in this directory"
    echo ""
    read -p "Press Enter to continue after setting up client.json..."
fi

# Check for uv (optional)
echo "📋 Checking for uv status..."
if [ "$UV_FOUND" = true ]; then
    echo "✅ uv is active - you can use 'uv run' for faster execution"
else
    echo "ℹ️  uv not found. You can install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Then run: uv pip install -r requirements.txt"
fi

# Create log files
echo "📋 Creating log files..."
touch logs/video_automation_pipeline.log
touch logs/video_automation_download.log
touch logs/video_automation_processing.log
touch logs/video_automation_upload.log
touch logs/video_automation_errors.log

echo "✅ Log files created"

# Test imports
echo "🧪 Testing Python imports..."
python3 -c "
import sys
try:
    import cv2
    import librosa
    import numpy as np
    from googleapiclient.discovery import build
    print('✅ All core imports successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ System ready!"
else
    echo "❌ Some imports failed. Please check the error above."
    exit 1
fi

# Display next steps
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Ensure your Telegram channel is configured in video_fetch.py"
echo "2. Make sure client.json is properly set up for YouTube API"
echo "3. Run the system: uv run video_fetch.py"
echo ""
echo ""
echo ""
echo "  - Run system:           uv run video_fetch.py"
echo "  - Test beat sync:       uv run beat_sync.py --photos ./test_photos --audio 'https://youtube.com/watch?v=example' --output ./output"
echo "  - Test video processing: uv run viralize_video.py --input ./test_video.mp4 --output ./output/test_processed.mp4"
echo ""
echo "📁 Logs will be saved in the 'logs/' directory"
echo "📁 Processed videos will be saved in 'output/' directory"
echo ""
echo "Happy content creation! 🚀"