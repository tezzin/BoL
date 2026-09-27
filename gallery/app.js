(function () {
  const $ = (id) => document.getElementById(id);
  const priceFmt = new Intl.NumberFormat(undefined, { style: "currency", currency: SITE.currency, maximumFractionDigits: 0 });
  const STATUS_LABEL = { available: "Available", reserved: "Reserved", sold: "Sold" };

  let filter = "all";
  let visible = PAINTINGS;
  let current = 0;

  // --- Site text ---
  document.title = `${SITE.artistName} — Paintings`;
  $("brand").textContent = SITE.artistName;
  $("hero-name").textContent = SITE.artistName;
  $("hero-tagline").textContent = SITE.tagline;
  $("about-text").textContent = SITE.about;
  $("footer-name").textContent = SITE.artistName;
  $("year").textContent = new Date().getFullYear();
  $("contact-link").href = mailto("Painting inquiry", "Hi,\n\n");
  if (SITE.instagram) {
    $("insta").hidden = false;
    $("insta-link").href = SITE.instagram;
  }

  function mailto(subject, body) {
    return `mailto:${SITE.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }

  function priceText(p) {
    return p.status === "sold" ? "Sold" : priceFmt.format(p.price);
  }

  // --- Grid ---
  function render() {
    visible = filter === "all" ? PAINTINGS : PAINTINGS.filter((p) => p.status === filter);
    const grid = $("grid");
    grid.innerHTML = "";
    visible.forEach((p, i) => {
      const li = document.createElement("li");
      li.className = `card is-${p.status}`;
      li.innerHTML = `
        <button type="button">
          <div class="frame"><img loading="lazy" alt=""></div>
          <div class="card-info">
            <div>
              <h3></h3>
              <p class="meta"></p>
            </div>
            <div style="text-align:right">
              <span class="badge ${p.status}">${STATUS_LABEL[p.status]}</span>
              <p class="price"></p>
            </div>
          </div>
        </button>`;
      li.querySelector("img").src = p.image;
      li.querySelector("img").alt = p.title;
      li.querySelector("h3").textContent = p.title;
      li.querySelector(".meta").textContent = `${p.medium} · ${p.size}`;
      li.querySelector(".price").textContent = p.status === "sold" ? "" : priceFmt.format(p.price);
      li.querySelector("button").addEventListener("click", () => open(i));
      grid.appendChild(li);
    });
  }

  document.querySelectorAll(".filter").forEach((btn) =>
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter").forEach((b) => b.classList.toggle("is-active", b === btn));
      filter = btn.dataset.filter;
      render();
    })
  );

  // --- Viewer ---
  const dialog = $("viewer");

  function show(i) {
    current = (i + visible.length) % visible.length;
    const p = visible[current];
    $("v-img").src = p.image;
    $("v-img").alt = p.title;
    $("v-title").textContent = p.title;
    $("v-meta").textContent = `${p.year} · ${p.medium} · ${p.size}`;
    $("v-desc").textContent = p.description || "";
    $("v-price").textContent = priceText(p);
    const status = $("v-status");
    status.className = `status badge ${p.status}`;
    status.textContent = STATUS_LABEL[p.status];

    const btn = $("v-inquire");
    if (p.status === "sold") {
      btn.textContent = "Sold — ask about similar work";
      btn.href = mailto(`Similar work to "${p.title}"`, `Hi,\n\nI saw "${p.title}" has sold. Do you have similar pieces or take commissions?\n\n`);
    } else {
      btn.textContent = p.status === "reserved" ? "Reserved — join the waitlist" : "Inquire about this painting";
      btn.href = mailto(
        `Inquiry: "${p.title}"`,
        `Hi,\n\nI'm interested in buying "${p.title}" (${p.size}, ${priceFmt.format(p.price)}).\n\nMy shipping location: \n\nThanks!`
      );
    }
    history.replaceState(null, "", `#${p.id}`);
  }

  function open(i) {
    show(i);
    if (!dialog.open) dialog.showModal();
  }

  $("v-close").addEventListener("click", () => dialog.close());
  $("v-prev").addEventListener("click", () => show(current - 1));
  $("v-next").addEventListener("click", () => show(current + 1));
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener("close", () => history.replaceState(null, "", location.pathname));
  document.addEventListener("keydown", (e) => {
    if (!dialog.open) return;
    if (e.key === "ArrowLeft") show(current - 1);
    if (e.key === "ArrowRight") show(current + 1);
  });

  render();

  // Open a painting directly from a shared link like index.html#harbor-at-dusk
  const linked = PAINTINGS.findIndex((p) => `#${p.id}` === location.hash);
  if (linked >= 0) open(linked);
})();
