(function () {
  "use strict";

  var cfg = window.peakmapConfig;
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));
  var statusEl = document.getElementById("status");

  // ---------------------------------------------------------------- shared view
  var shared = {
    camera: clone(cfg.camera),
    axes: clone(cfg.defaultAxes)
  };

  // panels that currently own a plotly graph, least recently used first
  var live = [];
  // the panel that the user moved last, used to skip re-writing it
  var driver = -1;

  function clone(value) {
    return value === undefined || value === null ? value : JSON.parse(JSON.stringify(value));
  }

  function plotOf(index) {
    return panels[index].querySelector(".plot");
  }

  // ---------------------------------------------------------------- comparison
  function sameNumber(a, b) {
    if (!isFinite(a) && !isFinite(b)) return true;
    return Math.abs((a || 0) - (b || 0)) < 1e-6;
  }

  function sameVector(a, b) {
    if (!a || !b) return false;
    return sameNumber(a.x, b.x) && sameNumber(a.y, b.y) && sameNumber(a.z, b.z);
  }

  function sameCamera(a, b) {
    if (!a || !b) return false;
    return sameVector(a.eye, b.eye) && sameVector(a.up, b.up) && sameVector(a.center, b.center);
  }

  function sameAxis(a, b) {
    a = a || {};
    b = b || {};
    if (!!a.autorange !== !!b.autorange) return false;
    if (a.autorange) return true;
    if (!a.range || !b.range) return false;
    return sameNumber(a.range[0], b.range[0]) && sameNumber(a.range[1], b.range[1]);
  }

  function sameAxes(a, b) {
    if (!a || !b) return false;
    return cfg.axes.every(function (key) { return sameAxis(a[key], b[key]); });
  }

  // ---------------------------------------------------------------- read layout
  // While the user drags, plotly only keeps the current view on the gl scene
  // object (scene._scene.getCamera()) and writes scene.camera when it saves the
  // layout, so try the live camera first.
  function readCamera(gd) {
    var scene = (gd._fullLayout && gd._fullLayout.scene) || {};
    var liveCamera = scene._scene && scene._scene.getCamera && scene._scene.getCamera();
    var cam = liveCamera || scene.camera ||
      (gd.layout && gd.layout.scene && gd.layout.scene.camera);
    if (!cam) return null;
    return {
      up: assign(clone(cfg.camera.up), cam.up),
      center: assign(clone(cfg.camera.center), cam.center),
      eye: assign(clone(cfg.camera.eye), cam.eye)
    };
  }

  function readAxes(gd) {
    var scene = (gd._fullLayout && gd._fullLayout.scene) ||
      (gd.layout && gd.layout.scene) || {};
    var axes = {};
    cfg.axes.forEach(function (key) {
      var axis = scene[key];
      if (!axis) return;
      if (axis.autorange) axes[key] = { autorange: true };
      else if (axis.range) axes[key] = { autorange: false, range: [axis.range[0], axis.range[1]] };
    });
    return axes;
  }

  function assign(target, source) {
    if (source) Object.keys(source).forEach(function (k) { target[k] = source[k]; });
    return target;
  }

  // ---------------------------------------------------------------- render
  function applySharedView(layout) {
    layout.scene = layout.scene || {};
    if (cfg.syncRotation && shared.camera) layout.scene.camera = clone(shared.camera);
    if (cfg.syncAxes && shared.axes) {
      cfg.axes.forEach(function (key) {
        if (!shared.axes[key]) return;
        layout.scene[key] = assign(layout.scene[key] || {}, shared.axes[key]);
      });
    }
    return layout;
  }

  // Plotly resolves the promise of newPlot once the graph is drawn, so a panel
  // owns a graph from that moment on and the budget of the viewport section
  // below stays a hard limit instead of a target.
  function build(index) {
    var gd = plotOf(index);
    var payload = cfg.figures[index];
    var layout = applySharedView(clone(payload.layout));
    gd.classList.remove("note");
    gd.innerHTML = ""; // drop a placeholder of an earlier attempt before plotly takes the div
    return Plotly.newPlot(gd, clone(payload.data), layout, {
      responsive: true,
      displaylogo: false,
      scrollZoom: true
    }).then(function () {
      if (gd.dataset.bound !== "1") {
        gd.dataset.bound = "1";
        var emit = function () { onView(index); };
        gd.on("plotly_afterplot", emit);
        gd.on("plotly_relayout", emit);
        gd.on("plotly_drag_begin", function () { startDragging(index); });
        gd.on("plotly_drag_end", function () { stopDragging(); onView(index); });
        gd.on("plotly_webglcontextlost", function () { lostContext(index); });
      }
      live.push(index);
      status();
    });
  }

  // The canvases of a graph hold the webgl contexts the browser counts, and a
  // canvas still knows its own context, so no plotly internals are needed here.
  function contextsOf(gd) {
    var canvases = gd.querySelectorAll("canvas");
    var contexts = [];
    Array.prototype.forEach.call(canvases, function (canvas) {
      var context = canvas.getContext("webgl2") || canvas.getContext("webgl");
      if (context) contexts.push(context);
    });
    return contexts;
  }

  function releaseContext(contexts) {
    contexts.forEach(function (context) {
      try {
        var lose = context.getExtension && context.getExtension("WEBGL_lose_context");
        if (lose && lose.loseContext) lose.loseContext();
      } catch (error) {
        // a context the driver already took away has no extension left to ask
      }
    });
  }

  // Plotly.purge() drops the graph but keeps its webgl context until the canvas is
  // collected, which lags behind scrolling, so the contexts are handed back by hand.
  // Purging comes first on purpose: purge() unsubscribes gl plot3d from the canvas,
  // and only its listener starts the recovery loop of plotly.
  function destroy(index) {
    var position = live.indexOf(index);
    if (position !== -1) live.splice(position, 1);
    var gd = plotOf(index);
    var contexts = contextsOf(gd);
    gd.dataset.bound = "0";
    Plotly.purge(gd);
    releaseContext(contexts);
    // the canvas goes with the markup, otherwise it cannot be collected
    gd.innerHTML = "";
  }

  // A panel whose context the browser took away is dropped instead of recovered:
  // plotly answers a loss by asking for a new context once per frame, and asking is
  // exactly what takes a context from the next panel, which then asks as well.
  function lostContext(index) {
    // the release in destroy() is a loss too, only a live panel lost something
    if (live.indexOf(index) === -1) return;
    budget = Math.max(1, budget - 1);
    destroy(index);
    panels[index].dataset.lost = "1";
    var gd = plotOf(index);
    gd.classList.add("note");
    gd.textContent = "the graphics context of this panel was lost, scroll away and back to draw it again";
    queue();
  }

  function touch(index) {
    var position = live.indexOf(index);
    if (position !== -1) live.splice(position, 1);
    live.push(index);
  }

  // ---------------------------------------------------------------- sync
  // Every graph gets its own flag instead of one global lock: a relayout that
  // never settles can then only mute its own panel, never the whole page.
  function patchFor(gd) {
    var patch = {};
    if (cfg.syncRotation && shared.camera && !sameCamera(readCamera(gd), shared.camera)) {
      patch["scene.camera"] = clone(shared.camera);
    }
    if (cfg.syncAxes && shared.axes) {
      var current = readAxes(gd);
      cfg.axes.forEach(function (key) {
        if (!shared.axes[key]) return;
        if (!sameAxis(current[key], shared.axes[key])) {
          patch["scene." + key] = clone(shared.axes[key]);
        }
      });
    }
    return patch;
  }

  function write(index) {
    var gd = plotOf(index);
    if (!gd || !gd._fullLayout) return;
    var patch = patchFor(gd);
    if (!Object.keys(patch).length) return;
    gd.dataset.applying = "1";
    var release = function () {
      gd.dataset.applying = "0";
      if (gd.dataset.timer) {
        window.clearTimeout(Number(gd.dataset.timer));
        gd.dataset.timer = "";
      }
    };
    // safety net in case plotly never resolves the relayout promise
    gd.dataset.timer = String(window.setTimeout(release, 500));
    try {
      Plotly.relayout(gd, patch).then(release, release);
    } catch (error) {
      release();
    }
  }

  // Plotly stays quiet while the mouse moves inside a 3D scene and only reports
  // the new camera when the drag ends, so follow the dragged panel frame by
  // frame to keep the other panels moving with it.
  var dragging = -1;
  var poll = 0;

  function startDragging(index) {
    dragging = index;
    if (poll) return;
    var step = function () {
      poll = 0;
      if (dragging === -1) return;
      onView(dragging);
      if (dragging !== -1) poll = window.requestAnimationFrame(step);
    };
    poll = window.requestAnimationFrame(step);
  }

  function stopDragging() {
    dragging = -1;
  }

  // relayouting every panel is not cheap, so batches are capped at ~25 per
  // second, which still feels immediate while dragging.
  var timer = 0;
  var lastSync = 0;

  function pushView() {
    timer = 0;
    lastSync = Date.now();
    // only the panels that own a graph can be looking at a different view
    live.slice().forEach(function (index) {
      if (index !== driver) write(index);
    });
    panels.forEach(function (panel, index) {
      panel.classList.toggle("driving", index === driver);
    });
  }

  function sync() {
    if (timer) return;
    var wait = Math.max(0, 40 - (Date.now() - lastSync));
    timer = window.setTimeout(pushView, wait);
  }

  function onView(index) {
    var gd = plotOf(index);
    if (!gd || gd.dataset.applying === "1") return; // this redraw came from us

    var changed = false;
    if (cfg.syncRotation) {
      var camera = readCamera(gd);
      if (camera && !sameCamera(camera, shared.camera)) {
        shared.camera = camera;
        changed = true;
      }
    }
    if (cfg.syncAxes) {
      var axes = readAxes(gd);
      if (Object.keys(axes).length && !sameAxes(axes, shared.axes)) {
        shared.axes = axes;
        changed = true;
      }
    }
    if (!changed) return;

    driver = index;
    touch(index);
    sync();
  }

  // ---------------------------------------------------------------- viewport
  // One graph is one webgl context and a browser only keeps a limited number of
  // them, so the budget is a hard limit rather than a target: a slot is freed
  // before the next panel is built, the panel closest to the middle of the window
  // goes first, and one panel is built per frame so that scrolling stays smooth.
  var budget = cfg.maxLive;
  var wanted = [];
  var building = false;
  var queued = false;

  function visible(index) {
    return !panels[index].classList.contains("hidden");
  }

  function distanceToMiddle(index) {
    var box = panels[index].getBoundingClientRect();
    return Math.abs((box.top + box.bottom) / 2 - window.innerHeight / 2);
  }

  // the panels the user could look at, best candidate first and never more than
  // the budget, so every panel on the list can really be given a graph
  function wantedPanels() {
    var list = [];
    panels.forEach(function (panel, index) {
      if (visible(index) && panel.dataset.inview === "1" && panel.dataset.lost !== "1") {
        list.push(index);
      }
    });
    list.sort(function (a, b) { return distanceToMiddle(a) - distanceToMiddle(b); });
    return list.slice(0, budget);
  }

  function missingPanels() {
    return wanted.filter(function (index) { return live.indexOf(index) === -1; });
  }

  // the oldest panel that is not wanted, and only if every live panel is wanted
  // the oldest of them, which the arithmetic below makes impossible anyway
  function victim() {
    for (var i = 0; i < live.length; i += 1) {
      if (wanted.indexOf(live[i]) === -1) return live[i];
    }
    return live.length ? live[0] : undefined;
  }

  function status() {
    var text = wanted.length + " of " + panels.length + " shown, " + live.length + " rendered";
    statusEl.textContent = budget === cfg.maxLive ? text : text + ", budget " + budget;
  }

  function buildNext() {
    if (building) return;
    var missing = missingPanels();
    if (!missing.length) return;

    building = true;
    var settled = function () {
      building = false;
      queue(); // the next panel waits for the next frame, whichever path it takes
    };
    build(missing[0]).then(settled, settled);
  }

  function refresh() {
    wanted = wantedPanels();

    wanted.forEach(function (index) {
      if (live.indexOf(index) !== -1) touch(index);
    });

    // free one slot for every panel that still needs a graph, a live panel that
    // is not wanted keeps its graph until the budget really needs the room
    var missing = missingPanels();
    while (missing.length && live.length + missing.length > budget) {
      var dropped = victim();
      if (dropped === undefined) break;
      destroy(dropped);
    }

    status();
    buildNext();
  }

  function queue() {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(function () { queued = false; refresh(); });
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var index = Number(entry.target.dataset.index);
        entry.target.dataset.inview = entry.isIntersecting ? "1" : "0";
        // a panel whose context was lost is tried again the next time it is reached
        if (!entry.isIntersecting) entry.target.dataset.lost = "0";
        if (!entry.isIntersecting && live.indexOf(index) === -1) return;
        queue();
      });
    }, { rootMargin: cfg.preload + "px 0px " + cfg.preload + "px 0px" });
    panels.forEach(function (panel, index) {
      panel.dataset.index = String(index);
      observer.observe(panel);
    });
  } else {
    panels.forEach(function (panel, index) {
      panel.dataset.index = String(index);
      panel.dataset.inview = "1";
    });
    window.addEventListener("scroll", queue, { passive: true });
  }

  // ---------------------------------------------------------------- controls
  document.getElementById("filter").addEventListener("input", function (event) {
    var query = event.target.value.trim().toLowerCase();
    panels.forEach(function (panel) {
      var name = panel.getAttribute("data-name").toLowerCase();
      panel.classList.toggle("hidden", !!query && name.indexOf(query) === -1);
    });
    queue();
  });

  document.getElementById("sync-rotation").addEventListener("change", function (event) {
    cfg.syncRotation = event.target.checked;
  });

  document.getElementById("sync-axes").addEventListener("change", function (event) {
    cfg.syncAxes = event.target.checked;
  });

  document.getElementById("reset-view").addEventListener("click", function () {
    shared.camera = clone(cfg.camera);
    shared.axes = clone(cfg.defaultAxes);
    driver = -1;
    live.slice().forEach(write);
    panels.forEach(function (panel) { panel.classList.remove("driving"); });
  });

  // handy when checking the report in the developer console
  window.peakmapDebug = function () {
    return {
      shared: shared,
      live: live.slice(),
      wanted: wanted.slice(),
      budget: budget,
      building: building,
      lostPanels: panels.map(function (p) { return p.dataset.lost; }).filter(function (l) { return l === "1"; }).length,
      drivers: panels.map(function (p) { return p.classList.contains("driving"); }),
      applying: panels.map(function (p) { return p.querySelector(".plot").dataset.applying; })
    };
  };

  refresh();
})();
