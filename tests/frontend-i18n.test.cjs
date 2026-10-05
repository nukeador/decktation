const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const {createRequire}=require('node:module');
const ts=require('typescript');
const source=path.resolve(__dirname,'../src/i18n.ts');
function load(saved, language='en-US', blocked=false, steam){
 const values=new Map(saved?[['decktation.interfaceLanguage',saved]]:[]);
 const storage={getItem:key=>{if(blocked)throw Error('blocked');return values.get(key);},setItem:(key,v)=>{if(blocked)throw Error('blocked');values.set(key,v);}};
 const exports={};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true}}).outputText,{exports,require:createRequire(source),window:{localStorage:storage,SteamClient:steam},navigator:{language},Intl,setTimeout,clearTimeout});
 return {api:exports,values};
}
test('catalog coverage and placeholders match',()=>{
 const en=require('../src/locales/en.json'),es=require('../src/locales/es.json');
 assert.deepEqual(Object.keys(es).sort(),Object.keys(en).sort());
 for(const key of Object.keys(en)){
  assert.ok(es[key].trim());
  assert.deepEqual((es[key].match(/\{\w+\}/g)||[]).sort(),(en[key].match(/\{\w+\}/g)||[]).sort(),key);
 }
});
test('regional Spanish, English fallback and explicit preference',()=>{
 const {api,values}=load(null,'es-MX');
 assert.equal(api.t('Advanced settings'),'Ajustes avanzados');
 assert.equal(api.resolveLocale('auto','fr-FR'),'en');
 api.setInterfacePreference('en');assert.equal(api.t('Back'),'Back');
 assert.equal(values.get('decktation.interfaceLanguage'),'en');
 assert.equal(load('es','en-US').api.t('Back'),'Volver');
 assert.equal(api.t('Custom profile'),'Custom profile');
});
test('safe storage, interpolation and dictation names',()=>{
 const {api}=load(null,'en',true);api.setInterfacePreference('es');
 assert.equal(api.t('Button {number}',{number:2}),'Botón 2');
 assert.equal(api.languageName('auto','Auto Detect'),'Detección automática');
 assert.equal(api.languageName('en','English'),'inglés');
 assert.equal(api.languageName('not_a_code','Original label'),'Original label');
});

test('Steam language overrides renderer locale but never explicit selection',async()=>{
 const {api}=load(null,'en-US',false,{Settings:{GetCurrentLanguage:async()=> 'spanish'}});
 await api.initializeSteamLanguage();assert.equal(api.t('Back'),'Volver');
 api.setInterfacePreference('en');assert.equal(api.t('Back'),'Back');
 assert.equal(api.resolveLocale('auto','latam'),'es');
 const failure=load(null,'es-ES',false,{Settings:{GetCurrentLanguage:async()=>{throw Error('unavailable');}}});
 await failure.api.initializeSteamLanguage();assert.equal(failure.api.t('Back'),'Volver');
});
