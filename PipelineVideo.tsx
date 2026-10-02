import {
	AbsoluteFill,
	interpolate,
	Sequence,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import React from 'react';

export const PipelineVideo: React.FC = () => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	// Stage 1: WhatsApp Text Entry (0-60 frames)
	const textEntryProgress = spring({
		frame,
		fps,
		config: { damping: 200 },
	});

	// Stage 2: Transform to AI JSON (60-120 frames)
	const jsonProgress = spring({
		frame: frame - 60,
		fps,
		config: { damping: 200 },
	});

	// Stage 3: Encrypt to Ciphertext (120-180 frames)
	const encryptProgress = spring({
		frame: frame - 120,
		fps,
		config: { damping: 200 },
	});

	// Stage 4: Slot into Xero Draft Bill (180-240 frames)
	const xeroProgress = spring({
		frame: frame - 180,
		fps,
		config: { damping: 200 },
	});

	// Opacities for smooth transitions
	const textOpacity = interpolate(frame, [50, 70], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const jsonOpacity = interpolate(frame, [60, 80, 110, 130], [0, 1, 1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const encryptOpacity = interpolate(frame, [120, 140, 170, 190], [0, 1, 1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const xeroOpacity = interpolate(frame, [180, 200], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const scale = interpolate(frame, [0, 240], [1, 1.1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill style={{ backgroundColor: '#0f172a', justifyContent: 'center', alignItems: 'center', fontFamily: 'monospace', color: '#f8fafc', transform: `scale(${scale})` }}>
			
			{/* Stage 1: WhatsApp Text */}
			<AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: textOpacity }}>
				<div style={{
					backgroundColor: '#25D366',
					padding: '20px 40px',
					borderRadius: '20px',
					fontSize: '40px',
					fontWeight: 'bold',
					transform: `translateY(${interpolate(textEntryProgress, [0, 1], [50, 0])}px)`,
					boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
				}}>
					"Bought a MacBook Pro for £1200"
				</div>
			</AbsoluteFill>

			{/* Stage 2: AI JSON */}
			<AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: jsonOpacity }}>
				<pre style={{
					backgroundColor: '#1e293b',
					padding: '40px',
					borderRadius: '10px',
					fontSize: '32px',
					color: '#38bdf8',
					border: '1px solid #334155'
				}}>
{`{
  "item": "MacBook Pro",
  "amount": 1200.00,
  "currency": "GBP",
  "category": "IT Equipment"
}`}
				</pre>
			</AbsoluteFill>

			{/* Stage 3: Encryption */}
			<AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: encryptOpacity }}>
				<div style={{
					fontSize: '32px',
					color: '#a3e635',
					width: '80%',
					wordWrap: 'break-word',
					textAlign: 'center'
				}}>
					{`0x${Array.from({length: 64}).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`}
					<br/><br/>
					<span style={{color: '#94a3b8', fontSize: '24px'}}>Encrypting Payload... AES-256</span>
				</div>
			</AbsoluteFill>

			{/* Stage 4: Xero Draft Bill */}
			<AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: xeroOpacity }}>
				<div style={{
					backgroundColor: '#ffffff',
					color: '#0f172a',
					padding: '40px',
					borderRadius: '10px',
					width: '70%',
					boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
				}}>
					<h1 style={{color: '#13b5ea', marginBottom: '20px', fontSize: '40px', borderBottom: '2px solid #e2e8f0', paddingBottom: '10px'}}>Xero: Draft Bill</h1>
					<div style={{display: 'flex', justifyContent: 'space-between', fontSize: '28px', marginBottom: '10px'}}>
						<span><strong>Description:</strong> MacBook Pro</span>
						<span><strong>Total:</strong> £1200.00</span>
					</div>
					<div style={{display: 'flex', justifyContent: 'space-between', fontSize: '28px'}}>
						<span><strong>Account:</strong> 720 - IT Equipment</span>
						<span><strong>Status:</strong> DRAFT</span>
					</div>
					<div style={{
						marginTop: '40px',
						backgroundColor: '#f1f5f9',
						padding: '20px',
						borderRadius: '8px',
						textAlign: 'center',
						fontSize: '24px',
						color: '#64748b'
					}}>
						Ready for Review
					</div>
				</div>
			</AbsoluteFill>

		</AbsoluteFill>
	);
};
