document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("navToggle");
  const menu = document.getElementById("navMenu");

  if (toggle && menu) {
    toggle.addEventListener("click", () => {
      const isOpen = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (menu.classList.contains("open")) {
          menu.classList.remove("open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    });
  }

  const userToggle = document.getElementById("userToggle");
  const userMenu = document.getElementById("userMenu");

  const closeUserMenu = () => {
    if (userMenu && userMenu.classList.contains("open")) {
      userMenu.classList.remove("open");
      if (userToggle) {
        userToggle.setAttribute("aria-expanded", "false");
      }
    }
  };

  if (userToggle && userMenu) {
    userToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      const isOpen = userMenu.classList.toggle("open");
      userToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    document.addEventListener("click", (event) => {
      if (!userMenu.contains(event.target) && !userToggle.contains(event.target)) {
        closeUserMenu();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeUserMenu();
      }
    });
  }

  const flashMessages = document.querySelectorAll(".flash");
  flashMessages.forEach((flash) => {
    setTimeout(() => {
      flash.classList.add("flash--hide");
    }, 4500);
  });
});
