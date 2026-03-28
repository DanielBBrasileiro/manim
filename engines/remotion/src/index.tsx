import React from 'react';
import { registerRoot, Composition } from 'remotion';
import { CinematicNarrative } from './compositions/CinematicNarrative';
import { v4 } from './theme';

const Root: React.FC = () => {
  const { width, height } = v4.layout.formats.vertical_9_16;
  
  return (
    <>
      <Composition
        id="CinematicNarrative-v4"
        component={CinematicNarrative}
        durationInFrames={900} // 15s at 60fps
        fps={60}
        width={width}
        height={height}
      />
    </>
  );
};

registerRoot(Root);
