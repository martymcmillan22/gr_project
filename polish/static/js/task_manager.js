/* ============================================================
   Enterprise Task Manager Admin - JS Enhancements
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    const root = document.querySelector(".task-manager-admin");
    const body = document.body;
    if (!root) {
        return;
    }

    const tabs = Array.from(root.querySelectorAll(".tm-tab[data-tab]"));
    const panels = Array.from(root.querySelectorAll(".tm-tab-content"));
    const sidebarLinks = Array.from(root.querySelectorAll(".tm-sidebar-content [data-tab]"));
    const quickActionTabs = Array.from(root.querySelectorAll(".tm-quick-action[data-tab]"));
    const sectionAnchors = Array.from(root.querySelectorAll(".tm-section-anchor[data-tab]"));
    const order = ["create", "attach", "assignment", "item", "metrics", "ops-metrics", "quarantine", "activity"];
    const metricsUrl = root.dataset.metricsUrl;
    const activityUrl = root.dataset.activityUrl;
    const themeStorageKey = "bt.dashboard.theme";
    const themeToggles = Array.from(new Set([
        root.querySelector("#tm-theme-toggle"),
        document.getElementById("bt-theme-toggle"),
    ].filter(Boolean)));
    const contrastToggle = root.querySelector("#tm-contrast-toggle");
    const contrastBadge = root.querySelector("#tm-contrast-badge");
    const quadrantRing = root.querySelector("#tm-quadrant-ring");

    if (!panels.length) {
        return;
    }

    root.setAttribute("role", "application");

    const tabsContainer = root.querySelector(".tm-tabs");
    if (tabsContainer) {
        tabsContainer.setAttribute("role", "tablist");
        tabsContainer.setAttribute("aria-label", "Task Manager Tabs");
    }

    let activeTab = (root.dataset.activeTab || "create").trim();
    if (!order.includes(activeTab)) {
        activeTab = "create";
    }

    function tabFromHash() {
        const raw = window.location.hash.replace(/^#/, "").trim();
        return order.includes(raw) ? raw : null;
    }

    function updateHash(id) {
        if (!order.includes(id) || window.location.hash === "#" + id) {
            return;
        }
        window.history.replaceState(null, "", "#" + id);
    }

    const hashedTab = tabFromHash();
    if (hashedTab) {
        activeTab = hashedTab;
    }

    function activateTab(id, options) {
        const settings = options || {};
        const scroll = settings.scroll !== false;
        const updateAnchor = settings.updateHash !== false;

        if (!order.includes(id)) {
            id = "create";
        }

        const visiblePanelIds = id === "metrics" ? ["metrics"] : [id, "metrics"];

        panels.forEach(function (panel) {
            panel.style.display = "none";
            panel.classList.remove("tm-panel-fade");
            panel.setAttribute("aria-hidden", "true");
        });

        tabs.forEach(function (tab) {
            tab.classList.remove("tm-tab-active");
            tab.setAttribute("aria-selected", "false");
            tab.setAttribute("tabindex", "-1");
            tab.setAttribute("role", "tab");
        });

        const panel = root.querySelector("#" + id);
        const tab = root.querySelector('.tm-tab[data-tab="' + id + '"]');

        visiblePanelIds.forEach(function (panelId, index) {
            const visiblePanel = root.querySelector("#" + panelId);
            if (!visiblePanel) {
                return;
            }
            visiblePanel.style.display = "block";
            visiblePanel.classList.add("tm-panel-fade");
            visiblePanel.setAttribute("aria-hidden", "false");
            visiblePanel.setAttribute("role", "tabpanel");
            visiblePanel.setAttribute("tabindex", "0");

            if (scroll && index === 0) {
                visiblePanel.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });

        if (tab) {
            tab.classList.add("tm-tab-active");
            tab.setAttribute("aria-selected", "true");
            tab.setAttribute("tabindex", "0");
        }

        activeTab = id;
        if (updateAnchor) {
            updateHash(id);
        }
    }

    function applyTheme(theme) {
        if (theme !== "dark" && theme !== "light") {
            return;
        }

        const darkModeEnabled = theme === "dark";
        body.classList.toggle("bt-theme-dark", darkModeEnabled);
        root.dataset.theme = theme;
        themeToggles.forEach(function (toggle) {
            toggle.setAttribute("aria-pressed", darkModeEnabled ? "true" : "false");
            toggle.innerText = darkModeEnabled ? "Light" : "Dark";
        });
        window.localStorage.setItem(themeStorageKey, theme);
        window.localStorage.setItem("tmTheme", theme);
    }

    function quadrantFromCompartment(code) {
        const token = (code || "").toUpperCase();
        if (token.indexOf("R") !== -1) {
            return "r";
        }
        if (token.indexOf("B") !== -1) {
            return "b";
        }
        if (token.indexOf("Y") !== -1) {
            return "y";
        }
        return "g";
    }

    function phaseRgb(phase) {
        const styles = getComputedStyle(root);
        if (phase === "post") {
            return styles.getPropertyValue("--tm-phase-post-rgb").trim() || "245, 158, 11";
        }
        if (phase === "work") {
            return styles.getPropertyValue("--tm-phase-work-rgb").trim() || "22, 163, 74";
        }
        return styles.getPropertyValue("--tm-phase-create-rgb").trim() || "37, 99, 235";
    }

    function quadrantRgb(quadrant) {
        const styles = getComputedStyle(root);
        if (quadrant === "r") {
            return styles.getPropertyValue("--tm-q-r-rgb").trim() || "229, 57, 53";
        }
        if (quadrant === "b") {
            return styles.getPropertyValue("--tm-q-b-rgb").trim() || "30, 136, 229";
        }
        if (quadrant === "y") {
            return styles.getPropertyValue("--tm-q-y-rgb").trim() || "249, 168, 37";
        }
        return styles.getPropertyValue("--tm-q-g-rgb").trim() || "46, 125, 50";
    }

    function compartmentRgb(node) {
        const key = (node.slot_key || ((node.phase || "") + "-" + (node.raw_code || node.code || "")))
            .toLowerCase()
            .replace(/\s+/g, "-");
        const map = {
            "create-r": "220, 38, 38",
            "create-b": "37, 99, 235",
            "create-y": "234, 179, 8",
            "create-g": "34, 197, 94",
            "post-p": "147, 51, 234",
            "post-t": "20, 184, 166",
            "post-o": "249, 115, 22",
            "post-l": "132, 204, 22",
            "work-p": "236, 72, 153",
            "work-c": "6, 182, 212",
            "work-a": "251, 191, 36",
            "work-g-l": "100, 116, 139"
        };
        return map[key] || "99, 102, 241";
    }

    function applyContrast(level) {
        if (level !== "standard" && level !== "high" && level !== "ultra") {
            return;
        }
        root.dataset.contrast = level;
        const badgeText =
            level === "ultra"
                ? "Contrast: Ultra"
                : (level === "high" ? "Contrast: High" : "Contrast: Standard");
        if (contrastToggle) {
            const emphasized = level !== "standard";
            contrastToggle.setAttribute("aria-pressed", emphasized ? "true" : "false");
            contrastToggle.innerText = badgeText;
        }
        if (contrastBadge) {
            contrastBadge.innerText = badgeText;
        }
        window.localStorage.setItem("tmContrast", level);
    }

    function updateBarCharts(data) {
        const assignmentsBar = document.getElementById("bar-assignments");
        const itemsBar = document.getElementById("bar-items");
        if (!assignmentsBar || !itemsBar) {
            return;
        }

        const total = Math.max(data.total_assignments || 0, data.total_items || 0, 1);
        assignmentsBar.style.width = (data.total_assignments / total) * 100 + "%";
        itemsBar.style.width = (data.total_items / total) * 100 + "%";
    }

    function updateDonut(data) {
        const donut = document.getElementById("tm-donut");
        if (!donut) {
            return;
        }

        const create = data.phase_counts ? (data.phase_counts.create || 0) : 0;
        const post = data.phase_counts ? (data.phase_counts.post || 0) : 0;
        const work = data.phase_counts ? (data.phase_counts.work || 0) : 0;
        const total = Math.max(create + post + work, 1);

        const createPct = (create / total) * 360;
        const postPct = (post / total) * 360;
        const workPct = (work / total) * 360;

        donut.style.setProperty("--create", createPct + "deg");
        donut.style.setProperty("--post", createPct + postPct + "deg");
        donut.style.setProperty("--work", createPct + postPct + workPct + "deg");
    }

    function updatePhaseFlow(data) {
        const createNode = document.getElementById("flow-create");
        const postNode = document.getElementById("flow-post");
        const workNode = document.getElementById("flow-work");
        if (!createNode || !postNode || !workNode || !data.phase_counts) {
            return;
        }

        const maxValue = Math.max(
            data.phase_counts.create || 0,
            data.phase_counts.post || 0,
            data.phase_counts.work || 0,
            1
        );

        const contrast = root.dataset.contrast || "high";
        const floor = contrast === "ultra" ? 0.32 : (contrast === "high" ? 0.25 : 0.15);
        const borderAlpha = contrast === "ultra" ? 1 : (contrast === "high" ? 0.85 : 0.6);

        const createAlpha = Math.max(floor, data.phase_counts.create / maxValue);
        const postAlpha = Math.max(floor, data.phase_counts.post / maxValue);
        const workAlpha = Math.max(floor, data.phase_counts.work / maxValue);

        const createRgb = phaseRgb("create");
        const postRgb = phaseRgb("post");
        const workRgb = phaseRgb("work");

        createNode.style.background = "rgba(" + createRgb + "," + createAlpha + ")";
        postNode.style.background = "rgba(" + postRgb + "," + postAlpha + ")";
        workNode.style.background = "rgba(" + workRgb + "," + workAlpha + ")";
        createNode.style.borderColor = "rgba(" + createRgb + "," + borderAlpha + ")";
        postNode.style.borderColor = "rgba(" + postRgb + "," + borderAlpha + ")";
        workNode.style.borderColor = "rgba(" + workRgb + "," + borderAlpha + ")";
    }

    function renderCompartmentFlow(data) {
        const container = document.getElementById("tm-compartment-flow");
        if (!container) {
            return;
        }

        const flow = data.compartment_flow || [];
        const maxCount = Math.max.apply(
            null,
            flow.map(function (node) {
                return node.count || 0;
            }).concat([1])
        );

        container.innerHTML = "";
        flow.forEach(function (node, index) {
            const item = document.createElement("div");
            item.className = "tm-compartment-node";
            item.style.setProperty("--flow-delay", index * 0.12 + "s");

            const intensity = Math.round(((node.count || 0) / maxCount) * 100);
            const quadrant = quadrantFromCompartment(node.code || "");
            const phaseColor = phaseRgb(node.phase || "create");
            const slotColor = compartmentRgb(node);

            item.dataset.quadrant = quadrant;
            item.dataset.phase = node.phase || "create";
            item.style.background =
                "linear-gradient(135deg, rgba(" + phaseColor + ",0.22) 0%, rgba(" + slotColor + ",0.34) 100%)";
            item.style.borderColor = "rgba(" + slotColor + ",0.92)";
            item.innerHTML =
                "<strong>" + node.code + "</strong>" +
                "<span>" + (node.phase || "create") + " · " + (node.count || 0) + "</span>" +
                '<div class="tm-compartment-intensity" style="--intensity: ' + intensity + '%; --intensity-color: rgba(' + slotColor + ',0.96)"></div>';
            container.appendChild(item);
        });
    }

    function syncQuadrantRing() {
        if (!quadrantRing) {
            return;
        }
        const enabled = root.dataset.quadrantRing === "on";
        quadrantRing.style.display = enabled ? "block" : "none";
    }

    function renderAssignmentTimeline(data) {
        const container = document.getElementById("tm-assignment-timeline");
        if (!container) {
            return;
        }

        const points = data.assignment_timeline || [];
        const maxCount = Math.max.apply(
            null,
            points
                .map(function (point) {
                    return Math.max(point.created || 0, point.completed || 0);
                })
                .concat([1])
        );

        container.innerHTML = "";
        points.forEach(function (point) {
            const date = new Date(point.day + "T00:00:00");
            const label = date.toLocaleDateString(undefined, { weekday: "short" });
            const createdValue = point.created || 0;
            const completedValue = point.completed || 0;
            const createdHeight = createdValue > 0 ? Math.max(6, Math.round((createdValue / maxCount) * 120)) : 0;
            const completedHeight = completedValue > 0 ? Math.max(6, Math.round((completedValue / maxCount) * 120)) : 0;

            const day = document.createElement("div");
            day.className = "tm-timeline-day";
            day.innerHTML =
                '<div class="tm-timeline-bars">' +
                '<div class="tm-timeline-bar tm-timeline-bar-created" title="Created: ' + createdValue + '" style="height:' + createdHeight + 'px"></div>' +
                '<div class="tm-timeline-bar tm-timeline-bar-completed" title="Completed: ' + completedValue + '" style="height:' + completedHeight + 'px"></div>' +
                "</div>" +
                '<div class="tm-timeline-label">' + label + "</div>";
            container.appendChild(day);
        });
    }

    function renderItemLifecycleHeatmap(data) {
        const container = document.getElementById("tm-item-lifecycle-heatmap");
        if (!container) {
            return;
        }

        const heatmap = data.item_lifecycle_heatmap || {};
        const phases = heatmap.phases || [];
        const statuses = heatmap.statuses || [];
        const matrix = heatmap.matrix || [];

        const allValues = [];
        matrix.forEach(function (row) {
            row.forEach(function (value) {
                allValues.push(value || 0);
            });
        });
        const maxValue = Math.max.apply(null, allValues.concat([1]));

        container.innerHTML = "";
        container.appendChild(Object.assign(document.createElement("div"), { className: "tm-heatmap-header", innerText: "Status \\ Phase" }));
        phases.forEach(function (phase) {
            container.appendChild(Object.assign(document.createElement("div"), { className: "tm-heatmap-header", innerText: phase }));
        });

        statuses.forEach(function (status, rowIndex) {
            container.appendChild(Object.assign(document.createElement("div"), { className: "tm-heatmap-row-label", innerText: status }));
            phases.forEach(function (phase, colIndex) {
                const value = (matrix[rowIndex] && matrix[rowIndex][colIndex]) || 0;
                const intensity = Math.round((value / maxValue) * 100);
                const contrast = root.dataset.contrast || "high";
                const minAlpha = root.dataset.theme === "dark"
                    ? (contrast === "ultra" ? 0.4 : (contrast === "high" ? 0.28 : 0.18))
                    : (contrast === "ultra" ? 0.24 : (contrast === "high" ? 0.16 : 0.1));
                const alpha = value === 0 ? 0 : Math.max(minAlpha, intensity / 100);
                const heatmapRgb = getComputedStyle(root).getPropertyValue("--tm-heatmap-rgb").trim() || "0, 95, 184";
                const cell = document.createElement("div");
                cell.className = "tm-heatmap-cell";
                cell.setAttribute("data-intensity", String(intensity));
                cell.style.background = "rgba(" + heatmapRgb + "," + alpha + ")";
                cell.style.borderColor = value > 0 ? "rgba(" + heatmapRgb + ",0.75)" : "";
                cell.innerText = String(value);
                cell.title = status + " in " + phase + ": " + value;
                container.appendChild(cell);
            });
        });
    }

    function refreshMetrics() {
        if (!metricsUrl) {
            return;
        }
        fetch(metricsUrl)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                const fields = {
                    "tm-total-assignments": data.total_assignments,
                    "tm-active-assignments": data.active_assignments,
                    "tm-completed-assignments": data.completed_assignments,
                    "tm-total-items": data.total_items,
                    "tm-items-progress": data.items_in_progress,
                    "tm-items-completed": data.items_completed,
                    "tm-phase-create": data.phase_counts ? data.phase_counts.create : 0,
                    "tm-phase-post": data.phase_counts ? data.phase_counts.post : 0,
                    "tm-phase-work": data.phase_counts ? data.phase_counts.work : 0,
                };

                Object.keys(fields).forEach(function (id) {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerText = fields[id];
                    }
                });

                if (Array.isArray(data.compartment_slots)) {
                    data.compartment_slots.forEach(function (slot) {
                        const el = document.getElementById("tm-compartment-" + slot.slot_key);
                        if (el) {
                            el.innerText = slot.count || 0;
                        }
                    });
                } else if (data.compartment_counts) {
                    Object.entries(data.compartment_counts).forEach(function (entry) {
                        const code = entry[0];
                        const count = entry[1];
                        const el = document.getElementById("tm-compartment-" + code.toLowerCase());
                        if (el) {
                            el.innerText = count;
                        }
                    });
                }

                updateBarCharts(data);
                updateDonut(data);
                updatePhaseFlow(data);
                renderCompartmentFlow(data);
                renderAssignmentTimeline(data);
                renderItemLifecycleHeatmap(data);

                const ops = data.operational_metrics || {};
                const opsFields = {
                    "tm-throughput-7d": ops.assignment_throughput_7d || 0,
                    "tm-item-velocity": ops.item_velocity_steps_per_day || 0,
                    "tm-create-start-latency": ops.phase_transition_latency_hours
                        ? (ops.phase_transition_latency_hours.create_to_start_hours || 0)
                        : 0,
                    "tm-start-complete-latency": ops.phase_transition_latency_hours
                        ? (ops.phase_transition_latency_hours.start_to_complete_hours || 0)
                        : 0,
                };

                Object.keys(opsFields).forEach(function (id) {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerText = opsFields[id];
                    }
                });

                const refreshedAt = document.getElementById("tm-metrics-refresh");
                if (refreshedAt) {
                    const now = new Date();
                    refreshedAt.innerText =
                        "Last refreshed: " + now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
                }

                const dwellList = document.getElementById("tm-compartment-dwell-list");
                if (dwellList) {
                    dwellList.innerHTML = "";
                    const dwell = ops.compartment_dwell_time_hours || {};
                    const dwellEntries = Object.entries(dwell);
                    if (!dwellEntries.length) {
                        const empty = document.createElement("li");
                        empty.innerText = "No dwell data available.";
                        dwellList.appendChild(empty);
                    } else {
                        dwellEntries.forEach(function (entry) {
                            const li = document.createElement("li");
                            li.innerText = entry[0] + ": " + entry[1];
                            dwellList.appendChild(li);
                        });
                    }
                }

                const productivityList = document.getElementById("tm-productivity-list");
                if (productivityList) {
                    productivityList.innerHTML = "";
                    const rows = ops.per_user_productivity || [];
                    if (!rows.length) {
                        const empty = document.createElement("li");
                        empty.innerText = "No productivity data available.";
                        productivityList.appendChild(empty);
                    } else {
                        rows.forEach(function (row) {
                            const li = document.createElement("li");
                            li.innerText =
                                row.user + ": " + row.completed + "/" + row.total + " completed (" + row.completion_rate + "%)";
                            productivityList.appendChild(li);
                        });
                    }
                }
            });
    }

    function refreshActivity() {
        if (!activityUrl) {
            return;
        }
        fetch(activityUrl)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                const feed = document.getElementById("tm-activity-feed");
                if (!feed) {
                    return;
                }
                feed.innerHTML = "";

                (data.events || []).forEach(function (event) {
                    const li = document.createElement("li");
                    li.innerText = event.timestamp + " - " + event.message;
                    feed.appendChild(li);
                });
            });
    }

    function toggleSidebar() {
        const container = root.querySelector("#tm-sidebar-content");
        const toggleButton = root.querySelector(".tm-sidebar-toggle");
        if (!container || !toggleButton) {
            return;
        }

        const isOpen = container.style.display === "flex";
        container.style.display = isOpen ? "none" : "flex";
        toggleButton.setAttribute("aria-expanded", isOpen ? "false" : "true");
    }

    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            const id = tab.getAttribute("data-tab");
            activateTab(id, { scroll: true });
        });
    });

    sidebarLinks.forEach(function (link) {
        link.addEventListener("click", function () {
            const id = link.getAttribute("data-tab");
            activateTab(id, { scroll: true });
        });
    });

    quickActionTabs.forEach(function (action) {
        action.addEventListener("click", function () {
            const id = action.getAttribute("data-tab");
            activateTab(id, { scroll: true });
        });
    });

    sectionAnchors.forEach(function (anchor) {
        anchor.addEventListener("click", function (event) {
            event.preventDefault();
            const id = anchor.getAttribute("data-tab");
            activateTab(id, { scroll: true });
        });
    });

    window.addEventListener("hashchange", function () {
        const id = tabFromHash();
        if (id && id !== activeTab) {
            activateTab(id, { scroll: true, updateHash: false });
        }
    });

    const sidebarToggle = root.querySelector(".tm-sidebar-toggle");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", toggleSidebar);
    }

    themeToggles.forEach(function (toggle) {
        toggle.addEventListener("click", function () {
            const current = root.dataset.theme === "dark" ? "dark" : "light";
            applyTheme(current === "dark" ? "light" : "dark");
            refreshMetrics();
        });
    });

    if (contrastToggle) {
        contrastToggle.addEventListener("click", function () {
            const current = root.dataset.contrast || "high";
            const next = current === "standard" ? "high" : (current === "high" ? "ultra" : "standard");
            applyContrast(next);
            refreshMetrics();
        });
    }

    document.addEventListener("keydown", function (e) {
        const focusedInsideTaskManager = root.contains(document.activeElement);
        if (!focusedInsideTaskManager) {
            return;
        }

        const currentIndex = order.indexOf(activeTab);
        if (currentIndex === -1) {
            return;
        }

        if (e.key === "ArrowRight") {
            e.preventDefault();
            const next = order[(currentIndex + 1) % order.length];
            activateTab(next, { scroll: true });
            return;
        }

        if (e.key === "ArrowLeft") {
            e.preventDefault();
            const prev = order[(currentIndex - 1 + order.length) % order.length];
            activateTab(prev, { scroll: true });
        }
    });

    const storedTheme = window.localStorage.getItem(themeStorageKey) || window.localStorage.getItem("tmTheme");
    if (storedTheme === "dark" || storedTheme === "light") {
        applyTheme(storedTheme);
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        applyTheme("dark");
    } else {
        applyTheme("light");
    }

    const storedContrast = window.localStorage.getItem("tmContrast");
    if (storedContrast === "standard" || storedContrast === "high" || storedContrast === "ultra") {
        applyContrast(storedContrast);
    } else {
        applyContrast("high");
    }

    syncQuadrantRing();

    activateTab(activeTab, { scroll: false });
    refreshMetrics();
    refreshActivity();
    setInterval(refreshMetrics, 10000);
    setInterval(refreshActivity, 10000);
});
