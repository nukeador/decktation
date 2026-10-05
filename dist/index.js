(function (deckyFrontendLib, React) {
    'use strict';

    function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

    var React__default = /*#__PURE__*/_interopDefaultLegacy(React);

    var _manifest = {"name":"Decktation","version":"0.3.20-dev.i18n.1","author":"silverfoxy","flags":["root"],"api_version":1,"publish":{"tags":["voice","dictation","speech-to-text","input","chat","gaming","accessibility"],"description":"Push-to-talk dictation for Steam Deck. Context-aware speech-to-text using whisper.cpp.","image":"https://raw.githubusercontent.com/silverfoxy/decktation/master/store-card.png"}};

    const manifest = _manifest;
    const API_VERSION = 2;
    if (!manifest?.name) {
        throw new Error('[@decky/api]: Failed to find plugin manifest.');
    }
    const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
    if (!internalAPIConnection) {
        throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
    }
    let api;
    try {
        api = internalAPIConnection.connect(API_VERSION, manifest.name);
    }
    catch {
        api = internalAPIConnection.connect(1, manifest.name);
        console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
    }
    if (api._version != API_VERSION) {
        console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
    }
    api.call;
    const callable = api.callable;
    api.addEventListener;
    api.removeEventListener;
    api.routerHook;
    const toaster = api.toaster;
    api.openFilePicker;
    api.executeInTab;
    api.injectCssIntoTab;
    api.removeCssFromTab;
    api.fetchNoCors;
    api.getExternalResourceURL;
    api.useQuickAccessVisible;

    var DefaultContext = {
      color: undefined,
      size: undefined,
      className: undefined,
      style: undefined,
      attr: undefined
    };
    var IconContext = React__default["default"].createContext && React__default["default"].createContext(DefaultContext);

    var __assign = window && window.__assign || function () {
      __assign = Object.assign || function (t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
          s = arguments[i];
          for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }
        return t;
      };
      return __assign.apply(this, arguments);
    };
    var __rest = window && window.__rest || function (s, e) {
      var t = {};
      for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0) t[p] = s[p];
      if (s != null && typeof Object.getOwnPropertySymbols === "function") for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
        if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i])) t[p[i]] = s[p[i]];
      }
      return t;
    };
    function Tree2Element(tree) {
      return tree && tree.map(function (node, i) {
        return React__default["default"].createElement(node.tag, __assign({
          key: i
        }, node.attr), Tree2Element(node.child));
      });
    }
    function GenIcon(data) {
      // eslint-disable-next-line react/display-name
      return function (props) {
        return React__default["default"].createElement(IconBase, __assign({
          attr: __assign({}, data.attr)
        }, props), Tree2Element(data.child));
      };
    }
    function IconBase(props) {
      var elem = function (conf) {
        var attr = props.attr,
          size = props.size,
          title = props.title,
          svgProps = __rest(props, ["attr", "size", "title"]);
        var computedSize = size || conf.size || "1em";
        var className;
        if (conf.className) className = conf.className;
        if (props.className) className = (className ? className + " " : "") + props.className;
        return React__default["default"].createElement("svg", __assign({
          stroke: "currentColor",
          fill: "currentColor",
          strokeWidth: "0"
        }, conf.attr, attr, svgProps, {
          className: className,
          style: __assign(__assign({
            color: props.color || conf.color
          }, conf.style), props.style),
          height: computedSize,
          width: computedSize,
          xmlns: "http://www.w3.org/2000/svg"
        }), title && React__default["default"].createElement("title", null, title), props.children);
      };
      return IconContext !== undefined ? React__default["default"].createElement(IconContext.Consumer, null, function (conf) {
        return elem(conf);
      }) : elem(DefaultContext);
    }

    // THIS FILE IS AUTO GENERATED
    function FaMicrophone (props) {
      return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 352 512"},"child":[{"tag":"path","attr":{"d":"M176 352c53.02 0 96-42.98 96-96V96c0-53.02-42.98-96-96-96S80 42.98 80 96v160c0 53.02 42.98 96 96 96zm160-160h-16c-8.84 0-16 7.16-16 16v48c0 74.8-64.49 134.82-140.79 127.38C96.71 376.89 48 317.11 48 250.3V208c0-8.84-7.16-16-16-16H16c-8.84 0-16 7.16-16 16v40.16c0 89.64 63.97 169.55 152 181.69V464H96c-8.84 0-16 7.16-16 16v16c0 8.84 7.16 16 16 16h160c8.84 0 16-7.16 16-16v-16c0-8.84-7.16-16-16-16h-56v-33.77C285.71 418.47 352 344.9 352 256v-48c0-8.84-7.16-16-16-16z"}}]})(props);
    }function FaTrash (props) {
      return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 448 512"},"child":[{"tag":"path","attr":{"d":"M432 32H312l-9.4-18.7A24 24 0 0 0 281.1 0H166.8a23.72 23.72 0 0 0-21.4 13.3L136 32H16A16 16 0 0 0 0 48v32a16 16 0 0 0 16 16h416a16 16 0 0 0 16-16V48a16 16 0 0 0-16-16zM53.2 467a48 48 0 0 0 47.9 45h245.8a48 48 0 0 0 47.9-45L416 128H32z"}}]})(props);
    }

    var Back$1 = "Back";
    var Enable$1 = "Enable";
    var Game$1 = "Game";
    var Language$1 = "Language";
    var Binding$1 = "Binding";
    var Result$1 = "Result";
    var Model$1 = "Model";
    var Sending$1 = "Sending";
    var Confirm$1 = "Confirm";
    var Manual$1 = "Manual";
    var Feedback$1 = "Feedback";
    var Toast$1 = "Toast";
    var Overlay$1 = "Overlay";
    var None$1 = "None";
    var Diagnostics$1 = "Diagnostics";
    var Controller$1 = "Controller";
    var Yes$1 = "Yes";
    var No$1 = "No";
    var Backend$1 = "Backend";
    var Ready$1 = "Ready";
    var Unavailable$1 = "Unavailable";
    var Loading$1 = "Loading";
    var Share$1 = "Share";
    var Permissions$1 = "Permissions";
    var Recording$1 = "Recording";
    var Generic$1 = "Generic";
    var en = {
      Back: Back$1,
      Enable: Enable$1,
      "Quick settings": "Quick settings",
      Game: Game$1,
      Language: Language$1,
      Binding: Binding$1,
      "Edit Bindings": "Edit Bindings",
      "Try it": "Try it",
      "Recording...": "Recording...",
      "Transcribing...": "Transcribing...",
      "Test Dictation (3s)": "Test Dictation (3s)",
      "Shows a transcription here without sending text to your game.": "Shows a transcription here without sending text to your game.",
      Result: Result$1,
      "No speech detected": "No speech detected",
      "Advanced settings": "Advanced settings",
      "Transcription model": "Transcription model",
      Model: Model$1,
      "Recording binding": "Recording binding",
      Sending: Sending$1,
      Confirm: Confirm$1,
      "Delay before send": "Delay before send",
      Manual: Manual$1,
      "You press Enter": "You press Enter",
      "Remember channel": "Remember channel",
      "Reuse the last spoken channel": "Reuse the last spoken channel",
      Feedback: Feedback$1,
      "Recording cue": "Recording cue",
      Toast: Toast$1,
      Overlay: Overlay$1,
      None: None$1,
      "Haptic feedback": "Haptic feedback",
      "Cues on the controller when recording starts and stops": "Cues on the controller when recording starts and stops",
      Diagnostics: Diagnostics$1,
      "Help & permissions": "Help & permissions",
      "Input and service": "Input and service",
      Controller: Controller$1,
      "Binding supported": "Binding supported",
      Yes: Yes$1,
      No: No$1,
      "Held buttons": "Held buttons",
      "Keyboard helper": "Keyboard helper",
      Backend: Backend$1,
      Ready: Ready$1,
      Unavailable: Unavailable$1,
      Loading: Loading$1,
      "Diagnostics sharing": "Diagnostics sharing",
      Share: Share$1,
      "Optional scrubbed diagnostics sent to Sentry": "Optional scrubbed diagnostics sent to Sentry",
      "How to use": "How to use",
      Permissions: Permissions$1,
      "Auto Detect": "Auto Detect",
      "Popular Steam languages": "Popular Steam languages",
      "Other languages": "Other languages",
      "Add Button": "Add Button",
      "Button {number}": "Button {number}",
      "Remove button {number}": "Remove button {number}",
      "Hold {binding} to record": "Hold {binding} to record",
      "Hold {binding} {together}to record. Release to transcribe and type into the active game or app. Keep it in the foreground.": "Hold {binding} {together}to record. Release to transcribe and type into the active game or app. Keep it in the foreground.",
      "together ": "together ",
      "Decktation uses Decky root access only to read raw Steam Deck controller input and to create virtual keyboard events for dictated text. Your transcription is passed to the bundled keyboard helper as data, never as a shell command.": "Decktation uses Decky root access only to read raw Steam Deck controller input and to create virtual keyboard events for dictated text. Your transcription is passed to the bundled keyboard helper as data, never as a shell command.",
      "Base is fastest. Small balances speed and accuracy. Medium is more accurate but slower and may download on first use.": "Base is fastest. Small balances speed and accuracy. Medium is more accurate but slower and may download on first use.",
      "whisper.cpp runs on the GPU via Vulkan.": "whisper.cpp runs on the GPU via Vulkan.",
      "whisper.cpp runs on the CPU.": "whisper.cpp runs on the CPU.",
      "Connecting to Decktation...": "Connecting to Decktation...",
      "Keyboard helper unavailable. Reload or reinstall Decktation.": "Keyboard helper unavailable. Reload or reinstall Decktation.",
      "Loading transcription model...": "Loading transcription model...",
      "Decktation is off": "Decktation is off",
      "Model not ready": "Model not ready",
      "Controller unavailable": "Controller unavailable",
      "Backend unavailable: {error}": "Backend unavailable: {error}",
      "Recording for 3 seconds...": "Recording for 3 seconds...",
      Recording: Recording$1,
      "Sending in {seconds}s": "Sending in {seconds}s",
      "\"{text}\" — hold PTT to cancel": "\"{text}\" — hold PTT to cancel",
      "Interface language": "Interface language",
      "Automatic (system)": "Automatic (system)",
      "Only changes the menu language, not the dictation language.": "Only changes the menu language, not the dictation language.",
      Generic: Generic$1,
      "Base · Fast": "Base · Fast",
      "Small · Balanced": "Small · Balanced",
      "Medium · More accurate": "Medium · More accurate",
      "Could not start test recording": "Could not start test recording",
      "Could not transcribe test recording": "Could not transcribe test recording",
      "Could not read test transcription": "Could not read test transcription",
      "Could not update enabled state": "Could not update enabled state",
      "Could not load Whisper model": "Could not load Whisper model",
      "Could not remove button": "Could not remove button",
      "Could not update channel setting": "Could not update channel setting",
      "Could not update recording cue": "Could not update recording cue",
      "Could not update haptic feedback": "Could not update haptic feedback",
      "Could not update diagnostics setting": "Could not update diagnostics setting",
      "Could not update game": "Could not update game",
      "Could not update model size": "Could not update model size",
      "Could not update binding": "Could not update binding",
      "Could not update language": "Could not update language",
      "L1 Bumper": "L1 Bumper",
      "R1 Bumper": "R1 Bumper",
      "L2 Trigger": "L2 Trigger",
      "R2 Trigger": "R2 Trigger",
      "L4 Grip": "L4 Grip",
      "R4 Grip": "R4 Grip",
      "L5 Grip": "L5 Grip",
      "R5 Grip": "R5 Grip",
      "Waiting for input": "Waiting for input",
      "Status unavailable": "Status unavailable",
      "Backend status request failed": "Backend status request failed",
      "Could not update language setting": "Could not update language setting"
    };

    var Back = "Volver";
    var Enable = "Activar";
    var Game = "Juego";
    var Language = "Idioma del dictado";
    var Binding = "Combinación";
    var Result = "Resultado";
    var Model = "Modelo";
    var Sending = "Envío";
    var Confirm = "Confirmar";
    var Manual = "Envío manual";
    var Feedback = "Indicadores";
    var Toast = "Notificación";
    var Overlay = "Indicador en pantalla";
    var None = "Ninguno";
    var Diagnostics = "Diagnóstico";
    var Controller = "Mando";
    var Yes = "Sí";
    var No = "No";
    var Backend = "Servicio del plugin";
    var Ready = "Listo";
    var Unavailable = "No disponible";
    var Loading = "Cargando";
    var Share = "Compartir";
    var Permissions = "Permisos";
    var Recording = "Grabación";
    var Generic = "Texto general";
    var es = {
      Back: Back,
      Enable: Enable,
      "Quick settings": "Ajustes rápidos",
      Game: Game,
      Language: Language,
      Binding: Binding,
      "Edit Bindings": "Editar combinación",
      "Try it": "Prueba de dictado",
      "Recording...": "Grabando...",
      "Transcribing...": "Transcribiendo...",
      "Test Dictation (3s)": "Probar dictado (3 s)",
      "Shows a transcription here without sending text to your game.": "Muestra el texto aquí sin enviarlo al juego.",
      Result: Result,
      "No speech detected": "No se detectó voz",
      "Advanced settings": "Ajustes avanzados",
      "Transcription model": "Modelo de transcripción",
      Model: Model,
      "Recording binding": "Combinación para grabar",
      Sending: Sending,
      Confirm: Confirm,
      "Delay before send": "Esperar antes de enviar",
      Manual: Manual,
      "You press Enter": "Pulsa Intro para enviar",
      "Remember channel": "Recordar canal",
      "Reuse the last spoken channel": "Reutilizar el último canal indicado",
      Feedback: Feedback,
      "Recording cue": "Indicador de grabación",
      Toast: Toast,
      Overlay: Overlay,
      None: None,
      "Haptic feedback": "Vibración al grabar",
      "Cues on the controller when recording starts and stops": "Vibración en el mando al iniciar y terminar la grabación",
      Diagnostics: Diagnostics,
      "Help & permissions": "Ayuda y permisos",
      "Input and service": "Entrada y servicio",
      Controller: Controller,
      "Binding supported": "Combinación compatible",
      Yes: Yes,
      No: No,
      "Held buttons": "Botones pulsados",
      "Keyboard helper": "Servicio de teclado",
      Backend: Backend,
      Ready: Ready,
      Unavailable: Unavailable,
      Loading: Loading,
      "Diagnostics sharing": "Compartir diagnóstico",
      Share: Share,
      "Optional scrubbed diagnostics sent to Sentry": "Envía datos de diagnóstico depurados a Sentry (opcional)",
      "How to use": "Cómo usarlo",
      Permissions: Permissions,
      "Auto Detect": "Detección automática",
      "Popular Steam languages": "Idiomas habituales de Steam",
      "Other languages": "Otros idiomas",
      "Add Button": "Añadir botón",
      "Button {number}": "Botón {number}",
      "Remove button {number}": "Eliminar botón {number}",
      "Hold {binding} to record": "Mantén {binding} para grabar",
      "Hold {binding} {together}to record. Release to transcribe and type into the active game or app. Keep it in the foreground.": "Mantén {binding} {together}para grabar. Suelta para transcribir y escribir en el juego o aplicación que esté en primer plano.",
      "together ": "a la vez ",
      "Decktation uses Decky root access only to read raw Steam Deck controller input and to create virtual keyboard events for dictated text. Your transcription is passed to the bundled keyboard helper as data, never as a shell command.": "Decktation usa el acceso root de Decky para leer los botones del mando y generar eventos de teclado con el dictado. La transcripción se transmite como texto, nunca como un comando de consola.",
      "Base is fastest. Small balances speed and accuracy. Medium is more accurate but slower and may download on first use.": "Base es el más rápido. Small equilibra rapidez y precisión. Medium ofrece más precisión, pero es más lento y puede descargarse al usarlo por primera vez.",
      "whisper.cpp runs on the GPU via Vulkan.": "whisper.cpp usa la GPU mediante Vulkan.",
      "whisper.cpp runs on the CPU.": "whisper.cpp usa la CPU.",
      "Connecting to Decktation...": "Conectando con Decktation...",
      "Keyboard helper unavailable. Reload or reinstall Decktation.": "El servicio de teclado no está disponible. Recarga o reinstala Decktation.",
      "Loading transcription model...": "Cargando el modelo de transcripción...",
      "Decktation is off": "Decktation está desactivado",
      "Model not ready": "El modelo no está listo",
      "Controller unavailable": "Mando no disponible",
      "Backend unavailable: {error}": "Servicio no disponible: {error}",
      "Recording for 3 seconds...": "Grabando durante 3 segundos...",
      Recording: Recording,
      "Sending in {seconds}s": "Envío en {seconds} s",
      "\"{text}\" — hold PTT to cancel": "«{text}» — mantén la combinación de grabación para cancelar",
      "Interface language": "Idioma de la interfaz",
      "Automatic (system)": "Automático (sistema)",
      "Only changes the menu language, not the dictation language.": "Solo cambia el idioma del menú, no el del dictado.",
      Generic: Generic,
      "Base · Fast": "Base · Rápido",
      "Small · Balanced": "Small · Equilibrado",
      "Medium · More accurate": "Medium · Más preciso",
      "Could not start test recording": "No se pudo iniciar la prueba",
      "Could not transcribe test recording": "No se pudo transcribir la prueba",
      "Could not read test transcription": "No se pudo leer el resultado de la prueba",
      "Could not update enabled state": "No se pudo activar o desactivar Decktation",
      "Could not load Whisper model": "No se pudo cargar el modelo Whisper",
      "Could not remove button": "No se pudo eliminar el botón",
      "Could not update channel setting": "No se pudo cambiar el ajuste del canal",
      "Could not update recording cue": "No se pudo cambiar el indicador de grabación",
      "Could not update haptic feedback": "No se pudo cambiar la vibración",
      "Could not update diagnostics setting": "No se pudo cambiar el ajuste de diagnóstico",
      "Could not update game": "No se pudo cambiar el juego",
      "Could not update model size": "No se pudo cambiar el modelo",
      "Could not update binding": "No se pudo cambiar la combinación",
      "Could not update language": "No se pudo cambiar el idioma",
      "L1 Bumper": "L1 (superior)",
      "R1 Bumper": "R1 (superior)",
      "L2 Trigger": "L2 (gatillo)",
      "R2 Trigger": "R2 (gatillo)",
      "L4 Grip": "L4 (trasero)",
      "R4 Grip": "R4 (trasero)",
      "L5 Grip": "L5 (trasero)",
      "R5 Grip": "R5 (trasero)",
      "Waiting for input": "Esperando entrada",
      "Status unavailable": "Estado no disponible",
      "Backend status request failed": "No se pudo consultar el estado del servicio",
      "Could not update language setting": "No se pudo cambiar el idioma del dictado"
    };

    const STORAGE_KEY = "decktation.interfaceLanguage";
    let preference = "auto";
    try {
        const saved = window.localStorage.getItem(STORAGE_KEY);
        if (saved === "en" || saved === "es")
            preference = saved;
    }
    catch (_) { /* Storage may be unavailable in the Steam renderer. */ }
    function getInterfacePreference() { return preference; }
    function setInterfacePreference(value) {
        if (!["auto", "en", "es"].includes(value))
            return;
        preference = value;
        try {
            window.localStorage.setItem(STORAGE_KEY, value);
        }
        catch (_) { }
    }
    function resolveLocale(value, systemLanguage) {
        if (value !== "auto")
            return value;
        return /^es(?:[-_]|$)/i.test(systemLanguage) ? "es" : "en";
    }
    function locale() {
        return resolveLocale(preference, typeof navigator === "undefined" ? "en" : navigator.language);
    }
    function t(key, values = {}) {
        const english = en;
        const translated = es;
        const text = (locale() === "es" ? translated[key] : undefined) || english[key] || key;
        return text.replace(/\{(\w+)\}/g, (match, name) => values[name] === undefined ? match : String(values[name]));
    }
    function languageName(code, fallback) {
        if (code === "auto")
            return t("Auto Detect");
        // Intl supplies localized names; original labels are the safe fallback for
        // Whisper codes not recognised by the renderer. No codes are rewritten.
        try {
            const names = new Intl.DisplayNames([locale()], { type: "language" });
            const name = names.of(code);
            return name && name !== code ? name : fallback;
        }
        catch (_) {
            return fallback;
        }
    }

    const getStatus = callable("get_status");
    const getButtonConfig = callable("get_button_config");
    const getPresets = callable("get_presets");
    const setEnabledRpc = callable("set_enabled");
    const loadModel = callable("load_model");
    const startRecording = callable("start_recording");
    const stopRecording = callable("stop_recording");
    const getLastTranscription = callable("get_last_transcription");
    const setConfirmModeRpc = callable("set_confirm_mode");
    const setManualSendRpc = callable("set_manual_send");
    const setRememberLastChannelRpc = callable("set_remember_last_channel");
    const setShareDiagnosticsRpc = callable("set_share_diagnostics");
    const setRecordingIndicatorRpc = callable("set_recording_indicator");
    const setHapticFeedbackRpc = callable("set_haptic_feedback");
    const setActivePresetRpc = callable("set_active_preset");
    const setModelSizeRpc = callable("set_model_size");
    const setTranscriptionOptionsRpc = callable("set_transcription_options");
    const setButtonConfig = callable("set_button_config");
    class DecktationLogic {
        constructor() {
            this.enabled = false;
            this.recording = false;
            this.recordingIndicator = "toast";
            this.prevRecordingStartCount = 0;
            this.prevPendingText = "";
            this.lastPendingToastId = -1;
            this.notify = async (message, duration = 2000, body = "") => {
                if (!body) {
                    body = message;
                }
                const toast = {
                    title: message,
                    body: body,
                    duration: duration,
                    critical: false,
                };
                const id = window.NotificationStore ? window.NotificationStore.m_nNextTestNotificationID++ : 0;
                const toastData = {
                    nNotificationID: id,
                    bNewIndicator: false,
                    rtCreated: Date.now(),
                    eType: 43,
                    eSource: 1,
                    nToastDurationMS: duration,
                    data: toast,
                    decky: true,
                };
                const info = {
                    showToast: true,
                    sound: 6,
                    playSound: false,
                    eFeature: 0,
                    toastDurationMS: duration,
                    bCritical: false,
                    fnTray: (_t, tray) => { tray.unshift({ eType: 31, notifications: [toastData] }); },
                };
                try {
                    window.NotificationStore.ProcessNotification(info, toastData, 0);
                }
                catch (_e) {
                    // fallback to standard toaster if direct call fails
                    toaster.toast({ title: message, body: toast.body, duration: duration, critical: false });
                }
                return id;
            };
            this.dismissNotification = (id) => {
                // Force-expire the toast by reprocessing it with a 1ms duration
                try {
                    const toastData = {
                        nNotificationID: id,
                        bNewIndicator: false,
                        rtCreated: Date.now(),
                        eType: 43,
                        eSource: 1,
                        nToastDurationMS: 1,
                        data: { title: "", body: "", duration: 1, critical: false },
                        decky: true,
                    };
                    const info = {
                        showToast: true,
                        sound: 6,
                        playSound: false,
                        eFeature: 0,
                        toastDurationMS: 1,
                        bCritical: false,
                        fnTray: (_t, tray) => { tray.unshift({ eType: 31, notifications: [toastData] }); },
                    };
                    window.NotificationStore.ProcessNotification(info, toastData, 0);
                }
                catch (_e) { }
            };
            this.testRecording = async (onComplete, onPhase) => {
                onPhase("recording");
                try {
                    if (this.recordingIndicator === "toast")
                        this.notify("Decktation", 1000, t("Recording for 3 seconds..."));
                    const started = await startRecording();
                    if (!started.success)
                        throw new Error(started.error || t("Could not start test recording"));
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    // Keep the no-send argument: test text must never reach the active game.
                    onPhase("transcribing");
                    const transcription = stopRecording(false);
                    if (this.recordingIndicator === "toast")
                        this.notify("Decktation", 1500, t("Transcribing..."));
                    const stopped = await transcription;
                    if (!stopped.success)
                        throw new Error(stopped.error || t("Could not transcribe test recording"));
                    const result = await getLastTranscription();
                    if (!result.success)
                        throw new Error(result.error || t("Could not read test transcription"));
                    const data = result.transcription;
                    onComplete(data?.text || "", data?.timestamp ? new Date(data.timestamp * 1000).toLocaleTimeString() : "");
                }
                finally {
                    onPhase("idle");
                }
            };
        }
    }
    // Available button options
    const BUTTON_OPTIONS = [
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
    const WHISPER_LANGUAGE_OPTIONS = [
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
    const MODEL_SIZE_OPTIONS = [
        { data: "base", label: "Base · Fast" },
        { data: "small", label: "Small · Balanced" },
        { data: "medium", label: "Medium · More accurate" },
    ];
    const POPULAR_STEAM_LANGUAGE_CODES = new Set(["en", "zh", "ru", "es", "pt", "de", "ja", "fr", "pl", "ko"]);
    const byLanguageName = (left, right) => String(left.label).localeCompare(String(right.label));
    const POPULAR_LANGUAGE_OPTIONS = WHISPER_LANGUAGE_OPTIONS.filter(option => POPULAR_STEAM_LANGUAGE_CODES.has(String(option.data))).sort(byLanguageName);
    const OTHER_LANGUAGE_OPTIONS = WHISPER_LANGUAGE_OPTIONS.filter(option => option.data !== "auto" && !POPULAR_STEAM_LANGUAGE_CODES.has(String(option.data))).sort(byLanguageName);
    const PRESET_DISPLAY_NAMES = {
        wow: "World of Warcraft",
        guildwars2: "Guild Wars 2",
        generic: "Generic",
    };
    const DecktationPanel = ({ logic }) => {
        const [interfaceLanguage, updateInterfaceLanguage] = React.useState(getInterfacePreference);
        const [page, setPage] = React.useState("main");
        const panelRef = React.useRef(null);
        const languageMenuAnchorRef = React.useRef(null);
        const advancedModelRowRef = React.useRef(null);
        const [bindingButtonIndex, setBindingButtonIndex] = React.useState(0);
        const [enabled, setEnabled] = React.useState(false);
        const [recording, setRecording] = React.useState(false);
        const [serviceReady, setServiceReady] = React.useState(false);
        const [modelReady, setModelReady] = React.useState(false);
        const [inferenceDevice, setInferenceDevice] = React.useState(null);
        const [modelLoading, setModelLoading] = React.useState(false);
        const [isToggling, setIsToggling] = React.useState(false);
        const [inputReady, setInputReady] = React.useState(true);
        const [buttonState, setButtonState] = React.useState("None");
        const [controllerReady, setControllerReady] = React.useState(false);
        const [controllerStatus, setControllerStatus] = React.useState("Waiting for input");
        const [controllerComboSupported, setControllerComboSupported] = React.useState(true);
        const [buttons, setButtons] = React.useState(["L1", "R1"]);
        const [recordingIndicator, setRecordingIndicator] = React.useState("toast");
        const [hapticFeedback, setHapticFeedback] = React.useState(false);
        const [activePreset, setActivePreset] = React.useState("wow");
        const [presets, setPresets] = React.useState([]);
        const [confirmMode, setConfirmMode] = React.useState(false);
        const [manualSend, setManualSend] = React.useState(false);
        const [rememberLastChannel, setRememberLastChannel] = React.useState(false);
        const [shareDiagnostics, setShareDiagnostics] = React.useState(false);
        const [modelSize, setModelSize] = React.useState("base");
        const [transcriptionLanguage, setTranscriptionLanguage] = React.useState("auto");
        const [lastTranscription, setLastTranscription] = React.useState("");
        const [lastTranscriptionTime, setLastTranscriptionTime] = React.useState("");
        const [rpcError, setRpcError] = React.useState("");
        const [statusError, setStatusError] = React.useState("");
        const [testPhase, setTestPhase] = React.useState("idle");
        const [hasTestResult, setHasTestResult] = React.useState(false);
        React.useEffect(() => {
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
                    const opts = result.presets.map((p) => ({
                        data: p.id,
                        label: PRESET_DISPLAY_NAMES[p.id] || p.name,
                    }));
                    setPresets(opts);
                }
            }).catch((error) => setRpcError(String(error)));
        }, []);
        React.useEffect(() => {
            let cancelled = false;
            let timeout;
            const poll = async () => {
                try {
                    const result = await getStatus();
                    if (cancelled)
                        return;
                    if (result.success) {
                        setButtonState(result.detected_button || "None");
                        setControllerReady(result.controller_ready === true);
                        setControllerStatus(result.controller_status || "Waiting for input");
                        setControllerComboSupported(result.controller_combo_supported !== false);
                        setStatusError("");
                        setServiceReady(result.service_ready);
                        setModelReady(result.model_ready);
                        setInferenceDevice(result.inference_device === "gpu" || result.inference_device === "cpu"
                            ? result.inference_device
                            : null);
                        setModelLoading(result.model_loading);
                        setInputReady(result.input_ready !== false);
                        if (logic.enabled) {
                            setRecording(result.recording);
                        }
                    }
                    else {
                        setControllerReady(false);
                        setControllerStatus("Status unavailable");
                        setStatusError(result.error || t("Backend status request failed"));
                    }
                }
                catch (error) {
                    setControllerReady(false);
                    setControllerStatus("Status unavailable");
                    setStatusError(String(error));
                }
                finally {
                    if (!cancelled)
                        timeout = setTimeout(poll, 100);
                }
            };
            void poll();
            return () => {
                cancelled = true;
                if (timeout)
                    clearTimeout(timeout);
            };
        }, [logic.enabled]);
        React.useEffect(() => {
            // Steam's QAM keeps its scroll position when the content changes in place.
            const resetScroll = () => {
                let node = panelRef.current?.parentElement;
                while (node) {
                    if (node.scrollHeight > node.clientHeight)
                        node.scrollTop = 0;
                    node = node.parentElement;
                }
            };
            resetScroll();
            const frame = requestAnimationFrame(() => {
                resetScroll();
                if (page === "advanced") {
                    advancedModelRowRef.current?.querySelector('[role="button"], button')?.focus();
                }
            });
            return () => cancelAnimationFrame(frame);
        }, [page]);
        const goBack = () => setPage(page === "diagnostics" || page === "help" || page === "model" || page === "binding-button" ? "advanced" : "main");
        const chooseLanguage = async (language) => {
            const result = await setTranscriptionOptionsRpc(language);
            if (result.success) {
                setTranscriptionLanguage(language);
                setRpcError("");
            }
            else {
                setRpcError(result.error || t("Could not update language setting"));
            }
        };
        const runTest = async () => {
            if (testPhase !== "idle")
                return;
            setRpcError("");
            setHasTestResult(false);
            try {
                await logic.testRecording((text, time) => {
                    setLastTranscription(text);
                    setLastTranscriptionTime(time);
                    setHasTestResult(true);
                }, setTestPhase);
            }
            catch (error) {
                setRpcError(String(error));
            }
        };
        const statusMessage = statusError ? t("Backend unavailable: {error}", { error: statusError })
            : rpcError ? rpcError
                : !serviceReady ? t("Connecting to Decktation...")
                    : !inputReady ? t("Keyboard helper unavailable. Reload or reinstall Decktation.")
                        : recording ? t("Recording...")
                            : modelLoading ? t("Loading transcription model...")
                                : !enabled ? t("Decktation is off")
                                    : !modelReady ? t("Model not ready")
                                        : !controllerReady ? t("Controller unavailable")
                                            : t("Ready");
        const statusProblem = !!(statusError || rpcError || (serviceReady && !inputReady) || (enabled && serviceReady && !controllerReady));
        return (React__default["default"].createElement(deckyFrontendLib.Focusable, { onCancel: page === "main" ? undefined : (event) => {
                event.stopPropagation();
                goBack();
            }, onCancelActionDescription: page === "main" ? undefined : t("Back") },
            React__default["default"].createElement("div", { ref: panelRef },
                React__default["default"].createElement("style", null, `.decktation-trash-focused { outline: 3px solid #66c0f4 !important; outline-offset: 2px; background-color: #456b90 !important; box-shadow: 0 0 0 2px rgba(102, 192, 244, 0.38) !important; }`),
                page !== "main" && (React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                    React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: goBack }, t("Back")))),
                page === "main" && React__default["default"].createElement(React__default["default"].Fragment, null,
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: "Decktation" },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Enable"), checked: enabled, disabled: !serviceReady || modelLoading || isToggling, onChange: async (next) => {
                                    if (isToggling)
                                        return;
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
                                            setRpcError(result.error || t("Could not update enabled state"));
                                            return;
                                        }
                                        if (next && logic.enabled) {
                                            setModelLoading(true);
                                            const modelResult = await loadModel();
                                            if (!modelResult.success) {
                                                setRpcError(modelResult.error || t("Could not load Whisper model"));
                                            }
                                        }
                                    }
                                    catch (error) {
                                        setEnabled(!next);
                                        logic.enabled = !next;
                                        setRpcError(String(error));
                                    }
                                    finally {
                                        setIsToggling(false);
                                    }
                                } })),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { role: "status", style: { padding: statusProblem ? '10px' : '4px 0', borderRadius: '6px', backgroundColor: statusProblem ? '#713030' : undefined } }, statusMessage))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Quick settings") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.DropdownItem, { label: t("Interface language"), description: t("Only changes the menu language, not the dictation language."), rgOptions: [{ data: "auto", label: t("Automatic (system)") }, { data: "en", label: "English" }, { data: "es", label: "Español" }], selectedOption: interfaceLanguage, onChange: option => { const next = String(option.data); setInterfacePreference(next); updateInterfaceLanguage(next); } })),
                        presets.length > 0 && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("game") },
                                "Game: ",
                                t(String(presets.find(option => option.data === activePreset)?.label || activePreset)))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { style: { position: 'relative', width: '100%' } },
                                React__default["default"].createElement("span", { ref: languageMenuAnchorRef, "aria-hidden": "true", style: { position: 'absolute', left: 0, top: 0, width: '1px', height: '1px', pointerEvents: 'none' } }),
                                React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: (event) => {
                                        deckyFrontendLib.showContextMenu(React__default["default"].createElement(deckyFrontendLib.Menu, { label: t("Language") },
                                            React__default["default"].createElement(deckyFrontendLib.MenuItem, { selected: transcriptionLanguage === "auto", onSelected: () => { void chooseLanguage("auto"); } }, t("Auto Detect")),
                                            React__default["default"].createElement("div", { className: deckyFrontendLib.gamepadContextMenuClasses.ContextMenuSeparator }),
                                            React__default["default"].createElement("div", { className: deckyFrontendLib.gamepadContextMenuClasses.MenuSectionHeader }, t("Popular Steam languages")),
                                            POPULAR_LANGUAGE_OPTIONS.map(option => React__default["default"].createElement(deckyFrontendLib.MenuItem, { key: String(option.data), selected: option.data === transcriptionLanguage, onSelected: () => { void chooseLanguage(String(option.data)); } }, languageName(String(option.data), String(option.label)))),
                                            React__default["default"].createElement("div", { className: deckyFrontendLib.gamepadContextMenuClasses.ContextMenuSeparator }),
                                            React__default["default"].createElement("div", { className: deckyFrontendLib.gamepadContextMenuClasses.MenuSectionHeader }, t("Other languages")),
                                            OTHER_LANGUAGE_OPTIONS.map(option => React__default["default"].createElement(deckyFrontendLib.MenuItem, { key: String(option.data), selected: option.data === transcriptionLanguage, onSelected: () => { void chooseLanguage(String(option.data)); } }, languageName(String(option.data), String(option.label))))), languageMenuAnchorRef.current || event.currentTarget);
                                    } },
                                    t("Language"),
                                    ": ",
                                    languageName(transcriptionLanguage, String(WHISPER_LANGUAGE_OPTIONS.find(option => option.data === transcriptionLanguage)?.label || transcriptionLanguage))))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Binding"),
                                ": ",
                                React__default["default"].createElement("strong", null, buttons.join(' + ')))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("advanced") }, t("Edit Bindings")))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Try it") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: runTest, disabled: !enabled || !modelReady || modelLoading || recording || testPhase !== "idle" },
                                React__default["default"].createElement(FaMicrophone, { size: 14 }),
                                " ",
                                testPhase === "recording" ? t("Recording...") : testPhase === "transcribing" ? t("Transcribing...") : t("Test Dictation (3s)"))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { style: { fontSize: '12px', opacity: 0.85 } }, t("Shows a transcription here without sending text to your game."))),
                        hasTestResult && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { role: "status", style: { padding: '10px', backgroundColor: '#233829', borderRadius: '6px', overflowWrap: 'anywhere' } },
                                React__default["default"].createElement("strong", null, t("Result")),
                                React__default["default"].createElement("div", null, lastTranscription || t("No speech detected")),
                                React__default["default"].createElement("small", null, lastTranscriptionTime)))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("advanced") }, t("Advanced settings")))),
                page === "advanced" && React__default["default"].createElement(React__default["default"].Fragment, null,
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Transcription model") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { ref: advancedModelRowRef },
                                React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("model") },
                                    "Model: ",
                                    t(String(MODEL_SIZE_OPTIONS.find(option => option.data === modelSize)?.label || modelSize))))),
                        modelReady && !modelLoading && inferenceDevice && (React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null, inferenceDevice === "gpu"
                                ? t("whisper.cpp runs on the GPU via Vulkan.")
                                : t("whisper.cpp runs on the CPU.")))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { style: { fontSize: '12px' } }, t("Base is fastest. Small balances speed and accuracy. Medium is more accurate but slower and may download on first use.")))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Recording binding") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null, t("Hold {binding} to record", { binding: buttons.join("+") }))),
                        buttons.map((button, index) => React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, { key: index },
                            React__default["default"].createElement(deckyFrontendLib.Focusable, { "flow-children": "row", style: { display: 'flex', alignItems: 'center', gap: '4px', width: '100%', minWidth: 0, boxSizing: 'border-box' } },
                                React__default["default"].createElement("div", { style: { flex: '1 1 0', minWidth: 0, overflow: 'hidden' } },
                                    React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => { setBindingButtonIndex(index); setPage("binding-button"); } },
                                        t("Button {number}", { number: index + 1 }),
                                        ": ",
                                        button)),
                                buttons.length > 1 && React__default["default"].createElement(deckyFrontendLib.Focusable, { role: "button", tabIndex: 0, focusClassName: "decktation-trash-focused", "aria-label": t("Remove button {number}", { number: index + 1 }), onActivate: async () => {
                                        const next = buttons.filter((_, i) => i !== index);
                                        const result = await setButtonConfig(next);
                                        if (result.success)
                                            setButtons(next);
                                        else
                                            setRpcError(result.error || t("Could not remove button"));
                                    }, style: { flex: '0 0 36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '4px', backgroundColor: '#3b4252' } },
                                    React__default["default"].createElement(FaTrash, { size: 14, "aria-hidden": "true" }))))),
                        buttons.length < 5 && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: async () => {
                                    const available = BUTTON_OPTIONS.find(opt => !buttons.includes(opt.data));
                                    if (available) {
                                        const next = [...buttons, available.data];
                                        setButtons(next);
                                        await setButtonConfig(next);
                                    }
                                } }, t("Add Button")))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Sending") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Confirm"), description: t("Delay before send"), checked: confirmMode, onChange: async (next) => { setConfirmMode(next); await setConfirmModeRpc(next); } })),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Manual"), description: t("You press Enter"), checked: manualSend, onChange: async (next) => { setManualSend(next); await setManualSendRpc(next); } })),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Remember channel"), description: t("Reuse the last spoken channel"), checked: rememberLastChannel, onChange: async (next) => {
                                    setRememberLastChannel(next);
                                    const result = await setRememberLastChannelRpc(next);
                                    if (!result.success) {
                                        setRememberLastChannel(!next);
                                        setRpcError(result.error || t("Could not update channel setting"));
                                    }
                                } }))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Feedback") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.DropdownItem, { label: t("Recording cue"), menuLabel: t("Recording cue"), rgOptions: [{ data: "toast", label: t("Toast") }, { data: "overlay", label: t("Overlay") }, { data: "none", label: t("None") }], selectedOption: recordingIndicator, onChange: async (option) => { const mode = option.data; setRecordingIndicator(mode); logic.recordingIndicator = mode; const result = await setRecordingIndicatorRpc(mode); if (!result.success)
                                    setRpcError(result.error || t("Could not update recording cue")); } })),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Haptic feedback"), description: t("Cues on the controller when recording starts and stops"), checked: hapticFeedback, onChange: async (next) => {
                                    const result = await setHapticFeedbackRpc(next);
                                    if (result.success)
                                        setHapticFeedback(next);
                                    else
                                        setRpcError(result.error || t("Could not update haptic feedback"));
                                } }))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("diagnostics") }, t("Diagnostics"))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: () => setPage("help") }, t("Help & permissions")))),
                page === "diagnostics" && React__default["default"].createElement(React__default["default"].Fragment, null,
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Input and service") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Controller"),
                                ": ",
                                t(controllerStatus))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Binding supported"),
                                ": ",
                                controllerComboSupported ? t("Yes") : t("No"))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Held buttons"),
                                ": ",
                                React__default["default"].createElement("strong", null, t(buttonState)))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Keyboard helper"),
                                ": ",
                                inputReady ? t("Ready") : t("Unavailable"))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Backend"),
                                ": ",
                                serviceReady ? t("Ready") : t("Unavailable"))),
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", null,
                                t("Model"),
                                ": ",
                                modelLoading ? t("Loading") : modelReady ? t("Ready") : t("Unavailable"))),
                        (statusError || rpcError) && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { role: "alert" }, statusError || rpcError))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Diagnostics sharing") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement(deckyFrontendLib.ToggleField, { label: t("Share"), description: t("Optional scrubbed diagnostics sent to Sentry"), checked: shareDiagnostics, onChange: async (next) => {
                                    setShareDiagnostics(next);
                                    const result = await setShareDiagnosticsRpc(next);
                                    if (!result.success) {
                                        setShareDiagnostics(!next);
                                        setRpcError(result.error || t("Could not update diagnostics setting"));
                                    }
                                } })))),
                page === "game" && React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Game") },
                    rpcError && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement("div", { role: "alert" }, rpcError)),
                    presets.map(option => React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, { key: String(option.data) },
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: async () => {
                                const next = option.data;
                                setRpcError("");
                                const result = await setActivePresetRpc(next);
                                if (result.success) {
                                    setActivePreset(next);
                                    setPage("main");
                                }
                                else
                                    setRpcError(result.error || t("Could not update game"));
                            } },
                            option.data === activePreset ? "✓ " : "",
                            t(String(option.label)))))),
                page === "model" && React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Model") },
                    rpcError && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement("div", { role: "alert" }, rpcError)),
                    MODEL_SIZE_OPTIONS.map(option => React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, { key: String(option.data) },
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: async () => {
                                const next = option.data;
                                setRpcError("");
                                if (enabled && modelReady)
                                    setModelLoading(true);
                                const result = await setModelSizeRpc(next);
                                if (result.success) {
                                    setModelSize(next);
                                    setPage("advanced");
                                }
                                else {
                                    setModelLoading(false);
                                    setRpcError(result.error || t("Could not update model size"));
                                }
                            } },
                            option.data === modelSize ? "✓ " : "",
                            t(String(option.label)))))),
                page === "binding-button" && React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Button {number}", { number: bindingButtonIndex + 1 }) },
                    rpcError && React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                        React__default["default"].createElement("div", { role: "alert" }, rpcError)),
                    BUTTON_OPTIONS.map(option => React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, { key: String(option.data) },
                        React__default["default"].createElement(deckyFrontendLib.ButtonItem, { layout: "below", onClick: async () => {
                                const next = [...buttons];
                                next[bindingButtonIndex] = option.data;
                                setRpcError("");
                                const result = await setButtonConfig(next);
                                if (result.success) {
                                    setButtons(next);
                                    setPage("advanced");
                                }
                                else
                                    setRpcError(result.error || t("Could not update binding"));
                            } },
                            option.data === buttons[bindingButtonIndex] ? "✓ " : "",
                            t(String(option.label)))))),
                page === "help" && React__default["default"].createElement(React__default["default"].Fragment, null,
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("How to use") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { style: { fontSize: '13px', lineHeight: '1.6' } }, t("Hold {binding} {together}to record. Release to transcribe and type into the active game or app. Keep it in the foreground.", { binding: buttons.join("+"), together: buttons.length > 1 ? t("together ") : "" })))),
                    React__default["default"].createElement(deckyFrontendLib.PanelSection, { title: t("Permissions") },
                        React__default["default"].createElement(deckyFrontendLib.PanelSectionRow, null,
                            React__default["default"].createElement("div", { style: { fontSize: '13px', lineHeight: '1.5' } }, t("Decktation uses Decky root access only to read raw Steam Deck controller input and to create virtual keyboard events for dictated text. Your transcription is passed to the bundled keyboard helper as data, never as a shell command."))))))));
    };
    var index = deckyFrontendLib.definePlugin(() => {
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
            if (!logic.enabled || notifyPollInFlight)
                return;
            notifyPollInFlight = true;
            try {
                const result = await getStatus();
                if (result.success) {
                    if (logic.recordingIndicator !== "none") {
                        const startCount = result.recording_start_count || 0;
                        if (logic.recordingIndicator === "toast" && startCount > logic.prevRecordingStartCount) {
                            logic.notify(t("Recording"), 1500, "🎤 " + t("Recording..."));
                        }
                        logic.prevRecordingStartCount = startCount;
                        const pendingText = result.pending_text || "";
                        const pendingDelay = result.pending_delay || 0;
                        if (pendingText && !logic.prevPendingText) {
                            const secs = Math.round(pendingDelay);
                            logic.notify(t("Sending in {seconds}s", { seconds: secs }), (pendingDelay + 0.5) * 1000, t("\"{text}\" — hold PTT to cancel", { text: pendingText }))
                                .then(id => { logic.lastPendingToastId = id; });
                        }
                        else if (!pendingText && logic.prevPendingText) {
                            if (logic.lastPendingToastId >= 0) {
                                logic.dismissNotification(logic.lastPendingToastId);
                                logic.lastPendingToastId = -1;
                            }
                        }
                        logic.prevPendingText = pendingText;
                    }
                }
            }
            catch (_e) {
            }
            finally {
                notifyPollInFlight = false;
            }
        }, 1000);
        return {
            title: React__default["default"].createElement("div", { className: deckyFrontendLib.quickAccessMenuClasses.Title }, "Decktation"),
            content: React__default["default"].createElement(DecktationPanel, { logic: logic }),
            icon: React__default["default"].createElement(FaMicrophone, null),
            onDismount() {
                clearInterval(bgNotifyInterval);
                if (logic.recording) {
                    void stopRecording();
                }
            },
            alwaysRender: true
        };
    });

    return index;

})(DFL, SP_REACT);
