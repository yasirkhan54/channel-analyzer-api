// Live quota-day clock for the Swagger UI info section (SERVICE_DESCRIPTION). Swagger renders the description
// after loading the spec, so this waits for it. The quota day runs midnight to midnight America/Los_Angeles.
(() => {
  const ptClock = new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const pkt = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Karachi", weekday: "short", hour: "2-digit", minute: "2-digit" });
  const pad = (n) => String(n).padStart(2, "0");

  function tick(root) {
    const now = new Date();
    const p = Object.fromEntries(ptClock.formatToParts(now).map((x) => [x.type, x.value]));
    const done = (Number(p.hour) % 24) * 3600 + Number(p.minute) * 60 + Number(p.second);
    const left = 86400 - done;
    const reset = new Date(now.getTime() + left * 1000);
    root.querySelector(".ytca-count").textContent = `${pad(Math.floor(left / 3600))}:${pad(Math.floor((left % 3600) / 60))}:${pad(left % 60)}`;
    root.querySelector(".ytca-reset-at").textContent = `until reset, ${pkt.format(reset)} PKT`;
    root.querySelector(".ytca-day").style.setProperty("--ratio", (done / 86400).toFixed(4));
    root.querySelector(".ytca-day").setAttribute("aria-valuenow", Math.round((done / 86400) * 100));
  }

  const wait = setInterval(() => {
    const root = document.querySelector(".ytca-quota");
    if (!root) return;
    clearInterval(wait);
    tick(root);
    setInterval(() => tick(root), 1000);
  }, 200);
})();
