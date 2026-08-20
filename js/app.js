(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  function el(n, a) { const e = document.createElementNS(NS, n); for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); return e; }
  const gray = v => { const c = Math.round(v * 255); return 'rgb(' + c + ',' + c + ',' + c + ')'; };

  /* ===== STEP 1：本文の図1（4×4・8階調） ===== */
  const G = [[6, 5, 4, 3], [5, 4, 3, 2], [4, 3, 2, 1], [3, 2, 1, 0]];
  let stage = 0, sel = null;                     // 0:元画像 1:標本化 2:量子化 3:符号化
  function pxTable(kind) {
    let h = '<table class="px">';
    for (let y = 0; y < 4; y++) {
      h += '<tr>';
      for (let x = 0; x < 4; x++) {
        const v = G[y][x], bg = gray(v / 7);
        const fg = v / 7 > 0.55 ? '#15181c' : '#fff';
        const s = (sel && sel[0] === x && sel[1] === y) ? ' sel' : '';
        if (kind === 'raw') h += '<td class="' + s.trim() + '" style="background:' + bg + ';border-color:' + bg + '" data-x="' + x + '" data-y="' + y + '"></td>';
        else if (kind === 'samp') h += '<td class="' + s.trim() + '" style="background:' + bg + '" data-x="' + x + '" data-y="' + y + '"></td>';
        else if (kind === 'quant') h += '<td class="' + s.trim() + '" style="background:' + bg + ';color:' + fg + '" data-x="' + x + '" data-y="' + y + '">' + v + '</td>';
        else h += '<td class="' + s.trim() + '" style="font-size:.6rem" data-x="' + x + '" data-y="' + y + '">' + v.toString(2).padStart(3, '0') + '</td>';
      }
      h += '</tr>';
    }
    return h + '</table>';
  }
  const STAGES = [
    { t: 'もとの画像', k: 'raw', d: 'アナログの濃淡' },
    { t: '手順1', k: 'samp', d: '格子状の区画（画素）に分ける' },
    { t: '手順2', k: 'quant', d: '濃淡を整数値に置きかえる' },
    { t: '手順3', k: 'code', d: '整数値を2進法にする' }
  ];
  function drawPipe() {
    $('pipeBox').innerHTML = STAGES.map((s, i) =>
      '<div class="cell' + (i > stage ? ' dim' : '') + '"><h4>' + s.t + '</h4>' +
      (i > stage ? '<div style="height:140px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:.8rem">？</div>'
                 : pxTable(s.k)) +
      '<p class="small" style="margin:8px 0 0;color:var(--muted)">' + s.d + '</p></div>').join('');
    $('pipeBox').querySelectorAll('td[data-x]').forEach(td => td.addEventListener('click', () => {
      sel = [+td.dataset.x, +td.dataset.y]; drawPipe(); showCell();
    }));
    const n = $('pipeNote');
    const msg = [
      ['info', 'まだデジタル化していない、濃淡が連続した画像です。ここから3つの手順で0と1に直します。'],
      ['ok', '<strong>手順1＝標本化</strong>。画像を等間隔の格子状の区画に分割し、区画ごとに代表の色を取り出します。この1つ1つの区画を<strong>画素（ピクセル）</strong>といいます。'],
      ['ok', '<strong>手順2＝量子化</strong>。区画の濃淡を、決められた段階のいちばん近い整数値に置きかえます。ここでは8階調なので 0〜7 の値になります。<br>本文の【ア】は「区画の濃淡を一定の規則に従って整数値に置き換えており」、【イ】は「<strong>量子</strong>化」です。'],
      ['ok', '<strong>手順3＝符号化</strong>。整数値を2進法に直します。8階調＝2<sup>3</sup> なので1画素3ビット。16画素なので 16×3＝<strong>48ビット＝6バイト</strong>です。']
    ][stage];
    n.className = 'note ' + msg[0]; n.innerHTML = msg[1];
    $('stepPrev').disabled = stage === 0; $('stepNext').disabled = stage === 3;
  }
  function showCell() {
    if (!sel) return;
    const v = G[sel[1]][sel[0]];
    $('cellNote').className = 'note ok';
    $('cellNote').innerHTML = '左から' + (sel[0] + 1) + '番目、上から' + (sel[1] + 1) + '番目の画素：' +
      '濃さは8階調のうち <strong>' + v + '</strong>（0が黒、7が白）。2進法では <strong class="mono">' + v.toString(2).padStart(3, '0') + '</strong>。';
  }

  /* ===== STEP 2 ===== */
  const PICS = {
    grad: (x, y) => 0.15 + 0.7 * ((x + y) / 2),
    face: (x, y) => {
      const d = Math.hypot(x - 0.5, y - 0.52);
      if (d > 0.42) return 0.95;
      if (Math.hypot(x - 0.36, y - 0.42) < 0.06 || Math.hypot(x - 0.64, y - 0.42) < 0.06) return 0.1;
      if (y > 0.62 && y < 0.70 && x > 0.32 && x < 0.68) return 0.25;
      return 0.62;
    },
    text: (x, y) => 0.5 + 0.45 * Math.sin(x * 26) * Math.cos(y * 22)
  };
  function svgGrid(n, fn, levels) {
    const S = 240, c = S / n;
    const svg = el('svg', { viewBox: '0 0 ' + S + ' ' + S, role: 'img', 'shape-rendering': 'crispEdges' });
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      let v = fn((x + 0.5) / n, (y + 0.5) / n);
      v = Math.max(0, Math.min(1, v));
      if (levels) v = Math.round(v * (levels - 1)) / (levels - 1);
      svg.appendChild(el('rect', { x: x * c, y: y * c, width: c + 0.5, height: c + 0.5, fill: gray(v) }));
    }
    return svg;
  }
  let lastPic = null;
  function drawImg() {
    const n = +$('res').value, bits = +$('lv').value, levels = Math.pow(2, bits);
    const key = $('picSel').value, fn = PICS[key];
    $('resV').textContent = n; $('resV2').textContent = n;
    $('lvV').textContent = levels; $('lvBit').textContent = bits;
    if (lastPic !== key) { lastPic = key; $('imgOrig').innerHTML = ''; $('imgOrig').appendChild(svgGrid(80, fn, 0)); }
    $('imgDig').innerHTML = ''; $('imgDig').appendChild(svgGrid(n, fn, levels));
    const px = n * n, bitsTotal = px * bits;
    $('mPx').textContent = px.toLocaleString() + ' 画素';
    $('mBpp').textContent = bits + ' ビット';
    $('mSize').textContent = bitsTotal.toLocaleString() + ' ビット（' + (Math.round(bitsTotal / 8 * 10) / 10).toLocaleString() + ' B）';
    const nt = $('imgNote');
    const good = n >= 24 && levels >= 16;
    nt.className = 'note ' + (good ? 'ok' : 'warn');
    nt.innerHTML = good
      ? '画素が細かく階調も多いので、もとの画像にかなり近づいています。そのぶんデータ量は ' + bitsTotal.toLocaleString() + 'ビットに増えました。'
      : (n < 12 ? '画素が粗いので、四角いブロックがはっきり見えます（<strong>ジャギー</strong>）。' : '') +
        (levels <= 4 ? '階調が少ないので、なめらかな濃淡が段々に見えます。' : '') +
        '解像度を上げるとデータ量は<strong>2乗で</strong>増え、階調のビット数を1増やすと<strong>比例して</strong>増えます。';
  }

  /* ===== STEP 3 ===== */
  function drawCalc() {
    const w = +$('pw').value || 0, h = +$('ph').value || 0, b = +$('pb').value || 0;
    const bits = w * h * b, bytes = bits / 8;
    $('pEq').innerHTML = w.toLocaleString() + ' × ' + h.toLocaleString() + ' × ' + b + '（ビット）<br>＝ ' + bits.toLocaleString() + '（ビット）';
    let size;
    if (bytes >= 1e6) size = (Math.round(bytes / 1e6 * 100) / 100) + ' MB';
    else if (bytes >= 1e3) size = (Math.round(bytes / 1e3 * 10) / 10) + ' kB';
    else size = bytes + ' B';
    $('pSize').textContent = size;
    $('pLv').textContent = b <= 30 ? Math.pow(2, b).toLocaleString() + ' 階調' : '2^' + b;
    const n = $('pNote');
    n.className = 'note info';
    n.innerHTML = (w === 4 && h === 4 && b === 3)
      ? '本文の図1の条件です。16画素 × 3ビット ＝ <strong>48ビット ＝ 6バイト</strong>。'
      : (b === 24
        ? 'フルカラーはR・G・Bにそれぞれ8ビット割り当てて 8×3＝24ビット。約1678万色を表せます。'
        : '1画素 ' + b + ' ビットなので ' + Math.pow(2, b).toLocaleString() + ' 階調。圧縮しない場合の大きさです。');
  }

  /* ===== STEP 4 ===== */
  const BLANKS = [
    { k: 'ア', q: '手順2では', ch: ['区画の濃淡を一定の規則に従って整数値に置き換えており', '画像を等間隔の格子状の区画に分割しており', '整数値を2進法で表現しており', 'しきい値を基準に白と黒の2階調に変換しており'],
      a: '区画の濃淡を一定の規則に従って整数値に置き換えており',
      why: '手順1で格子に分け（標本化）、手順2で濃淡を整数値に直し（量子化）、手順3で2進法にします（符号化）。' },
    { k: 'イ', q: 'このことを【　】化という。', ch: ['符号', '量子', '標本', '二値'], a: '量子',
      why: '値を決められた段階に割り当てる操作が量子化です。格子に分けるのが標本化、2進法に直すのが符号化。' },
    { k: 'ウ', q: '画素の大きさが【A】、階調の値が【B】ほど、元のアナログ画像に近い形でデジタル化できる。',
      ch: ['A：細かく　B：大きい', 'A：細かく　B：小さい', 'A：粗く　B：大きい', 'A：粗く　B：小さい'], a: 'A：細かく　B：大きい',
      why: '画素が細かい（解像度が高い）ほど形を、階調が大きいほど濃淡を細かく表せます。ただしデータ量は増えます。STEP 2 で確かめられます。' }
  ];
  let bAns = {};
  function drawBlanks() {
    $('blankBox').innerHTML = BLANKS.map((b, i) =>
      '<div' + (i ? ' style="margin-top:18px;padding-top:16px;border-top:1px solid var(--line)"' : '') + '>' +
      '<p class="qhead" style="margin:0 0 8px">【' + b.k + '】　' + b.q + '</p>' +
      '<div class="choice4 v" data-i="' + i + '">' + b.ch.map((c, j) =>
        '<button class="btn" data-i="' + i + '" data-c="' + c + '" style="text-align:left">' + '⓪①②③'[j] + '　' + c + '</button>').join('') +
      '</div><div class="note" id="bfb' + i + '" hidden></div></div>').join('');
    $('blankBox').querySelectorAll('button[data-c]').forEach(btn => btn.addEventListener('click', () => {
      const i = +btn.dataset.i, b = BLANKS[i], ok = btn.dataset.c === b.a;
      const row = $('blankBox').querySelector('.choice4[data-i="' + i + '"]');
      row.classList.add('locked');
      [...row.children].forEach(x => { if (x.dataset.c === b.a) x.classList.add('correct'); else if (x === btn) x.classList.add('wrong'); });
      const fb = $('bfb' + i);
      fb.hidden = false; fb.className = 'note ' + (ok ? 'ok' : 'ng');
      fb.innerHTML = (ok ? '正解。' : '正解は <strong>' + b.a + '</strong>。') + b.why;
      bAns[i] = ok;
      const done = Object.keys(bAns).length, right = Object.values(bAns).filter(Boolean).length;
      const n = $('blankNote');
      n.className = 'note ' + (done === BLANKS.length ? (right === done ? 'ok' : 'warn') : 'info');
      n.innerHTML = done + ' / ' + BLANKS.length + ' 問解答（正解 ' + right + ' 問）' +
        (done === BLANKS.length ? '<br>本文の答えは【ア】⓪　【イ】①　【ウ】⓪ です。' : '');
    }));
    $('blankNote').className = 'note info';
    $('blankNote').textContent = '0 / ' + BLANKS.length + ' 問解答';
  }

  function init() {
    $('stepNext').addEventListener('click', () => { if (stage < 3) { stage++; drawPipe(); } });
    $('stepPrev').addEventListener('click', () => { if (stage > 0) { stage--; drawPipe(); } });
    $('stepAll').addEventListener('click', () => { stage = 3; drawPipe(); });
    ['res', 'lv'].forEach(i => $(i).addEventListener('input', drawImg));
    $('picSel').addEventListener('change', drawImg);
    ['pw', 'ph', 'pb'].forEach(i => $(i).addEventListener('input', drawCalc));
    document.querySelectorAll('button[data-pre]').forEach(b => b.addEventListener('click', () => {
      const v = b.dataset.pre.split(',');
      $('pw').value = v[0]; $('ph').value = v[1]; $('pb').value = v[2]; drawCalc();
    }));
    window.Terms.glossary($('glossBox'), ['標本化', '量子化', '符号化', '画素', '解像度', '階調', 'ラスタ形式', 'ジャギー', 'デジタル', 'ビット']);
    drawPipe(); drawImg(); drawCalc(); drawBlanks();
    window.Terms.attach();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
