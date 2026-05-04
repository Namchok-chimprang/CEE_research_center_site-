(function () {
    const previewParams = new URLSearchParams(window.location.search);
    const previewModeEnabled = previewParams.get("live_preview") === "1";

    function readLivePreviewState() {
        if (!previewModeEnabled || typeof window.localStorage === "undefined") {
            return null;
        }
        try {
            const raw = window.localStorage.getItem("publicationTreePreviewState");
            return raw ? JSON.parse(raw) : null;
        } catch (error) {
            return null;
        }
    }

    function renderTree(options) {
        const container = options.container;
        const canvasWrap = options.canvasWrap;
        const preset = options.preset;
        const nodes = options.nodes || [];
        const leafScale = Number(options.leafScale || 1);
        const presetLeafColor = preset.leafColor || null;
        const presetLeafOpacity = Number(preset.defaultLeafOpacity || 0.42);
        const selectedValue = options.selectedValue ?? null;
        const onNodeClick = options.onNodeClick || null;
        const onNodeEnter = options.onNodeEnter || null;
        const onNodeMove = options.onNodeMove || null;
        const onNodeLeave = options.onNodeLeave || null;
        const heightOverride = options.heightOverride || null;
        const nodeKey = options.nodeKey || function (item, index) {
            return item.number ?? index + 1;
        };

        if (!container || !preset || typeof d3 === "undefined") {
            return;
        }

        if (canvasWrap) {
            canvasWrap.style.setProperty(
                "--sdg-tree-branch-image",
                `url('${preset.branchImage}')`
            );
            canvasWrap.style.setProperty(
                "--sdg-tree-branch-size",
                preset.branchSize || "86% auto"
            );
            canvasWrap.style.setProperty(
                "--sdg-tree-branch-position",
                preset.branchPosition || "center 76%"
            );
        }

        const measuredWidth = container.offsetWidth || container.clientWidth || container.getBoundingClientRect().width;
        const width = Math.max(320, Math.floor(measuredWidth));
        const height = heightOverride || (width < 760 ? 560 : 640);

        container.innerHTML = "";

        const svg = d3
            .select(container)
            .append("svg")
            .attr("viewBox", `0 0 ${width} ${height}`)
            .attr("width", "100%")
            .attr("height", height)
            .attr("aria-label", options.ariaLabel || `SDG infographic ${preset.title || ""}`);

        const values = nodes.map((item) => item.visual_count || item.count || 1);
        const minValue = values.length ? Math.min(...values) : 1;
        const maxValue = values.length ? Math.max(...values) : 1;
        const valueRange = Math.max(1, maxValue - minValue);
        const layer = svg.append("g").attr("class", "tree-node-layer");

        nodes.forEach((item, index) => {
            const anchor = preset.anchors[index] || preset.anchors[preset.anchors.length - 1];
            if (!anchor) {
                return;
            }
            const key = nodeKey(item, index);

            const value = item.visual_count || item.count || 1;
            const normalized = (value - minValue) / valueRange;
            const fillColor = anchor.color || presetLeafColor || item.color || "#6e8bdc";
            const fillOpacity = Number(anchor.opacity || presetLeafOpacity);
            const radius = ((preset.baseRadius || 56) + normalized * (preset.radiusGain || 18)) * leafScale;
            const x = width * anchor.x;
            const y = height * anchor.y;
            const group = layer.append("g")
                .attr("transform", `translate(${x},${y})`)
                .attr("class", "sdg-leaf-node")
                .style("cursor", onNodeClick ? "pointer" : "default");

            group.append("circle")
                .attr("r", radius)
                .attr("fill", fillColor)
                .attr("opacity", fillOpacity);

            group.append("circle")
                .attr("r", radius * 0.9)
                .attr("fill", "#ffffff")
                .attr("opacity", 0.06);

            if (selectedValue !== null && selectedValue === key) {
                group.append("circle")
                    .attr("r", radius + 9)
                    .attr("fill", "none")
                    .attr("stroke", "#1f2933")
                    .attr("stroke-width", 3)
                    .lower();
            }

            if (onNodeEnter || onNodeMove || onNodeLeave || onNodeClick) {
                if (onNodeEnter) {
                    group.on("mouseenter", function (event) {
                        d3.select(this)
                            .transition()
                            .duration(150)
                            .attr("transform", `translate(${x},${y}) scale(1.06)`);
                        onNodeEnter(event, item, { x, y, radius, width, height, key });
                    });
                }
                if (onNodeMove) {
                    group.on("mousemove", function (event) {
                        onNodeMove(event, item, { x, y, radius, width, height, key });
                    });
                }
                if (onNodeLeave) {
                    group.on("mouseleave", function (event) {
                        d3.select(this)
                            .transition()
                            .duration(150)
                            .attr("transform", `translate(${x},${y}) scale(1)`);
                        onNodeLeave(event, item, { x, y, radius, width, height, key });
                    });
                }
                if (onNodeClick) {
                    group.on("click", function (event) {
                        onNodeClick(event, item, { x, y, radius, width, height, key });
                    });
                }
            }
        });

        return { width, height };
    }

    window.PublicationTreeRenderer = {
        render: renderTree,
    };

    const allNode = document.getElementById("sdg-tree-data");
    const featuredNode = document.getElementById("sdg-featured-data");
    const layoutsNode = document.getElementById("sdg-tree-layouts-data");
    const container = document.getElementById("sdgTreeCanvas");
    const canvasWrap = container ? container.closest(".sdg-tree-canvas-wrap") : null;
    const leftCalloutContainer = document.getElementById("sdgCalloutLeft");
    const rightCalloutContainer = document.getElementById("sdgCalloutRight");
    const leafSizeInput = document.getElementById("sdgLeafSize");
    const leafSizeValue = document.getElementById("sdgLeafSizeValue");
    const filterLabel = document.getElementById("publicationFilterLabel");
    const clearFilterButton = document.getElementById("clearPublicationFilter");
    const publicationCards = Array.from(document.querySelectorAll(".publication-card-col"));
    const presetButtons = Array.from(document.querySelectorAll("[data-tree-preset]"));

    if (!allNode || !featuredNode || !container || typeof d3 === "undefined") {
        return;
    }

    const sdgData = JSON.parse(allNode.textContent || "[]");
    const featuredData = JSON.parse(featuredNode.textContent || "[]");
    const defaultTreePresets = {
        five: {
            leafCount: 5,
            title: "5-leaf tree",
            branchImage: "/static/images/tree-background-five.svg",
            branchSize: "80% auto",
            branchPosition: "center 77%",
            baseRadius: 52,
            radiusGain: 18,
            leafColor: "#6e8bdc",
            anchors: [
                { x: 0.19, y: 0.19 },
                { x: 0.38, y: 0.10 },
                { x: 0.58, y: 0.19 },
                { x: 0.14, y: 0.38 },
                { x: 0.65, y: 0.37 },
            ],
        },
        four: {
            leafCount: 4,
            title: "4-leaf tree",
            branchImage: "/static/images/tree-background-three.svg",
            branchSize: "74% auto",
            branchPosition: "center 84%",
            baseRadius: 50,
            radiusGain: 16,
            leafColor: "#6e8bdc",
            anchors: [
                { x: 0.35, y: 0.50 },
                { x: 0.54, y: 0.40 },
                { x: 0.66, y: 0.58 },
                { x: 0.22, y: 0.58 },
            ],
        },
        three: {
            leafCount: 3,
            title: "3-leaf tree",
            branchImage: "/static/images/tree-background-four.svg",
            branchSize: "70% auto",
            branchPosition: "center 80%",
            baseRadius: 54,
            radiusGain: 18,
            leafColor: "#6e8bdc",
            anchors: [
                { x: 0.40, y: 0.30 },
                { x: 0.57, y: 0.12 },
                { x: 0.75, y: 0.40 },
            ],
        },
    };
    const savedLayouts = layoutsNode ? JSON.parse(layoutsNode.textContent || "{}") : {};
    const treePresets = Object.assign({}, defaultTreePresets, savedLayouts);
    const livePreviewState = readLivePreviewState();

    if (livePreviewState && livePreviewState.layouts) {
        Object.entries(livePreviewState.layouts).forEach(([key, value]) => {
            treePresets[key] = value;
        });
    }

    let selectedSdg = null;
    let activePresetKey = (livePreviewState && livePreviewState.presetKey) || container.dataset.initialPreset || "five";
    let leafScale = 1;
    let tooltip;

    setupTooltip();
    setupFilterReset();
    setupPresetButtons();
    setupLeafSizeControl();
    renderCallouts();
    resizeChart();
    window.addEventListener("resize", resizeChart);

    function setupTooltip() {
        tooltip = d3.select("body")
            .append("div")
            .attr("class", "sdg-tree-tooltip")
            .style("opacity", 0);
    }

    function setupFilterReset() {
        if (!clearFilterButton) {
            return;
        }
        clearFilterButton.addEventListener("click", function () {
            selectedSdg = null;
            applyPublicationFilter();
            resizeChart();
        });
    }

    function setupPresetButtons() {
        presetButtons.forEach((button) => {
            button.addEventListener("click", function () {
                setPreset(button.dataset.treePreset);
            });
        });
        presetButtons.forEach((item) => {
            item.classList.toggle("is-active", item.dataset.treePreset === activePresetKey);
        });
    }

    function setupLeafSizeControl() {
        leafScale = 1;
        if (livePreviewState && livePreviewState.leafScale) {
            leafScale = Number(livePreviewState.leafScale);
        }
        if (getActivePreset().defaultLeafScale) {
            leafScale = Number(getActivePreset().defaultLeafScale);
        }
        if (livePreviewState && livePreviewState.leafScale) {
            leafScale = Number(livePreviewState.leafScale);
        }
        if (!leafSizeInput) {
            updateLeafSizeLabel();
            return;
        }
        leafSizeInput.value = String(leafScale);
        updateLeafSizeLabel();
        leafSizeInput.addEventListener("input", function () {
            setLeafScale(Number(leafSizeInput.value || 1));
        });
    }

    function updateLeafSizeLabel() {
        if (!leafSizeValue) {
            return;
        }
        leafSizeValue.textContent = `${Math.round(leafScale * 100)}%`;
    }

    function getActivePreset() {
        return treePresets[activePresetKey];
    }

    function setPreset(nextPreset) {
        if (!treePresets[nextPreset] || activePresetKey === nextPreset) {
            return;
        }
        activePresetKey = nextPreset;
        leafScale = Number(getActivePreset().defaultLeafScale || leafScale || 1);
        if (leafSizeInput) {
            leafSizeInput.value = String(leafScale);
        }
        updateLeafSizeLabel();
        presetButtons.forEach((item) => {
            item.classList.toggle("is-active", item.dataset.treePreset === activePresetKey);
        });
        renderCallouts();
        resizeChart();
    }

    function setLeafScale(nextScale) {
        leafScale = Number(nextScale || 1);
        if (leafSizeInput) {
            leafSizeInput.value = String(leafScale);
        }
        updateLeafSizeLabel();
        resizeChart();
    }

    function updateLayouts(nextLayouts) {
        Object.entries(nextLayouts || {}).forEach(([key, value]) => {
            treePresets[key] = value;
        });
        renderCallouts();
        resizeChart();
    }

    function getActiveNodes() {
        const preset = getActivePreset();
        const selectedNumbers = Array.isArray(preset.sdgNumbers) ? preset.sdgNumbers.filter(Boolean) : [];
        if (selectedNumbers.length) {
            return selectedNumbers
                .map((number) => sdgData.find((item) => item.number === Number(number)))
                .filter(Boolean)
                .slice(0, preset.leafCount);
        }
        return featuredData.slice(0, preset.leafCount);
    }

    function renderCallouts() {
        if (!leftCalloutContainer || !rightCalloutContainer) {
            return;
        }

        const nodes = getActiveNodes();
        const splitIndex = Math.ceil(nodes.length / 2);
        renderCalloutColumn(leftCalloutContainer, nodes.slice(0, splitIndex), false);
        renderCalloutColumn(rightCalloutContainer, nodes.slice(splitIndex), true);
        syncCalloutState();
    }

    function renderCalloutColumn(containerNode, items, reverse) {
        containerNode.innerHTML = "";
        items.forEach((item) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "sdg-callout";
            button.dataset.sdg = String(item.number);
            button.style.setProperty("--sdg-color", item.color);
            button.innerHTML = reverse
                ? `
                    <span class="sdg-callout__body">
                        <span class="sdg-callout__title">${item.label}</span>
                        <span class="sdg-callout__meta">${item.visual_count} paper${item.visual_count === 1 ? "" : "s"}</span>
                    </span>
                    <span class="sdg-callout__badge">${item.number}</span>
                `
                : `
                    <span class="sdg-callout__badge">${item.number}</span>
                    <span class="sdg-callout__body">
                        <span class="sdg-callout__title">${item.label}</span>
                        <span class="sdg-callout__meta">${item.visual_count} paper${item.visual_count === 1 ? "" : "s"}</span>
                    </span>
                `;
            button.addEventListener("click", function () {
                const value = Number(button.dataset.sdg);
                selectedSdg = selectedSdg === value ? null : value;
                applyPublicationFilter();
                resizeChart();
            });
            containerNode.appendChild(button);
        });
    }

    function resizeChart() {
        window.PublicationTreeRenderer.render({
            container,
            canvasWrap,
            preset: getActivePreset(),
            nodes: getActiveNodes(),
            leafScale,
            selectedValue: selectedSdg,
            ariaLabel: `SDG infographic ${getActivePreset().title}`,
            onNodeEnter(event, node) {
                const value = node.visual_count || node.count || 0;
                const isDemo = (node.count || 0) === 0;
                tooltip
                    .style("opacity", 1)
                    .html(`
                        <strong>SDG ${node.number}</strong><br>
                        ${node.label}<br>
                        ${value} paper${value === 1 ? "" : "s"}${isDemo ? " (demo)" : ""}
                    `);
                moveTooltip(event);
            },
            onNodeMove(event) {
                moveTooltip(event);
            },
            onNodeLeave() {
                tooltip.style("opacity", 0);
            },
            onNodeClick(event, node) {
                selectedSdg = selectedSdg === node.number ? null : node.number;
                applyPublicationFilter();
                resizeChart();
            },
        });
        syncCalloutState();
    }

    function moveTooltip(event) {
        tooltip
            .style("left", event.pageX + 18 + "px")
            .style("top", event.pageY - 28 + "px");
    }

    function syncCalloutState() {
        const allCallouts = Array.from(document.querySelectorAll(".sdg-callout"));
        allCallouts.forEach((button) => {
            const number = Number(button.dataset.sdg);
            button.classList.toggle("sdg-callout--selected", selectedSdg === number);
        });
    }

    function applyPublicationFilter() {
        publicationCards.forEach((card) => {
            const values = (card.dataset.sdgs || "")
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean)
                .map((value) => Number(value));
            const matches = !selectedSdg || values.includes(selectedSdg);
            card.hidden = !matches;
        });

        if (filterLabel) {
            filterLabel.textContent = selectedSdg
                ? `Showing publications tagged with SDG ${selectedSdg}`
                : "Showing all publications";
        }

        if (clearFilterButton) {
            clearFilterButton.hidden = !selectedSdg;
        }

        syncCalloutState();
    }

    window.PublicationTreePage = {
        setPreset,
        setLeafScale,
        updateLayouts,
        getState() {
            return {
                activePresetKey,
                leafScale,
            };
        },
    };
})();
