#!/bin/bash

# Configuration
MANIM_RENDER_DIR="engines/manim/media/videos"
REMOTION_PUBLIC_DIR="engines/remotion/public/manim"

# 1. Create target directory
mkdir -p "$REMOTION_PUBLIC_DIR"

# 2. Sync Manim renders (recursive search for mp4s)
echo "🚀 Syncing all engine outputs to Remotion..."
find engines -name "*.mp4" -exec cp {} "$REMOTION_PUBLIC_DIR/" \;

# 3. List results
echo "✅ Sync complete. Ready for composition."
ls -l "$REMOTION_PUBLIC_DIR"
