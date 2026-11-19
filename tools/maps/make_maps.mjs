// 產生簡報用的地圖 SVG 路徑（tools/maps/maps.json）
// 資料：world-atlas（Natural Earth，公眾領域）、taiwan-atlas（內政部開放資料）
// 用法：在含 node_modules 的資料夾執行 node make_maps.mjs <輸出路徑>
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire(process.cwd() + '/');
const d3 = require('d3-geo');
const topo = require('topojson-client');
const out = process.argv[2];
const r = n => Math.round(n * 10) / 10;
const rnd = d => d && d.replace(/-?\d+\.\d+/g, m => String(r(+m)));

// ---------- 世界（歐亞非，涵蓋陸路與繞過非洲的海路） ----------
const W = 700, H = 440;
const world = require('world-atlas/countries-110m.json');
const countries = topo.feature(world, world.objects.countries).features;
const frame = { type: 'MultiPoint', coordinates: [[-14, 68], [148, 68], [-14, -36], [148, -36]] };
const pw = d3.geoNaturalEarth1().fitExtent([[6, 6], [W - 6, H - 6]], frame);
const pathW = d3.geoPath(pw);
const P = (lon, lat) => pw([lon, lat]).map(r);
const wpts = {
  中國: P(104, 33), 日本: P(138.5, 36.5), 韓國: P(127.8, 36.8), 葡萄牙: P(-8.3, 39.6),
  俄羅斯: P(48, 57), 土耳其: P(34.5, 39), 伊朗: P(54, 32.5), 印度: P(78.5, 22.5),
  荷蘭: P(5.3, 52.2), 英國: P(-1.8, 53), 法國: P(2.4, 46.6), 西班牙: P(-3.7, 40.2), 德國: P(10.4, 51.1),
};
const line = coords => rnd(pathW({ type: 'LineString', coordinates: coords }));
const routes = {
  land: line([[112, 34], [103, 36.5], [94, 40], [80, 41], [68, 39], [58, 36.5], [51, 35.5], [42, 38], [35, 39.5]]),
  sea: line([[118.5, 24.2], [114, 14], [106, 4], [96, 2], [80, 4], [62, -6], [46, -24], [26, -36], [13, -30],
             [7, -10], [-4, 4], [-17, 15], [-16, 28], [-12, 40], [-6, 47], [2.5, 51.4]]),
};
const worldOut = {
  viewBox: [W, H],
  countries: countries.map(f => ({ name: f.properties.name, d: rnd(pathW(f)) })).filter(c => c.d),
  points: wpts, routes,
};

// ---------- 台灣本島 ----------
const TW = 340, TH = 470;
const tw = require('taiwan-atlas/counties-10t.json');
const counties = topo.feature(tw, tw.objects.counties).features
  .filter(f => !['金門縣', '連江縣'].includes(f.properties.COUNTYNAME));
const mainland = { type: 'FeatureCollection', features: counties.filter(f => f.properties.COUNTYNAME !== '澎湖縣') };
const pt = d3.geoMercator().fitExtent([[10, 10], [TW - 10, TH - 10]], mainland);
const pathT = d3.geoPath(pt);
const T = (lon, lat) => pt([lon, lat]).map(r);
const tpts = {
  坪林: T(121.711, 24.936), 三峽: T(121.369, 24.934), 木柵: T(121.571, 24.989), 北埔: T(121.054, 24.700),
  梨山: T(121.250, 24.255), 鹿谷: T(120.752, 23.745), 名間: T(120.683, 23.850), 魚池: T(120.935, 23.880),
  阿里山: T(120.802, 23.508), 瑞穗: T(121.376, 23.497), 鹿野: T(121.135, 22.913),
};
const twOut = {
  viewBox: [TW, TH],
  counties: counties.filter(f => f.properties.COUNTYNAME !== '澎湖縣')
    .map(f => ({ name: f.properties.COUNTYNAME, d: rnd(pathT(f)) })),
  points: tpts,
};
fs.writeFileSync(out, JSON.stringify({ world: worldOut, taiwan: twOut }));
console.log('world', worldOut.countries.length, 'countries; taiwan', twOut.counties.length, 'counties →', out);
