const { chromium } = require('playwright');
(async()=>{
 const [from,to]=process.argv.slice(2).map(Number);
 const b = await chromium.launch(); const p = await b.newPage({viewport:{width:540,height:960},deviceScaleFactor:2});
 await p.goto('file://'+__dirname+'/promo.html'); await p.waitForTimeout(400);
 for (let i=from;i<to;i++){ await p.evaluate(t=>seek(t), i/30); await p.screenshot({path:`fr/${String(i).padStart(5,'0')}.jpg`,type:'jpeg',quality:93}); }
 await b.close();
})();
