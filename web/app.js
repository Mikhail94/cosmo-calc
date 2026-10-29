// Интерфейс калькулятора: кнопки, темы и анимированный фон.

const THEMES = {
  space: { label: "✦ космос", title: "✦ COSMO CALC", bar: "#05030f" },
  kitty: { label: "♥ китти",  title: "♥ KITTY CALC", bar: "#ffe4ef" },
};
const THEME_ORDER = Object.keys(THEMES);

const LAYOUT = [
  [["C", "func"], ["⌫", "func"], ["%", "func"], ["÷", "op"]],
  [["7", "num"], ["8", "num"], ["9", "num"], ["×", "op"]],
  [["4", "num"], ["5", "num"], ["6", "num"], ["−", "op"]],
  [["1", "num"], ["2", "num"], ["3", "num"], ["+", "op"]],
  [["±", "func"], ["0", "num"], [".", "num"], ["=", "eq"]],
];

const calc = Calc.create();
const $ = (id) => document.getElementById(id);
const bigEl = $("big"), smallEl = $("small");

// ---------- Настройки (тема сохраняется между запусками) ----------
const storage = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* не страшно */ } },
};

let theme = new URLSearchParams(location.search).get("theme") || storage.get("theme");
if (!(theme in THEMES)) theme = THEME_ORDER[0];

function applyTheme() {
  document.body.dataset.theme = theme;
  $("title").textContent = THEMES[theme].title;
  $("themeSwitch").textContent = THEMES[theme].label + " ▸";
  document.querySelector('meta[name="theme-color"]').content = THEMES[theme].bar;
  sky.reset();
}

$("themeSwitch").addEventListener("click", () => {
  theme = THEME_ORDER[(THEME_ORDER.indexOf(theme) + 1) % THEME_ORDER.length];
  storage.set("theme", theme);
  applyTheme();
});

// ---------- Экран ----------
function updateDisplay() {
  bigEl.textContent = calc.bigText();
  smallEl.textContent = calc.smallText();
  // Длинное число уменьшаем, чтобы оно влезло в экран
  bigEl.style.fontSize = "";
  const ratio = bigEl.clientWidth / bigEl.scrollWidth;
  if (ratio < 1) {
    const base = parseFloat(getComputedStyle(bigEl).fontSize);
    bigEl.style.fontSize = Math.max(16, Math.floor(base * ratio)) + "px";
  }
}

// ---------- Кнопки ----------
const buttons = {};
for (const row of LAYOUT) {
  for (const [label, style] of row) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `k ${style}`;
    b.textContent = label;
    b.addEventListener("pointerdown", (e) => { e.preventDefault(); press(label); });
    $("keys").appendChild(b);
    buttons[label] = b;
  }
}

function press(label) {
  const b = buttons[label];
  b.classList.add("pressed");
  setTimeout(() => b.classList.remove("pressed"), 120);
  if (navigator.vibrate) navigator.vibrate(8);       // лёгкая вибрация на телефоне
  calc.press(label);
  updateDisplay();
}

// Клавиатура (если открыть на компьютере)
document.addEventListener("keydown", (e) => {
  const map = { "+": "+", "-": "−", "*": "×", "/": "÷", ".": ".", ",": ".", "%": "%", "=": "=",
                Enter: "=", Backspace: "⌫", Escape: "C", Delete: "C" };
  const label = /^\d$/.test(e.key) ? e.key : map[e.key];
  if (label) { e.preventDefault(); press(label); }
});

// ---------- Анимированный фон ----------
const sky = (() => {
  const canvas = $("sky");
  const ctx = canvas.getContext("2d");
  let w = 0, h = 0, particles = [], effects = [], nextEffect = 0;

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    w = innerWidth; h = innerHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    reset();
  }

  function reset() {
    const rnd = (a, b) => a + Math.random() * (b - a);
    effects = [];
    nextEffect = performance.now() + 1500;
    if (theme === "space") {
      const colors = ["#ffffff", "#cfe0ff", "#ffe9c4", "#d9c8ff"];
      particles = Array.from({ length: Math.round(w * h / 1800) }, () => {
        const size = [1, 1, 1, 1.5, 2, 2.5][Math.floor(Math.random() * 6)];
        return { x: rnd(0, w), y: rnd(0, h), size, color: colors[Math.floor(Math.random() * 4)],
                 speed: 0.08 + size * 0.12, phase: rnd(0, 6.28), twinkle: rnd(1, 3.5) };
      });
    } else {
      const colors = ["#ff8fb8", "#ffb3cf", "#ff6fa3", "#ffffff", "#ffc4dc"];
      particles = Array.from({ length: Math.round(w * h / 11000) }, () => {
        const size = rnd(5, 12);
        return { x: rnd(0, w), y: rnd(0, h), size, color: colors[Math.floor(Math.random() * 5)],
                 speed: 0.25 + size * 0.05, phase: rnd(0, 6.28) };
      });
    }
  }

  function nebula(x, y, r, color) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color);
    g.addColorStop(1, "transparent");
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
  }

  function heart(x, y, s) {
    ctx.beginPath();
    for (let i = 0; i <= 24; i++) {
      const t = (Math.PI * 2 * i) / 24;
      const hx = 16 * Math.sin(t) ** 3;
      const hy = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t));
      ctx.lineTo(x + (hx * s) / 16, y + (hy * s) / 16);
    }
    ctx.fill();
  }

  function sparkle(x, y, r) {
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (Math.PI / 4) * i - Math.PI / 2;
      const rr = i % 2 ? r * 0.3 : r;
      ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
    }
    ctx.fill();
  }

  function frame(now) {
    const t = now / 1000;
    ctx.clearRect(0, 0, w, h);

    if (theme === "space") {
      ctx.globalAlpha = 0.55;
      nebula(w * 0.15, h * 0.7, w * 0.6, "#3b1466");
      nebula(w * 0.9, h * 0.5, w * 0.5, "#0f3a55");
      nebula(w * 0.5, h, w * 0.55, "#4a1640");
      for (const s of particles) {
        s.y += s.speed; s.x -= s.speed * 0.25;
        if (s.y > h || s.x < -3) { s.y = -3; s.x = Math.random() * (w + 60); }
        ctx.globalAlpha = 0.55 + 0.45 * Math.sin(s.phase + t * s.twinkle);
        ctx.fillStyle = s.color;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size / 2, 0, Math.PI * 2);
        ctx.fill();
      }
      // Кометы
      if (now > nextEffect) {
        effects.push({ x: w * (0.3 + Math.random() * 0.8), y: Math.random() * h * 0.45, age: 0 });
        nextEffect = now + 2500 + Math.random() * 4500;
      }
      ctx.globalAlpha = 1;
      for (const c of effects) {
        c.x -= 0.87 * 12; c.y += 0.5 * 12; c.age++;
        const g = ctx.createLinearGradient(c.x, c.y, c.x + 0.87 * 110, c.y - 0.5 * 110);
        g.addColorStop(0, "#ffffff");
        g.addColorStop(1, "transparent");
        ctx.strokeStyle = g;
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(c.x, c.y);
        ctx.lineTo(c.x + 0.87 * 110, c.y - 0.5 * 110);
        ctx.stroke();
      }
      effects = effects.filter((c) => c.age < 45);
    } else {
      for (const p of particles) {
        p.y -= p.speed;
        p.x += Math.sin(t * 1.5 + p.phase) * 0.4;
        if (p.y < -25) { p.y = h + 25; p.x = Math.random() * w; }
        ctx.globalAlpha = 0.9;
        ctx.fillStyle = p.color;
        heart(p.x, p.y, p.size);
      }
      // Искорки: вспыхивают и тают
      if (now > nextEffect) {
        const colors = ["#ff4f8f", "#ffb300", "#ff7aa8"];
        effects.push({ x: Math.random() * w, y: Math.random() * h, age: 0,
                       color: colors[Math.floor(Math.random() * 3)] });
        nextEffect = now + 600 + Math.random() * 1000;
      }
      for (const e of effects) {
        e.age++;
        const k = e.age / 30;                        // 0 → 1 за ~полсекунды
        ctx.globalAlpha = 1 - Math.max(0, k - 0.5) * 2;
        ctx.fillStyle = e.color;
        sparkle(e.x, e.y, 4 + 14 * Math.sin(Math.min(k, 1) * Math.PI));
      }
      effects = effects.filter((e) => e.age < 30);
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(frame);
  }

  addEventListener("resize", resize);
  return { reset, start() { resize(); requestAnimationFrame(frame); } };
})();

applyTheme();
sky.start();
updateDisplay();

// ---------- Работа без интернета ----------
if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
  navigator.serviceWorker.register("sw.js");
}
