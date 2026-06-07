// Form Logic - Store Data Collection System

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("customerForm");
  const storeSelect = document.getElementById("store_id");
  const mobileInput = document.getElementById("mobile_number");
  const issueSelect = document.getElementById("invitation_card_issue");
  const issueContainer = document.getElementById("issue-description-container");
  const issueTextarea = document.getElementById("issue_description");
  const successToast = document.getElementById("successToast");
  const submitBtn = document.getElementById("submitBtn");

  // Fetch stores from backend and populate dropdown
  async function fetchStores() {
    try {
      const response = await fetch("/stores");
      const result = await response.json();
      
      if (result.success && Array.isArray(result.data)) {
        // Clear default options, keeping only placeholder
        storeSelect.innerHTML = '<option value="" disabled selected>Select a store</option>';
        
        result.data.forEach(store => {
          const option = document.createElement("option");
          option.value = store.id;
          option.textContent = store.store_name;
          storeSelect.appendChild(option);
        });
      } else {
        console.error("Failed to load stores from API:", result.message);
      }
    } catch (error) {
      console.error("Network error fetching stores:", error);
    }
  }

  // Handle dynamic field display for Invitation Issues
  issueSelect.addEventListener("change", () => {
    if (issueSelect.value === "Yes") {
      issueContainer.classList.add("show");
      issueTextarea.setAttribute("required", "true");
    } else {
      issueContainer.classList.remove("show");
      issueTextarea.removeAttribute("required");
      issueTextarea.value = ""; // Clear text
      clearError(issueTextarea);
    }
  });

  // Numbers-only helper for Mobile Input
  mobileInput.addEventListener("input", (e) => {
    // Replace any non-numeric character
    e.target.value = e.target.value.replace(/[^0-9]/g, "");
    if (e.target.value.length === 10) {
      clearError(mobileInput);
    }
  });

  // Clear errors dynamically when input is modified
  const formInputs = form.querySelectorAll(".form-control");
  formInputs.forEach(input => {
    input.addEventListener("input", () => {
      if (input.value.trim() !== "") {
        clearError(input);
      }
    });
    input.addEventListener("change", () => {
      if (input.value.trim() !== "") {
        clearError(input);
      }
    });
  });

  // Error state helpers
  function showError(input, errorElementId) {
    const formGroup = input.closest(".form-group");
    if (formGroup) {
      formGroup.classList.add("has-error");
    }
    const errorEl = document.getElementById(errorElementId);
    if (errorEl) {
      errorEl.style.display = "flex";
    }
  }

  function clearError(input) {
    const formGroup = input.closest(".form-group");
    if (formGroup) {
      formGroup.classList.remove("has-error");
    }
    
    // Find matching error elements within parent
    const card = input.closest(".card");
    if (card) {
      const errorMsg = card.querySelector(".error-msg");
      if (errorMsg) {
        errorMsg.style.display = "none";
      }
    }
  }

  // Custom Form Validation
  function validateForm() {
    let isValid = true;
    let firstInvalidCard = null;

    // Validate Store
    if (!storeSelect.value) {
      showError(storeSelect, "store-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-store");
    } else {
      clearError(storeSelect);
    }

    // Validate Customer Name
    const nameInput = document.getElementById("customer_name");
    if (!nameInput.value.trim()) {
      showError(nameInput, "name-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-name");
    } else {
      clearError(nameInput);
    }

    // Validate Mobile Number (10 digits)
    const mobileValue = mobileInput.value.trim();
    if (!mobileValue || mobileValue.length !== 10 || !/^[0-9]{10}$/.test(mobileValue)) {
      showError(mobileInput, "mobile-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-mobile");
    } else {
      clearError(mobileInput);
    }

    // Validate Registration Status
    const regStatus = document.getElementById("app_registration_status");
    if (!regStatus.value) {
      showError(regStatus, "registration-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-registration");
    } else {
      clearError(regStatus);
    }

    // Validate Issue option selection
    if (!issueSelect.value) {
      showError(issueSelect, "issue-option-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-issue-option");
    } else {
      clearError(issueSelect);
    }

    // Validate Issue Description (conditional)
    if (issueSelect.value === "Yes" && !issueTextarea.value.trim()) {
      showError(issueTextarea, "issue-desc-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-issue-option");
    } else {
      clearError(issueTextarea);
    }

    // Smooth scroll to the first invalid field card
    if (firstInvalidCard) {
      firstInvalidCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    return isValid;
  }

  // Handle Form Reset / Clear
  form.addEventListener("reset", () => {
    // Remove all error classes & hide description
    const formGroups = form.querySelectorAll(".form-group");
    formGroups.forEach(group => group.classList.remove("has-error"));
    
    const errorMsgs = form.querySelectorAll(".error-msg");
    errorMsgs.forEach(msg => msg.style.display = "none");
    
    issueContainer.classList.remove("show");
    issueTextarea.removeAttribute("required");
  });

  // Handle Form Submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Gather Form Data
    const payload = {
      store_id: storeSelect.value,
      customer_name: document.getElementById("customer_name").value,
      mobile_number: mobileInput.value,
      app_registration_status: document.getElementById("app_registration_status").value,
      invitation_card_issue: issueSelect.value,
      issue_description: issueTextarea.value
    };

    // Disable button to prevent double submit
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving Response...";

    try {
      const response = await fetch("/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Show success toast
        successToast.classList.add("show");
        
        // Hide success toast after 3.5s
        setTimeout(() => {
          successToast.classList.remove("show");
        }, 3500);

        // Reset form details
        form.reset();
        
      } else {
        alert("Submission Failed: " + (result.message || "Unknown error occurred."));
      }
    } catch (error) {
      console.error("Submission network error:", error);
      alert("Submission error. Could not connect to API server.");
    } finally {
      // Re-enable submit button
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Response";
    }
  });

  // Initialize page components
  fetchStores();
});
