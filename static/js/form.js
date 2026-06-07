// Public Form Logic - Store Data Collection System

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("customerForm");
  const storeSelect = document.getElementById("store_id"); // hidden input
  const mobileInput = document.getElementById("mobile_number");
  const issueSelect = document.getElementById("invitation_card_issue");
  const issueContainer = document.getElementById("issue-description-container");
  const issueTextarea = document.getElementById("issue_description");
  const successToast = document.getElementById("successToast");
  const successModal = document.getElementById("successModal");
  const modalCloseBtn = document.getElementById("modalCloseBtn");
  const submitBtn = document.getElementById("submitBtn");

  // Custom Store Selector Dialog Modal Elements
  const storeTrigger = document.getElementById("store_trigger");
  const storeSelectModal = document.getElementById("storeSelectModal");
  const storeModalCloseBtn = document.getElementById("storeModalCloseBtn");
  const storeSearchInput = document.getElementById("storeSearchInput");
  const storeOptionsList = document.getElementById("storeOptionsList");
  const selectedTextSpan = storeTrigger ? storeTrigger.querySelector(".selected-text") : null;

  let allStores = [];
  let selectedStoreId = "";

  // Fetch stores list from Backend REST API
  async function fetchStores() {
    try {
      const response = await fetch("/api/stores");
      const result = await response.json();
      
      if (result.success && Array.isArray(result.data)) {
        allStores = result.data;
        renderStoreOptions(allStores);
      } else {
        console.error("Failed to load stores from API:", result.message);
        if (storeOptionsList) {
          storeOptionsList.innerHTML = `
            <div class="store-no-results">
              <p style="margin-bottom: 8px;">Unable to load stores. Please try again.</p>
              <button type="button" class="btn btn-secondary" id="storeRetryBtn" style="padding: 6px 12px; font-size: 0.8rem; height: auto;">Retry Connection</button>
            </div>
          `;
          const retryBtn = document.getElementById("storeRetryBtn");
          if (retryBtn) {
            retryBtn.addEventListener("click", (e) => {
              e.stopPropagation();
              storeOptionsList.innerHTML = '<div class="store-loading">Loading stores...</div>';
              fetchStores();
            });
          }
        }
      }
    } catch (error) {
      console.error("Network error fetching stores:", error);
      if (storeOptionsList) {
        storeOptionsList.innerHTML = `
          <div class="store-no-results">
            <p style="margin-bottom: 8px;">Error connecting to server. Please try again.</p>
            <button type="button" class="btn btn-secondary" id="storeRetryBtn" style="padding: 6px 12px; font-size: 0.8rem; height: auto;">Retry Connection</button>
          </div>
        `;
        const retryBtn = document.getElementById("storeRetryBtn");
        if (retryBtn) {
          retryBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            storeOptionsList.innerHTML = '<div class="store-loading">Loading stores...</div>';
            fetchStores();
          });
        }
      }
    }
  }

  function renderStoreOptions(storesList) {
    if (!storeOptionsList) return;
    
    if (storesList.length === 0) {
      storeOptionsList.innerHTML = '<div class="store-no-results">No stores found matching search</div>';
      return;
    }

    storeOptionsList.innerHTML = "";
    storesList.forEach(store => {
      const item = document.createElement("div");
      item.className = "store-option-item";
      if (store.id.toString() === selectedStoreId.toString()) {
        item.classList.add("selected");
      }
      item.textContent = store.store_name;
      item.addEventListener("click", () => {
        selectStore(store);
      });
      storeOptionsList.appendChild(item);
    });
  }

  function selectStore(store) {
    selectedStoreId = store.id.toString();
    if (storeSelect) {
      storeSelect.value = selectedStoreId;
    }
    if (selectedTextSpan) {
      selectedTextSpan.textContent = store.store_name;
      selectedTextSpan.classList.remove("text-muted");
    }
    
    // Clear validation error if any
    if (storeTrigger) {
      clearError(storeTrigger);
    }
    
    // Update selected class in modal
    if (storeOptionsList) {
      const items = storeOptionsList.querySelectorAll(".store-option-item");
      items.forEach(item => {
        if (item.textContent === store.store_name) {
          item.classList.add("selected");
        } else {
          item.classList.remove("selected");
        }
      });
    }

    closeStoreModal();
  }

  function openStoreModal() {
    if (!storeSelectModal) return;
    storeSelectModal.classList.add("show");
    if (storeSearchInput) {
      storeSearchInput.value = "";
    }
    renderStoreOptions(allStores);
    setTimeout(() => {
      if (storeSearchInput) {
        storeSearchInput.focus();
      }
    }, 100);
  }

  function closeStoreModal() {
    if (storeSelectModal) {
      storeSelectModal.classList.remove("show");
    }
  }

  // Bind Custom Select events
  if (storeTrigger) {
    storeTrigger.addEventListener("click", openStoreModal);
    storeTrigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openStoreModal();
      }
    });
  }

  if (storeModalCloseBtn) {
    storeModalCloseBtn.addEventListener("click", closeStoreModal);
  }

  if (storeSelectModal) {
    storeSelectModal.addEventListener("click", (e) => {
      if (e.target === storeSelectModal) {
        closeStoreModal();
      }
    });
  }

  // Close modal on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeStoreModal();
    }
  });

  // Search filter
  if (storeSearchInput) {
    storeSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      const filtered = allStores.filter(store => 
        store.store_name.toLowerCase().includes(query)
      );
      renderStoreOptions(filtered);
    });
  }

  // Toggle display of Issue Description conditionally
  if (issueSelect) {
    issueSelect.addEventListener("change", () => {
      if (issueSelect.value === "Yes") {
        if (issueContainer) issueContainer.classList.add("show");
        if (issueTextarea) issueTextarea.setAttribute("required", "true");
      } else {
        if (issueContainer) issueContainer.classList.remove("show");
        if (issueTextarea) {
          issueTextarea.removeAttribute("required");
          issueTextarea.value = "";
          clearError(issueTextarea);
        }
      }
    });
  }

  // Numeric only clean filter for mobile number
  if (mobileInput) {
    mobileInput.addEventListener("input", (e) => {
      e.target.value = e.target.value.replace(/[^0-9]/g, "");
      if (e.target.value.length === 10) {
        clearError(mobileInput);
      }
    });
  }

  // Clear errors dynamically on input changes
  if (form) {
    const formInputs = form.querySelectorAll(".form-control");
    formInputs.forEach(input => {
      input.addEventListener("input", () => {
        if (input.value && input.value.trim() !== "") {
          clearError(input);
        }
      });
      input.addEventListener("change", () => {
        if (input.value && input.value.trim() !== "") {
          clearError(input);
        }
      });
    });
  }

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
      const errorMsg = formGroup.querySelector(".error-msg");
      if (errorMsg) {
        errorMsg.style.display = "none";
      }
    }
  }

  // Frontend validations
  function validateForm() {
    let isValid = true;
    let firstInvalidCard = null;

    if (!storeSelect.value) {
      showError(storeSelect, "store-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-store");
    } else {
      clearError(storeSelect);
    }

    const nameInput = document.getElementById("customer_name");
    if (!nameInput.value.trim()) {
      showError(nameInput, "name-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-customer-details");
    } else {
      clearError(nameInput);
    }

    const mobileValue = mobileInput.value.trim();
    if (!mobileValue || mobileValue.length !== 10 || !/^[0-9]{10}$/.test(mobileValue)) {
      showError(mobileInput, "mobile-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-customer-details");
    } else {
      clearError(mobileInput);
    }

    const regStatus = document.getElementById("app_registration_status");
    if (!regStatus.value) {
      showError(regStatus, "registration-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-registration");
    } else {
      clearError(regStatus);
    }

    if (!issueSelect.value) {
      showError(issueSelect, "issue-option-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-issue-option");
    } else {
      clearError(issueSelect);
    }

    if (issueSelect.value === "Yes" && !issueTextarea.value.trim()) {
      showError(issueTextarea, "issue-desc-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-issue-option");
    } else {
      clearError(issueTextarea);
    }

    if (firstInvalidCard) {
      firstInvalidCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    return isValid;
  }

  // Handle resets
  form.addEventListener("reset", () => {
    const formGroups = form.querySelectorAll(".form-group");
    formGroups.forEach(group => group.classList.remove("has-error"));
    
    const errorMsgs = form.querySelectorAll(".error-msg");
    errorMsgs.forEach(msg => msg.style.display = "none");
    
    issueContainer.classList.remove("show");
    issueTextarea.removeAttribute("required");

    // Reset Custom Store Selector
    selectedStoreId = "";
    if (storeSelect) {
      storeSelect.value = "";
    }
    if (selectedTextSpan) {
      selectedTextSpan.textContent = "Select a store";
      selectedTextSpan.classList.add("text-muted");
    }
  });

  // Handle Close Success Modal
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", () => {
      if (successModal) successModal.classList.remove("show");
      if (form) form.reset();
    });
  }

  // Handle AJAX submissions
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      const payload = {
        store_id: storeSelect ? storeSelect.value : "",
        customer_name: document.getElementById("customer_name") ? document.getElementById("customer_name").value : "",
        mobile_number: mobileInput ? mobileInput.value : "",
        app_registration_status: document.getElementById("app_registration_status") ? document.getElementById("app_registration_status").value : "",
        invitation_issue: issueSelect ? issueSelect.value : "",
        issue_description: issueTextarea ? issueTextarea.value : ""
      };

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting response...";
      }

      try {
        const response = await fetch("/api/submit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Show Animated Success Modal
          if (successModal) successModal.classList.add("show");
          
          // Secondary Toast Notification
          if (successToast) {
            successToast.classList.add("show");
            setTimeout(() => {
              successToast.classList.remove("show");
            }, 3000);
          }
        } else {
          alert("Submission Failed: " + (result.message || "Unknown error occurred."));
        }
      } catch (error) {
        console.error("Submissions error:", error);
        alert("Submission error. Could not connect to API server.");
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit Response";
        }
      }
    });
  }

  // Run stores loader
  fetchStores();
});
