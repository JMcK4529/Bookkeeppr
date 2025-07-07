let currentPage = 1;

function renderPage(page, perPage) {
    const rows = document.querySelectorAll("#results table tbody tr");
    const totalPages = Math.ceil(rows.length / perPage);
    currentPage = page;
    rows.forEach((row, index) => {
        row.style.display = (index >= (page - 1) * perPage && index < page * perPage) ? "" : "none";
    });
    updatePaginationControls(totalPages, perPage);
}

function updatePaginationControls(totalPages, perPage) {
    const container = document.getElementById("pagination-controls");
    container.innerHTML = "";

    if (totalPages <= 1) return;

    if (currentPage > 1) {
        const prev = document.createElement("button");
        prev.textContent = "Previous";
        prev.onclick = () => renderPage(currentPage - 1, perPage);
        container.appendChild(prev);
    }

    const status = document.createElement("span");
    status.textContent = ` Page ${currentPage} of ${totalPages} `;
    container.appendChild(status);

    if (currentPage < totalPages) {
        const next = document.createElement("button");
        next.textContent = "Next";
        next.onclick = () => renderPage(currentPage + 1, perPage);
        container.appendChild(next);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const PER_PAGE = window.PAGINATE_PER_PAGE || 3;
    renderPage(1, PER_PAGE);
});