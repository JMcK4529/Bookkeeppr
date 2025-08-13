// Auto-dismiss existing flash after 15 seconds
setTimeout(() => {
    const msg = document.querySelector(".flash-banner");
    if (msg) msg.remove();
}, 15000);

// Expand/collapse flash message on click (but not when clicking the ❌)
document.addEventListener("click", (e) => {
    const msg = e.target.closest(".flash-banner");
    if (!msg) return;

    const isDismiss = e.target.classList.contains("dismiss-btn");
    if (!isDismiss) {
        msg.classList.toggle("expanded");
    }
});