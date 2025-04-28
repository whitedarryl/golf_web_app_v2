document.addEventListener("DOMContentLoaded", function () {
  console.log("🔥 DOM ready. JS starting");

  const playerInput = document.getElementById("playerName");
  const scoreInputs = document.querySelectorAll(".score-input");
  const submitButton = document.getElementById("submitBtn");
  const coursePar = parseInt(document.getElementById("coursePar").value);
  const outTotal = document.getElementById("outTotal");
  const inTotal = document.getElementById("inTotal");
  const grandTotal = document.getElementById("grandTotal");
  const adminToggle = document.getElementById("adminToggle");
  const adminControls = document.getElementById("adminControls");
  const toast = document.getElementById("toast");
  let playerNames = [];
  let awesomplete = null;

  if (adminToggle && adminControls) {
    adminToggle.addEventListener("click", () => {
      const isVisible = adminControls.style.display === "block";
      adminControls.style.display = isVisible ? "none" : "block";
      adminToggle.textContent = isVisible ? "👀 Show Admin Controls" : "🙈 Hide Admin Controls";
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.style.visibility = "visible";
    toast.style.opacity = 1;
    setTimeout(() => {
      toast.style.opacity = 0;
      toast.style.visibility = "hidden";
    }, 3000);
  }

  function calculateTotal(className, outputElement) {
    const inputs = document.querySelectorAll(`.score-input.${className}`);
    let total = 0;
    inputs.forEach((input) => {
      const value = parseInt(input.value);
      if (!isNaN(value)) {
        total += value;
      }
    });
    outputElement.textContent = total;
    return total;
  }

  function updateTotals() {
    const out = calculateTotal("front", outTotal);
    const back = calculateTotal("back", inTotal);
    grandTotal.textContent = out + back;
  }

  function resetForm() {
    playerInput.value = "";
    scoreInputs.forEach((input) => (input.value = ""));
    outTotal.textContent = "0";
    inTotal.textContent = "0";
    grandTotal.textContent = "0";
    submitButton.disabled = true;
    playerInput.focus();
  }

  if (scoreInputs.length) {
    scoreInputs.forEach((input, idx) => {
      input.addEventListener("input", function () {
        const val = this.value;
        if (/^[1-8]$/.test(val)) {
          if (idx + 1 < scoreInputs.length) {
            scoreInputs[idx + 1].focus();
          }
        } else {
          this.value = "";
        }
        updateTotals();
      });

      input.addEventListener("keydown", function (e) {
        if (e.key === "Backspace") {
          if (this.value === "" && idx > 0) {
            scoreInputs[idx - 1].focus();
          }
        } else if (e.key === "Enter") {
          if (!submitButton.disabled) {
            submitButton.click();
          }
        }
      });
    });
  }

  if (playerInput && scoreInputs.length && submitButton) {
    submitButton.disabled = true;

    function checkFormValidity() {
      const nameValid = playerInput.value.trim().length > 0;
      const scoresFilled = Array.from(scoreInputs).some(
        (input) => input.value.trim() !== ""
      );
      submitButton.disabled = !(nameValid && scoresFilled);
    }

    playerInput.addEventListener("input", checkFormValidity);
    scoreInputs.forEach((input) => {
      input.addEventListener("input", checkFormValidity);
    });

    fetch("/golf_score_calculator/get_names")
      .then(res => res.json())
      .then(data => {
        playerNames = data
          .filter(player => !player.is_submitted)
          .map(player => player.name);

        awesomplete = new Awesomplete(playerInput, {
          list: playerNames,
          minChars: 1,
          autoFirst: true
        });
        playerInput.awesomplete = awesomplete;

        const totalEl = document.getElementById("totalPlayers");
        const submittedEl = document.getElementById("submittedPlayers");
        const leftEl = document.querySelector(".players-left");

        totalEl.textContent = data.length;
        submittedEl.textContent = data.length - playerNames.length;
        leftEl.textContent = `✔️ ${playerNames.length} left`;
      })
      .catch(async (err) => {
        const raw = await err.response?.text?.();
        console.error("❌ Failed to load names:", err.message);
        if (raw) console.warn("🧾 Raw error response:\\n", raw);
      });

    playerInput.addEventListener("keydown", function (e) {
      const active = awesomplete.ul?.querySelector(".awesomplete__item--selected");
      if ((e.key === "Tab" || e.key === "Enter") && active) {
        e.preventDefault();
        awesomplete.select();
      }
    });

    playerInput.addEventListener("awesomplete-selectcomplete", function () {
      const hole1 = document.getElementById("hole-1");
      if (hole1) hole1.focus();
    });

    submitButton.addEventListener("click", () => {
      const scores = Array.from(scoreInputs).map(input => parseInt(input.value) || 0);
      const out = scores.slice(0, 9).reduce((sum, val) => sum + val, 0);
      const inn = scores.slice(9).reduce((sum, val) => sum + val, 0);
      const total = out + inn;

      const payload = {
        name: playerInput.value.trim(),
        scores: scores,
        out: out,
        inn: inn,
        total: total,
        par: coursePar
      };

      fetch(SUBMIT_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            const index = playerNames.indexOf(payload.name);
            if (index !== -1) {
              playerNames.splice(index, 1);
              awesomplete.list = playerNames;
            }

            const submittedEl = document.getElementById("submittedPlayers");
            const totalEl = document.getElementById("totalPlayers");
            const leftEl = document.querySelector(".players-left");

            let submitted = parseInt(submittedEl.textContent);
            let total = parseInt(totalEl.textContent);
            submitted += 1;
            submittedEl.textContent = submitted;
            const playersLeft = total - submitted;
            leftEl.textContent = `✔️ ${playersLeft} left`;

            showToast(data.message);
            resetForm();
          } else {
            showToast("❌ " + data.message);
          }
        })
        .catch(err => {
          console.error("❌ Submission error:", err);
          showToast("❌ Failed to submit score.");
        });
    });
  }

  const simulateBtn = document.getElementById("simulateBtn");
  if (simulateBtn) {
    simulateBtn.addEventListener("click", async () => {
      console.log("🔥 CLEAN SIMULATION TRIGGERED");

      if (playerNames.length === 0) {
        alert("✅ All players already have scores!");
        return;
      }

      for (let name of playerNames) {
        const scores = Array.from({ length: 18 }, () => Math.floor(Math.random() * 7) + 2);
        console.log("🔢 Generated scores:", scores);

        const out = scores.slice(0, 9).reduce((a, b) => a + b, 0);
        const inn = scores.slice(9).reduce((a, b) => a + b, 0);
        const total = out + inn;

        const [first_name, ...rest] = name.split(" ");
        const last_name = rest.join(" ");

        const payload = {
          name,
          first_name,
          last_name,
          scores,
          out,
          inn,
          total
        };

        console.log("📦 Payload being submitted:", payload);

        try {
          const res = await fetch("/golf_score_calculator/golf_score_calculator/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          const data = await res.json();
          console.log(`📨 Submitted: ${name} → ${data.message}`);
        } catch (err) {
          console.error(`❌ Failed to submit for ${name}`, err);
        }
      }

      alert("✅ Dummy data submission complete!");
    });
  }

  const resetScoresBtn = document.getElementById("resetScoresBtn");
  if (resetScoresBtn) {
    resetScoresBtn.addEventListener("click", () => {
      if (!confirm("Are you sure you want to DELETE ALL SCORES?")) return;

      fetch("/golf_score_calculator/reset_scores", {
        method: "POST"
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("✅ All scores cleared.");
            window.location.reload();
          } else {
            console.error("Reset failed:", data.error);
            alert("❌ Failed to reset scores.");
          }
        })
        .catch(err => {
          console.error("Reset error:", err);
          alert("❌ Reset request failed.");
        });
    });
  }

  console.log("✅ simulateBtn listener attached");

  const exportBtn = document.getElementById("exportBtn");
  const progressBar = document.getElementById("exportBar");
  const exportProgress = document.getElementById("exportProgress");
  
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      exportBtn.disabled = true;
      exportProgress.style.display = "block";
      progressBar.value = 30;
  
      fetch("/golf_score_calculator/export_to_excel", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          progressBar.value = 100;
          alert(data.message || "✅ Export complete!");
        })
        .catch(err => {
          console.error("❌ Export error:", err);
          alert("❌ Failed to export to Excel.");
        })
        .finally(() => {
          exportBtn.disabled = false;
          exportProgress.style.display = "none";
        });
    });
  }
  
  

});


