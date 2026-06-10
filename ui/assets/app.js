(() => {
  const feed = document.getElementById("feed");
  const form = document.getElementById("composer");
  const input = document.getElementById("command");
  const btnHelp = document.getElementById("btnHelp");
  const btnClear = document.getElementById("btnClear");
  const btnRefreshLogs = document.getElementById("btnRefreshLogs");
  const logs = document.getElementById("logs");
  const status = document.getElementById("status");
  const statusDot = document.getElementById("statusDot");
  const leaguePicker = document.getElementById("leaguePicker");
  const menuContent = document.getElementById("menuContent");
  const menuButtons = Array.from(document.querySelectorAll(".menu-btn"));

  const state = {
    activeMenu: "leagues",
    leagues: [],
    teams: [],
    selectedLeagueId: null,
    leagueTeams: [],
    matches: [],
  };

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
    if (statusDot) {
      statusDot.classList.remove("bad", "good", "busy");
      if (kind === "bad") statusDot.classList.add("bad");
      if (kind === "good") statusDot.classList.add("good");
      if (!kind) statusDot.classList.add("busy");
    }
    status.textContent = text;
  };

  const renderLogs = (items) => {
    if (!logs) return;
    logs.innerHTML = "";
    if (!items || !items.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "Няма налични логове.";
      logs.appendChild(empty);
      return;
    }

    items.forEach((line) => {
      const row = document.createElement("div");
      row.textContent = line;
      logs.appendChild(row);
    });
    logs.scrollTop = logs.scrollHeight;
  };

  const refreshLogs = async () => {
    if (!logs) return;
    try {
      const res = await fetch("/api/logs");
      const data = await res.json();
      if (!res.ok || !data.ok) {
        renderLogs([`ERROR: ${(data && data.error) || "Неуспешно зареждане на логове."}`]);
        return;
      }
      renderLogs(data.logs || []);
    } catch (e) {
      renderLogs([`ERROR: ${e && e.message ? e.message : String(e)}`]);
    }
  };

  const safeText = (value) => {
    if (value === null || value === undefined) return "";
    return String(value);
  };

  const clearElement = (node) => {
    while (node && node.firstChild) {
      node.removeChild(node.firstChild);
    }
  };

  const createRow = (left, right) => {
    const row = document.createElement("div");
    row.className = "menu-row";

    const leftEl = document.createElement("div");
    leftEl.className = "menu-main";
    leftEl.textContent = safeText(left);

    const rightEl = document.createElement("div");
    rightEl.className = "menu-meta";
    rightEl.textContent = safeText(right);

    row.appendChild(leftEl);
    row.appendChild(rightEl);
    return row;
  };

  const createEmpty = (text) => {
    const empty = document.createElement("div");
    empty.className = "menu-empty";
    empty.textContent = text;
    return empty;
  };

  const loadLeagues = async () => {
    const res = await fetch("/api/leagues");
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error((data && data.error) || "Неуспешно зареждане на лиги.");
    }
    state.leagues = Array.isArray(data.leagues) ? data.leagues : [];
    if (state.leagues.length && !state.selectedLeagueId) {
      state.selectedLeagueId = Number(state.leagues[0].id);
    }
    if (
      state.leagues.length &&
      state.selectedLeagueId &&
      !state.leagues.some((l) => Number(l.id) === Number(state.selectedLeagueId))
    ) {
      state.selectedLeagueId = Number(state.leagues[0].id);
    }
    if (!state.leagues.length) {
      state.selectedLeagueId = null;
    }
  };

  const loadTeams = async () => {
    const res = await fetch("/api/teams");
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error((data && data.error) || "Неуспешно зареждане на отбори.");
    }
    state.teams = Array.isArray(data.teams) ? data.teams : [];
  };

  const loadLeagueTeams = async () => {
    if (!state.selectedLeagueId) {
      state.leagueTeams = [];
      return;
    }
    const res = await fetch(`/api/league-teams?league_id=${encodeURIComponent(state.selectedLeagueId)}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error((data && data.error) || "Неуспешно зареждане на отборите в лигата.");
    }
    state.leagueTeams = Array.isArray(data.teams) ? data.teams : [];
  };

  const loadMatches = async () => {
    if (!state.selectedLeagueId) {
      state.matches = [];
      return;
    }
    const res = await fetch(`/api/matches?league_id=${encodeURIComponent(state.selectedLeagueId)}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error((data && data.error) || "Неуспешно зареждане на мачове.");
    }
    state.matches = Array.isArray(data.matches) ? data.matches : [];
  };

  const renderLeaguePicker = () => {
    if (!leaguePicker) return;
    clearElement(leaguePicker);
    if (!state.leagues.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Няма налични лиги";
      leaguePicker.appendChild(opt);
      leaguePicker.disabled = true;
      return;
    }

    leaguePicker.disabled = false;
    state.leagues.forEach((league) => {
      const opt = document.createElement("option");
      opt.value = String(league.id);
      opt.textContent = `${league.name} ${league.season}`;
      if (Number(league.id) === Number(state.selectedLeagueId)) {
        opt.selected = true;
      }
      leaguePicker.appendChild(opt);
    });
  };

  const renderLeaguesMenu = () => {
    clearElement(menuContent);
    if (!state.leagues.length) {
      menuContent.appendChild(createEmpty("Няма създадени лиги."));
      return;
    }
    state.leagues.forEach((league) => {
      const subtitle = `${league.season} • Отбори: ${league.teams_count || 0} • Мачове: ${league.matches_count || 0}`;
      menuContent.appendChild(createRow(league.name, subtitle));
    });
  };

  const renderTeamsMenu = () => {
    clearElement(menuContent);
    if (!state.selectedLeagueId) {
      menuContent.appendChild(createEmpty("Избери лига, за да видиш отборите."));
      return;
    }
    if (!state.leagueTeams.length) {
      menuContent.appendChild(createEmpty("Няма добавени отбори в избраната лига."));
      return;
    }

    const playersById = new Map(state.teams.map((team) => [Number(team.id), Number(team.players_count || 0)]));
    state.leagueTeams.forEach((team) => {
      const playersCount = playersById.get(Number(team.id)) || 0;
      menuContent.appendChild(createRow(team.name, `Играчи: ${playersCount}`));
    });
  };

  const renderMatchesMenu = () => {
    clearElement(menuContent);
    if (!state.selectedLeagueId) {
      menuContent.appendChild(createEmpty("Избери лига, за да видиш мачовете."));
      return;
    }
    if (!state.matches.length) {
      menuContent.appendChild(createEmpty("Няма генерирана програма за тази лига."));
      return;
    }

    state.matches.forEach((match) => {
      const score = match.home_goals === null || match.away_goals === null
        ? ""
        : ` (${match.home_goals}:${match.away_goals})`;
      const main = `Кръг ${match.round_no}: ${match.home_name} vs ${match.away_name}${score}`;
      const meta = `Мач #${match.id} • ${match.status || "scheduled"}`;
      menuContent.appendChild(createRow(main, meta));
    });
  };

  const renderMenu = () => {
    if (!menuContent) return;
    if (state.activeMenu === "teams") {
      renderTeamsMenu();
      return;
    }
    if (state.activeMenu === "matches") {
      renderMatchesMenu();
      return;
    }
    renderLeaguesMenu();
  };

  const syncMenuButtons = () => {
    menuButtons.forEach((btn) => {
      const menu = btn.getAttribute("data-menu") || "";
      const active = menu === state.activeMenu;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
  };

  const loadBrowserData = async () => {
    try {
      await loadLeagues();
      await loadTeams();
      await loadLeagueTeams();
      await loadMatches();
      renderLeaguePicker();
      syncMenuButtons();
      renderMenu();
    } catch (e) {
      if (menuContent) {
        clearElement(menuContent);
        menuContent.appendChild(createEmpty(`Грешка: ${e && e.message ? e.message : String(e)}`));
      }
    }
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
      await refreshLogs();
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

  if (btnRefreshLogs) {
    btnRefreshLogs.addEventListener("click", () => {
      refreshLogs();
    });
  }

  document.querySelectorAll(".chip").forEach((b) => {
    b.addEventListener("click", () => {
      const cmd = b.getAttribute("data-cmd") || "";
      sendCommand(cmd);
    });
  });

  if (leaguePicker) {
    leaguePicker.addEventListener("change", async () => {
      const next = Number(leaguePicker.value || 0);
      state.selectedLeagueId = Number.isFinite(next) && next > 0 ? next : null;
      await loadLeagueTeams();
      await loadMatches();
      renderMenu();
    });
  }

  menuButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const menu = btn.getAttribute("data-menu") || "leagues";
      state.activeMenu = menu;
      syncMenuButtons();
      renderMenu();
    });
  });

  // Initial welcome
  addMessage(
    "bot",
    "Готово. Напиши 'помощ' за всички команди.\n\nПодсказка: UI изпраща текста 1:1 към чатбота (router.handle)."
  );
  refreshLogs();
  loadBrowserData();
})();
