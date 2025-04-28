document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ tournament-runner.js loaded");

  const runBtn = document.getElementById("runScriptsBtn");
  const output = document.getElementById("output");
  const spinner = document.getElementById("spinner");

  if (!runBtn || !output || !spinner) {
    console.error("❌ Missing DOM elements for run script");
    return;
  }

  runBtn.addEventListener("click", async () => {
    const courseName = document.getElementById("courseName")?.value || "";
    const courseDate = document.getElementById("courseDate")?.value || "";

    const payload = {
      course_name: courseName,
      course_date: courseDate
    };

    spinner.style.display = "block";
    output.textContent = "";

    try {
      const response = await fetch("/golf_score_calculator/run_tournament_scripts_v2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errText}`);
      }

      const result = await response.json();
      spinner.style.display = "none";

      if (result.logs?.length) {
        output.textContent = result.logs.join("\n");
      }

      if (result.log_path) {
        const link = document.createElement("a");
        link.href = result.log_path;
        link.textContent = "📥 Download Full Log";
        link.download = "";
        link.style.display = "block";
        link.style.marginTop = "10px";
        output.appendChild(link);
      }

    } catch (err) {
      spinner.style.display = "none";
      output.textContent = "❌ Error: " + err.message;
    }
  });
});
