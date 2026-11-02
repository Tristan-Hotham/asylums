// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8798; set PORT to change).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked
// here, so the screenshots show the offline base map (Natural Earth coast and county outlines). NOML=1 blocks MapLibre
// too, to check that the page degrades gracefully.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError|tile/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8798) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(2500);
    const tag = process.env.NOML ? "noml_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    if (!process.env.NOML) {
      await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 1880; r.dispatchEvent(new Event("input")); });
      await p.waitForTimeout(900); await shot("#atlas", "map_1880");
      await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 2005; r.dispatchEvent(new Event("input")); });
      await p.waitForTimeout(900); await shot("#atlas", "map_2005");
      await p.click("#play"); await p.waitForTimeout(1200); await p.click("#play");
      await p.click('#modeRow [data-m="all"]');
      await p.fill("#q", "Colney"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2200); await shot("#atlas", "search_colney");
      await p.click("#focusRow .btn:nth-child(3)"); await p.waitForTimeout(1500); await shot("#atlas", "london");
      await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(1500); await shot("#atlas", "epsom");
      // click a circle at the map centre (Epsom cluster) to open a popup
      const box = await p.locator("#map").boundingBox();
      const pt = await p.evaluate(() => { const q = SITE.rows.findIndex(r => r[0] === "Horton Hospital"); return null; });
      await p.click(".lyrBtn"); await p.waitForTimeout(300);
      await p.locator('.lyrPanel [data-k="relief"]').check(); await p.waitForTimeout(500); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
      await p.click("#focusRow .btn:nth-child(2)"); await p.waitForTimeout(1200);
      await p.click("#fateRow .btn:nth-child(3)"); await p.waitForTimeout(700); await shot("#atlas", "fate_homes"); await p.click("#fateRow .btn:nth-child(2)");
    }
    for (const c of ["decChart", "openChart", "bigChart", "fateChart", "nameChart", "townChart", "allTable"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1200); await shot("#atlas", "dark_map"); await shot("#decChart", "dark_dec");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
      await p.click(".mfs-btn"); await p.waitForTimeout(600);
    }
    if (!process.env.NOML) {
      // popup: click the first visible circle
      await p.locator("#map").scrollIntoViewIfNeeded(); await p.waitForTimeout(400);
      const hit = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["pts"] }); if (!f.length) return null; const c = f.find(x => P[x.properties.i].title === "Whittingham Hospital") || f[0]; const xy = map.project(c.geometry.coordinates); const r = map.getContainer().getBoundingClientRect(); return [r.left + xy.x, r.top + xy.y]; });
      if (hit) { await p.mouse.click(hit[0], hit[1]); await p.waitForTimeout(800); await shot("#atlas", "popup"); }
      else errs.push(nm + ": no circles rendered");
      const nf = await p.evaluate(() => map.queryRenderedFeatures({ layers: ["pts"] }).length); console.log(nm, "circles rendered:", nf);
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
