/* Cookie selection/export derived from M-rcus; MIT, see LICENSE.md.
 * Modified by ZenoBell, 2026-11-06. Shared by popup and synthetic Node tests.
 */
"use strict";
const CookieHelper = (() => {
    const messages = Object.freeze({
        TAB: "The selected tab is unavailable. Reopen the helper and select a regular OnlyFans tab. [TAB]",
        PAGE_ACCESS: "Could not run the helper script in the selected tab. Check site access, reload the tab and retry; if it persists, report this code. [PAGE_ACCESS]",
        PAGE_RESULT: "The browser did not return page data. Reload the OnlyFans tab and retry. [PAGE_RESULT]",
        COOKIE_ACCESS: "The browser could not read this tab's cookies. Check extension site access and cookie-isolation settings. [COOKIE_ACCESS]",
        LOGIN: "No complete signed-in session was found in the selected tab/container. Sign in there and retry. [LOGIN]",
        AMBIGUOUS: "Conflicting authentication cookies were found in this container. Sign out of OnlyFans and sign in again. [AMBIGUOUS]",
        TOKEN: "The selected page has no usable X-BC token yet. Let OnlyFans finish loading, reload the tab, and retry. [TOKEN]",
        USER_AGENT: "The browser did not provide a valid user agent. Reload the tab and retry. [USER_AGENT]",
        CHANGED: "The tab changed during export. Wait for it to finish loading and export again. [CHANGED]"
    });
    class ExportError extends Error {
        constructor(code) { super(messages[code]); this.code = code; }
    }
    function diagnostic(error) {
        // Only our fixed messages may reach the popup. Never expose browser/page exceptions.
        return error instanceof ExportError ? messages[error.code] : "Export failed unexpectedly. Reopen the helper and retry. [UNEXPECTED]";
    }
    function safeValue(value, optional = false, code = "LOGIN") {
        if (optional && (value === undefined || value === "")) return "";
        if (typeof value !== "string" || !value.trim() || value.length > 8192 || /[\x00-\x1f\x7f]/.test(value)) {
            throw new ExportError(code);
        }
        return value;
    }

    function makeExport(cookies, page) {
        function cookieValue(name) {
            // Browsers may return duplicate names for unrelated site/analytics cookies.
            // Only the three exported auth cookies can make this session ambiguous.
            const values = new Set(cookies.filter(cookie => cookie.name === name).map(cookie => cookie.value));
            if (values.size > 1) {
                throw new ExportError("AMBIGUOUS");
            }
            return values.values().next().value;
        }
        const authId = safeValue(cookieValue("auth_id"));
        if (!/^[0-9]+$/.test(authId)) throw new ExportError("LOGIN");
        const sess = safeValue(cookieValue("sess"));
        const uid = safeValue(cookieValue(`auth_uid_${authId}`), true);
        if ([sess, uid].some(value => value.includes(";"))) throw new ExportError("LOGIN");
        // Preserve upstream export structure, including optional legacy metadata.
        return {auth: {
            username: "u" + authId,
            cookie: `auth_id=${authId}; sess=${sess}; auth_hash=; auth_uniq_${authId}=; auth_uid_${authId}=${uid};`,
            user_agent: safeValue(page?.user_agent, false, "USER_AGENT"),
            x_bc: safeValue(page?.x_bc, false, "TOKEN"),
            support_2fa: true, active: true, email: "", password: "", hashed: false
        }};
    }

    async function collect(api, tabId) {
        let tab;
        try { tab = await api.tabs.get(tabId); }
        catch { throw new ExportError("TAB"); }
        if (!tab.url || new URL(tab.url).origin !== "https://onlyfans.com" || tab.incognito) {
            throw new ExportError("TAB");
        }
        const options = {url: "https://onlyfans.com/"};
        // Firefox containers: cookies and page localStorage must come from the same tab.
        if (tab.cookieStoreId) options.storeId = tab.cookieStoreId;
        let results;
        try {
            results = await api.scripting.executeScript({
                // Firefox resolves a relative path against popup/cookies.html.
                // Anchor at the extension root in both browsers.
                target: {tabId, frameIds: [0]}, files: ["/content_scripts/bcToken.js"]
            });
        } catch { throw new ExportError("PAGE_ACCESS"); }
        if (results?.[0]?.error) throw new ExportError("PAGE_ACCESS");
        if (!results?.[0]?.result) throw new ExportError("PAGE_RESULT");
        let cookies;
        try { cookies = await api.cookies.getAll(options); }
        catch { throw new ExportError("COOKIE_ACCESS"); }
        let after;
        try { after = await api.tabs.get(tabId); }
        catch { throw new ExportError("TAB"); }
        if (after.url !== tab.url || after.cookieStoreId !== tab.cookieStoreId) {
            throw new ExportError("CHANGED");
        }
        return makeExport(cookies, results[0]?.result);
    }
    return {makeExport, collect, diagnostic};
})();
if (typeof module !== "undefined") module.exports = CookieHelper;
