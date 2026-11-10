(() => {
  "use strict";

  const script = document.currentScript;
  const sessionId = script?.dataset.sessionId || "";
  const endpoint = script?.dataset.endpoint || "";
  const sendIntervalMs = Number(script?.dataset.sendInterval || 30000);
  const onTouch = script?.dataset.includeTouch === "true";

  // Only aggregate values that the model was trained to consume. Pointer
  // coordinates stay in the browser and are never included in the request.
  const features = {
    mouse_event_count: 0,
    total_distance: 0,
    average_distance_per_move: 0,
    average_speed: 0,
    max_speed: 0,
    direction_changes: 0,
    average_time_gap: 0,
    pause_count: 0,
    left_clicks: 0,
    right_clicks: 0,
    middle_clicks: 0,
  };

  let previousPoint = null;
  let previousHeading = null;
  let moveSegments = 0;
  let speedTotal = 0;
  let gapTotal = 0;
  let sendInProgress = false;

  const pauseGapMs = 1000;
  const directionTurnRadians = Math.PI / 4;

  function makeSummary() {
    return {
      mouse_event_count: features.mouse_event_count,
      total_distance: features.total_distance,
      average_distance_per_move: moveSegments
        ? features.total_distance / moveSegments
        : 0,
      average_speed: moveSegments ? speedTotal / moveSegments : 0,
      max_speed: features.max_speed,
      direction_changes: features.direction_changes,
      average_time_gap: moveSegments ? gapTotal / moveSegments : 0,
      pause_count: features.pause_count,
      left_clicks: features.left_clicks,
      right_clicks: features.right_clicks,
      middle_clicks: features.middle_clicks,
    };
  }

  function publishSummary() {
    // Used by the included local test page; contains summary values, not coordinates.
    window.dispatchEvent(new CustomEvent("botmouse:summary", {
      detail: makeSummary(),
    }));
  }

  document.addEventListener("pointermove", (event) => {
    if (event.pointerType === "touch" && !onTouch) return;

    const now = performance.now();
    const point = { x: event.clientX, y: event.clientY, time: now };
    features.mouse_event_count += 1;

    if (previousPoint) {
      const dx = point.x - previousPoint.x;
      const dy = point.y - previousPoint.y;
      const distance = Math.hypot(dx, dy);
      const gap = now - previousPoint.time;
      const speed = gap > 0 ? distance / gap : 0;

      moveSegments += 1;
      features.total_distance += distance;
      gapTotal += gap;
      speedTotal += speed;
      features.max_speed = Math.max(features.max_speed, speed);
      // These thresholds define the feature contract for this collector. They
      // should be checked against the dataset's original preprocessing.
      if (gap > pauseGapMs) features.pause_count += 1;

      const heading = Math.atan2(dy, dx);
      if (previousHeading !== null) {
        let turn = Math.abs(heading - previousHeading);
        if (turn > Math.PI) turn = 2 * Math.PI - turn;
        if (turn > directionTurnRadians) features.direction_changes += 1;
      }
      previousHeading = heading;
    }

    previousPoint = point;
    publishSummary();
  }, { passive: true });

  document.addEventListener("click", (event) => {
    if (event.button === 0) features.left_clicks += 1;
    else if (event.button === 1) features.middle_clicks += 1;
    else if (event.button === 2) features.right_clicks += 1;
    publishSummary();
  }, { passive: true });

  async function sendSummary() {
    if (!endpoint || !sessionId || !features.mouse_event_count || sendInProgress) return;
    sendInProgress = true;
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionid: sessionId, features: makeSummary() }),
      });
      if (!response.ok) {
        console.error(`Mouse collector: ${endpoint} returned HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Mouse collector: request failed", error);
    } finally {
      sendInProgress = false;
    }
  }

  if (endpoint && sessionId && Number.isFinite(sendIntervalMs) && sendIntervalMs >= 1000) {
    window.setInterval(sendSummary, sendIntervalMs);
  }

  publishSummary();
})();
