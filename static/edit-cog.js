document.addEventListener("DOMContentLoaded", () => {
  const cogButton = document.createElement("button");
  cogButton.textContent = "⚙️";
  cogButton.className = "cog-btn";
  cogButton.type = "button";

  document.querySelectorAll(".clickable-row").forEach(row => {
    const cell = row.querySelector("td.cog-col");
    cell.style.position = "relative";

    row.addEventListener("mouseenter", () => {
      cogButton.dataset.href = row.dataset.href;
      cell.innerHTML = "";
      cell.appendChild(cogButton);
    });

    row.addEventListener("mouseleave", () => {
      cell.innerHTML = "";
    });
  });

  cogButton.addEventListener("click", (e) => {
    e.stopPropagation();
    window.location.href = cogButton.dataset.href;
  });
});