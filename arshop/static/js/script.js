// Cart functionality
document.addEventListener("DOMContentLoaded", function () {
  // Quantity buttons
  const quantityButtons = document.querySelectorAll(".quantity-btn");
  quantityButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const input = this.parentElement.querySelector(".quantity-input");
      let quantity = parseInt(input.value);

      if (this.classList.contains("decrease")) {
        if (quantity > 1) {
          input.value = quantity - 1;
        }
      } else {
        input.value = quantity + 1;
      }
    });
  });

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });

  // Form validation
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const requiredFields = this.querySelectorAll("[required]");
      let valid = true;

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          valid = false;
          field.classList.add("border-red-500");
        } else {
          field.classList.remove("border-red-500");
        }
      });

      if (!valid) {
        e.preventDefault();
        alert("Please fill in all required fields.");
      }
    });
  });

  // Product search
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("keyup", function () {
      const searchTerm = this.value.toLowerCase();
      const products = document.querySelectorAll(".product-card");

      products.forEach((product) => {
        const productName = product
          .querySelector("h3")
          .textContent.toLowerCase();
        if (productName.includes(searchTerm)) {
          product.style.display = "block";
        } else {
          product.style.display = "none";
        }
      });
    });
  }
});

// Toast notifications
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
    type === "success"
      ? "bg-green-500"
      : type === "error"
      ? "bg-red-500"
      : "bg-blue-500"
  }`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}
