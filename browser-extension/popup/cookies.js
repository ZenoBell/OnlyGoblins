/* Derived from M-rcus/OnlyFans-Cookie-Helper; MIT, see LICENSE.md.
 * Modified by ZenoBell, 2026-11-06: no automatic extraction or persistent secrets.
 */
"use strict";
const api = typeof browser !== "undefined" ? browser : chrome;
let exportText = "";
let generation = 0;
const byId = id => document.getElementById(id);

function clearExport() {
    generation++;
    exportText = "";
    byId("json").value = "";
    byId("copy-to-clipboard").disabled = true;
    byId("save-json").disabled = true;
    byId("status").textContent = "No session collected. Click Export when ready.";
}

async function getContainers() {
    clearExport();
    // Enumerate tab/container labels only; no cookies or page storage are read here.
    const names = {};
    if (api.contextualIdentities) {
        try {
            for (const identity of await api.contextualIdentities.query({})) {
                names[identity.cookieStoreId] = identity.name;
            }
        } catch { /* Containers may be disabled; default tabs still work. */ }
    }
    const tabs = await api.tabs.query({url: "https://onlyfans.com/*"});
    tabs.sort((a, b) => (names[a.cookieStoreId] || "Default").localeCompare(names[b.cookieStoreId] || "Default"));
    for (const tab of tabs.filter(tab => !tab.incognito)) {
        const option = document.createElement("option");
        option.value = String(tab.id);
        option.textContent = `${names[tab.cookieStoreId] || "Default"} — OnlyFans tab ${tab.id}${tab.active ? " (active)" : ""}`;
        byId("tab-list").appendChild(option);
        if (tab.active) option.selected = true;
    }
    byId("export").disabled = !byId("tab-list").options.length;
    if (byId("export").disabled) byId("status").textContent = "Open OnlyFans, sign in, then reopen this helper. Allow site access if prompted.";
}

async function grabCookies() {
    clearExport();
    const current = generation;
    byId("export").disabled = true;
    byId("tab-list").disabled = true;
    try {
        const data = await CookieHelper.collect(api, Number(byId("tab-list").value));
        if (current !== generation) return;
        exportText = JSON.stringify(data, null, 2);
        byId("json").value = exportText;
        byId("copy-to-clipboard").disabled = false;
        byId("save-json").disabled = false;
        byId("status").textContent = "Ready. Copy or save, then import in OnlyGoblins. Keep this private.";
    } catch (error) {
        if (current === generation) byId("status").textContent = CookieHelper.diagnostic(error);
    } finally {
        byId("export").disabled = false;
        byId("tab-list").disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    byId("export").addEventListener("click", grabCookies);
    byId("tab-list").addEventListener("change", clearExport);
    byId("clear").addEventListener("click", clearExport);
    // Register once; container switches cannot leave old-account copy handlers behind.
    byId("copy-to-clipboard").addEventListener("click", async () => {
        if (!exportText) return;
        try {
            await navigator.clipboard.writeText(exportText);
            byId("status").textContent = "Copied. Clear clipboard history after importing.";
        } catch {
            byId("status").textContent = "Clipboard unavailable. Select the JSON and copy manually.";
        }
    });
    byId("save-json").addEventListener("click", () => {
        if (!exportText) return;
        const url = URL.createObjectURL(new Blob([exportText], {type: "application/json"}));
        const link = document.createElement("a");
        link.href = url;
        link.download = "onlygoblins-auth-export.json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
    getContainers().catch(() => {
        byId("status").textContent = "Cannot list tabs. Allow OnlyFans site access and reopen the helper.";
    });
});
window.addEventListener("pagehide", clearExport);
