// Admin Logic - Store Data Collection System

document.addEventListener("DOMContentLoaded", () => {
  // Determine if we are on the login page or the dashboard page
  const loginForm = document.getElementById("loginForm");
  const dashboardContainer = document.querySelector(".dashboard-container");

  if (loginForm) {
    initLoginPage();
  } else if (dashboardContainer) {
    initDashboardPage();
  }

  // ====================================================
  // LOGIN PAGE LOGIC
  // ====================================================
  function initLoginPage() {
    // If token already exists, redirect to dashboard automatically
    const existingToken = localStorage.getItem("admin_token");
    if (existingToken) {
      window.location.href = "/admin-dashboard";
      return;
    }

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const loginBtn = document.getElementById("loginBtn");
    const errorContainer = document.getElementById("login-error-container");

    // Clear validation error styling on input
    [usernameInput, passwordInput].forEach(input => {
      input.addEventListener("input", () => {
        clearInputError(input);
        errorContainer.style.display = "none";
      });
    });

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      let isValid = true;
      errorContainer.style.display = "none";

      // Simple UI validations
      if (!usernameInput.value.trim()) {
        showInputError(usernameInput, "username-error");
        isValid = false;
      }
      
      if (!passwordInput.value.trim()) {
        showInputError(passwordInput, "password-error");
        isValid = false;
      }

      if (!isValid) return;

      // Prepare payload
      const payload = {
        username: usernameInput.value.trim(),
        password: passwordInput.value
      };

      // Set loading state
      loginBtn.disabled = true;
      loginBtn.textContent = "Authenticating...";

      try {
        const response = await fetch("/admin-login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Store token in localStorage
          localStorage.setItem("admin_token", result.token);
          // Redirect to dashboard
          window.location.href = "/admin-dashboard";
        } else {
          // Display error badge
          errorContainer.style.display = "flex";
          passwordInput.value = ""; // Clear password for security
        }
      } catch (error) {
        console.error("Login request error:", error);
        alert("An error occurred. Unable to contact authentication server.");
      } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "Login to Dashboard";
      }
    });

    function showInputError(input, errorId) {
      const formGroup = input.closest(".form-group");
      if (formGroup) formGroup.classList.add("has-error");
      const errorMsg = document.getElementById(errorId);
      if (errorMsg) errorMsg.style.display = "flex";
    }

    function clearInputError(input) {
      const formGroup = input.closest(".form-group");
      if (formGroup) formGroup.classList.remove("has-error");
      
      const card = input.closest(".card");
      if (card) {
        const errorMsg = card.querySelector(".error-msg");
        if (errorMsg) errorMsg.style.display = "none";
      }
    }
  }

  // ====================================================
  // DASHBOARD PAGE LOGIC
  // ====================================================
  function initDashboardPage() {
    const token = localStorage.getItem("admin_token");
    
    // Auth Check: Redirect to login if token is missing
    if (!token) {
      window.location.href = "/admin-login";
      return;
    }

    // Dashboard Selectors
    const filterStore = document.getElementById("filter-store");
    const filterStatus = document.getElementById("filter-status");
    const filterSearch = document.getElementById("filter-search");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");
    const exportCsvBtn = document.getElementById("exportCsvBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    
    const tableBody = document.getElementById("submissionsTableBody");
    
    // Metrics Selectors
    const statTotal = document.getElementById("stat-total");
    const statCompleted = document.getElementById("stat-completed");
    const statPending = document.getElementById("stat-pending");
    const statIssues = document.getElementById("stat-issues");

    let searchTimeout = null;

    // Fetch stores list for the filter dropdown
    async function loadStoresFilter() {
      try {
        const response = await fetch("/stores");
        const result = await response.json();
        
        if (result.success && Array.isArray(result.data)) {
          result.data.forEach(store => {
            const option = document.createElement("option");
            option.value = store.id;
            option.textContent = store.store_name;
            filterStore.appendChild(option);
          });
        }
      } catch (error) {
        console.error("Error loading stores filter:", error);
      }
    }

    // Fetch and render data submissions
    async function fetchSubmissions() {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();

      // Build Query String
      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);

      try {
        const response = await fetch(`/admin/submissions?${params.toString()}`, {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });

        if (response.status === 401) {
          // Token expired or invalid
          handleSessionExpired();
          return;
        }

        const result = await response.json();

        if (result.success && Array.isArray(result.data)) {
          renderTable(result.data);
          calculateStats(result.data);
        } else {
          showTableMessage("Error loading submissions: " + (result.message || "Unknown error"));
        }
      } catch (error) {
        console.error("Network error fetching submissions:", error);
        showTableMessage("Failed to connect to API server.");
      }
    }

    // Render data row elements
    function renderTable(submissions) {
      if (submissions.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="8" class="table-empty">
              <div class="icon">🔍</div>
              <div>No submissions found matching the criteria.</div>
            </td>
          </tr>
        `;
        return;
      }

      tableBody.innerHTML = "";
      
      submissions.forEach(sub => {
        const tr = document.createElement("tr");
        
        // Formatted Date
        const dateStr = sub.created_at 
          ? new Date(sub.created_at).toLocaleString() 
          : "N/A";
          
        // App status badge formatting
        let regBadgeClass = "badge-not-interested";
        if (sub.app_registration_status === "Completed") {
          regBadgeClass = "badge-completed";
        } else if (sub.app_registration_status === "Pending") {
          regBadgeClass = "badge-pending";
        }

        // Issue badge formatting
        const issueBadgeClass = sub.invitation_card_issue === "Yes" 
          ? "badge-issue-yes" 
          : "badge-issue-no";

        // HTML Row
        tr.innerHTML = `
          <td>${sub.id}</td>
          <td style="white-space: nowrap;">${dateStr}</td>
          <td><strong>${sub.store_name}</strong></td>
          <td class="td-name">${sub.customer_name}</td>
          <td>${sub.mobile_number}</td>
          <td><span class="badge ${regBadgeClass}">${sub.app_registration_status}</span></td>
          <td><span class="badge ${issueBadgeClass}">${sub.invitation_card_issue}</span></td>
          <td class="td-desc" title="${sub.issue_description}">${sub.issue_description || '<span style="color:hsl(220,10%,75%);">—</span>'}</td>
        `;

        // Expand issue description on click if it has value
        if (sub.issue_description) {
          const descCell = tr.querySelector(".td-desc");
          descCell.style.cursor = "pointer";
          descCell.addEventListener("click", () => {
            descCell.classList.toggle("expanded");
          });
        }

        tableBody.appendChild(tr);
      });
    }

    // Update Dashboard Metrics Cards
    function calculateStats(submissions) {
      const total = submissions.length;
      
      const completed = submissions.filter(
        sub => sub.app_registration_status === "Completed"
      ).length;
      
      const pending = submissions.filter(
        sub => sub.app_registration_status === "Pending"
      ).length;
      
      const issues = submissions.filter(
        sub => sub.invitation_card_issue === "Yes"
      ).length;

      // Animate/set counter texts
      statTotal.textContent = total;
      statCompleted.textContent = completed;
      statPending.textContent = pending;
      statIssues.textContent = issues;
    }

    // Helper to display text messages in the table area
    function showTableMessage(message) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="8" class="table-empty">
            <div class="icon">⚠</div>
            <div style="color: var(--color-danger);">${message}</div>
          </td>
        </tr>
      `;
    }

    // Force log out when session is expired
    function handleSessionExpired() {
      localStorage.removeItem("admin_token");
      alert("Your session has expired or is invalid. Please log in again.");
      window.location.href = "/admin-login";
    }

    // Event listeners for Filters
    filterStore.addEventListener("change", fetchSubmissions);
    filterStatus.addEventListener("change", fetchSubmissions);
    
    // Debounce search input to avoid hitting backend API on every keystroke
    filterSearch.addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(fetchSubmissions, 350); // Wait 350ms after typing stops
    });

    // Reset Filters button
    resetFiltersBtn.addEventListener("click", () => {
      filterStore.value = "";
      filterStatus.value = "";
      filterSearch.value = "";
      fetchSubmissions();
    });

    // Export submissions to CSV using authenticated query URL
    exportCsvBtn.addEventListener("click", () => {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();

      const params = new URLSearchParams();
      params.append("token", token); // Token appended as query param for browser download redirect
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);

      const downloadUrl = `/admin/export-csv?${params.toString()}`;
      
      // Triggers browser download directly
      window.location.href = downloadUrl;
    });

    // Handle Logout
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("admin_token");
      window.location.href = "/admin-login";
    });

    // Initialize Dashboard Component Fetches
    loadStoresFilter();
    fetchSubmissions();
  }
});
