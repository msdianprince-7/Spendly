// main.js — students will add JavaScript here as features are built

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".profile-bar[data-percent]").forEach((bar) => {
        bar.style.width = `${bar.dataset.percent}%`;
    });
});
