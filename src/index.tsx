import {
	definePlugin,
	PanelSection,
	PanelSectionRow,
	quickAccessMenuClasses,
	ToggleField,
	ButtonItem,
	DropdownOption,
	DropdownItem,
	Focusable,
	Menu,
	MenuItem,
	showContextMenu,
	gamepadContextMenuClasses,
} from "decky-frontend-lib";

import { callable, toaster } from "@decky/api";

import React, {
	VFC,
	useEffect,
	useRef,
	useState,
} from "react";

import { FaMicrophone, FaTrash } from "react-icons/fa";

type CompanionStatus = {
    state: string;
    age_seconds?: number | null;
    vocabulary_count: number;
    detail?: string;
};

type RpcResponse = { success: boolean; error?: string; [key: string]: any };

const getStatus = callable<[], RpcResponse>("get_status");
const getButtonConfig = callable<[], RpcResponse>("get_button_config");
const getPresets = callable<[], RpcResponse>("get_presets");
const setEnabledRpc = callable<[enabled: boolean], RpcResponse>("set_enabled");
const loadModel = callable<[], RpcResponse>("load_model");
const startRecording = callable<[], RpcResponse>("start_recording");
const stopRecording = callable<[send?: boolean], RpcResponse>("stop_recording");
const getLastTranscription = callable<[], RpcResponse>("get_last_transcription");
const setConfirmModeRpc = callable<[enabled: boolean], RpcResponse>("set_confirm_mode");
const setManualSendRpc = callable<[enabled: boolean], RpcResponse>("set_manual_send");
const setRememberLastChannelRpc = callable<[enabled: boolean], RpcResponse>("set_remember_last_channel");
const setShareDiagnosticsRpc = callable<[enabled: boolean], RpcResponse>("set_share_diagnostics");
const setRecordingIndicatorRpc = callable<[mode: string], RpcResponse>("set_recording_indicator");
const setHapticFeedbackRpc = callable<[enabled: boolean], RpcResponse>("set_haptic_feedback");
const setActivePresetRpc = callable<[game: string], RpcResponse>("set_active_preset");
const setWowCompanionRpc = callable<[enabled: boolean], RpcResponse>("set_wow_companion_enabled");
const setModelSizeRpc = callable<[modelSize: string], RpcResponse>("set_model_size");
const setTranscriptionOptionsRpc = callable<
	[language: string],
	RpcResponse
>("set_transcription_options");
const setButtonConfig = callable<
	[buttons: string[]],
	RpcResponse
>("set_button_config");

class DecktationLogic {
	enabled: boolean = false;
	recording: boolean = false;
	recordingIndicator: string = "toast";
	prevRecordingStartCount: number = 0;
	prevPendingText: string = "";
	lastPendingToastId: number = -1;

	notify = async (message: string, duration: number = 2000, body: string = ""): Promise<number> => {
		if (!body) {
			body = message;
		}
		const toast: any = {
			title: message,
			body: body,
			duration: duration,
			critical: false,
		};
		const id: number = (window as any).NotificationStore ? (window as any).NotificationStore.m_nNextTestNotificationID++ : 0;
		const toastData: any = {
			nNotificationID: id,
			bNewIndicator: false,
			rtCreated: Date.now(),
			eType: 43,
			eSource: 1,
			nToastDurationMS: duration,
			data: toast,
			decky: true,
		};
		const info: any = {
			showToast: true,
			sound: 6,
			playSound: false,
			eFeature: 0,
			toastDurationMS: duration,
			bCritical: false,
			fnTray: (_t: any, tray: any) => { tray.unshift({ eType: 31, notifications: [toastData] }); },
		};
		try {
			(window as any).NotificationStore.ProcessNotification(info, toastData, 0);
		} catch (_e) {
			// fallback to standard toaster if direct call fails
			toaster.toast({ title: message, body: toast.body, duration: duration, critical: false });
		}
		return id;
	}

	dismissNotification = (id: number) => {
		// Force-expire the toast by reprocessing it with a 1ms duration
		try {
			const toastData: any = {
				nNotificationID: id,
				bNewIndicator: false,
				rtCreated: Date.now(),
				eType: 43,
				eSource: 1,
				nToastDurationMS: 1,
				data: { title: "", body: "", duration: 1, critical: false },
				decky: true,
			};
			const info: any = {
				showToast: true,
				sound: 6,
				playSound: false,
				eFeature: 0,
				toastDurationMS: 1,
				bCritical: false,
				fnTray: (_t: any, tray: any) => { tray.unshift({ eType: 31, notifications: [toastData] }); },
			};
			(window as any).NotificationStore.ProcessNotification(info, toastData, 0);
		} catch (_e) {}
	}

	testRecording = async (
		onComplete: (text: string, time: string) => void,
		onPhase: (phase: "recording" | "transcribing" | "idle") => void,
	) => {
		onPhase("recording");
		try {
			if (this.recordingIndicator === "toast") this.notify("Decktation", 1000, "Recording for 3 seconds...");
			const started = await startRecording();
			if (!started.success) throw new Error(started.error || "Could not start test recording");

			await new Promise(resolve => setTimeout(resolve, 3000));
			// Keep the no-send argument: test text must never reach the active game.
			onPhase("transcribing");
			const transcription = stopRecording(false);
			if (this.recordingIndicator === "toast") this.notify("Decktation", 1500, "Transcribing...");
			const stopped = await transcription;
			if (!stopped.success) throw new Error(stopped.error || "Could not transcribe test recording");

			const result = await getLastTranscription();
			if (!result.success) throw new Error(result.error || "Could not read test transcription");
			const data = result.transcription;
			onComplete(
				data?.text || "",
				data?.timestamp ? new Date(data.timestamp * 1000).toLocaleTimeString() : "",
			);
		} finally {
			onPhase("idle");
		}
	}
}

// Available button options
const BUTTON_OPTIONS: DropdownOption[] = [
	{ data: "L1", label: "L1 Bumper" },
	{ data: "R1", label: "R1 Bumper" },
	{ data: "L2", label: "L2 Trigger" },
	{ data: "R2", label: "R2 Trigger" },
	{ data: "L4", label: "L4 Grip" },
	{ data: "R4", label: "R4 Grip" },
	{ data: "L5", label: "L5 Grip" },
	{ data: "R5", label: "R5 Grip" },
	{ data: "A", label: "A" },
	{ data: "B", label: "B" },
	{ data: "X", label: "X" },
	{ data: "Y", label: "Y" },
];

const WHISPER_LANGUAGE_OPTIONS: DropdownOption[] = [
	{ data: "auto", label: "Auto Detect" },
	{ data: "af", label: "Afrikaans" },
	{ data: "am", label: "Amharic" },
	{ data: "ar", label: "Arabic" },
	{ data: "as", label: "Assamese" },
	{ data: "az", label: "Azerbaijani" },
	{ data: "ba", label: "Bashkir" },
	{ data: "be", label: "Belarusian" },
	{ data: "bg", label: "Bulgarian" },
	{ data: "bn", label: "Bengali" },
	{ data: "bo", label: "Tibetan" },
	{ data: "br", label: "Breton" },
	{ data: "bs", label: "Bosnian" },
	{ data: "ca", label: "Catalan" },
	{ data: "cs", label: "Czech" },
	{ data: "cy", label: "Welsh" },
	{ data: "da", label: "Danish" },
	{ data: "de", label: "German" },
	{ data: "el", label: "Greek" },
	{ data: "en", label: "English" },
	{ data: "es", label: "Spanish" },
	{ data: "et", label: "Estonian" },
	{ data: "eu", label: "Basque" },
	{ data: "fa", label: "Persian" },
	{ data: "fi", label: "Finnish" },
	{ data: "fo", label: "Faroese" },
	{ data: "fr", label: "French" },
	{ data: "gl", label: "Galician" },
	{ data: "gu", label: "Gujarati" },
	{ data: "ha", label: "Hausa" },
	{ data: "haw", label: "Hawaiian" },
	{ data: "he", label: "Hebrew" },
	{ data: "hi", label: "Hindi" },
	{ data: "hr", label: "Croatian" },
	{ data: "ht", label: "Haitian Creole" },
	{ data: "hu", label: "Hungarian" },
	{ data: "hy", label: "Armenian" },
	{ data: "id", label: "Indonesian" },
	{ data: "is", label: "Icelandic" },
	{ data: "it", label: "Italian" },
	{ data: "ja", label: "Japanese" },
	{ data: "jw", label: "Javanese" },
	{ data: "ka", label: "Georgian" },
	{ data: "kk", label: "Kazakh" },
	{ data: "km", label: "Khmer" },
	{ data: "kn", label: "Kannada" },
	{ data: "ko", label: "Korean" },
	{ data: "la", label: "Latin" },
	{ data: "lb", label: "Luxembourgish" },
	{ data: "ln", label: "Lingala" },
	{ data: "lo", label: "Lao" },
	{ data: "lt", label: "Lithuanian" },
	{ data: "lv", label: "Latvian" },
	{ data: "mg", label: "Malagasy" },
	{ data: "mi", label: "Maori" },
	{ data: "mk", label: "Macedonian" },
	{ data: "ml", label: "Malayalam" },
	{ data: "mn", label: "Mongolian" },
	{ data: "mr", label: "Marathi" },
	{ data: "ms", label: "Malay" },
	{ data: "mt", label: "Maltese" },
	{ data: "my", label: "Myanmar" },
	{ data: "ne", label: "Nepali" },
	{ data: "nl", label: "Dutch" },
	{ data: "nn", label: "Norwegian Nynorsk" },
	{ data: "no", label: "Norwegian" },
	{ data: "oc", label: "Occitan" },
	{ data: "pa", label: "Punjabi" },
	{ data: "pl", label: "Polish" },
	{ data: "ps", label: "Pashto" },
	{ data: "pt", label: "Portuguese" },
	{ data: "ro", label: "Romanian" },
	{ data: "ru", label: "Russian" },
	{ data: "sa", label: "Sanskrit" },
	{ data: "sd", label: "Sindhi" },
	{ data: "si", label: "Sinhala" },
	{ data: "sk", label: "Slovak" },
	{ data: "sl", label: "Slovenian" },
	{ data: "sn", label: "Shona" },
	{ data: "so", label: "Somali" },
	{ data: "sq", label: "Albanian" },
	{ data: "sr", label: "Serbian" },
	{ data: "su", label: "Sundanese" },
	{ data: "sv", label: "Swedish" },
	{ data: "sw", label: "Swahili" },
	{ data: "ta", label: "Tamil" },
	{ data: "te", label: "Telugu" },
	{ data: "tg", label: "Tajik" },
	{ data: "th", label: "Thai" },
	{ data: "tk", label: "Turkmen" },
	{ data: "tl", label: "Tagalog" },
	{ data: "tr", label: "Turkish" },
	{ data: "tt", label: "Tatar" },
	{ data: "uk", label: "Ukrainian" },
	{ data: "ur", label: "Urdu" },
	{ data: "uz", label: "Uzbek" },
	{ data: "vi", label: "Vietnamese" },
	{ data: "yi", label: "Yiddish" },
	{ data: "yo", label: "Yoruba" },
	{ data: "yue", label: "Cantonese" },
	{ data: "zh", label: "Chinese" },
];

const MODEL_SIZE_OPTIONS: DropdownOption[] = [
	{ data: "base", label: "Base · Fast" },
	{ data: "small", label: "Small · Balanced" },
	{ data: "medium", label: "Medium · More accurate" },
];

const POPULAR_STEAM_LANGUAGE_CODES = new Set(["en", "zh", "ru", "es", "pt", "de", "ja", "fr", "pl", "ko"]);
const byLanguageName = (left: DropdownOption, right: DropdownOption) => String(left.label).localeCompare(String(right.label));
const POPULAR_LANGUAGE_OPTIONS = WHISPER_LANGUAGE_OPTIONS.filter(option => POPULAR_STEAM_LANGUAGE_CODES.has(String(option.data))).sort(byLanguageName);
const OTHER_LANGUAGE_OPTIONS = WHISPER_LANGUAGE_OPTIONS.filter(option => option.data !== "auto" && !POPULAR_STEAM_LANGUAGE_CODES.has(String(option.data))).sort(byLanguageName);

const PRESET_DISPLAY_NAMES: Record<string, string> = {
	wow: "World of Warcraft",
	guildwars2: "Guild Wars 2",
	generic: "Generic",
};

type PanelPage = "main" | "advanced" | "diagnostics" | "help" | "game" | "model" | "binding-button";

const DecktationPanel: VFC<{ logic: DecktationLogic }> = ({ logic }) => {
	const [page, setPage] = useState<PanelPage>("main");
	const panelRef = useRef<HTMLDivElement>(null);
	const languageMenuAnchorRef = useRef<HTMLSpanElement>(null);
	const advancedModelRowRef = useRef<HTMLDivElement>(null);
	const [bindingButtonIndex, setBindingButtonIndex] = useState<number>(0);
	const [enabled, setEnabled] = useState<boolean>(false);
	const [recording, setRecording] = useState<boolean>(false);
	const [serviceReady, setServiceReady] = useState<boolean>(false);
	const [modelReady, setModelReady] = useState<boolean>(false);
	const [inferenceDevice, setInferenceDevice] = useState<"cpu" | "gpu" | null>(null);
	const [modelLoading, setModelLoading] = useState<boolean>(false);
	const [isToggling, setIsToggling] = useState<boolean>(false);
	const [inputReady, setInputReady] = useState<boolean>(true);
	const [buttonState, setButtonState] = useState<string>("None");
	const [controllerReady, setControllerReady] = useState<boolean>(false);
	const [controllerStatus, setControllerStatus] = useState<string>("Waiting for input");
	const [controllerComboSupported, setControllerComboSupported] = useState<boolean>(true);
	const [buttons, setButtons] = useState<string[]>(["L1", "R1"]);
	const [recordingIndicator, setRecordingIndicator] = useState<string>("toast");
	const [hapticFeedback, setHapticFeedback] = useState<boolean>(false);
	const [activePreset, setActivePreset] = useState<string>("wow");
	const [presets, setPresets] = useState<DropdownOption[]>([]);
	const [confirmMode, setConfirmMode] = useState<boolean>(false);
	const [manualSend, setManualSend] = useState<boolean>(false);
	const [rememberLastChannel, setRememberLastChannel] = useState<boolean>(false);
	const [shareDiagnostics, setShareDiagnostics] = useState<boolean>(false);
	const [wowCompanionEnabled, setWowCompanionEnabled] = useState<boolean>(false);
	const [companionStatus, setCompanionStatus] = useState<CompanionStatus>({state: "Disabled", vocabulary_count: 0});
	const [modelSize, setModelSize] = useState<string>("base");
	const [transcriptionLanguage, setTranscriptionLanguage] = useState<string>("auto");
	const [lastTranscription, setLastTranscription] = useState<string>("");
	const [lastTranscriptionTime, setLastTranscriptionTime] = useState<string>("");
	const [rpcError, setRpcError] = useState<string>("");
	const [statusError, setStatusError] = useState<string>("");
	const [testPhase, setTestPhase] = useState<"idle" | "recording" | "transcribing">("idle");
	const [hasTestResult, setHasTestResult] = useState<boolean>(false);

	useEffect(() => {
		setEnabled(logic.enabled);
		setRecording(logic.recording);

		// Load button configuration, settings, and active game preset
		getButtonConfig().then((result) => {
			if (result.success) {
				const config = result.config;
				if (config) {
					if (config.buttons) {
						setButtons(config.buttons);
					}
					const indicator = config.recordingIndicator || (config.showNotifications === false ? "none" : "toast");
					setRecordingIndicator(indicator);
					logic.recordingIndicator = indicator;
					if (config.hapticFeedback !== undefined) {
						setHapticFeedback(config.hapticFeedback);
					}
					if (config.game) {
						setActivePreset(config.game);
					}
					if (config.confirmMode !== undefined) {
						setConfirmMode(config.confirmMode);
					}
					if (config.manualSend !== undefined) {
						setManualSend(config.manualSend);
					}
					if (config.rememberLastChannel !== undefined) {
						setRememberLastChannel(config.rememberLastChannel);
					}
					if (config.shareDiagnostics !== undefined) {
						setShareDiagnostics(config.shareDiagnostics);
					}
					setWowCompanionEnabled(config.wowCompanionEnabled === true);
					if (config.modelSize) {
						setModelSize(config.modelSize);
					}
					if (config.transcriptionLanguage) {
						setTranscriptionLanguage(config.transcriptionLanguage);
					}
					// Restore enabled state
					if (config.enabled) {
						setEnabled(true);
						logic.enabled = true;
						setModelLoading(true);
						void loadModel();
					}
				}
			}
		}).catch((error) => setRpcError(String(error)));

		// Load available game presets
		getPresets().then((result) => {
			if (result.success) {
				const opts: DropdownOption[] = result.presets.map((p: { id: string; name: string }) => ({
					data: p.id,
					label: PRESET_DISPLAY_NAMES[p.id] || p.name,
				}));
				setPresets(opts);
			}
		}).catch((error) => setRpcError(String(error)));
	}, []);

	useEffect(() => {
		let cancelled = false;
		let timeout: ReturnType<typeof setTimeout> | undefined;
		const poll = async () => {
			try {
				const result = await getStatus();
				if (cancelled) return;
				if (result.success) {
					setButtonState(result.detected_button || "None");
					setControllerReady(result.controller_ready === true);
					setCompanionStatus(result.companion || {state: "Disabled", vocabulary_count: 0});
					setControllerStatus(result.controller_status || "Waiting for input");
					setControllerComboSupported(result.controller_combo_supported !== false);
					setStatusError("");
					setServiceReady(result.service_ready);
					setModelReady(result.model_ready);
					setInferenceDevice(
						result.inference_device === "gpu" || result.inference_device === "cpu"
							? result.inference_device
							: null,
					);
					setModelLoading(result.model_loading);
					setInputReady(result.input_ready !== false);
					if (logic.enabled) {
						setRecording(result.recording);
					}
				} else {
					setControllerReady(false);
					setControllerStatus("Status unavailable");
					setStatusError(result.error || "Backend status request failed");
				}
			} catch (error) {
				setControllerReady(false);
				setControllerStatus("Status unavailable");
				setStatusError(String(error));
			} finally {
				if (!cancelled) timeout = setTimeout(poll, 100);
			}
		};
		void poll();
		return () => {
			cancelled = true;
			if (timeout) clearTimeout(timeout);
		};
	}, [logic.enabled]);

	useEffect(() => {
		// Steam's QAM keeps its scroll position when the content changes in place.
		const resetScroll = () => {
			let node = panelRef.current?.parentElement;
			while (node) {
				if (node.scrollHeight > node.clientHeight) node.scrollTop = 0;
				node = node.parentElement;
			}
		};
		resetScroll();
		const frame = requestAnimationFrame(() => {
			resetScroll();
			if (page === "advanced") {
				(advancedModelRowRef.current?.querySelector('[role="button"], button') as HTMLElement | null)?.focus();
			}
		});
		return () => cancelAnimationFrame(frame);
	}, [page]);

	const goBack = () => setPage(page === "diagnostics" || page === "help" || page === "model" || page === "binding-button" ? "advanced" : "main");
	const chooseLanguage = async (language: string) => {
		const result = await setTranscriptionOptionsRpc(language);
		if (result.success) {
			setTranscriptionLanguage(language);
			setRpcError("");
		} else {
			setRpcError(result.error || "Could not update language setting");
		}
	};
	const runTest = async () => {
		if (testPhase !== "idle") return;
		setRpcError("");
		setHasTestResult(false);
		try {
			await logic.testRecording((text, time) => {
				setLastTranscription(text);
				setLastTranscriptionTime(time);
				setHasTestResult(true);
			}, setTestPhase);
		} catch (error) {
			setRpcError(String(error));
		}
	};
	const statusMessage = statusError ? `Backend unavailable: ${statusError}`
		: rpcError ? rpcError
		: !serviceReady ? "Connecting to Decktation..."
		: !inputReady ? "Keyboard helper unavailable. Reload or reinstall Decktation."
		: recording ? "Recording..."
		: modelLoading ? "Loading transcription model..."
		: !enabled ? "Decktation is off"
		: !modelReady ? "Model not ready"
		: !controllerReady ? "Controller unavailable"
		: "Ready";
	const statusProblem = !!(statusError || rpcError || (serviceReady && !inputReady) || (enabled && serviceReady && !controllerReady));

	return (
		<Focusable onCancel={page === "main" ? undefined : (event) => {
			event.stopPropagation();
			goBack();
		}} onCancelActionDescription={page === "main" ? undefined : "Back"}>
			<div ref={panelRef}>
				<style>{`.decktation-trash-focused { outline: 3px solid #66c0f4 !important; outline-offset: 2px; background-color: #456b90 !important; box-shadow: 0 0 0 2px rgba(102, 192, 244, 0.38) !important; }`}</style>
				{page !== "main" && (
					<PanelSectionRow><ButtonItem layout="below" onClick={goBack}>Back</ButtonItem></PanelSectionRow>
				)}
				{page === "main" && <>
					<PanelSection title="Decktation">
						<PanelSectionRow>
							<ToggleField label="Enable" checked={enabled} disabled={!serviceReady || modelLoading || isToggling}
								onChange={async (next) => {
									if (isToggling) return;
									setIsToggling(true);
									setEnabled(next);
									logic.enabled = next;
									if (!next) {
										setModelReady(false);
										logic.recording = false;
										setRecording(false);
									}
									try {
										const result = await setEnabledRpc(next);
										if (!result.success) {
											setEnabled(!next);
											logic.enabled = !next;
											setRpcError(result.error || "Could not update enabled state");
											return;
										}
										if (next && logic.enabled) {
											setModelLoading(true);
											const modelResult = await loadModel();
											if (!modelResult.success) {
												setRpcError(modelResult.error || "Could not load Whisper model");
											}
										}
									} catch (error) {
										setEnabled(!next);
										logic.enabled = !next;
										setRpcError(String(error));
									} finally {
										setIsToggling(false);
									}
								}} />
						</PanelSectionRow>
						<PanelSectionRow>
							<div role="status" style={{ padding: statusProblem ? '10px' : '4px 0', borderRadius: '6px', backgroundColor: statusProblem ? '#713030' : undefined }}>
								{statusMessage}
							</div>
						</PanelSectionRow>
					</PanelSection>
					<PanelSection title="Quick settings">
						{presets.length > 0 && <PanelSectionRow><ButtonItem layout="below" onClick={() => setPage("game")}>
							Game: {presets.find(option => option.data === activePreset)?.label || activePreset}
						</ButtonItem></PanelSectionRow>}
						<PanelSectionRow><div style={{ position: 'relative', width: '100%' }}>
							<span ref={languageMenuAnchorRef} aria-hidden="true" style={{ position: 'absolute', left: 0, top: 0, width: '1px', height: '1px', pointerEvents: 'none' }} />
							<ButtonItem layout="below" onClick={(event) => {
							showContextMenu(
								<Menu label="Language">
									<MenuItem selected={transcriptionLanguage === "auto"} onSelected={() => { void chooseLanguage("auto"); }}>Auto Detect</MenuItem>
									<div className={gamepadContextMenuClasses.ContextMenuSeparator} />
									<div className={gamepadContextMenuClasses.MenuSectionHeader}>Popular Steam languages</div>
									{POPULAR_LANGUAGE_OPTIONS.map(option => <MenuItem key={String(option.data)} selected={option.data === transcriptionLanguage}
										onSelected={() => { void chooseLanguage(String(option.data)); }}>{option.label}</MenuItem>)}
									<div className={gamepadContextMenuClasses.ContextMenuSeparator} />
									<div className={gamepadContextMenuClasses.MenuSectionHeader}>Other languages</div>
									{OTHER_LANGUAGE_OPTIONS.map(option => <MenuItem key={String(option.data)} selected={option.data === transcriptionLanguage}
											onSelected={() => { void chooseLanguage(String(option.data)); }}>{option.label}</MenuItem>)}
								</Menu>,
								languageMenuAnchorRef.current || event.currentTarget,
							);
							}}>Language: {WHISPER_LANGUAGE_OPTIONS.find(option => option.data === transcriptionLanguage)?.label || transcriptionLanguage}</ButtonItem>
						</div></PanelSectionRow>
						<PanelSectionRow><div>Binding: <strong>{buttons.join(' + ')}</strong></div></PanelSectionRow>
						<PanelSectionRow><ButtonItem layout="below" onClick={() => setPage("advanced")}>Edit Bindings</ButtonItem></PanelSectionRow>
					</PanelSection>
					<PanelSection title="Try it">
						<PanelSectionRow><ButtonItem layout="below" onClick={runTest}
							disabled={!enabled || !modelReady || modelLoading || recording || testPhase !== "idle"}>
							<FaMicrophone size={14} /> {testPhase === "recording" ? "Recording..." : testPhase === "transcribing" ? "Transcribing..." : "Test Dictation (3s)"}
						</ButtonItem></PanelSectionRow>
						<PanelSectionRow><div style={{ fontSize: '12px', opacity: 0.85 }}>Shows a transcription here without sending text to your game.</div></PanelSectionRow>
						{hasTestResult && <PanelSectionRow><div role="status" style={{ padding: '10px', backgroundColor: '#233829', borderRadius: '6px', overflowWrap: 'anywhere' }}>
							<strong>Result</strong><div>{lastTranscription || "No speech detected"}</div><small>{lastTranscriptionTime}</small>
						</div></PanelSectionRow>}
					</PanelSection>
					<PanelSectionRow><ButtonItem layout="below" onClick={() => setPage("advanced")}>Advanced settings</ButtonItem></PanelSectionRow>
				</>}
		{page === "advanced" && <>
					<PanelSection title="Transcription model">
						<PanelSectionRow><div ref={advancedModelRowRef}><ButtonItem layout="below" onClick={() => setPage("model")}>
							Model: {MODEL_SIZE_OPTIONS.find(option => option.data === modelSize)?.label || modelSize}
						</ButtonItem></div></PanelSectionRow>
						{modelReady && !modelLoading && inferenceDevice && (
							<PanelSectionRow><div>
								{inferenceDevice === "gpu"
									? "whisper.cpp runs on the GPU via Vulkan."
									: "whisper.cpp runs on the CPU."}
							</div></PanelSectionRow>
						)}
						<PanelSectionRow><div style={{ fontSize: '12px' }}>Base is fastest. Small balances speed and accuracy. Medium is more accurate but slower and may download on first use.</div></PanelSectionRow>
					</PanelSection>
					<PanelSection title="Recording binding">
						<PanelSectionRow><div>Hold <strong>{buttons.join('+')}</strong> to record</div></PanelSectionRow>
						{buttons.map((button, index) => <PanelSectionRow key={index}>
							<Focusable flow-children="row" style={{ display: 'flex', alignItems: 'center', gap: '4px', width: '100%', minWidth: 0, boxSizing: 'border-box' }}>
								<div style={{ flex: '1 1 0', minWidth: 0, overflow: 'hidden' }}>
									<ButtonItem layout="below" onClick={() => { setBindingButtonIndex(index); setPage("binding-button"); }}>
										Button {index + 1}: {button}
									</ButtonItem>
								</div>
								{buttons.length > 1 && <Focusable role="button" tabIndex={0} focusClassName="decktation-trash-focused" aria-label={`Remove button ${index + 1}`}
									onActivate={async () => {
										const next = buttons.filter((_, i) => i !== index);
										const result = await setButtonConfig(next);
										if (result.success) setButtons(next);
										else setRpcError(result.error || "Could not remove button");
									}} style={{ flex: '0 0 36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '4px', backgroundColor: '#3b4252' }}>
									<FaTrash size={14} aria-hidden="true" />
								</Focusable>}
							</Focusable>
						</PanelSectionRow>)}
						{buttons.length < 5 && <PanelSectionRow><ButtonItem layout="below" onClick={async () => {
							const available = BUTTON_OPTIONS.find(opt => !buttons.includes(opt.data as string));
							if (available) {
								const next = [...buttons, available.data as string];
								setButtons(next);
								await setButtonConfig(next);
							}
						}}>Add Button</ButtonItem></PanelSectionRow>}
					</PanelSection>
					<PanelSection title="Sending">
						<PanelSectionRow><ToggleField label="Confirm" description="Delay before send" checked={confirmMode}
							onChange={async (next) => { setConfirmMode(next); await setConfirmModeRpc(next); }} /></PanelSectionRow>
						<PanelSectionRow><ToggleField label="Manual" description="You press Enter" checked={manualSend}
							onChange={async (next) => { setManualSend(next); await setManualSendRpc(next); }} /></PanelSectionRow>
						<PanelSectionRow><ToggleField label="Remember channel" description="Reuse the last spoken channel" checked={rememberLastChannel}
							onChange={async (next) => {
								setRememberLastChannel(next);
								const result = await setRememberLastChannelRpc(next);
								if (!result.success) { setRememberLastChannel(!next); setRpcError(result.error || "Could not update channel setting"); }
							}} /></PanelSectionRow>
					</PanelSection>
					            {activePreset === "wow" && <PanelSection title="WoW Companion (experimental)">
                <PanelSectionRow>
                    <ToggleField label="WoW Companion context"
                        description="Use live game names as speech vocabulary. Requires the Companion addon; capture runs while WoW and dictation are enabled."
                        checked={wowCompanionEnabled}
                        onChange={async (enabled) => {
                            const result = await setWowCompanionRpc(enabled);
                            if (result.success) setWowCompanionEnabled(enabled);
                            else setRpcError(result.error || "Could not update Companion setting");
                        }} />
                </PanelSectionRow>
                <PanelSectionRow>
                    <div>{companionStatus.state} · {companionStatus.vocabulary_count || 0} vocabulary terms
                        {companionStatus.age_seconds != null ? ` · ${companionStatus.age_seconds}s old` : ""}
                        {companionStatus.detail ? <div>{companionStatus.detail}</div> : null}
                    </div>
                </PanelSectionRow>
            </PanelSection>}
					<PanelSection title="Feedback">
						<PanelSectionRow><DropdownItem label="Recording cue" menuLabel="Recording cue" rgOptions={[{data:"toast",label:"Toast"},{data:"overlay",label:"Overlay"},{data:"none",label:"None"}]} selectedOption={recordingIndicator} onChange={async (option) => { const mode = option.data as string; setRecordingIndicator(mode); logic.recordingIndicator = mode; const result = await setRecordingIndicatorRpc(mode); if (!result.success) setRpcError(result.error || "Could not update recording cue"); }} /></PanelSectionRow>
						<PanelSectionRow><ToggleField label="Haptic feedback" description="Cues on the controller when recording starts and stops"
							checked={hapticFeedback} onChange={async (next) => {
								const result = await setHapticFeedbackRpc(next);
								if (result.success) setHapticFeedback(next);
								else setRpcError(result.error || "Could not update haptic feedback");
							}} /></PanelSectionRow>
					</PanelSection>
					<PanelSectionRow><ButtonItem layout="below" onClick={() => setPage("diagnostics")}>Diagnostics</ButtonItem></PanelSectionRow>
					<PanelSectionRow><ButtonItem layout="below" onClick={() => setPage("help")}>Help & permissions</ButtonItem></PanelSectionRow>
				</>}
				{page === "diagnostics" && <>
					<PanelSection title="Input and service">
						<PanelSectionRow><div>Controller: {controllerStatus}</div></PanelSectionRow>
						<PanelSectionRow><div>Binding supported: {controllerComboSupported ? "Yes" : "No"}</div></PanelSectionRow>
						<PanelSectionRow><div>Held buttons: <strong>{buttonState}</strong></div></PanelSectionRow>
						<PanelSectionRow><div>Keyboard helper: {inputReady ? "Ready" : "Unavailable"}</div></PanelSectionRow>
						<PanelSectionRow><div>Backend: {serviceReady ? "Ready" : "Unavailable"}</div></PanelSectionRow>
						<PanelSectionRow><div>Model: {modelLoading ? "Loading" : modelReady ? "Ready" : "Unavailable"}</div></PanelSectionRow>
						{(statusError || rpcError) && <PanelSectionRow><div role="alert">{statusError || rpcError}</div></PanelSectionRow>}
					</PanelSection>
					<PanelSection title="Diagnostics sharing">
						<PanelSectionRow><ToggleField label="Share" description="Optional scrubbed diagnostics sent to Sentry"
							checked={shareDiagnostics} onChange={async (next) => {
								setShareDiagnostics(next);
								const result = await setShareDiagnosticsRpc(next);
								if (!result.success) { setShareDiagnostics(!next); setRpcError(result.error || "Could not update diagnostics setting"); }
							}} /></PanelSectionRow>
					</PanelSection>
				</>}
				{page === "game" && <PanelSection title="Game">
					{rpcError && <PanelSectionRow><div role="alert">{rpcError}</div></PanelSectionRow>}
					{presets.map(option => <PanelSectionRow key={String(option.data)}><ButtonItem layout="below" onClick={async () => {
						const next = option.data as string;
						setRpcError("");
						const result = await setActivePresetRpc(next);
						if (result.success) { setActivePreset(next); setPage("main"); }
						else setRpcError(result.error || "Could not update game");
					}}>{option.data === activePreset ? "✓ " : ""}{option.label}</ButtonItem></PanelSectionRow>)}
				</PanelSection>}
				{page === "model" && <PanelSection title="Model">
					{rpcError && <PanelSectionRow><div role="alert">{rpcError}</div></PanelSectionRow>}
					{MODEL_SIZE_OPTIONS.map(option => <PanelSectionRow key={String(option.data)}><ButtonItem layout="below" onClick={async () => {
						const next = option.data as string;
						setRpcError("");
						if (enabled && modelReady) setModelLoading(true);
						const result = await setModelSizeRpc(next);
						if (result.success) { setModelSize(next); setPage("advanced"); }
						else { setModelLoading(false); setRpcError(result.error || "Could not update model size"); }
					}}>{option.data === modelSize ? "✓ " : ""}{option.label}</ButtonItem></PanelSectionRow>)}
				</PanelSection>}
				{page === "binding-button" && <PanelSection title={`Button ${bindingButtonIndex + 1}`}>
					{rpcError && <PanelSectionRow><div role="alert">{rpcError}</div></PanelSectionRow>}
					{BUTTON_OPTIONS.map(option => <PanelSectionRow key={String(option.data)}><ButtonItem layout="below" onClick={async () => {
						const next = [...buttons];
						next[bindingButtonIndex] = option.data as string;
						setRpcError("");
						const result = await setButtonConfig(next);
						if (result.success) { setButtons(next); setPage("advanced"); }
						else setRpcError(result.error || "Could not update binding");
					}}>{option.data === buttons[bindingButtonIndex] ? "✓ " : ""}{option.label}</ButtonItem></PanelSectionRow>)}
				</PanelSection>}
				{page === "help" && <>
					<PanelSection title="How to use">
						<PanelSectionRow><div style={{ fontSize: '13px', lineHeight: '1.6' }}>
							Hold <strong>{buttons.join('+')}</strong> {buttons.length > 1 ? "together " : ""}to record.
							Release to transcribe and type into the active game or app. Keep it in the foreground.
						</div></PanelSectionRow>
					</PanelSection>
					<PanelSection title="Permissions">
						<PanelSectionRow><div style={{ fontSize: '13px', lineHeight: '1.5' }}>
							Decktation uses Decky root access only to read raw Steam Deck controller input and to create virtual keyboard events for dictated text.
							Your transcription is passed to the bundled keyboard helper as data, never as a shell command.
						</div></PanelSectionRow>
					</PanelSection>
				</>}
			</div>
		</Focusable>
	);
};


export default definePlugin(() => {
	let logic = new DecktationLogic();
	// Seed the recording start count so we don't fire a spurious toast on load
	getStatus().then((result) => {
		if (result.success) {
			logic.prevRecordingStartCount = result.recording_start_count || 0;
		}
	});

	// Background notification polling — runs for the full plugin lifetime regardless
	// of whether the Decky panel is open, so toasts appear while in-game.
	let notifyPollInFlight = false;
	const bgNotifyInterval = setInterval(async () => {
		if (!logic.enabled || notifyPollInFlight) return;
		notifyPollInFlight = true;
		try {
			const result = await getStatus();
			if (result.success) {
				if (logic.recordingIndicator !== "none") {
					const startCount: number = result.recording_start_count || 0;
					if (logic.recordingIndicator === "toast" && startCount > logic.prevRecordingStartCount) {
						logic.notify("Recording", 1500, "🎤 Recording...");
					}
					logic.prevRecordingStartCount = startCount;

					const pendingText: string = result.pending_text || "";
					const pendingDelay: number = result.pending_delay || 0;
					if (pendingText && !logic.prevPendingText) {
						const secs = Math.round(pendingDelay);
						logic.notify(`Sending in ${secs}s`, (pendingDelay + 0.5) * 1000, `"${pendingText}" — hold PTT to cancel`)
							.then(id => { logic.lastPendingToastId = id; });
					} else if (!pendingText && logic.prevPendingText) {
						if (logic.lastPendingToastId >= 0) {
							logic.dismissNotification(logic.lastPendingToastId);
							logic.lastPendingToastId = -1;
						}
					}
					logic.prevPendingText = pendingText;
				}
			}
		} catch (_e) {
		} finally {
			notifyPollInFlight = false;
		}
	}, 1000);

	return {
		title: <div className={quickAccessMenuClasses.Title}>Decktation</div>,
		content: <DecktationPanel logic={logic} />,
		icon: <FaMicrophone />,
		onDismount() {
			clearInterval(bgNotifyInterval);
			if (logic.recording) {
				void stopRecording();
			}
		},
		alwaysRender: true
	};
});
