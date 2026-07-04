  (function () {
    var storageKey = "bt.dashboard.theme";
    var btn = document.getElementById("bt-theme-toggle");
    var root = document.body;

    if (!btn || !root) {
      return;
    }

    var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function applySavedTheme() {
      var saved = localStorage.getItem(storageKey);
      if (saved === "dark") {
        root.classList.add("bt-theme-dark");
        btn.textContent = "Light";
      } else {
        btn.textContent = "Dark";
      }
    }

    function wireThemeToggle() {
      btn.addEventListener("click", function () {
        var isDark = root.classList.toggle("bt-theme-dark");
        localStorage.setItem(storageKey, isDark ? "dark" : "light");
        btn.textContent = isDark ? "Light" : "Dark";
      });
    }

    function getQuadrantClass(element) {
      var target = element;
      while (target && target !== document.body) {
        if (target.classList && target.classList.contains("bt-q-red")) {
          return "bt-ripple-red";
        }
        if (target.classList && target.classList.contains("bt-q-blue")) {
          return "bt-ripple-blue";
        }
        if (target.classList && target.classList.contains("bt-q-yellow")) {
          return "bt-ripple-yellow";
        }
        if (target.classList && target.classList.contains("bt-q-green")) {
          return "bt-ripple-green";
        }
        target = target.parentElement;
      }
      return "bt-ripple-blue";
    }

    function wireQuadrantRipples() {
      if (reducedMotion) {
        return;
      }

      var interactiveTargets = document.querySelectorAll(
        ".bt-card, .bt-overview-card, .bt-model-card, .bt-flow-panel, .bt-task-panel, .bt-settings-panel, .bt-analytics-card, .bt-role-card, .bt-twist-panel, .bt-center-panel, .bt-flow-chip, .bt-task-chip, .bt-action, .bt-flow-link, .bt-task-link, .bt-role-link, .bt-analytics-link, .bt-settings-link"
      );

      interactiveTargets.forEach(function (target) {
        target.classList.add("bt-interactive");
        target.addEventListener("pointerdown", function (event) {
          var rect = target.getBoundingClientRect();
          var ripple = document.createElement("span");
          ripple.className = "bt-ripple " + getQuadrantClass(target);
          ripple.style.left = event.clientX - rect.left + "px";
          ripple.style.top = event.clientY - rect.top + "px";
          target.appendChild(ripple);
          window.setTimeout(function () {
            ripple.remove();
          }, 520);
        });
      });
    }

    function pulseWheel(targetId) {
      var wheel = document.querySelector(".bt-wheel");
      if (!wheel || reducedMotion) {
        return;
      }

      var idMap = {
        "#bt-top": "bt-wheel-q-red",
        "#bt-ops": "bt-wheel-q-red",
        "#bt-analytics": "bt-wheel-q-blue",
        "#bt-system": "bt-wheel-q-green",
      };
      var activeQuadrantClass = idMap[targetId] || "bt-wheel-q-red";

      wheel.querySelectorAll(".bt-wheel-q").forEach(function (q) {
        q.classList.remove("is-active");
      });
      var activeQuadrant = wheel.querySelector("." + activeQuadrantClass);
      if (activeQuadrant) {
        activeQuadrant.classList.add("is-active");
      }

      wheel.classList.remove("bt-wheel-pulse");
      window.requestAnimationFrame(function () {
        wheel.classList.add("bt-wheel-pulse");
      });
    }

    function focusSection(targetId) {
      var section = document.querySelector(targetId);
      if (!section) {
        return;
      }
      section.classList.remove("bt-section-focus");
      window.requestAnimationFrame(function () {
        section.classList.add("bt-section-focus");
        window.setTimeout(function () {
          section.classList.remove("bt-section-focus");
        }, 720);
      });
    }

    function wireWheelLinks() {
      var anchors = document.querySelectorAll('a[href^="#bt-"]');
      anchors.forEach(function (anchor) {
        anchor.addEventListener("click", function () {
          var href = anchor.getAttribute("href");
          pulseWheel(href);
          focusSection(href);
        });
      });

      if (window.location.hash && window.location.hash.indexOf("#bt-") === 0) {
        pulseWheel(window.location.hash);
      }
    }

    function wireBrandedEnterSequence() {
      if (reducedMotion) {
        return;
      }

      var sequenceTargets = document.querySelectorAll(
        ".bt-brand-header, .bt-actions, .bt-grid, .bt-flow-panel, .bt-task-panel, .bt-role-grid, .bt-settings-panel, .bt-analytics-grid, .bt-extra-grid"
      );

      sequenceTargets.forEach(function (node, index) {
        node.classList.add("bt-enter-seq");
        node.style.setProperty("--bt-enter-delay", (index * 48 + 60) + "ms");
      });

      window.requestAnimationFrame(function () {
        root.classList.add("bt-enter-ready");
      });
    }

    function wireMiniTrendChart() {
      var chart = document.querySelector("[data-mini-trend-chart]");
      var summary = document.querySelector("[data-mini-trend-summary]");
      if (!chart || !summary) {
        return;
      }

      var dayLabel = summary.querySelector("[data-mini-trend-day]");
      var countLabel = summary.querySelector("[data-mini-trend-count]");
      var pctLabel = summary.querySelector("[data-mini-trend-pct]");
      var bars = chart.querySelectorAll("[data-trend-day]");
      var selectedBar = null;

      function updateSummary(bar) {
        if (!bar || !dayLabel || !countLabel || !pctLabel) {
          return;
        }
        dayLabel.textContent = bar.getAttribute("data-trend-day") || "-";
        countLabel.textContent = bar.getAttribute("data-trend-count") || "0";
        pctLabel.textContent = (bar.getAttribute("data-trend-pct") || "0") + "%";
      }

      function setSelected(bar) {
        bars.forEach(function (item) {
          item.classList.remove("is-selected");
          item.setAttribute("aria-pressed", "false");
        });
        selectedBar = bar;
        if (selectedBar) {
          selectedBar.classList.add("is-selected");
          selectedBar.setAttribute("aria-pressed", "true");
          updateSummary(selectedBar);
        }
      }

      bars.forEach(function (bar) {
        bar.addEventListener("pointerenter", function () {
          bar.classList.add("is-hovered");
          updateSummary(bar);
        });

        bar.addEventListener("pointerleave", function () {
          bar.classList.remove("is-hovered");
          if (selectedBar) {
            updateSummary(selectedBar);
          }
        });

        bar.addEventListener("focus", function () {
          bar.classList.add("is-hovered");
          updateSummary(bar);
        });

        bar.addEventListener("blur", function () {
          bar.classList.remove("is-hovered");
          if (selectedBar) {
            updateSummary(selectedBar);
          }
        });

        bar.addEventListener("click", function () {
          setSelected(bar);
        });

        bar.addEventListener("keydown", function (event) {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setSelected(bar);
          }
        });
      });

      if (bars.length) {
        setSelected(bars[bars.length - 1]);
      }
    }

    applySavedTheme();
    wireThemeToggle();
    wireQuadrantRipples();
    wireWheelLinks();
    wireBrandedEnterSequence();
    wireMiniTrendChart();
  })();