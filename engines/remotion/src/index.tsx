import React from 'react';
import { registerRoot, Composition } from 'remotion';
import { TargetedCinematicNarrative } from './compositions/TargetedCinematicNarrative';
import { TargetedStillComposition } from './compositions/TargetedStillComposition';
import { REMOTION_TARGET_ORDER, getTargetDurationInFrames, type RemotionTargetConfig } from './targets';

const Root: React.FC = () => {
  const makeCompositionProps = (target: RemotionTargetConfig) => ({
    target: target.id,
    renderManifest: {
      target: target.id,
      targetId: target.id,
      targetKind: target.kind,
    },
    ...(target.kind === 'still'
      ? {
          frameOverride: target.defaultStillFrame,
          renderManifest: {
            target: target.id,
            targetId: target.id,
            targetKind: target.kind,
            frameOverride: target.defaultStillFrame,
            stillFrame: target.defaultStillFrame,
          },
        }
      : {}),
  });

  return (
    <>
      {REMOTION_TARGET_ORDER.map((target) => {
        const compositionProps = makeCompositionProps(target);
        const requestedDuration = (compositionProps.renderManifest as {durationInFrames?: number; duration_in_frames?: number} | undefined)?.durationInFrames ?? (compositionProps.renderManifest as {durationInFrames?: number; duration_in_frames?: number} | undefined)?.duration_in_frames;

        return (
          <Composition
            key={target.compositionId}
            id={target.compositionId}
            component={
              target.id === 'linkedin_feed_4_5' || target.id === 'youtube_thumbnail_16_9'
                ? TargetedStillComposition
                : TargetedCinematicNarrative
            }
            durationInFrames={getTargetDurationInFrames(target, requestedDuration)}
            fps={target.fps}
            width={target.width}
            height={target.height}
            defaultProps={compositionProps}
            calculateMetadata={({props}) => {
              const manifest = props?.renderManifest as {durationInFrames?: number; duration_in_frames?: number} | undefined;
              const requestedFrames = Number(manifest?.durationInFrames ?? manifest?.duration_in_frames);

              return {
                durationInFrames:
                  Number.isFinite(requestedFrames) && requestedFrames > 0
                    ? requestedFrames
                    : target.durationInFrames,
              };
            }}
          />
        );
      })}
    </>
  );
};

registerRoot(Root);
