// Public Form Logic - Store Data Collection System

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("customerForm");
  const storeSelect = document.getElementById("store_id"); // hidden input
  const mobileInput = document.getElementById("mobile_number");
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

  // Custom Registration Status Elements
  const regStatusTrigger = document.getElementById("reg_status_trigger");
  const regStatusModal = document.getElementById("regStatusModal");
  const regStatusCloseBtn = document.getElementById("regStatusCloseBtn");
  const regStatusSearchInput = document.getElementById("regStatusSearchInput");
  const regStatusOptionsList = document.getElementById("regStatusOptionsList");
  const regStatusInput = document.getElementById("app_registration_status"); // hidden input
  const regStatusText = regStatusTrigger ? regStatusTrigger.querySelector(".selected-text") : null;

  // Custom Invitation Elements
  const invitationTrigger = document.getElementById("invitation_trigger");
  const invitationModal = document.getElementById("invitationModal");
  const invitationCloseBtn = document.getElementById("invitationCloseBtn");
  const invitationSearchInput = document.getElementById("invitationSearchInput");
  const invitationOptionsList = document.getElementById("invitationOptionsList");
  const invitationInput = document.getElementById("invitation_card_issue"); // hidden input
  const invitationText = invitationTrigger ? invitationTrigger.querySelector(".selected-text") : null;

  const issueContainer = document.getElementById("issue-description-container");
  const issueTextarea = document.getElementById("issue_description");

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

  // --- App Registration Status Custom Select Logic ---
  function openRegStatusModal() {
    if (!regStatusModal) return;
    regStatusModal.classList.add("show");
    if (regStatusSearchInput) {
      regStatusSearchInput.value = "";
    }
    const val = regStatusInput ? regStatusInput.value : "";
    if (regStatusOptionsList) {
      const items = regStatusOptionsList.querySelectorAll(".store-option-item");
      items.forEach(item => {
        item.style.display = "";
        if (item.getAttribute("data-value") === val) {
          item.classList.add("selected");
        } else {
          item.classList.remove("selected");
        }
      });
    }
    setTimeout(() => {
      if (regStatusSearchInput) {
        regStatusSearchInput.focus();
      }
    }, 100);
  }

  function closeRegStatusModal() {
    if (regStatusModal) {
      regStatusModal.classList.remove("show");
    }
  }

  function selectRegStatus(value, text) {
    if (regStatusInput) {
      regStatusInput.value = value;
    }
    if (regStatusText) {
      regStatusText.textContent = text;
      regStatusText.classList.remove("text-muted");
    }
    if (regStatusTrigger) {
      clearError(regStatusTrigger);
    }
    closeRegStatusModal();
  }

  if (regStatusTrigger) {
    regStatusTrigger.addEventListener("click", openRegStatusModal);
    regStatusTrigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openRegStatusModal();
      }
    });
  }

  if (regStatusCloseBtn) {
    regStatusCloseBtn.addEventListener("click", closeRegStatusModal);
  }

  if (regStatusModal) {
    regStatusModal.addEventListener("click", (e) => {
      if (e.target === regStatusModal) {
        closeRegStatusModal();
      }
    });
  }

  if (regStatusSearchInput) {
    regStatusSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (regStatusOptionsList) {
        const items = regStatusOptionsList.querySelectorAll(".store-option-item");
        items.forEach(item => {
          const text = item.textContent.toLowerCase();
          if (text.includes(query)) {
            item.style.display = "";
          } else {
            item.style.display = "none";
          }
        });
      }
    });
  }

  if (regStatusOptionsList) {
    const items = regStatusOptionsList.querySelectorAll(".store-option-item");
    items.forEach(item => {
      item.addEventListener("click", () => {
        selectRegStatus(item.getAttribute("data-value"), item.textContent);
      });
    });
  }

  // --- Invitation Card Details Custom Select Logic ---
  function openInvitationModal() {
    if (!invitationModal) return;
    invitationModal.classList.add("show");
    if (invitationSearchInput) {
      invitationSearchInput.value = "";
    }
    const val = invitationInput ? invitationInput.value : "";
    if (invitationOptionsList) {
      const items = invitationOptionsList.querySelectorAll(".store-option-item");
      items.forEach(item => {
        item.style.display = "";
        if (item.getAttribute("data-value") === val) {
          item.classList.add("selected");
        } else {
          item.classList.remove("selected");
        }
      });
    }
    setTimeout(() => {
      if (invitationSearchInput) {
        invitationSearchInput.focus();
      }
    }, 100);
  }

  function closeInvitationModal() {
    if (invitationModal) {
      invitationModal.classList.remove("show");
    }
  }

  function selectInvitation(value, text) {
    if (invitationInput) {
      invitationInput.value = value;
    }
    if (invitationText) {
      invitationText.textContent = text;
      invitationText.classList.remove("text-muted");
    }
    if (invitationTrigger) {
      clearError(invitationTrigger);
    }
    
    // Toggle display of Issue Description conditionally
    if (value === "Yes") {
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
    
    closeInvitationModal();
  }

  if (invitationTrigger) {
    invitationTrigger.addEventListener("click", openInvitationModal);
    invitationTrigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openInvitationModal();
      }
    });
  }

  if (invitationCloseBtn) {
    invitationCloseBtn.addEventListener("click", closeInvitationModal);
  }

  if (invitationModal) {
    invitationModal.addEventListener("click", (e) => {
      if (e.target === invitationModal) {
        closeInvitationModal();
      }
    });
  }

  if (invitationSearchInput) {
    invitationSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (invitationOptionsList) {
        const items = invitationOptionsList.querySelectorAll(".store-option-item");
        items.forEach(item => {
          const text = item.textContent.toLowerCase();
          if (text.includes(query)) {
            item.style.display = "";
          } else {
            item.style.display = "none";
          }
        });
      }
    });
  }

  if (invitationOptionsList) {
    const items = invitationOptionsList.querySelectorAll(".store-option-item");
    items.forEach(item => {
      item.addEventListener("click", () => {
        selectInvitation(item.getAttribute("data-value"), item.textContent);
      });
    });
  }

  // Close all modals on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeStoreModal();
      closeRegStatusModal();
      closeInvitationModal();
    }
  });

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
      showError(storeTrigger, "store-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-store");
    } else {
      clearError(storeTrigger);
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

    if (!regStatusInput.value) {
      showError(regStatusTrigger, "registration-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-registration");
    } else {
      clearError(regStatusTrigger);
    }

    if (!invitationInput.value) {
      showError(invitationTrigger, "issue-option-error");
      isValid = false;
      if (!firstInvalidCard) firstInvalidCard = document.getElementById("card-issue-option");
    } else {
      clearError(invitationTrigger);
    }

    if (invitationInput.value === "Yes" && !issueTextarea.value.trim()) {
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
    if (issueTextarea) {
      issueTextarea.removeAttribute("required");
    }

    // Reset Custom Store Selector
    selectedStoreId = "";
    if (storeSelect) {
      storeSelect.value = "";
    }
    if (selectedTextSpan) {
      selectedTextSpan.textContent = "Select a store";
      selectedTextSpan.classList.add("text-muted");
    }

    // Reset Custom App Registration Status
    if (regStatusInput) {
      regStatusInput.value = "";
    }
    if (regStatusText) {
      regStatusText.textContent = "Choose registration status";
      regStatusText.classList.add("text-muted");
    }

    // Reset Custom Invitation Issues
    if (invitationInput) {
      invitationInput.value = "";
    }
    if (invitationText) {
      invitationText.textContent = "Choose option";
      invitationText.classList.add("text-muted");
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
        app_registration_status: regStatusInput ? regStatusInput.value : "",
        invitation_issue: invitationInput ? invitationInput.value : "",
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
