// IMACID Logistics Performance - interactions front-end légères
document.addEventListener("DOMContentLoaded", function () {
    // Fermeture automatique des alertes après 5s
    document.querySelectorAll(".alert").forEach(function (alertEl) {
        setTimeout(function () {
            var alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (alert) alert.close();
        }, 5000);
    });
});

// Palette de couleurs partagée pour les graphiques Chart.js
const IMACID_COLORS = {
    blue: "#1d6fa5",
    darkBlue: "#0b2545",
    orange: "#f0862d",
    green: "#1f9d55",
    red: "#d64545",
    gray: "#9ca3af",
    palette: ["#1d6fa5", "#f0862d", "#1f9d55", "#d64545", "#7c3aed", "#0891b2", "#ca8a04", "#be185d"],
};
