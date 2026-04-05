import React from 'react';
import {createRoot} from 'react-dom/client';
import {StillComposer, type StillComposerProps} from '../src/compositions/StillComposer';
import {VideoConfigProvider} from './remotion-still-shim';

declare global {
	interface Window {
		__AIOX_STILL_PROPS__?: StillComposerProps;
	}
}

const rootElement = document.getElementById('root');

if (!rootElement) {
	throw new Error('Missing #root element for still comparison page.');
}

const props: StillComposerProps = window.__AIOX_STILL_PROPS__ ?? {};
const renderManifest = props.renderManifest ?? {};
const width = Number((renderManifest as {width?: number}).width ?? 1080);
const height = Number((renderManifest as {height?: number}).height ?? 1350);

document.body.style.margin = '0';
document.body.style.background = '#000';
document.body.style.width = `${width}px`;
document.body.style.height = `${height}px`;
document.body.style.overflow = 'hidden';

createRoot(rootElement).render(
	<React.StrictMode>
		<VideoConfigProvider config={{width, height, fps: 30, durationInFrames: 1}}>
			<div
				style={{
					position: 'relative',
					width,
					height,
					overflow: 'hidden',
					background: '#000',
				}}
			>
				<StillComposer
					{...props}
					target={props.target ?? 'linkedin_feed_4_5'}
					renderManifest={{
						target: 'linkedin_feed_4_5',
						targetId: 'linkedin_feed_4_5',
						targetKind: 'still',
						width,
						height,
						...(props.renderManifest ?? {}),
					}}
				/>
			</div>
		</VideoConfigProvider>
	</React.StrictMode>
);
