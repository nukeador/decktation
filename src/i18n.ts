import en from "./locales/en.json";
import es from "./locales/es.json";

export type InterfacePreference = "auto" | "en" | "es";
const STORAGE_KEY = "decktation.interfaceLanguage";
let preference: InterfacePreference = "auto";
let steamLanguage: string | undefined;
try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "es") preference = saved;
} catch (_) { /* Storage may be unavailable in the Steam renderer. */ }

export function getInterfacePreference(): InterfacePreference { return preference; }
export function setInterfacePreference(value: InterfacePreference): void {
    if (!["auto", "en", "es"].includes(value)) return;
    preference = value;
    try { window.localStorage.setItem(STORAGE_KEY, value); } catch (_) {}
}
export function resolveLocale(value: InterfacePreference, systemLanguage: string): "en" | "es" {
    if (value !== "auto") return value;
    return /^(?:es(?:[-_]|$)|spanish$|latam$)/i.test(systemLanguage) ? "es" : "en";
}
export async function initializeSteamLanguage(): Promise<void> {
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
        const settings = (window as any).SteamClient?.Settings;
        if (typeof settings?.GetCurrentLanguage !== "function") return;
        const value = await Promise.race([
            settings.GetCurrentLanguage(),
            new Promise(resolve => { timer = setTimeout(() => resolve(undefined), 1500); }),
        ]);
        if (typeof value === "string" && value) steamLanguage = value;
    } catch (_) { /* Use navigator.language if Steam cannot provide its locale. */ }
    finally { if (timer !== undefined) clearTimeout(timer); }
}
function locale(): "en" | "es" {
    return resolveLocale(preference, steamLanguage || (typeof navigator === "undefined" ? "en" : navigator.language));
}
export function t(key: string, values: Record<string, string | number> = {}): string {
    const english = en as Record<string, string>;
    const translated = es as Record<string, string>;
    const text = (locale() === "es" ? translated[key] : undefined) || english[key] || key;
    return text.replace(/\{(\w+)\}/g, (match, name) => values[name] === undefined ? match : String(values[name]));
}
export function languageName(code: string, fallback: string): string {
    if (code === "auto") return t("Auto Detect");
    // Intl supplies localized names; original labels are the safe fallback for
    // Whisper codes not recognised by the renderer. No codes are rewritten.
    try {
        const names = new (Intl as any).DisplayNames([locale()], {type: "language"});
        const name = names.of(code);
        return name && name !== code ? name : fallback;
    } catch (_) { return fallback; }
}
