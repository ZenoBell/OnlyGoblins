// Synthetic data only. Node's built-in test runner; no npm dependencies.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {makeExport, collect, diagnostic} = require('../popup/export.js');
const page = {x_bc: 'synthetic-bc', user_agent: 'Synthetic Firefox (Test; offline)'};
const cookies = [{name:'auth_id',value:'123'}, {name:'sess',value:'synthetic-session'},
                 {name:'auth_uid_123',value:'synthetic-uid'}];

test('upstream-shaped export preserves actual UID and user agent', () => {
    const output = makeExport(cookies, page);
    assert.match(output.auth.cookie, /auth_uid_123=synthetic-uid;/);
    assert.equal(output.auth.x_bc, page.x_bc);
    assert.equal(output.auth.user_agent, page.user_agent);
    assert.equal(output.auth.password, '');
});
test('missing optional UID exports an empty value', () => {
    assert.match(makeExport(cookies.slice(0,2), page).auth.cookie, /auth_uid_123=;/);
});
test('missing and ambiguous credentials fail without echoing secrets', () => {
    for (const [c, p] of [[[], page], [cookies, {}], [[...cookies, {name:'sess',value:'secret-do-not-echo'}],page]]) {
        assert.throws(() => makeExport(c,p), error => !error.message.includes('secret-do-not-echo'));
    }
});
test('container cookies and page read use the selected tab only', async () => {
    const tab = {id: 42, url:'https://onlyfans.com/', cookieStoreId:'firefox-container-7'};
    const calls = [];
    const api = {
        tabs: {get: async id => {assert.equal(id,42); return tab;}},
        scripting: {executeScript: async opts => {calls.push(opts); return [{result:page}];}},
        cookies: {getAll: async opts => {calls.push(opts); return cookies;}}
    };
    assert.equal((await collect(api,42)).auth.x_bc, 'synthetic-bc');
    assert.deepEqual(calls[0], {target:{tabId:42,frameIds:[0]},files:['/content_scripts/bcToken.js']});
    assert.equal(new URL(calls[0].files[0], 'moz-extension://synthetic-id/popup/cookies.html').pathname, '/content_scripts/bcToken.js');
    assert.deepEqual(calls[1], {url:'https://onlyfans.com/',storeId:'firefox-container-7'});
});
test('Chromium does not require a Firefox cookieStoreId', async () => {
    const api = {tabs:{get:async()=>({url:'https://onlyfans.com/'})},
        scripting:{executeScript:async()=>[{result:page}]},
        cookies:{getAll:async opts=>{assert.deepEqual(opts,{url:'https://onlyfans.com/'});return cookies;}}};
    await collect(api,1);
});
test('unrelated/private tabs never trigger script or cookie access', async () => {
    for (const tab of [{url:'https://example.com/'}, {url:'https://onlyfans.com/',incognito:true}]) {
        await assert.rejects(collect({tabs:{get:async()=>tab}},1));
    }
});
test('navigation while collecting aborts', async () => {
    let count = 0;
    const api = {tabs:{get:async()=>({url:count++ ? 'https://onlyfans.com/changed':'https://onlyfans.com/'})},
        scripting:{executeScript:async()=>[{result:page}]}, cookies:{getAll:async()=>cookies}};
    await assert.rejects(collect(api,1), /tab changed/);
});

test('duplicate unrelated cookies do not block a valid session', () => {
    const duplicateNoise = [{name:'analytics',value:'synthetic-a'},{name:'analytics',value:'synthetic-b'},
        {name:'auth_uid_999',value:'unused-a'},{name:'auth_uid_999',value:'unused-b'}];
    assert.deepEqual(makeExport([...cookies,...duplicateNoise],page), makeExport(cookies,page));
});
test('only fixed safe diagnostics are displayed for failures', async () => {
    assert.ok(!diagnostic(Error('synthetic-private-error')).includes('synthetic-private-error'));
    const api = {tabs:{get:async()=>({url:'https://onlyfans.com/'})},
        scripting:{executeScript:async()=>{throw Error('synthetic-private-error');}}};
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[PAGE_ACCESS]'));
    api.scripting.executeScript = async()=>[{error:Error('synthetic-private-error')}];
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[PAGE_ACCESS]'));
    api.scripting.executeScript = async()=>[{result:undefined}];
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[PAGE_RESULT]'));
    api.scripting.executeScript = async()=>[{result:page}];
    api.cookies = {getAll:async()=>{throw Error('synthetic-private-error');}};
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[COOKIE_ACCESS]'));
    api.cookies.getAll = async()=>[];
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[LOGIN]'));
    api.cookies.getAll = async()=>cookies;
    api.scripting.executeScript = async()=>[{result:{user_agent:page.user_agent}}];
    await assert.rejects(collect(api,1), error => diagnostic(error).endsWith('[TOKEN]'));
});
