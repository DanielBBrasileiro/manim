import React, {useMemo} from 'react';
import {resolvePrimitive} from '../utils/primitives';

export interface CompositionPrimitiveProps {
	seed: string;
	type?: string;
	weight?: number;
	opacity?: number;
	tension?: number;
	color?: string;
	style?: React.CSSProperties;
}

export const CompositionPrimitive: React.FC<CompositionPrimitiveProps> = ({
	seed,
	type,
	weight,
	opacity,
	tension,
	color = '#FFFFFF',
	style,
}) => {
	const rendered = useMemo(() => {
		return resolvePrimitive(
			{
				type: type as any,
				thickness: weight,
				opacity,
				tension,
			},
			seed
		);
	}, [seed, type, weight, opacity, tension]);

	const strokeWidth = weight ?? 1.8;
	const mainOpacity = opacity ?? 0.75;

	return (
		<svg
			viewBox="0 0 100 100"
			preserveAspectRatio="none"
			style={{
				position: 'absolute',
				width: '100%',
				height: '100%',
				overflow: 'visible',
				pointerEvents: 'none',
				...style,
			}}
		>
			<path
				d={rendered.path}
				fill="none"
				stroke={color}
				strokeWidth={strokeWidth}
				strokeLinecap="round"
				vectorEffect="non-scaling-stroke"
				style={{
					opacity: mainOpacity,
					...rendered.style,
				}}
			/>
			{rendered.path2 && (
				<path
					d={rendered.path2}
					fill="none"
					stroke={color}
					strokeWidth={strokeWidth}
					strokeLinecap="round"
					vectorEffect="non-scaling-stroke"
					style={{
						opacity: mainOpacity * 0.6,
						...rendered.style,
					}}
				/>
			)}
		</svg>
	);
};
