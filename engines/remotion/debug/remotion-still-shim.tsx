import React, {createContext, useContext} from 'react';

type VideoConfig = {
	width: number;
	height: number;
	fps: number;
	durationInFrames: number;
};

const defaultConfig: VideoConfig = {
	width: 1080,
	height: 1350,
	fps: 30,
	durationInFrames: 1,
};

const VideoConfigContext = createContext<VideoConfig>(defaultConfig);

export const VideoConfigProvider: React.FC<{
	config?: Partial<VideoConfig>;
	children: React.ReactNode;
}> = ({config, children}) => {
	return (
		<VideoConfigContext.Provider value={{...defaultConfig, ...(config ?? {})}}>
			{children}
		</VideoConfigContext.Provider>
	);
};

export const useVideoConfig = (): VideoConfig => {
	return useContext(VideoConfigContext);
};

export const AbsoluteFill: React.FC<{
	style?: React.CSSProperties;
	children?: React.ReactNode;
}> = ({style, children}) => {
	return (
		<div
			style={{
				position: 'absolute',
				inset: 0,
				...style,
			}}
		>
			{children}
		</div>
	);
};

export const Img: React.FC<React.ImgHTMLAttributes<HTMLImageElement>> = (props) => {
	return <img {...props} />;
};

export const staticFile = (src: string): string => src;
