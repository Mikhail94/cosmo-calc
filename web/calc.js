// Логика калькулятора (без интерфейса) — та же, что в cosmo_calc.pyw.
const Calc = (() => {
  // Считает выражение вроде "2+3*4": числа, + - * / и унарный минус.
  function evaluate(src) {
    let i = 0;
    const peek = () => src[i];

    function number() {
      const m = /^(\d+\.?\d*|\.\d+)(e[+-]?\d+)?/i.exec(src.slice(i));
      if (!m) throw new Error("syntax");
      i += m[0].length;
      return parseFloat(m[0]);
    }
    function unary() {
      if (peek() === "-") { i++; return -unary(); }
      if (peek() === "+") { i++; return unary(); }
      return number();
    }
    function term() {
      let v = unary();
      while (peek() === "*" || peek() === "/") {
        const op = src[i++];
        const r = unary();
        if (op === "/" && r === 0) throw new Error("div0");
        v = op === "*" ? v * r : v / r;
      }
      return v;
    }
    function expr() {
      let v = term();
      while (peek() === "+" || peek() === "-") {
        const op = src[i++];
        const r = term();
        v = op === "+" ? v + r : v - r;
      }
      return v;
    }

    const v = expr();
    if (i !== src.length) throw new Error("syntax");
    return v;
  }

  // Аккуратная строка: 4 -> "4", 0.1+0.2 -> "0.3".
  function fmt(v) {
    if (!Number.isFinite(v)) throw new Error("overflow");
    if (Number.isInteger(v) && Math.abs(v) < 1e15) return String(v);
    return String(Number(v.toPrecision(12)));
  }

  // Внутренняя запись -> то, что видит пользователь.
  const pretty = (e) => e.replace(/\*/g, "×").replace(/\//g, "÷").replace(/-/g, "−");

  const OP_SYMBOLS = { "+": "+", "−": "-", "×": "*", "÷": "/" };

  function create() {
    const s = { expr: "", history: "", justEvaluated: false };

    const lastNumber = () => /(\d+\.?\d*|\.\d+)$/.exec(s.expr);

    function inputDigit(d) {
      if (s.justEvaluated) s.expr = "";
      if (s.expr.length >= 40) return;
      const m = lastNumber();
      if (m && m[0] === "0") s.expr = s.expr.slice(0, -1);   // не даём писать "007"
      s.expr += d;
    }

    function inputDot() {
      if (s.justEvaluated) s.expr = "";
      const m = lastNumber();
      if (m && m[0].includes(".")) return;
      s.expr += m ? "." : "0.";
    }

    function inputOperator(op) {
      if (!s.expr || s.expr === "-") {
        if (op === "-") s.expr = "-";
        return;
      }
      const last = s.expr.slice(-1);
      if ("+-*/".includes(last)) {
        if (op === "-" && "*/".includes(last)) { s.expr += op; return; }   // разрешаем 5 × −3
        s.expr = s.expr.replace(/[+\-*/]+$/, "");
      }
      s.expr += op;
    }

    function toggleSign() {
      const m = lastNumber();
      if (!m) return;
      const e = s.expr, i = m.index;
      if (i >= 1 && e[i - 1] === "-" && (i === 1 || "+-*/".includes(e[i - 2]))) {
        s.expr = e.slice(0, i - 1) + e.slice(i);                         // убираем унарный минус
      } else if (i >= 1 && "+-".includes(e[i - 1])) {
        s.expr = e.slice(0, i - 1) + (e[i - 1] === "-" ? "+" : "-") + e.slice(i);
      } else {
        s.expr = e.slice(0, i) + "-" + e.slice(i);
      }
    }

    function equals() {
      const e = s.expr.replace(/[+\-*/]+$/, "");
      if (!e || e === "-") return;
      try {
        const result = fmt(evaluate(e));
        s.history = pretty(e) + " =";
        s.expr = result;
      } catch (err) {
        s.history = err.message === "div0" ? "∞ чёрная дыра! на ноль делить нельзя"
                                           : "ошибка в выражении";
        s.expr = "";
      }
      s.justEvaluated = true;
    }

    s.press = (label) => {
      if (/^\d$/.test(label)) inputDigit(label);
      else if (label === ".") inputDot();
      else if (label in OP_SYMBOLS) inputOperator(OP_SYMBOLS[label]);
      else if (label === "=") { equals(); return; }
      else if (label === "C") s.expr = "";
      else if (label === "⌫") s.expr = s.justEvaluated ? "" : s.expr.slice(0, -1);
      else if (label === "%") {
        const m = lastNumber();
        if (m) s.expr = s.expr.slice(0, m.index) + fmt(parseFloat(m[0]) / 100);
      }
      else if (label === "±") toggleSign();
      s.justEvaluated = false;
    };

    // Подсказка с результатом прямо во время ввода.
    s.preview = () => {
      const e = s.expr.replace(/[+\-*/]+$/, "");
      if (!/\d[+\-*/]/.test(e)) return "";
      try { return "= " + fmt(evaluate(e)); } catch { return ""; }
    };

    s.bigText = () => pretty(s.expr) || "0";
    s.smallText = () => (s.justEvaluated ? s.history : s.preview());
    return s;
  }

  return { create, evaluate, fmt, pretty };
})();

if (typeof module !== "undefined") module.exports = Calc;
