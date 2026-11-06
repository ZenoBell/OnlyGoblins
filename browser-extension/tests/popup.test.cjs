// Synthetic DOM/API harness. This is not a live-browser installation test.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function harness() {
    const elements = {};
    for (const id of ['json','status','copy-to-clipboard','save-json','clear','export','tab-list']) {
        elements[id] = {value:'',options:[],events:{},disabled:false,textContent:'',
            addEventListener(type, fn){assert.equal(this.events[type],undefined);this.events[type]=fn;},
            appendChild(option){this.options.push(option);this.value=option.value;}};
    }
    let ready;
    const calls = {collected:0, copied:[], saved:0};
    const context = vm.createContext({
        browser:{tabs:{query:async()=>[{id:1,active:true,cookieStoreId:'container-1'}]},
            contextualIdentities:{query:async()=>[{cookieStoreId:'container-1',name:'Synthetic container'}]}},
        CookieHelper:{collect:async()=>{calls.collected++;return {auth:{cookie:'synthetic-only'}};},
            diagnostic:require('../popup/export.js').diagnostic},
        document:{getElementById:id=>elements[id],addEventListener:(event,fn)=>{ready=fn;},
            createElement:tag=>({click:()=>{calls.saved++;}})},
        window:{addEventListener(){}},navigator:{clipboard:{writeText:async text=>calls.copied.push(text)}},
        URL:{createObjectURL:()=> 'blob:synthetic',revokeObjectURL(){}},Blob:class {},setTimeout:fn=>fn()
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname,'../popup/cookies.js'),'utf8'),context);
    ready();
    return {elements,calls,context};
}
test('popup open lists tabs but does not extract; explicit export/copy/save/clear', async () => {
    const {elements:e,calls} = harness();
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(calls.collected,0);
    assert.equal(e['tab-list'].options.length,1);
    assert.equal(e['copy-to-clipboard'].disabled,true);
    await e.export.events.click();
    assert.equal(calls.collected,1);
    await e['copy-to-clipboard'].events.click();
    assert.match(calls.copied[0], /synthetic-only/);
    e['save-json'].events.click();
    assert.equal(calls.saved,1);
    e.clear.events.click();
    assert.equal(e.json.value,'');
    await e['copy-to-clipboard'].events.click();
    assert.equal(calls.copied.length,1);
});
test('container switch clears stale export; copy handler is registered once', async () => {
    const {elements:e,calls} = harness();
    await new Promise(resolve=>setImmediate(resolve));
    await e.export.events.click();
    e['tab-list'].events.change();
    assert.equal(e.json.value,'');
    await e['copy-to-clipboard'].events.click();
    assert.equal(calls.copied.length,0);
    await e.export.events.click();
    await e['copy-to-clipboard'].events.click();
    assert.equal(calls.copied.length,1);
});
test('API error diagnostics never echo raw errors or previous export', async () => {
    const {elements:e,context} = harness();
    await new Promise(resolve=>setImmediate(resolve));
    await e.export.events.click();
    context.CookieHelper.collect = async()=>{throw Error('private-synthetic-value');};
    await e.export.events.click();
    assert.equal(e.json.value,'');
    assert.equal(e['copy-to-clipboard'].disabled,true);
    assert.ok(!e.status.textContent.includes('private-synthetic-value'));
});
