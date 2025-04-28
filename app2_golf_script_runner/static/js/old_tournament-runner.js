document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ tournament-runner.js loaded");

  const form = document.getElementById("tourneyRunner");
  const runBtn = document.getElementById("runScriptsBtn");
  const spinner = document.getElementById("spinner");
  const output = document.getElementById("output");

  if (!form || !runBtn) {
    console.warn("🚫 Form or button not found in DOM.");
    return;
  }

  console.log("✅ Found #tourneyRunner element");
  console.log("✅ Run Scripts button found");

  runBtn.addEventListener("click", async () => {
    console.log("🟢 Run Scripts button clicked!");

    const courseName = document.getElementById("courseName")?.value;
    const courseDate = document.getElementById("courseDate")?.value;

    if (!courseName || !courseDate) {
      output.textContent = "⚠️ Please fill out both Course Name and Date.";
      return;
    }

    const formData = new FormData();
    formData.append("course_name", courseName);
    formData.append("course_date", courseDate);

    spinner.style.display = "block";
    output.textContent = "";

    try {
      const response = await fetch("/golf_score_calculator/run_tournament_scripts", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      spinner.style.display = "none";

      if (result.success) {
        console.log("✅ Server responded with success:", result);
        output.textContent = result.logs.join("\n") || "✅ Scripts completed.";
      } else {
        console.error("❌ Server responded with failure:", result.message);
        output.textContent = "❌ Error: " + (result.message || "Unknown error");
      }
    } catch (err) {
      spinner.style.display = "none";
      console.error("🔥 Fetch failed:", err);
      output.textContent = "🔥 Fetch Error: " + err.message;
    }
  });
});
