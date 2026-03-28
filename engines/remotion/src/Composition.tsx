import React from 'react';
import { AbsoluteFill, Video, staticFile, spring, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import rawTokens from '../../../assets/brand/tokens.json';
const tokens = rawTokens as any;
import timingElite from '../../../assets/brand/timing_elite.json';
import timingIndustrial from '../../../assets/brand/timing_industrial.json';
import timing from '../../../assets/brand/timing_python.json';

// --- Professional UI Components ---

const GlassLabel: React.FC<{ 
    text: string; 
    opacity: number; 
    translateY?: number; 
}> = ({ text, opacity, translateY = 0 }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  
  // Spring transition for the Y-axis and Scale (Elite Physics)
  const entryS = spring({ 
    frame: opacity > 0 ? frame : 0, 
    fps, 
    config: { stiffness: 120, damping: 14 } 
  });
  
  const scale = interpolate(entryS, [0, 1], [0.95, 1]);

  return (
    <div style={{
      color: tokens.colors.text,
      fontSize: '44px',
      fontWeight: 700,
      fontFamily: tokens.fonts.heading_font,
      opacity: opacity,
      transform: `translateY(${translateY}px) scale(${scale})`,
      backgroundColor: 'rgba(9, 9, 11, 0.6)', // Off-black translucent
      padding: '20px 40px',
      borderRadius: tokens.materials.radius,
      backdropFilter: `blur(${tokens.materials.blur})`,
      border: `1px solid ${tokens.colors.primary}22`,
      boxShadow: `0 20px 80px rgba(0,0,0,0.8), inset 0 0 20px ${tokens.colors.primary}11`,
      letterSpacing: '-0.02em',
      textTransform: 'uppercase'
    }}>
      {text}
    </div>
  );
};

export const ElitePythonDB: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const getFrame = (name: string) => {
        const event = (timingElite as any[]).find((e: any) => e.event === name);
        return event ? (event.timestamp_ms / 1000) * fps : 0;
    };

    const sourceReady = getFrame("source_ready");
    const destReady = getFrame("dest_ready");
    const complete = getFrame("pipeline_complete");

    // Spring-like smooth entry
    const sourceS = spring({ frame: frame - sourceReady, fps, config: { stiffness: 120, damping: 14 } });
    const destS = spring({ frame: frame - destReady, fps, config: { stiffness: 120, damping: 14 } });

    const sourceOp = interpolate(sourceS, [0, 1], [0, 1]);
    const sourceY = interpolate(sourceS, [0, 1], [20, 0]);
    
    const destOp = interpolate(destS, [0, 1], [0, 1]);
    const destY = interpolate(destS, [0, 1], [20, 0]);

    const successOp = interpolate(frame, [complete, complete + 20], [0, 1], { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill style={{ 
          background: tokens.colors.background,
          color: tokens.colors.text
        }}>
            {/* Fine Grain Overlay (Apple Aesthetic) */}
            <AbsoluteFill style={{ 
              opacity: 0.1, 
              mixBlendMode: 'overlay',
              pointerEvents: 'none',
              backgroundImage: `url('https://www.transparenttextures.com/patterns/carbon-fibre.png')` 
            }} />

            {/* Manim Technical Layer */}
            <AbsoluteFill>
                <Video 
                    src={staticFile("manim/PythonDBElite.webm")} 
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
            </AbsoluteFill>

            {/* Decentralized Typography Layer (React/CSS) */}
            <div style={{ position: 'absolute', bottom: '150px', left: '15%' }}>
                <GlassLabel text="PYTHON 3.12" opacity={sourceOp} translateY={sourceY} />
            </div>

            <div style={{ position: 'absolute', bottom: '150px', right: '15%' }}>
                <GlassLabel text="POSTGRESQL DB" opacity={destOp} translateY={destY} />
            </div>

            {/* Premium Success Badge */}
            <div style={{ 
              position: 'absolute', 
              top: '50%', 
              left: '50%', 
              transform: 'translate(-50%, -50%)',
              opacity: successOp,
              textAlign: 'center'
            }}>
                <div style={{ 
                  fontSize: '120px', 
                  fontWeight: 900, 
                  letterSpacing: '-0.08em',
                  background: 'linear-gradient(to bottom, #fff 0%, #aaa 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.8))'
                }}>
                  PIPELINE PRO
                </div>
                <div style={{ color: tokens.colors.primary, fontSize: '30px', fontWeight: 600, marginTop: '20px' }}>
                  RENDERING CONTRACT COMPLETE
                </div>
            </div>
        </AbsoluteFill>
    );
};

export const PythonDBPipeline: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const getFrame = (name: string) => {
        const event = (timing as any[]).find((e: any) => e.event === name);
        return event ? (event.timestamp_ms / 1000) * fps : 0;
    };

    // Timing Points
    const sourceReady = getFrame("source_ready");
    const dbReady = getFrame("db_ready");
    const dbFill4 = getFrame("db_fill_4");

    // Opacities
    const sourceOpacity = interpolate(frame, [sourceReady, sourceReady + 10], [0, 1], { extrapolateRight: 'clamp' });
    const dbOpacity = interpolate(frame, [dbReady, dbReady + 10], [0, 1], { extrapolateRight: 'clamp' });
    const successOpacity = interpolate(frame, [dbFill4, dbFill4 + 10], [0, 1], { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill style={{ 
          background: 'linear-gradient(135deg, #0f172a 0%, #000 100%)',
          color: 'white'
        }}>
            {/* Background Grain */}
            <AbsoluteFill style={{ opacity: 0.05, backgroundImage: `url('https://www.transparenttextures.com/patterns/clean-gray-paper.png')`, pointerEvents: 'none' }} />

            {/* Scene 1: Python Source */}
            {frame < (dbReady || 300) && (
              <AbsoluteFill>
                <Video 
                    src={staticFile("manim/PythonSource.webm")} 
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
                <div style={{ position: 'absolute', top: '70%', left: '15%', opacity: sourceOpacity }}>
                    <GlassLabel text="PYTHON ➔ DATA SOURCE" opacity={1} />
                </div>
              </AbsoluteFill>
            )}

            {/* Scene 2: DB Ingestion */}
            {frame >= (dbReady || 300) && (
              <AbsoluteFill>
                <Video 
                    src={staticFile("manim/DBIngestion.webm")} 
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
                <div style={{ position: 'absolute', top: '70%', left: '55%', opacity: dbOpacity }}>
                    <GlassLabel text="POSTGRESQL ➔ DESTINY" opacity={1} />
                </div>
              </AbsoluteFill>
            )}

            {/* Final Success Overlay */}
            {frame > dbFill4 && (
              <AbsoluteFill style={{ 
                justifyContent: 'center', 
                alignItems: 'center', 
                backgroundColor: 'rgba(51, 103, 145, 0.2)',
                backdropFilter: 'blur(5px)',
                opacity: successOpacity
               }}>
                <div style={{ fontSize: '80px', fontWeight: 900, textTransform: 'uppercase' }}>
                  Pipeline Success
                </div>
              </AbsoluteFill>
            )}
        </AbsoluteFill>
    );
};

export const EliteIndustrialPipeline: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Load dynamic intelligence
    const strategy = tokens.strategy || { pacing: "fast", energy_curve: [0.2, 0.5, 1.0] };

    const getFrame = (name: string) => {
        const event = (timingIndustrial as any[]).find((e: any) => e.event === name);
        return event ? (event.timestamp_ms / 1000) * fps : 0;
    };

    const lakeReady = getFrame("lake_ready");
    const rustReady = getFrame("rust_ready");
    const pythonReady = getFrame("python_ready");
    const dbReady = getFrame("db_ready");
    const tableauReady = getFrame("tableau_ready");
    const complete = getFrame("pipeline_complete");

    // v3.0 Dynamic Physics from Motion Contract
    const springConfig = { 
        stiffness: tokens.physics.stiffness || 140, 
        damping: tokens.physics.damping || 12 
    };

    const lakeS = spring({ frame: frame - lakeReady, fps, config: springConfig });
    const rustS = spring({ frame: frame - rustReady, fps, config: springConfig });
    const pythonS = spring({ frame: frame - pythonReady, fps, config: springConfig });
    const dbS = spring({ frame: frame - dbReady, fps, config: springConfig });
    const tableauS = spring({ frame: frame - tableauReady, fps, config: springConfig });

    // Energy Curve (Aria's Strategy)
    const energy = interpolate(frame, [0, 300, 600, 720], [0.2, 0.5, 0.9, 1.0]);

    return (
        <AbsoluteFill style={{ background: tokens.colors.background }}>
            {/* Mirror Mode Grid Overlay */}
            <AbsoluteFill style={{ 
                opacity: 0.05 * energy, 
                backgroundImage: `radial-gradient(circle at center, ${tokens.colors.primary} 0%, transparent 70%)`,
                mixBlendMode: 'screen'
            }} />
            
            <AbsoluteFill>
                <Video src={staticFile("manim/EliteDataPipeline.mp4")} style={{ width: '100%', height: '100%', filter: `contrast(${1 + energy * 0.1})` }} />
            </AbsoluteFill>

            {/* v3.0 Intelligence Labels */}
            <div style={{ position: 'absolute', bottom: '100px', left: '5%', transform: `scale(${interpolate(lakeS, [0, 1], [0.8, 1])})`, opacity: lakeS }}>
                <GlassLabel text="V3: DATA LAKE" opacity={1} />
            </div>
            <div style={{ position: 'absolute', bottom: '200px', left: '25%', transform: `scale(${interpolate(rustS, [0, 1], [0.8, 1])})`, opacity: rustS }}>
                <GlassLabel text="V3: RUST ENGINE" opacity={1} />
            </div>
            <div style={{ position: 'absolute', top: '100px', left: '45%', transform: `scale(${interpolate(pythonS, [0, 1], [0.8, 1])})`, opacity: pythonS }}>
                <GlassLabel text="V3: PYTHON ORCH" opacity={1} />
            </div>
            <div style={{ position: 'absolute', bottom: '100px', right: '25%', transform: `scale(${interpolate(dbS, [0, 1], [0.8, 1])})`, opacity: dbS }}>
                <GlassLabel text="V3: POSTGRES DB" opacity={1} />
            </div>
            <div style={{ position: 'absolute', top: '200px', right: '5%', transform: `scale(${interpolate(tableauS, [0, 1], [0.8, 1])})`, opacity: tableauS }}>
                <GlassLabel text="V3: TABLEAU INSIGHT" opacity={1} />
            </div>

            {/* AIOX Mirror Image v3.0 Reveal */}
            {frame > complete && (
                <AbsoluteFill style={{ background: 'rgba(9, 9, 11, 0.8)', backdropFilter: 'blur(10px)' }}>
                   <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                      <div style={{ fontSize: '100px', fontWeight: 900, color: 'white', letterSpacing: '-0.02em' }}>AIOX MIRROR IMAGE</div>
                      <div style={{ color: tokens.colors.primary, fontSize: '50px', fontWeight: 700 }}>DESIGN COMPILER V3.0</div>
                      <div style={{ color: tokens.colors.text, opacity: 0.5, marginTop: '20px', fontSize: '20px' }}>ARIA | DARA | UMA</div>
                   </div>
                </AbsoluteFill>
            )}
        </AbsoluteFill>
    );
};
