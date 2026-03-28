#!/bin/bash

# Configuration
BRIEFS_DIR=".agents/briefs"
TYPE=${1:-technical}
NAME=${2:-new_video}

# 1. Ensure directory exists
mkdir -p "$BRIEFS_DIR"

# 2. Template content
cat <<EOF > "$BRIEFS_DIR/$NAME.yaml"
type: $TYPE
title: "New Video Project"
subtitle: "Description of the flow"
duration_sec: 30
aspect: "16:9"
fps: 60
resolution: "1920x1080"

brand:
  tokens: "assets/brand/tokens.json"

scenes:
  - id: "intro"
    engine: manim
    duration_sec: 5
    description: "Intro scene with title"
  - id: "reveal"
    engine: motion-canvas
    duration_sec: 5
    description: "Logo reveal"

composition:
  engine: remotion
EOF

echo "🚀 Created new brief at: $BRIEFS_DIR/$NAME.yaml"
echo "👉 Run with: python3 scripts/run_pipeline.py --brief $BRIEFS_DIR/$NAME.yaml"
