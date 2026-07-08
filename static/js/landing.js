(function () {
    var VIDEO_ID = "dQw4w9WgXcQ"; // placeholder — replace with the real demo video ID

    var openBtn = document.getElementById("how-it-works-btn");
    var closeBtn = document.getElementById("how-it-works-close");
    var modal = document.getElementById("how-it-works-modal");
    var iframe = document.getElementById("how-it-works-iframe");

    if (!openBtn || !closeBtn || !modal || !iframe) return;

    function openModal(event) {
        event.preventDefault();
        iframe.src = "https://www.youtube.com/embed/" + VIDEO_ID + "?autoplay=1";
        modal.hidden = false;
    }

    function closeModal() {
        modal.hidden = true;
        iframe.src = "";
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", function (event) {
        if (event.target === modal) closeModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !modal.hidden) closeModal();
    });
})();
