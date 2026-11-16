/* ============================================================
   AtlasIQ — main.js
   Smooth scrolling (Lenis) + scroll animations (GSAP ScrollTrigger)
   ============================================================ */

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ------------------------------------------------------------
   PROGRESS TRACKER — edit this list to update the public status.
   status: "complete" | "current" | "next" | "planned"
   Exactly one milestone should be "current" (it gets the big
   highlight + progress bar). progress: 0–100 (current only).
   ------------------------------------------------------------ */
const STATUS_DATE = "July 2026";

const MILESTONES = [
  {
    title: "Strategy & market research",
    date: "Jul 2026",
    status: "complete",
    detail:
      "Full business & AI agent strategy plan drafted — market sizing, the product wedge we're building first, and the build order for v1 and v1.5.",
  },
  {
    title: "Landing page live",
    date: "Jul 2026",
    status: "complete",
    detail:
      "You're looking at it. Every pilot conversation now has a credible destination to point to.",
  },
  {
    title: "MVP — order-entry agent",
    date: "In build now",
    status: "current",
    progress: 40,
    progressLabel: "Extraction engine · load records · pilot dashboard",
    detail:
      "The core wedge is being built right now: an agent that reads shipment emails, PDFs and spreadsheets and builds the load record automatically — feeding a live pilot dashboard and SMS alerts. Customer discovery with Australian brokers, growers and fleets runs in parallel.",
  },
  {
    title: "Free pilots with real Australian customers",
    date: "Up next",
    status: "next",
    detail:
      "1–3 live pilots — brokers, growers, small fleets — running AtlasIQ on their own documents, with case-study numbers captured as we go.",
  },
  {
    title: "v1.5 — compliance document drafting",
    date: "Planned",
    status: "planned",
    detail:
      "Our moat, built on the same engine: auto-drafted certificates of origin, biosecurity declarations, HS classifications and bills of lading — with mismatches flagged before submission.",
  },
];

/* ------------------------------------------------------------
   LIVE WAITLIST COUNT — fetched from the Google Apps Script
   endpoint (doGet returns {"count": N}). Cached in localStorage
   and refreshed at most once a day, plus on every page load.
   ------------------------------------------------------------ */
const WAITLIST_ENDPOINT =
  "https://script.google.com/macros/s/AKfycbywPnTvachGE1UISZHB5uMHncTxuanwQwVoOKds9nPwplyHahzkoSajNhFD2L_mHOxdQQ/exec";
const WL_CACHE_KEY = "atlasiq_wl_count";
const WL_DAY_MS = 24 * 60 * 60 * 1000;

function renderWaitlistCount(count) {
  document.querySelectorAll("[data-wl-count]").forEach((el) => {
    el.textContent = count;
  });
  document.querySelectorAll("[data-wl-wrap]").forEach((w) => w.classList.remove("wl--nocount"));
}

async function updateWaitlistCount() {
  if (!document.querySelector("[data-wl-count]")) return;

  let cached = null;
  try { cached = JSON.parse(localStorage.getItem(WL_CACHE_KEY)); } catch (_) { /* ignore */ }
  if (cached && typeof cached.count === "number") renderWaitlistCount(cached.count);

  const isFresh = cached && Date.now() - cached.ts < WL_DAY_MS;
  try {
    const res = await fetch(WAITLIST_ENDPOINT, { method: "GET" });
    const data = await res.json();
    if (typeof data.count === "number") {
      renderWaitlistCount(data.count);
      localStorage.setItem(WL_CACHE_KEY, JSON.stringify({ count: data.count, ts: Date.now() }));
    }
  } catch (_) {
    // network/endpoint unavailable: keep cached count, or the
    // "waitlist now open" fallback text if we never had one.
    if (isFresh && cached) renderWaitlistCount(cached.count);
  }
}
updateWaitlistCount();
setInterval(updateWaitlistCount, 6 * 60 * 60 * 1000); // re-check while the tab stays open

function renderTimeline() {
  const wrap = document.getElementById("timeline");
  if (!wrap) return;

  const badgeText = {
    complete: "Complete",
    current: "In build",
    next: "Up next",
    planned: "Planned",
  };

  const html = MILESTONES.map((m) => {
    const bar =
      m.status === "current"
        ? `<div class="mvpbar">
             <div class="mvpbar__track"><div class="mvpbar__fill" data-progress="${m.progress || 0}"></div></div>
             <div class="mvpbar__label"><span>${m.progressLabel || ""}</span><span>${m.progress || 0}%</span></div>
           </div>`
        : "";
    return `<div class="milestone milestone--${m.status}">
        <span class="milestone__dot"></span>
        <div class="milestone__head">
          <h3>${m.title}</h3>
          <span class="milestone__badge">${badgeText[m.status]}</span>
          <span class="milestone__date">${m.date}</span>
        </div>
        <p>${m.detail}</p>
        ${bar}
      </div>`;
  }).join("");

  wrap.innerHTML = `<div class="timeline__fill"></div>${html}`;

  const dateEl = document.getElementById("statusDate");
  if (dateEl) dateEl.textContent = STATUS_DATE;
}

/* ------------------------------------------------------------
   Boot
   ------------------------------------------------------------ */
renderTimeline();

const hasGsap = typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined";

if (hasGsap && !REDUCED_MOTION) {
  gsap.registerPlugin(ScrollTrigger);

  /* --- Lenis smooth scroll wired into GSAP's ticker --- */
  if (typeof Lenis !== "undefined") {
    const lenis = new Lenis({ lerp: 0.11, wheelMultiplier: 1 });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
  }

  /* --- Nav background on scroll --- */
  const nav = document.getElementById("nav");
  ScrollTrigger.create({
    start: 40,
    onUpdate: (self) => nav.classList.toggle("is-scrolled", self.scroll() > 40),
    onToggle: (self) => nav.classList.toggle("is-scrolled", self.scroll() > 40),
  });

  /* --- Hero entrance --- */
  const heroTl = gsap.timeline({ defaults: { ease: "power4.out" } });
  heroTl
    .to(".hero__title .line > span", { y: 0, duration: 1.15, stagger: 0.12 }, 0.15)
    .to(".hero .reveal", { opacity: 1, y: 0, duration: 0.9, stagger: 0.12 }, 0.5)
    .from(".hero__stats .stat", { opacity: 0, y: 20, duration: 0.7, stagger: 0.08 }, 0.9);

  /* --- Parallax backgrounds (hero + africa) --- */
  document.querySelectorAll("[data-parallax]").forEach((bg) => {
    gsap.to(bg, {
      yPercent: 12,
      ease: "none",
      scrollTrigger: { trigger: bg.parentElement, start: "top bottom", end: "bottom top", scrub: true },
    });
  });

  /* --- Generic reveals --- */
  document.querySelectorAll(".reveal").forEach((el) => {
    if (el.closest(".hero")) return; // hero handles its own
    gsap.to(el, {
      opacity: 1, y: 0, duration: 1, ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 85%" },
    });
  });

  document.querySelectorAll(".reveal-card").forEach((el, i) => {
    gsap.to(el, {
      opacity: 1, y: 0, duration: 1, ease: "power3.out", delay: (i % 3) * 0.1,
      scrollTrigger: { trigger: el, start: "top 88%" },
    });
  });

  document.querySelectorAll(".reveal-img").forEach((el) => {
    gsap.to(el, {
      opacity: 1, duration: 1.1, ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 85%" },
    });
    const img = el.querySelector("img");
    if (img) {
      gsap.fromTo(img, { scale: 1.14 }, {
        scale: 1, duration: 1.6, ease: "power2.out",
        scrollTrigger: { trigger: el, start: "top 85%" },
      });
    }
  });

  /* --- Counters --- */
  document.querySelectorAll("[data-count]").forEach((el) => {
    const end = parseFloat(el.dataset.count);
    const prefix = el.dataset.prefix || "";
    const suffix = el.dataset.suffix || "";
    const obj = { v: 0 };
    gsap.to(obj, {
      v: end, duration: 1.8, ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 90%" },
      onUpdate: () => { el.textContent = prefix + Math.round(obj.v) + suffix; },
    });
  });

  /* --- Ticker marquee --- */
  const track = document.querySelector(".ticker__track");
  if (track) {
    gsap.to(track, { xPercent: -50, ease: "none", duration: 26, repeat: -1 });
  }

  /* --- Corridor: pinned, scroll-driven route --- */
  const route = document.getElementById("routePath");
  const vessel = document.getElementById("vessel");
  const corridorPin = document.querySelector(".corridor__pin");
  if (route && vessel && corridorPin) {
    // dotted background grid
    const grid = document.querySelector(".corridor__grid");
    if (grid) {
      let dots = "";
      for (let x = 20; x < 520; x += 42) {
        for (let y = 20; y < 560; y += 42) {
          dots += `<circle cx="${x}" cy="${y}" r="1.6"></circle>`;
        }
      }
      grid.innerHTML = dots;
    }

    const len = route.getTotalLength();
    route.style.strokeDasharray = len;
    route.style.strokeDashoffset = len;

    const steps = gsap.utils.toArray(".cstep");
    const waypoints = gsap.utils.toArray(".wp");
    // journey runs "request in" (start) -> "cleared to ship" (end)
    const wpAt = [0, 0.32, 0.57, 0.8, 1];

    // truck marker follows the path and rotates to face the direction of travel
    const setVessel = (p) => {
      const d = p * len;
      const pt = route.getPointAtLength(d);
      const ahead = route.getPointAtLength(Math.min(len, d + 2));
      const behind = route.getPointAtLength(Math.max(0, d - 2));
      const angle = (Math.atan2(ahead.y - behind.y, ahead.x - behind.x) * 180) / Math.PI;
      // heading left? mirror across the local x-axis so the truck stays upright
      const flip = Math.abs(angle) > 90 ? " scale(1,-1)" : "";
      vessel.setAttribute("transform", `translate(${pt.x} ${pt.y}) rotate(${angle})${flip}`);
    };
    setVessel(0);
    waypoints.forEach((w) => {
      if (w.dataset.wp === "0") w.classList.add("is-lit");
    });

    // Pin only on desktop — on small screens the pinned content is taller
    // than the viewport, so scrub against the section's natural scroll instead.
    const isDesktop = window.matchMedia("(min-width: 981px)").matches;
    ScrollTrigger.create({
      trigger: ".corridor",
      start: isDesktop ? "top top" : "top 65%",
      end: isDesktop ? "+=220%" : "bottom 75%",
      pin: isDesktop ? corridorPin : false,
      scrub: 0.6,
      onUpdate: (self) => {
        const p = self.progress;
        route.style.strokeDashoffset = len * (1 - p);
        setVessel(p);
        // light waypoints as the vessel passes them
        waypoints.forEach((w) => {
          const idx = parseInt(w.dataset.wp, 10);
          w.classList.toggle("is-lit", p >= wpAt[idx] - 0.02);
        });
        // activate the matching narrative step
        const active = Math.min(steps.length - 1, Math.floor(p * steps.length));
        steps.forEach((s, i) => s.classList.toggle("is-active", i === active));
      },
    });
  }

  /* --- Road strips: trucks drive across as you scroll --- */
  document.querySelectorAll(".road").forEach((strip) => {
    const truck = strip.querySelector(".road__truck");
    if (!truck) return;
    const reverse = strip.classList.contains("road--reverse");
    const distance = () => window.innerWidth + 260;

    if (reverse) gsap.set(truck, { scaleX: -1 });
    gsap.fromTo(
      truck,
      { x: reverse ? distance() : -260 },
      {
        x: reverse ? -260 : distance(),
        ease: "none",
        scrollTrigger: {
          trigger: strip,
          start: "top bottom",
          end: "bottom top",
          scrub: 0.4,
          invalidateOnRefresh: true,
        },
      }
    );
    // wheels spin with the same scrub
    gsap.to(strip.querySelectorAll(".wheel"), {
      rotation: reverse ? -720 : 720,
      ease: "none",
      scrollTrigger: { trigger: strip, start: "top bottom", end: "bottom top", scrub: 0.4 },
    });
  });

  /* --- Progress timeline: line fill + milestone reveals + MVP bar --- */
  const timeline = document.getElementById("timeline");
  if (timeline) {
    const fill = timeline.querySelector(".timeline__fill");
    gsap.to(fill, {
      height: "100%", ease: "none",
      scrollTrigger: { trigger: timeline, start: "top 75%", end: "bottom 55%", scrub: true },
    });
    timeline.querySelectorAll(".milestone").forEach((m) => {
      gsap.from(m, {
        opacity: 0, x: -26, duration: 0.85, ease: "power3.out",
        scrollTrigger: { trigger: m, start: "top 88%" },
      });
    });
    const bar = timeline.querySelector(".mvpbar__fill");
    if (bar) {
      gsap.to(bar, {
        width: (bar.dataset.progress || 0) + "%", duration: 1.4, ease: "power3.out",
        scrollTrigger: { trigger: bar, start: "top 90%" },
      });
    }
  }
} else {
  /* --- No-animation fallback: show everything --- */
  document
    .querySelectorAll(".reveal, .reveal-card, .reveal-img, .hero__title .line > span")
    .forEach((el) => {
      el.style.opacity = 1;
      el.style.transform = "none";
    });
  const bar = document.querySelector(".mvpbar__fill");
  if (bar) bar.style.width = (bar.dataset.progress || 0) + "%";
  document.querySelectorAll(".cstep").forEach((s) => s.classList.add("is-active"));
  document.querySelectorAll(".wp").forEach((w) => w.classList.add("is-lit"));
  const route = document.getElementById("routePath");
  if (route) route.style.strokeDashoffset = 0;
}
