(function () {
  "use strict";


  const ENDPOINT_URL = "http://127.0.0.1:8000/fingerprint";
  const SESSION_STORAGE_KEY = "bfp_session_id";
  const SENT_FLAG_KEY = "bfp_fingerprint_sent";


  function getSessionId() {
    try {
      let id = sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (!id) {
        id =
          (window.crypto && crypto.randomUUID)
            ? crypto.randomUUID()
            : "sid-" + Date.now() + "-" + Math.random().toString(36).slice(2);
        sessionStorage.setItem(SESSION_STORAGE_KEY, id);
      }
      return id;
    } catch (e) {
      // sessionStorage blocked (e.g. private mode) -> fall back to a transient id
      return "sid-" + Date.now() + "-" + Math.random().toString(36).slice(2);
    }
  }


  function getWebglRenderer() {
    try {
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      if (!gl) return null;
      const dbgInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (dbgInfo) {
        return gl.getParameter(dbgInfo.UNMASKED_RENDERER_WEBGL);
      }
      return gl.getParameter(gl.RENDERER); // fallback, usually generic
    } catch (e) {
      return null;
    }
  }


  function detectAutomationFlags() {
    const flags = {
      selenium: false,
      playwright: false,
      puppeteer: false,
    };

    try {

      if (
        window.document.documentElement.getAttribute("webdriver") ||
        window.document.documentElement.getAttribute("selenium") ||
        window.document.documentElement.getAttribute("driver")
      ) {
        flags.selenium = true;
      }
      const cdcProps = Object.keys(window).filter((k) =>
        /^\$cdc_|^\$chrome_asyncScriptInfo|^__webdriver|^__selenium|^__fxdriver/.test(
          k
        )
      );
      if (cdcProps.length > 0) flags.selenium = true;
      if (window.document.$cdc_asdjflasutopfhvcZLmcfl_) flags.selenium = true;


      if (
        window.__playwright ||
        window.__pw_manual ||
        window.navigator.webdriver === true &&
          /HeadlessChrome/.test(navigator.userAgent)
      ) {
        flags.playwright = true;
      }


      if (
        window.__puppeteer_evaluation_script__ ||
        (window.chrome && !window.chrome.runtime && navigator.webdriver)
      ) {
        flags.puppeteer = true;
      }
    } catch (e) {

    }

    return flags;
  }


  function detectBrowserApis() {
    const apis = {
      canvas: false,
      webgl: false,
      local_storage: false,
      session_storage: false,
      indexeddb: false,
    };

    try {
      const canvas = document.createElement("canvas");
      apis.canvas = !!(canvas.getContext && canvas.getContext("2d"));
    } catch (e) {}

    try {
      const canvas = document.createElement("canvas");
      apis.webgl = !!(
        canvas.getContext("webgl") || canvas.getContext("experimental-webgl")
      );
    } catch (e) {}

    try {
      const testKey = "__bfp_test__";
      localStorage.setItem(testKey, "1");
      localStorage.removeItem(testKey);
      apis.local_storage = true;
    } catch (e) {}

    try {
      const testKey = "__bfp_test__";
      sessionStorage.setItem(testKey, "1");
      sessionStorage.removeItem(testKey);
      apis.session_storage = true;
    } catch (e) {}

    apis.indexeddb = !!window.indexedDB;

    return apis;
  }


  function buildFingerprint() {
    return {
      sessionid: getSessionId(),
      features: {
        webdriver: !!navigator.webdriver,
        user_agent: navigator.userAgent || null,
        platform: navigator.platform || null,
        language: navigator.language || null,
        webgl_renderer: getWebglRenderer(),
        automation_flags: detectAutomationFlags(),
        browser_apis: detectBrowserApis(),
      },
    };
  }


  function sendFingerprint(payload) {
    const body = JSON.stringify(payload);

  
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon(ENDPOINT_URL, blob);
      if (ok) return;
    }


    fetch(ENDPOINT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body,
      keepalive: true,
    }).catch(function (err) {
      console.warn("Fingerprint POST failed:", err);
    });
  }

  function init() {
    try {
      if (sessionStorage.getItem(SENT_FLAG_KEY)) return;
    } catch (e) {
   
    }

    const payload = buildFingerprint();
    sendFingerprint(payload);

    try {
      sessionStorage.setItem(SENT_FLAG_KEY, "1");
    } catch (e) {}
  }

  if (document.readyState === "complete") {
    init();
  } else {
    window.addEventListener("load", init);
  }
})();
