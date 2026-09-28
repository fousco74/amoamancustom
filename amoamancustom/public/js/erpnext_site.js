/* apps/amoamancustom/amoamancustom/public/js/erpnext_site.js
 *
 * Interactions du mini-site « Amoaman intégrateur ERPNext » (/erpnext/*).
 *
 * Volontairement autonome : public/js/main.js fait, ligne 44,
 *   document.querySelector('.timeline').addEventListener(...)
 * sans garde. `.timeline` n'existe que dans templates/includes/conformite.html,
 * donc sur toute autre page ce TypeError interrompt le script et emporte avec
 * lui les IIFE suivantes (smooth-scroll, reveal). Ici chaque bloc sort
 * proprement quand son point d'ancrage est absent — c'est la seule raison pour
 * laquelle ce fichier ne réutilise pas main.js.
 *
 * Aucune dépendance : ni jQuery, ni Bootstrap, ni frappe. Les pages qui
 * appellent le serveur (formulaire de contact) le font avec frappe.call dans
 * leur propre {% block script %}, qui appelle super().
 */

(function () {
  "use strict";

  /* ---------------------------------------------------------
   * Navigation mobile
   * ------------------------------------------------------- */
  function initNav() {
    var nav = document.querySelector("[data-erpx-nav]");
    if (!nav) return;

    var burger = nav.querySelector("[data-erpx-burger]");
    if (!burger) return;

    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    }

    burger.addEventListener("click", function () {
      setOpen(!nav.classList.contains("is-open"));
    });

    // Fermeture au clic sur un lien, puis au clic à l'extérieur.
    nav.addEventListener("click", function (event) {
      if (event.target.closest(".erpx-nav__link")) setOpen(false);
    });

    document.addEventListener("click", function (event) {
      if (!nav.contains(event.target)) setOpen(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setOpen(false);
    });
  }

  /* ---------------------------------------------------------
   * Accordéon FAQ — un seul panneau ouvert à la fois
   * ------------------------------------------------------- */
  function initFaq() {
    var groups = document.querySelectorAll("[data-erpx-faq]");
    if (!groups.length) return;

    groups.forEach(function (group) {
      var items = group.querySelectorAll(".erpx-faq__item");

      items.forEach(function (item) {
        var btn = item.querySelector(".erpx-faq__btn");
        if (!btn) return;

        btn.addEventListener("click", function () {
          var willOpen = !item.classList.contains("is-open");

          items.forEach(function (other) {
            other.classList.remove("is-open");
            var otherBtn = other.querySelector(".erpx-faq__btn");
            if (otherBtn) otherBtn.setAttribute("aria-expanded", "false");
          });

          if (willOpen) {
            item.classList.add("is-open");
            btn.setAttribute("aria-expanded", "true");
          }
        });
      });
    });
  }

  /* ---------------------------------------------------------
   * Carrousel « Découvrir d'autres modules »
   * ------------------------------------------------------- */
  function initCarousel() {
    var carousels = document.querySelectorAll("[data-erpx-carousel]");
    if (!carousels.length) return;

    carousels.forEach(function (carousel) {
      var track = carousel.querySelector(".erpx-carousel__track");
      var prev = carousel.querySelector("[data-erpx-carousel-prev]");
      var next = carousel.querySelector("[data-erpx-carousel-next]");
      if (!track) return;

      function step() {
        var first = track.firstElementChild;
        if (!first) return track.clientWidth;
        var gap = parseFloat(getComputedStyle(track).columnGap || "0") || 0;
        return first.getBoundingClientRect().width + gap;
      }

      function sync() {
        var max = track.scrollWidth - track.clientWidth - 1;
        if (prev) prev.disabled = track.scrollLeft <= 0;
        if (next) next.disabled = track.scrollLeft >= max;
      }

      if (prev) {
        prev.addEventListener("click", function () {
          track.scrollBy({ left: -step() * 2, behavior: "smooth" });
        });
      }
      if (next) {
        next.addEventListener("click", function () {
          track.scrollBy({ left: step() * 2, behavior: "smooth" });
        });
      }

      track.addEventListener("scroll", sync, { passive: true });
      window.addEventListener("resize", sync);
      sync();
    });
  }

  /* ---------------------------------------------------------
   * Sélecteur segmenté (carte Business de la tarification)
   * ------------------------------------------------------- */
  function initSegmented() {
    var groups = document.querySelectorAll("[data-erpx-segmented]");
    if (!groups.length) return;

    groups.forEach(function (group) {
      var options = group.querySelectorAll(".erpx-segmented__opt");

      options.forEach(function (option) {
        option.addEventListener("click", function () {
          options.forEach(function (other) {
            other.classList.remove("is-active");
            other.setAttribute("aria-selected", "false");
          });
          option.classList.add("is-active");
          option.setAttribute("aria-selected", "true");
        });
      });
    });
  }

  /* ---------------------------------------------------------
   * Liste deroulante a choix multiples (« Modules » du contact)
   * Le <details> et les cases a cocher fonctionnent seuls ; on recopie
   * simplement la selection dans le resume et on referme au clic exterieur.
   * ------------------------------------------------------- */
  function initMulti() {
    var listes = document.querySelectorAll("[data-erpx-multi]");
    if (!listes.length) return;

    listes.forEach(function (liste) {
      var texte = liste.querySelector("[data-erpx-multi-texte]");
      var cases = liste.querySelectorAll('input[type="checkbox"]');
      if (!texte) return;

      function maj() {
        var choix = [].slice.call(cases)
          .filter(function (c) { return c.checked; })
          .map(function (c) { return c.value; });
        texte.textContent = choix.length ? choix.join(", ") : texte.getAttribute("data-vide");
        liste.classList.toggle("is-rempli", choix.length > 0);
      }

      cases.forEach(function (c) { c.addEventListener("change", maj); });
      // form.reset() apres envoi : les cases se decochent sans evenement change.
      var form = liste.closest("form");
      if (form) form.addEventListener("reset", function () { setTimeout(maj, 0); });

      document.addEventListener("click", function (event) {
        if (liste.open && !liste.contains(event.target)) liste.open = false;
      });
    });
  }

  /* ---------------------------------------------------------
   * Défilement doux sur les ancres internes
   * ------------------------------------------------------- */
  function initSmoothScroll() {
    document.addEventListener("click", function (event) {
      var link = event.target.closest('a[href^="#"]');
      if (!link) return;

      var id = link.getAttribute("href");
      if (!id || id === "#") return;

      var target = document.querySelector(id);
      if (!target) return;

      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", id);
    });
  }

  /* ---------------------------------------------------------
   * Apparition au défilement
   * ------------------------------------------------------- */
  function initReveal() {
    var items = document.querySelectorAll(".erpx-reveal");
    if (!items.length) return;

    // Sans IntersectionObserver (ou en mode animations réduites), tout est
    // affiché d'emblée : le contenu ne doit jamais dépendre du script.
    if (!("IntersectionObserver" in window)) {
      items.forEach(function (item) { item.classList.add("is-visible"); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });

    items.forEach(function (item) { observer.observe(item); });

    // Filet de securite : si un observateur ne se declenche jamais (onglet en
    // arriere-plan au chargement, capture automatisee, navigateur exotique), le
    // contenu doit finir par apparaitre. Rien ne justifie une section vide.
    setTimeout(function () {
      items.forEach(function (item) { item.classList.add("is-visible"); });
    }, 2500);
  }

  function init() {
    initNav();
    initFaq();
    initCarousel();
    initSegmented();
    initMulti();
    initSmoothScroll();
    initReveal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
