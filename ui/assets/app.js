(() => {
  const feed = document.getElementById("feed");
  const form = document.getElementById("composer");
  const input = document.getElementById("command");
  const btnHelp = document.getElementById("btnHelp");
  const btnClear = document.getElementById("btnClear");
  const status = document.getElementById("status");

  const pad2 = (n) => (n < 10 ? `0${n}` : `${n}`);
  const timeStamp = () => {
    const d = new Date();
    return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
  };

  const addMessage = (who, text) => {
    const wrap = document.createElement("div");
    wrap.className = `msg ${who}`;

    const meta = document.createElement("div");
    meta.className = "meta";

    const left = document.createElement("div");
    left.className = "who";
    left.textContent = who === "user" ? "USER" : "BOT";

    const right = document.createElement("div");
    right.textContent = timeStamp();

    meta.appendChild(left);
    meta.appendChild(right);

    const body = document.createElement("div");
    body.className = "body";
    body.textContent = text;

    wrap.appendChild(meta);
    wrap.appendChild(body);
    feed.appendChild(wrap);
    feed.scrollTop = feed.scrollHeight;
  };

  const setStatus = (kind, text) => {
    status.classList.remove("bad", "good");
    if (kind) status.classList.add(kind);
    status.textContent = text;
  };

  const sendCommand = async (text) => {
    const trimmed = (text || "").trim();
    if (!trimmed) return;

    addMessage("user", trimmed);
    input.value = "";
    input.focus();
    setStatus(null, "Изпращане…");

    try {
      const res = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) {
        const err = (data && (data.error || data.response)) || "Server error";
        addMessage("bot", `ERROR: ${err}`);
        setStatus("bad", "Грешка при изпълнение.");
        return;
      }

      addMessage("bot", data.response || "");
      setStatus("good", "Готово.");
      if (data.exit) {
        setStatus("bad", "Ботът върна exit=true (UI остава отворен)." );
      }
    } catch (e) {
      addMessage("bot", `ERROR: ${e && e.message ? e.message : String(e)}`);
      setStatus("bad", "Няма връзка със сървъра.");
    }
  };

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendCommand(input.value);
  });

  btnHelp.addEventListener("click", () => sendCommand("помощ"));
  btnClear.addEventListener("click", () => {
    feed.innerHTML = "";
    input.focus();
  });

  document.querySelectorAll(".chip").forEach((b) => {
    b.addEventListener("click", () => {
      const cmd = b.getAttribute("data-cmd") || "";
      sendCommand(cmd);
    });
  });

  // Initial welcome
  addMessage(
    "bot",
    "Готово. Напиши 'помощ' за всички команди.\n\nПодсказка: UI изпраща текста 1:1 към чатбота (router.handle)."
  );
})();
