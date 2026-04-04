import React from 'react';
import '../styles/material_bridge.css';

export interface MaterialSurfaceProps {
    elevation?: 0 | 1 | 2 | 3 | 4 | 5;
    shape?: 'none' | 'extra-small' | 'small' | 'medium' | 'large' | 'extra-large' | 'full';
    children: React.ReactNode;
    style?: React.CSSProperties;
    className?: string;
}

export const MaterialSurface: React.FC<MaterialSurfaceProps> = ({
    elevation = 0,
    shape = 'medium',
    children,
    style = {},
    className = ''
}) => {
    // We utilize the native CSS mappings defined in material_bridge.css
    // This removes JS interpolation overhead from Remotion loops.
    const shadowToken = elevation === 0 ? 'none' : `var(--md-sys-elevation-level${elevation})`;
    
    // Tint mixing according to m3 specs:
    // Elevation increases cause the surface to shift slightly towards the Primary Color.
    const backgroundToken = elevation === 0 
        ? 'var(--md-sys-color-surface)' 
        : `var(--md-sys-surface-tint-${elevation})`;

    const radiusToken = `var(--md-sys-shape-corner-${shape})`;

    const surfaceStyle: React.CSSProperties = {
        backgroundColor: backgroundToken,
        boxShadow: shadowToken,
        borderRadius: radiusToken,
        color: 'var(--md-sys-color-on-surface)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        ...style
    };

    return (
        <div style={surfaceStyle} className={className}>
            {children}
        </div>
    );
};
