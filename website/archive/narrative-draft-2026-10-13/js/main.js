/* ============================================================
   AtlasIQ — main.js
   Smooth scrolling (Lenis) + scroll animations (GSAP ScrollTrigger)
   ============================================================ */

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.getElementById("copyrightYear").textContent = new Date().getFullYear();

let lenis = null;

const hasGsap = typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined";

if (hasGsap && !REDUCED_MOTION) {
  gsap.registerPlugin(ScrollTrigger);

  /* --- Lenis smooth scroll wired into GSAP's ticker --- */
  if (typeof Lenis !== "undefined") {
    lenis = new Lenis({ lerp: 0.11, wheelMultiplier: 1 });
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
    // Conceptual development path; proposed stages are labelled in the page.
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

  }
} else {
  /* --- No-animation fallback: show everything --- */
  document
    .querySelectorAll(".reveal, .reveal-card, .reveal-img, .hero__title .line > span")
    .forEach((el) => {
      el.style.opacity = 1;
      el.style.transform = "none";
    });
  document.querySelectorAll(".cstep").forEach((s) => s.classList.add("is-active"));
  document.querySelectorAll(".wp").forEach((w) => w.classList.add("is-lit"));
  const route = document.getElementById("routePath");
  if (route) route.style.strokeDashoffset = 0;
}

/* Anchor navigation must use the active scroll controller, including deep links. */
function scrollToHash(hash, immediate = false) {
  if (!hash || hash === "#") return;
  let id;
  try { id = decodeURIComponent(hash.slice(1)); } catch (_) { return; }
  const target = document.getElementById(id);
  if (!target) return;
  const offset = -(document.getElementById("nav")?.offsetHeight || 0) - 12;
  if (lenis) {
    lenis.scrollTo(target, { offset, immediate, force: true });
  } else {
    const top = target.getBoundingClientRect().top + window.scrollY + offset;
    window.scrollTo({ top: Math.max(0, top), behavior: REDUCED_MOTION || immediate ? "instant" : "smooth" });
  }
}

document.addEventListener("click", (event) => {
  const link = event.target.closest?.('a[href^="#"]');
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const hash = link.getAttribute("href");
  let target;
  try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch (_) { return; }
  if (!target) return;
  event.preventDefault();
  if (window.location.hash !== hash) history.pushState(null, "", hash);
  scrollToHash(hash);
});
window.addEventListener("hashchange", () => scrollToHash(window.location.hash));
window.addEventListener("popstate", () => scrollToHash(window.location.hash || "#top"));

function restoreInitialAnchor() {
  // Refresh pinned layout first so the target position includes generated spacers.
  if (hasGsap) ScrollTrigger.refresh();
  requestAnimationFrame(() => scrollToHash(window.location.hash, true));
}
if (document.readyState === "complete") restoreInitialAnchor();
else window.addEventListener("load", restoreInitialAnchor, { once: true });
if (document.fonts?.ready) document.fonts.ready.then(() => {
  if (hasGsap) ScrollTrigger.refresh();
});
