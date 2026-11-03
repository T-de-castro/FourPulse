(() => {
    const target = document.getElementById("live-clock");
    const formatter = new Intl.DateTimeFormat("pt-BR", {
        weekday: "short",
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });

    const updateClock = () => {
        if (target) {
            target.textContent = formatter.format(new Date()).replace(",", " ·");
        }
    };

    updateClock();
    window.setInterval(updateClock, 30_000);
})();
