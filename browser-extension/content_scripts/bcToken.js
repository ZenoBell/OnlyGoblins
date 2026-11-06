/* Derived from M-rcus/OnlyFans-Cookie-Helper; MIT, see LICENSE.md.
 * Modified by ZenoBell, 2026-11-06: execute only after an explicit export click.
 * No listeners, messages, storage writes or background collection.
 */
(() => {
    if (location.origin !== "https://onlyfans.com") return null;
    return {
        x_bc: window.localStorage.getItem("bcTokenSha"),
        user_agent: navigator.userAgent
    };
})();
