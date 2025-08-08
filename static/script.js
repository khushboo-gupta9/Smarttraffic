document.addEventListener("DOMContentLoaded", () => {
  const lights = document.querySelectorAll(".signal-box .light");
  const countdownEl = document.getElementById("countdown");

  // Load sound files
  const redSound = document.getElementById("redSound");
  const yellowSound = document.getElementById("yellowSound");
  const greenSound = document.getElementById("greenSound");

  let lastPlayedColor = {};

  // 🟢 Poll backend every second for live signal status
  setInterval(() => {
    fetch("/get_status")
      .then(res => res.json())
      .then(data => {
        updateLights(data);
        countdownEl.textContent = data.countdown;
      });
  }, 1000);

  function updateLights(data) {
    lights.forEach(light => {
      const dir = light.parentElement.id;
      light.className = "light"; // reset

      if (data[dir]) {
        light.classList.add(data[dir]);

        // Play sound only if color changes
        if (lastPlayedColor[dir] !== data[dir]) {
          if (data[dir] === "red") redSound.play();
          else if (data[dir] === "yellow") yellowSound.play();
          else if (data[dir] === "green") greenSound.play();
          lastPlayedColor[dir] = data[dir];
        }
      }
    });
  }

  // Mode buttons
  document.querySelectorAll(".mode").forEach(btn => {
    btn.addEventListener("click", () => {
      fetch("/set_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: btn.dataset.mode })
      });
      document.querySelectorAll(".mode").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  // Start / Stop
  document.querySelector(".start").addEventListener("click", () => {
    fetch("/start", { method: "POST" });
  });
  document.querySelector(".stop").addEventListener("click", () => {
    fetch("/stop", { method: "POST" });
  });

  // Manual timer slider
  const timerRange = document.querySelector("input[type='range']");
  const timerLabel = timerRange.nextElementSibling;
  timerRange.addEventListener("input", () => {
    timerLabel.textContent = `${timerRange.value}s`;
    fetch("/set_timer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ time: timerRange.value })
    });
  });

  // Live camera
  const video = document.getElementById("video");
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => video.srcObject = stream)
      .catch(err => console.error("Camera error:", err));
  }

  // Capture photo
  document.getElementById("captureBtn").addEventListener("click", () => {
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL("image/png");
    fetch("/save_image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl })
    })
    .then(res => res.text())
    .then(msg => alert("📸 " + msg))
    .catch(() => alert("❌ Capture failed"));
  });

  // Siren detection
  const sirenSound = document.getElementById("sirenSound");
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        source.connect(analyser);

        function detectSiren() {
          analyser.getByteFrequencyData(dataArray);
          let detected = false;
          for (let i = 0; i < dataArray.length; i++) {
            const freq = (i * audioCtx.sampleRate / 2) / dataArray.length;
            if (freq >= 700 && freq <= 1500 && dataArray[i] > 200) {
              detected = true;
              break;
            }
          }
          if (detected && (!window.lastSirenTime || Date.now() - window.lastSirenTime > 10000)) {
            window.lastSirenTime = Date.now();
            fetch("/emergency_detected", { method: "POST" });
            sirenSound.play();
          }
          requestAnimationFrame(detectSiren);
        }
        detectSiren();
      })
      .catch(err => console.error("Mic error:", err));
  }
});
