"""Debug _sce_r_skjhfnck signature and return value."""
import json, base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")

js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
ctx = MiniRacer()

setup_js = r"""
var window = this; var self = this; var global = this;
var navigator = { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN', canPlayType: function(){return '';} };
var document = {
    createElement: function() { return { setAttribute: function(){}, appendChild: function(){}, style: {}, getContext: function(){ return null; }, addEventListener: function(){} }; },
    getElementsByTagName: function() { return [{ appendChild: function(){}, addEventListener: function(){} }]; },
    getElementById: function() { return null; },
    body: { appendChild: function(){}, addEventListener: function(){} },
    head: { appendChild: function(){} },
    addEventListener: function(){}, removeEventListener: function(){},
    cookie: '', referrer: '', title: '', URL: 'https://www.youku.com/', domain: 'youku.com'
};
var location = { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '' };
var localStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
var sessionStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
var performance = { now: function(){ return Date.now(); }, timing: { navigationStart: 0 } };
var console = { log: function(){}, error: function(){}, warn: function(){}, debug: function(){}, info: function(){} };
var escape = function(str) {
    var r=''; for(var i=0;i<str.length;i++){var c=str.charCodeAt(i);
    if(c>127){r+='%'+c.toString(16).toUpperCase().padStart(2,'0');}
    else if(c<32||c==37||c==43||c==61||c==91||c==93||c==123||c==125||c==124||c==92||c==94||c==126||c==96||c==39||c==34){r+='%'+c.toString(16).toUpperCase().padStart(2,'0');}
    else{r+=str.charAt(i);}} return r;
};
var decodeURIComponent = function(str) {
    var bytes=[]; var i=0;
    while(i<str.length){if(str[i]=='%'&&i+2<str.length){bytes.push(parseInt(str.substr(i+1,2),16));i+=3;}
    else{bytes.push(str.charCodeAt(i));i++;}}
    var result=''; var j=0;
    while(j<bytes.length){var b=bytes[j];
    if(b<128){result+=String.fromCharCode(b);j++;}
    else if(b>=192&&b<224&&j+1<bytes.length){result+=String.fromCharCode(((b&31)<<6)|(bytes[j+1]&63));j+=2;}
    else if(b>=224&&b<240&&j+2<bytes.length){result+=String.fromCharCode(((b&15)<<12)|((bytes[j+1]&63)<<6)|(bytes[j+2]&63));j+=3;}
    else if(b>=240&&j+3<bytes.length){var cp=((b&7)<<18)|((bytes[j+1]&63)<<12)|((bytes[j+2]&63)<<6)|(bytes[j+3]&63);cp-=0x10000;result+=String.fromCharCode(0xD800+(cp>>10))+String.fromCharCode(0xDC00+(cp&0x3FF));j+=4;}
    else{result+=String.fromCharCode(b);j++;}} return result;
};
var encodeURIComponent = function(str) { return str; };
var atob = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    var str=s.replace(/=+$/,''); var result='';
    for(var i=0;i<str.length;i+=4){
    var n=(chars.indexOf(str[i])<<18)|(chars.indexOf(str[i+1])<<12)|(i+2<str.length?chars.indexOf(str[i+2])<<6:0)|(i+3<str.length?chars.indexOf(str[i+3]):0);
    result+=String.fromCharCode((n>>16)&255);
    if(i+2<str.length&&str[i+2]!='=')result+=String.fromCharCode((n>>8)&255);
    if(i+3<str.length&&str[i+3]!='=')result+=String.fromCharCode(n&255);} return result;
};
var btoa = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'; var result='';
    for(var i=0;i<s.length;i+=3){
    var n=(s.charCodeAt(i)<<16)|(i+1<s.length?s.charCodeAt(i+1)<<8:0)|(i+2<s.length?s.charCodeAt(i+2):0);
    result+=chars[(n>>18)&63]; result+=chars[(n>>12)&63];
    result+=i+1<s.length?chars[(n>>6)&63]:'='; result+=i+2<s.length?chars[n&63]:'=';} return result;
};
"""

ctx.eval(setup_js)
patched_js = js_code.replace(
    'decodeURIComponent(escape(f.stringify(r)))',
    'f.stringify(r)'
)
ctx.eval(patched_js)
print("JS loaded")

# Inspect _sce_r_skjhfnck
code = """
(function() {
    var info = {};
    info.exists = typeof _sce_r_skjhfnck === 'function';
    if (info.exists) {
        info.source = _sce_r_skjhfnck.toString().substring(0, 2000);
        info.length = _sce_r_skjhfnck.length; // number of params
    }

    // Try calling with no args
    try {
        var r0 = _sce_r_skjhfnck();
        info.noArgs = { type: typeof r0, value: r0 ? String(r0).substring(0, 100) : 'null/undefined' };
    } catch(e) { info.noArgs = { error: e.message }; }

    // Try calling with R1Random
    try {
        var r1 = _sce_r_skjhfnck('%s');
        info.withR1 = { type: typeof r1, value: r1 ? String(r1).substring(0, 100) : 'null/undefined' };
        if (r1 && typeof r1 === 'string') info.withR1.hex = Array.from(r1).map(function(c){return c.charCodeAt(0).toString(16).padStart(2,'0');}).join('');
        if (r1 && r1.length !== undefined && typeof r1 !== 'string') info.withR1.length = r1.length;
    } catch(e) { info.withR1 = { error: e.message }; }

    // Try calling with R1Random decoded as string
    try {
        var decoded = atob('%s');
        var r2 = _sce_r_skjhfnck(decoded);
        info.withDecoded = { type: typeof r2, value: r2 ? String(r2).substring(0, 100) : 'null/undefined' };
    } catch(e) { info.withDecoded = { error: e.message }; }

    return JSON.stringify(info);
})();
""" % (R1_RANDOM, R1_RANDOM)

result = ctx.eval(code)
info = json.loads(result)
print(json.dumps(info, indent=2))
