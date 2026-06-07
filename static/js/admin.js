// Admin Panel Logic - Team Saddam Zone Activities Data Collection

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const dashboardContainer = document.querySelector(".dashboard-layout");

  if (loginForm) {
    initLoginPage();
  } else if (dashboardContainer) {
    initDashboardPage();
  }

  // ====================================================
  // LOGIN PAGE LOGIC
  // ====================================================
  function initLoginPage() {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const passwordToggle = document.getElementById("passwordToggle");
    const loginBtn = document.getElementById("loginBtn");
    const loginSpinner = document.getElementById("loginSpinner");
    const loginBtnText = document.getElementById("loginBtnText");
    const errorContainer = document.getElementById("login-error-container");

    // Toggle Password Visibility
    passwordToggle.addEventListener("click", () => {
      if (passwordInput.type === "password") {
        passwordInput.type = "text";
        passwordToggle.textContent = "🙈";
      } else {
        passwordInput.type = "password";
        passwordToggle.textContent = "👁️";
      }
    });

    // Clear validation error styling on typing
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

      if (!usernameInput.value.trim()) {
        showInputError(usernameInput, "username-error");
        isValid = false;
      }
      
      if (!passwordInput.value.trim()) {
        showInputError(passwordInput, "password-error");
        isValid = false;
      }

      if (!isValid) return;

      const payload = {
        username: usernameInput.value.trim(),
        password: passwordInput.value
      };

      loginBtn.disabled = true;
      loginSpinner.style.display = "inline-block";
      loginBtnText.textContent = "Authenticating...";

      try {
        const response = await fetch("/api/admin/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.success) {
          window.location.href = "/admin-dashboard";
        } else {
          errorContainer.style.display = "flex";
          passwordInput.value = "";
        }
      } catch (error) {
        console.error("Login request error:", error);
        alert("An error occurred. Unable to contact authentication server.");
      } finally {
        loginBtn.disabled = false;
        loginSpinner.style.display = "none";
        loginBtnText.textContent = "Login to Dashboard";
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
      const errorMsg = formGroup ? formGroup.querySelector(".error-msg") : null;
      if (errorMsg) errorMsg.style.display = "none";
    }
  }

  // ====================================================
  // DASHBOARD PAGE LOGIC
  // ====================================================
  function initDashboardPage() {
    // Selectors
    const filterStore = document.getElementById("filter-store");
    const filterStatus = document.getElementById("filter-status");
    const filterDate = document.getElementById("filter-date");
    const filterSearch = document.getElementById("filter-search");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");
    
    const exportCsvBtn = document.getElementById("exportCsvBtn");
    const exportExcelBtn = document.getElementById("exportExcelBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    
    // Sidebar toggle (for mobile layout)
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    
    const tableBody = document.getElementById("submissionsTableBody");
    const pageSizeSelect = document.getElementById("pageSizeSelect");
    const prevPageBtn = document.getElementById("prevPageBtn");
    const nextPageBtn = document.getElementById("nextPageBtn");
    
    // Metrics Card elements
    const statTotal = document.getElementById("stat-total");
    const statCompleted = document.getElementById("stat-completed");
    const statPending = document.getElementById("stat-pending");
    const statNotInterested = document.getElementById("stat-not-interested");
    const statIssues = document.getElementById("stat-issues");
    
    // Advanced analytics elements
    const statTotalCustomers = document.getElementById("stat-total-customers");
    const statTodaysCustomers = document.getElementById("stat-todays-customers");
    const statTotalStores = document.getElementById("stat-total-stores");
    
    // Analytics filter elements
    const analyticsFilterStore = document.getElementById("analytics-filter-store");
    const analyticsFilterDate = document.getElementById("analytics-filter-date");
    const analyticsFilterStart = document.getElementById("analytics-filter-start");
    const analyticsFilterEnd = document.getElementById("analytics-filter-end");
    const analyticsFilterResult = document.getElementById("analyticsFilterResult");
    const analyticsResetBtn = document.getElementById("analyticsResetBtn");
    
    // Edit modal elements
    const editModalOverlay = document.getElementById("editModalOverlay");
    const editModalClose = document.getElementById("editModalClose");
    const editCustomerForm = document.getElementById("editCustomerForm");
    const editCancelBtn = document.getElementById("editCancelBtn");
    const editCustomerId = document.getElementById("editCustomerId");
    const editStoreId = document.getElementById("editStoreId");
    const editCustomerName = document.getElementById("editCustomerName");
    const editMobileNumber = document.getElementById("editMobileNumber");
    const editAppStatus = document.getElementById("editAppStatus");
    const editInvitationIssue = document.getElementById("editInvitationIssue");
    const editIssueDescription = document.getElementById("editIssueDescription");
    const editIssueDescGroup = document.getElementById("editIssueDescGroup");
    
    // Delete modal elements
    const deleteModalOverlay = document.getElementById("deleteModalOverlay");
    const deleteModalClose = document.getElementById("deleteModalClose");
    const deleteModalMessage = document.getElementById("deleteModalMessage");
    const deleteAllConfirmWrapper = document.getElementById("deleteAllConfirmWrapper");
    const deleteAllConfirmInput = document.getElementById("deleteAllConfirmInput");
    const deleteCancelBtn = document.getElementById("deleteCancelBtn");
    const deleteConfirmBtn = document.getElementById("deleteConfirmBtn");
    const deleteAllBtn = document.getElementById("deleteAllBtn");
    
    // Global data stores
    let storesList = [];
    let allFilteredEntries = [];
    let currentPage = 1;
    let pageSize = parseInt(pageSizeSelect.value, 10);
    let searchTimeout = null;
    let currentUserRole = '';
    let currentUserFullName = '';
    
    // Chart.js references
    let storeChartInstance = null;
    let statusChartInstance = null;
    let dayWiseChartInstance = null;
    
    // Delete operation state
    let pendingDeleteId = null;
    let pendingDeleteAll = false;

    // Sidebar Mobile Drawer Toggle
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebar.classList.toggle("active");
      });
      
      // Stop propagation inside the sidebar container to prevent closing it
      sidebar.addEventListener("click", (e) => {
        e.stopPropagation();
      });
      
      // Close sidebar if user clicks main area on mobile
      document.querySelector(".main-content").addEventListener("click", () => {
        if (sidebar.classList.contains("active")) {
          sidebar.classList.remove("active");
        }
      });
    }

    // Scroll offset selector highlight on sidebar navigation
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", (e) => {
        if (item.id === "nav-settings" || item.id === "nav-data-mgmt") {
          e.preventDefault();
          return; // Handled separately below
        }
        // Remove active from all items
        navItems.forEach(nav => nav.classList.remove("active"));
        item.classList.add("active");
        
        // Mobile layout: close sidebar on click
        if (sidebar && sidebar.classList.contains("active")) {
          sidebar.classList.remove("active");
        }
      });
    });

    // Handle settings click for RBAC validation
    const settingsBtn = document.getElementById("nav-settings");
    if (settingsBtn) {
      settingsBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        
        const userRoleGreetingText = document.getElementById("userRoleGreeting").textContent;
        if (userRoleGreetingText.includes("Admin & Store Head")) {
          alert("Access Denied: Saddam Husain (Admin & Store Head) has operational access only and does not have permission to view System Settings or system administration.");
          return;
        }
        
        try {
          const res = await fetch("/api/admin/settings");
          if (res.status === 403) {
            alert("Access Denied: Super Admin privileges required.");
            return;
          }
          const data = await res.json();
          alert(data.message || "Settings loaded successfully.");
        } catch (err) {
          console.error("Error loading settings:", err);
          alert("Failed to load system settings.");
        }
      });
    }

    // ====================================================
    // TOAST NOTIFICATION SYSTEM
    // ====================================================
    function showToast(message, type = 'success') {
      const container = document.getElementById("toastContainer");
      if (!container) return;
      
      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️'
      };
      
      const toast = document.createElement("div");
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `<span class="toast-icon">${icons[type] || '📢'}</span><span>${message}</span>`;
      container.appendChild(toast);
      
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 3200);
    }

    // ====================================================
    // DATA LOADING
    // ====================================================

    // Load active stores into the filter dropdowns
    async function loadStores() {
      try {
        const response = await fetch("/api/stores");
        const result = await response.json();
        
        if (result.success && Array.isArray(result.data)) {
          storesList = result.data;
          
          // Main filter dropdown
          filterStore.innerHTML = '<option value="">All Stores</option>';
          result.data.forEach(store => {
            const option = document.createElement("option");
            option.value = store.id;
            option.textContent = store.store_name;
            filterStore.appendChild(option);
          });
          
          // Analytics filter dropdown
          if (analyticsFilterStore) {
            analyticsFilterStore.innerHTML = '<option value="">All Stores</option>';
            result.data.forEach(store => {
              const option = document.createElement("option");
              option.value = store.id;
              option.textContent = store.store_name;
              analyticsFilterStore.appendChild(option);
            });
          }
          
          // Edit modal store dropdown
          if (editStoreId) {
            editStoreId.innerHTML = '';
            result.data.forEach(store => {
              const option = document.createElement("option");
              option.value = store.id;
              option.textContent = store.store_name;
              editStoreId.appendChild(option);
            });
          }
        }
      } catch (error) {
        console.error("Error loading stores:", error);
      }
    }

    // Fetch dashboard counters (Total, Completed, Pending, Not Interested, Issues)
    async function fetchDashboardStats() {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();
      const dateVal = filterDate.value;
      
      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);
      if (dateVal) params.append("date", dateVal);

      try {
        const response = await fetch(`/api/admin/dashboard?${params.toString()}`);
        if (response.status === 401) {
          handleSessionExpired();
          return;
        }
        
        const result = await response.json();
        if (result.success && result.stats) {
          statTotal.textContent = result.stats.total;
          statCompleted.textContent = result.stats.completed;
          statPending.textContent = result.stats.pending;
          statNotInterested.textContent = result.stats.not_interested || 0;
          statIssues.textContent = result.stats.issues;
        }
        
        // Apply dynamic greeting and lock System Settings for Saddam Husain (Admin & Store Head)
        if (result.success && result.user) {
          const role = result.user.role;
          currentUserRole = role;
          currentUserFullName = result.user.name || '';
          const roleText = role === 'super_admin' ? 'Super Admin' : 'Admin & Store Head';
          const userRoleGreeting = document.getElementById("userRoleGreeting");
          if (userRoleGreeting) {
            userRoleGreeting.textContent = `Logged in as: ${roleText}`;
          }
          
          const settingsLink = document.getElementById("nav-settings");
          if (settingsLink) {
            if (role === 'admin_store_head') {
              settingsLink.style.opacity = '0.5';
              settingsLink.style.cursor = 'not-allowed';
              settingsLink.title = 'Access Denied: Super Admin privileges required';
            } else {
              settingsLink.style.opacity = '1';
              settingsLink.style.cursor = 'pointer';
              settingsLink.title = 'System Configuration Settings';
            }
          }
          
          // Show/hide Delete All button based on role
          if (deleteAllBtn) {
            deleteAllBtn.style.display = (role === 'super_admin') ? 'inline-flex' : 'none';
          }
        }
      } catch (error) {
        console.error("Error loading stats cards:", error);
      }
    }

    // ====================================================
    // ADVANCED ANALYTICS - Stats & Charts
    // ====================================================
    async function fetchAdvancedStats(filterParams) {
      const params = filterParams || new URLSearchParams();
      
      try {
        const response = await fetch(`/api/admin/stats?${params.toString()}`);
        if (response.status === 401) {
          handleSessionExpired();
          return;
        }
        
        const result = await response.json();
        if (!result.success) return;
        
        // Update analytics overview cards
        if (statTotalCustomers) statTotalCustomers.textContent = result.total_customers || 0;
        if (statTodaysCustomers) statTodaysCustomers.textContent = result.todays_customers || 0;
        if (statTotalStores) statTotalStores.textContent = storesList.length || 13;
        
        // Day-Wise Chart
        renderDayWiseChart(result.day_wise_customers || []);
        
        // Store-Wise Summary Table (from stats API)
        renderStoreSummaryFromStats(result.store_wise_customers || []);
        
        // Update analytics filter result
        if (analyticsFilterResult && result.store_day_wise_customers) {
          analyticsFilterResult.textContent = `Filtered Count: ${result.store_day_wise_customers.count}`;
        }
        
      } catch (error) {
        console.error("Error fetching advanced stats:", error);
      }
    }

    // Render Day-Wise Line Chart
    function renderDayWiseChart(dayWiseData) {
      const canvas = document.getElementById("chartDayWise");
      if (!canvas) return;
      
      const ctx = canvas.getContext("2d");
      if (dayWiseChartInstance) dayWiseChartInstance.destroy();
      
      const labels = dayWiseData.map(d => d.date);
      const data = dayWiseData.map(d => d.total_customers);
      
      dayWiseChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Customers',
            data: data,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
            fill: true,
            tension: 0.35,
            pointBackgroundColor: '#2563eb',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1, color: '#6b7280', font: { family: 'Inter' } },
              grid: { color: '#f3f4f6' }
            },
            x: {
              ticks: { color: '#6b7280', font: { family: 'Inter', size: 10 }, maxRotation: 45, minRotation: 25 },
              grid: { display: false }
            }
          }
        }
      });
    }

    // Render Store-Wise summary table from stats API data
    function renderStoreSummaryFromStats(storeWiseData) {
      const storeSummaryBody = document.getElementById("storeSummaryTableBody");
      if (!storeSummaryBody) return;
      
      storeSummaryBody.innerHTML = "";
      
      if (storeWiseData.length === 0) {
        storeSummaryBody.innerHTML = `
          <tr>
            <td colspan="7" class="table-empty">
              <div class="icon">📭</div>
              <div>No store data available.</div>
            </td>
          </tr>
        `;
        return;
      }
      
      let sumTotal = 0;
      let sumToday = 0;
      let sumCompleted = 0;
      let sumPending = 0;
      let sumNotInterested = 0;
      let sumIssues = 0;

      const sorted = [...storeWiseData].sort((a, b) => a.store_name.localeCompare(b.store_name));
      sorted.forEach(stats => {
        sumTotal += stats.total_customers || 0;
        sumToday += stats.todays_customers || 0;
        sumCompleted += stats.completed || 0;
        sumPending += stats.pending || 0;
        sumNotInterested += stats.not_interested || 0;
        sumIssues += stats.invitation_issues || 0;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${stats.store_name}</strong></td>
          <td style="text-align: center; font-weight: 600;">${stats.total_customers}</td>
          <td style="text-align: center; color: var(--accent); font-weight: 600;">${stats.todays_customers}</td>
          <td style="text-align: center; color: var(--color-success); font-weight: 600;">${stats.completed}</td>
          <td style="text-align: center; color: var(--color-warning); font-weight: 600;">${stats.pending}</td>
          <td style="text-align: center; color: var(--text-muted);">${stats.not_interested}</td>
          <td style="text-align: center; color: var(--color-danger); font-weight: 600;">${stats.invitation_issues}</td>
        `;
        storeSummaryBody.appendChild(tr);
      });

      // Append Grand Total row
      const totalTr = document.createElement("tr");
      totalTr.style.background = "rgba(37, 99, 235, 0.05)";
      totalTr.style.borderTop = "2px solid var(--primary)";
      
      const totalLabel = currentUserRole === 'admin_store_head'
        ? "Saddam Husain (6172) Total"
        : (currentUserFullName ? `${currentUserFullName} Total` : "Saddam Husain (6172) Total");
        
      totalTr.innerHTML = `
        <td><strong>${totalLabel}</strong></td>
        <td style="text-align: center; font-weight: 700; color: var(--primary);">${sumTotal}</td>
        <td style="text-align: center; font-weight: 700; color: var(--accent);">${sumToday}</td>
        <td style="text-align: center; font-weight: 700; color: var(--color-success);">${sumCompleted}</td>
        <td style="text-align: center; font-weight: 700; color: var(--color-warning);">${sumPending}</td>
        <td style="text-align: center; font-weight: 700; color: var(--text-muted);">${sumNotInterested}</td>
        <td style="text-align: center; font-weight: 700; color: var(--color-danger);">${sumIssues}</td>
      `;
      storeSummaryBody.appendChild(totalTr);
    }

    // Compile Store-Wise summary grid from entries (fallback for existing charts)
    function renderStoreSummary(entries) {
      // This function is kept for backwards compatibility with chart rendering
      // The stats API now provides authoritative store summary data
    }

    // Render Charts visualizations
    function renderCharts(entries) {
      const storeLabels = [];
      const storeCounts = [];
      
      const storeCountsMap = {};
      storesList.forEach(s => {
        storeCountsMap[s.store_name] = 0;
      });
      
      entries.forEach(sub => {
        if (storeCountsMap[sub.store_name] !== undefined) {
          storeCountsMap[sub.store_name]++;
        }
      });
      
      const sortedStores = Object.keys(storeCountsMap).sort();
      sortedStores.forEach(name => {
        let label = name;
        if (name.includes(" - ")) {
          label = name.split(" - ")[0]; // e.g. "Nelamangala"
        }
        storeLabels.push(label);
        storeCounts.push(storeCountsMap[name]);
      });

      // status aggregation
      let completed = 0;
      let pending = 0;
      let notInterested = 0;
      
      entries.forEach(sub => {
        if (sub.app_registration_status === "Completed") completed++;
        else if (sub.app_registration_status === "Pending") pending++;
        else if (sub.app_registration_status === "Not Interested") notInterested++;
      });

      // Canvas 1: Submissions by Store
      const ctxStore = document.getElementById("chartSubmissionsByStore").getContext("2d");
      if (storeChartInstance) storeChartInstance.destroy();
      storeChartInstance = new Chart(ctxStore, {
        type: 'bar',
        data: {
          labels: storeLabels,
          datasets: [{
            data: storeCounts,
            backgroundColor: '#2563eb', // Royal Blue
            hoverBackgroundColor: '#1d4ed8',
            borderRadius: 4,
            barPercentage: 0.6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1, color: '#6b7280', font: { family: 'Inter' } },
              grid: { color: '#f3f4f6' }
            },
            x: {
              ticks: { color: '#6b7280', font: { family: 'Inter', size: 9 }, maxRotation: 45, minRotation: 45 },
              grid: { display: false }
            }
          }
        }
      });

      // Canvas 2: App Status doughnut
      const ctxStatus = document.getElementById("chartRegistrationStatus").getContext("2d");
      if (statusChartInstance) statusChartInstance.destroy();
      statusChartInstance = new Chart(ctxStatus, {
        type: 'doughnut',
        data: {
          labels: ['Completed', 'Pending', 'Not Interested'],
          datasets: [{
            data: [completed, pending, notInterested],
            backgroundColor: ['#10b981', '#f59e0b', '#9ca3af'],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#374151', font: { family: 'Inter', size: 11 } }
            }
          },
          cutout: '60%'
        }
      });
    }

    // Fetch and render customer list
    async function fetchCustomersList() {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();
      const dateVal = filterDate.value;

      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);
      if (dateVal) params.append("date", dateVal);

      try {
        const response = await fetch(`/api/admin/customers?${params.toString()}`);

        if (response.status === 401) {
          handleSessionExpired();
          return;
        }

        const result = await response.json();

        if (result.success && Array.isArray(result.data)) {
          allFilteredEntries = result.data;
          
          // Render global summaries and graphs with full filtered matches
          renderCharts(result.data);
          
          // Paginate customer log rows
          currentPage = 1;
          renderPaginatedTable();
        } else {
          showTableMessage("Error loading customer logs: " + (result.message || "Unknown error"));
        }
      } catch (error) {
        console.error("Network error fetching customers:", error);
        showTableMessage("Failed to connect to API server.");
      }
    }

    // Slice and bind log rows according to pagination controls
    function renderPaginatedTable() {
      const totalEntries = allFilteredEntries.length;
      const totalPages = Math.ceil(totalEntries / pageSize) || 1;
      
      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;
      
      const startIdx = (currentPage - 1) * pageSize;
      const paginatedData = allFilteredEntries.slice(startIdx, startIdx + pageSize);
      
      if (paginatedData.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="9" class="table-empty">
              <div class="icon">🔍</div>
              <div>No submissions found matching the criteria.</div>
            </td>
          </tr>
        `;
        
        document.getElementById("paginationInfo").textContent = "Showing 0-0 of 0 entries";
        prevPageBtn.disabled = true;
        nextPageBtn.disabled = true;
        return;
      }

      // Hide Actions header column if admin_store_head
      const actionsHeader = document.querySelector("#submissionsTable th:nth-child(9)");
      if (actionsHeader) {
        actionsHeader.style.display = (currentUserRole === 'admin_store_head') ? 'none' : '';
      }

      tableBody.innerHTML = "";
      
      paginatedData.forEach(sub => {
        const tr = document.createElement("tr");
        
        const dateStr = sub.created_at 
          ? new Date(sub.created_at).toLocaleString() 
          : "N/A";
          
        let regBadgeClass = "badge-not-interested";
        if (sub.app_registration_status === "Completed") {
          regBadgeClass = "badge-completed";
        } else if (sub.app_registration_status === "Pending") {
          regBadgeClass = "badge-pending";
        }

        const issueBadgeClass = sub.invitation_issue === "Yes" 
          ? "badge-issue-yes" 
          : "badge-issue-no";

        if (currentUserRole === 'admin_store_head') {
          tr.innerHTML = `
            <td>${sub.id}</td>
            <td style="white-space: nowrap;">${dateStr}</td>
            <td><strong>${sub.store_name}</strong></td>
            <td class="td-name">${sub.customer_name}</td>
            <td>${sub.mobile_number}</td>
            <td><span class="badge ${regBadgeClass}">${sub.app_registration_status}</span></td>
            <td><span class="badge ${issueBadgeClass}">${sub.invitation_issue}</span></td>
            <td class="td-desc" title="${sub.issue_description || 'No Issue'}">${sub.issue_description || '<span style="color:#9ca3af;">No Issue</span>'}</td>
          `;
        } else {
          tr.innerHTML = `
            <td>${sub.id}</td>
            <td style="white-space: nowrap;">${dateStr}</td>
            <td><strong>${sub.store_name}</strong></td>
            <td class="td-name">${sub.customer_name}</td>
            <td>${sub.mobile_number}</td>
            <td><span class="badge ${regBadgeClass}">${sub.app_registration_status}</span></td>
            <td><span class="badge ${issueBadgeClass}">${sub.invitation_issue}</span></td>
            <td class="td-desc" title="${sub.issue_description || 'No Issue'}">${sub.issue_description || '<span style="color:#9ca3af;">No Issue</span>'}</td>
            <td class="action-cell">
              <button class="action-btn action-btn-edit" title="Edit" data-id="${sub.id}">✏️</button>
              <button class="action-btn action-btn-delete" title="Delete" data-id="${sub.id}">🗑️</button>
            </td>
          `;
          
          // Bind edit button
          const editBtn = tr.querySelector(".action-btn-edit");
          if (editBtn) editBtn.addEventListener("click", () => openEditModal(sub));
          
          // Bind delete button
          const delBtn = tr.querySelector(".action-btn-delete");
          if (delBtn) delBtn.addEventListener("click", () => openDeleteModal(sub.id, sub.customer_name));
        }

        if (sub.issue_description) {
          const descCell = tr.querySelector(".td-desc");
          if (descCell) {
            descCell.style.cursor = "pointer";
            descCell.addEventListener("click", () => {
              descCell.classList.toggle("expanded");
            });
          }
        }

        tableBody.appendChild(tr);
      });

      // Pagination indicators
      const startEntry = startIdx + 1;
      const endEntry = Math.min(startIdx + pageSize, totalEntries);
      document.getElementById("paginationInfo").textContent = `Showing ${startEntry}-${endEntry} of ${totalEntries} entries`;
      
      prevPageBtn.disabled = currentPage === 1;
      nextPageBtn.disabled = currentPage === totalPages;
    }

    function showTableMessage(message) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="9" class="table-empty">
            <div class="icon">⚠️</div>
            <div style="color: var(--color-danger);">${message}</div>
          </td>
        </tr>
      `;
    }

    function handleSessionExpired() {
      alert("Your session has expired. Please log in again.");
      window.location.href = "/admin-login";
    }

    // ====================================================
    // EDIT MODAL LOGIC
    // ====================================================
    function openEditModal(sub) {
      editCustomerId.value = sub.id;
      editCustomerName.value = sub.customer_name;
      editMobileNumber.value = sub.mobile_number;
      editAppStatus.value = sub.app_registration_status;
      editInvitationIssue.value = sub.invitation_issue;
      editIssueDescription.value = sub.issue_description || '';
      
      // Set store selection
      const matchingStore = storesList.find(s => s.store_name === sub.store_name);
      if (matchingStore) {
        editStoreId.value = matchingStore.id;
      }
      
      // Toggle issue description visibility
      editIssueDescGroup.style.display = (sub.invitation_issue === 'Yes') ? 'block' : 'none';
      
      editModalOverlay.style.display = 'flex';
    }

    function closeEditModal() {
      editModalOverlay.style.display = 'none';
    }

    // Toggle issue description visibility on change
    if (editInvitationIssue) {
      editInvitationIssue.addEventListener("change", () => {
        editIssueDescGroup.style.display = (editInvitationIssue.value === 'Yes') ? 'block' : 'none';
      });
    }

    if (editModalClose) editModalClose.addEventListener("click", closeEditModal);
    if (editCancelBtn) editCancelBtn.addEventListener("click", closeEditModal);
    
    // Close on overlay click
    if (editModalOverlay) {
      editModalOverlay.addEventListener("click", (e) => {
        if (e.target === editModalOverlay) closeEditModal();
      });
    }

    // Save edited customer
    if (editCustomerForm) {
      editCustomerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const id = editCustomerId.value;
        const payload = {
          store_id: parseInt(editStoreId.value),
          customer_name: editCustomerName.value.trim(),
          mobile_number: editMobileNumber.value.trim(),
          app_registration_status: editAppStatus.value,
          invitation_issue: editInvitationIssue.value,
          issue_description: editIssueDescription.value.trim()
        };
        
        const saveBtn = document.getElementById("editSaveBtn");
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving...";
        
        try {
          const response = await fetch(`/api/admin/customer/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          
          const result = await response.json();
          
          if (response.ok && result.success) {
            showToast("Customer entry updated successfully!", "success");
            closeEditModal();
            refreshAllData();
          } else {
            showToast(result.message || "Update failed.", "error");
          }
        } catch (error) {
          console.error("Edit customer error:", error);
          showToast("Network error. Could not update.", "error");
        } finally {
          saveBtn.disabled = false;
          saveBtn.textContent = "💾 Save Changes";
        }
      });
    }

    // ====================================================
    // DELETE MODAL LOGIC
    // ====================================================
    function openDeleteModal(customerId, customerName) {
      pendingDeleteId = customerId;
      pendingDeleteAll = false;
      deleteAllConfirmWrapper.style.display = 'none';
      deleteAllConfirmInput.value = '';
      deleteModalMessage.textContent = `Are you sure you want to delete the entry for "${customerName}" (ID: ${customerId})?`;
      deleteConfirmBtn.textContent = '🗑️ Delete';
      deleteModalOverlay.style.display = 'flex';
    }

    function openDeleteAllModal() {
      pendingDeleteId = null;
      pendingDeleteAll = true;
      deleteAllConfirmWrapper.style.display = 'block';
      deleteAllConfirmInput.value = '';
      deleteModalMessage.textContent = '⚠️ This will permanently delete ALL customer entries from the database. This action cannot be undone.';
      deleteConfirmBtn.textContent = '🗑️ Delete All Records';
      deleteModalOverlay.style.display = 'flex';
    }

    function closeDeleteModal() {
      deleteModalOverlay.style.display = 'none';
      pendingDeleteId = null;
      pendingDeleteAll = false;
    }

    if (deleteModalClose) deleteModalClose.addEventListener("click", closeDeleteModal);
    if (deleteCancelBtn) deleteCancelBtn.addEventListener("click", closeDeleteModal);
    
    if (deleteModalOverlay) {
      deleteModalOverlay.addEventListener("click", (e) => {
        if (e.target === deleteModalOverlay) closeDeleteModal();
      });
    }

    // Delete All button
    if (deleteAllBtn) {
      deleteAllBtn.addEventListener("click", openDeleteAllModal);
    }

    // Confirm delete action
    if (deleteConfirmBtn) {
      deleteConfirmBtn.addEventListener("click", async () => {
        if (pendingDeleteAll) {
          // Validate DELETE confirmation text
          if (deleteAllConfirmInput.value.trim() !== 'DELETE') {
            showToast("Please type DELETE to confirm.", "warning");
            deleteAllConfirmInput.focus();
            return;
          }
          
          deleteConfirmBtn.disabled = true;
          deleteConfirmBtn.textContent = 'Deleting...';
          
          try {
            const response = await fetch("/api/admin/customers/delete-all", {
              method: "DELETE"
            });
            const result = await response.json();
            
            if (response.ok && result.success) {
              showToast("All customer entries deleted successfully!", "success");
              closeDeleteModal();
              refreshAllData();
            } else {
              showToast(result.message || "Delete all failed.", "error");
            }
          } catch (error) {
            console.error("Delete all error:", error);
            showToast("Network error. Could not delete.", "error");
          } finally {
            deleteConfirmBtn.disabled = false;
            deleteConfirmBtn.textContent = '🗑️ Delete All Records';
          }
        } else if (pendingDeleteId) {
          deleteConfirmBtn.disabled = true;
          deleteConfirmBtn.textContent = 'Deleting...';
          
          try {
            const response = await fetch(`/api/admin/customer/${pendingDeleteId}`, {
              method: "DELETE"
            });
            const result = await response.json();
            
            if (response.ok && result.success) {
              showToast("Customer entry deleted successfully!", "success");
              closeDeleteModal();
              refreshAllData();
            } else {
              showToast(result.message || "Delete failed.", "error");
            }
          } catch (error) {
            console.error("Delete customer error:", error);
            showToast("Network error. Could not delete.", "error");
          } finally {
            deleteConfirmBtn.disabled = false;
            deleteConfirmBtn.textContent = '🗑️ Delete';
          }
        }
      });
    }

    // ====================================================
    // REFRESH HELPER
    // ====================================================
    async function refreshAllData() {
      await fetchCustomersList();
      await fetchDashboardStats();
      await fetchAdvancedStats(getAnalyticsFilterParams());
    }

    function getAnalyticsFilterParams() {
      const params = new URLSearchParams();
      if (analyticsFilterStore && analyticsFilterStore.value) params.append("store_id", analyticsFilterStore.value);
      if (analyticsFilterDate && analyticsFilterDate.value) params.append("date", analyticsFilterDate.value);
      if (analyticsFilterStart && analyticsFilterStart.value) params.append("start_date", analyticsFilterStart.value);
      if (analyticsFilterEnd && analyticsFilterEnd.value) params.append("end_date", analyticsFilterEnd.value);
      return params;
    }

    // ====================================================
    // EVENT BINDINGS
    // ====================================================

    // Bind Pagination Events
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        renderPaginatedTable();
      }
    });

    nextPageBtn.addEventListener("click", () => {
      const totalPages = Math.ceil(allFilteredEntries.length / pageSize) || 1;
      if (currentPage < totalPages) {
        currentPage++;
        renderPaginatedTable();
      }
    });

    pageSizeSelect.addEventListener("change", () => {
      pageSize = parseInt(pageSizeSelect.value, 10);
      currentPage = 1;
      renderPaginatedTable();
    });

    // Refresh telemetry logs on filter changes
    filterStore.addEventListener("change", () => {
      fetchCustomersList();
      fetchDashboardStats();
    });
    filterStatus.addEventListener("change", () => {
      fetchCustomersList();
      fetchDashboardStats();
    });
    filterDate.addEventListener("change", () => {
      fetchCustomersList();
      fetchDashboardStats();
    });
    
    // Debounce search filter input (350ms)
    filterSearch.addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        fetchCustomersList();
        fetchDashboardStats();
      }, 350);
    });

    // Reset filters
    resetFiltersBtn.addEventListener("click", () => {
      filterStore.value = "";
      filterStatus.value = "";
      filterDate.value = "";
      filterSearch.value = "";
      fetchCustomersList();
      fetchDashboardStats();
    });

    // Analytics filter bindings
    if (analyticsFilterStore) {
      analyticsFilterStore.addEventListener("change", () => fetchAdvancedStats(getAnalyticsFilterParams()));
    }
    if (analyticsFilterDate) {
      analyticsFilterDate.addEventListener("change", () => {
        // Clear date range when specific date is selected
        if (analyticsFilterDate.value) {
          if (analyticsFilterStart) analyticsFilterStart.value = '';
          if (analyticsFilterEnd) analyticsFilterEnd.value = '';
        }
        fetchAdvancedStats(getAnalyticsFilterParams());
      });
    }
    if (analyticsFilterStart) {
      analyticsFilterStart.addEventListener("change", () => {
        if (analyticsFilterStart.value) {
          if (analyticsFilterDate) analyticsFilterDate.value = '';
        }
        fetchAdvancedStats(getAnalyticsFilterParams());
      });
    }
    if (analyticsFilterEnd) {
      analyticsFilterEnd.addEventListener("change", () => {
        if (analyticsFilterEnd.value) {
          if (analyticsFilterDate) analyticsFilterDate.value = '';
        }
        fetchAdvancedStats(getAnalyticsFilterParams());
      });
    }
    if (analyticsResetBtn) {
      analyticsResetBtn.addEventListener("click", () => {
        if (analyticsFilterStore) analyticsFilterStore.value = '';
        if (analyticsFilterDate) analyticsFilterDate.value = '';
        if (analyticsFilterStart) analyticsFilterStart.value = '';
        if (analyticsFilterEnd) analyticsFilterEnd.value = '';
        fetchAdvancedStats(new URLSearchParams());
      });
    }

    // Export Excel download redirect
    exportExcelBtn.addEventListener("click", () => {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();
      const dateVal = filterDate.value;

      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);
      if (dateVal) params.append("date", dateVal);

      window.location.href = `/api/admin/export-excel?${params.toString()}`;
    });

    // Export CSV download redirect
    exportCsvBtn.addEventListener("click", () => {
      const storeId = filterStore.value;
      const status = filterStatus.value;
      const search = filterSearch.value.trim();
      const dateVal = filterDate.value;

      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId);
      if (status) params.append("status", status);
      if (search) params.append("search", search);
      if (dateVal) params.append("date", dateVal);

      window.location.href = `/api/admin/export?${params.toString()}`;
    });

    // Sign out
    logoutBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/admin/logout", { method: "POST" });
      } catch (error) {
        console.error("Logout API failed:", error);
      } finally {
        window.location.href = "/admin-login";
      }
    });

    // ====================================================
    // DATA MANAGEMENT MODAL LOGIC
    // ====================================================
    const dmModalOverlay = document.getElementById("dmModalOverlay");
    const dmModalClose = document.getElementById("dmModalClose");
    const dmGrid = document.getElementById("dmGrid");
    const dmSubPanel = document.getElementById("dmSubPanel");
    const dmSubTitle = document.getElementById("dmSubTitle");
    const dmBackBtn = document.getElementById("dmBackBtn");
    const dmPreviewBtn = document.getElementById("dmPreviewBtn");
    const dmPreview = document.getElementById("dmPreview");
    const dmPreviewCount = document.getElementById("dmPreviewCount");
    const dmPreviewStores = document.getElementById("dmPreviewStores");
    const dmPreviewType = document.getElementById("dmPreviewType");
    const dmConfirm = document.getElementById("dmConfirm");
    const dmConfirmInput = document.getElementById("dmConfirmInput");
    const dmCancelOpBtn = document.getElementById("dmCancelOpBtn");
    const dmExecuteBtn = document.getElementById("dmExecuteBtn");
    const dmFilterStore = document.getElementById("dmFilterStore");
    const dmFilterDate = document.getElementById("dmFilterDate");
    const dmFilterStart = document.getElementById("dmFilterStart");
    const dmFilterEnd = document.getElementById("dmFilterEnd");
    const dmStoreSelect = document.getElementById("dmStoreSelect");
    const dmDateInput = document.getElementById("dmDateInput");
    const dmStartInput = document.getElementById("dmStartInput");
    const dmEndInput = document.getElementById("dmEndInput");
    const dmLogsBody = document.getElementById("dmLogsBody");
    const dmNavBtn = document.getElementById("nav-data-mgmt");

    let currentDmOp = '';

    // Populate DM store dropdown
    function populateDmStores() {
      if (!dmStoreSelect) return;
      dmStoreSelect.innerHTML = '<option value="">Select Store</option>';
      storesList.forEach(store => {
        const opt = document.createElement("option");
        opt.value = store.id;
        opt.textContent = store.store_name;
        dmStoreSelect.appendChild(opt);
      });
    }

    // Open DM Modal
    function openDmModal() {
      if (!dmModalOverlay) return;

      // Lock super-admin-only cards if not super admin
      const superOnlyCards = dmModalOverlay.querySelectorAll('.dm-super-only');
      superOnlyCards.forEach(card => {
        if (currentUserRole !== 'super_admin') {
          card.classList.add('dm-locked');
        } else {
          card.classList.remove('dm-locked');
        }
      });

      populateDmStores();
      resetDmSubPanel();
      dmModalOverlay.style.display = 'flex';
      loadDeleteLogs();
    }

    function closeDmModal() {
      if (dmModalOverlay) dmModalOverlay.style.display = 'none';
      resetDmSubPanel();
    }

    function resetDmSubPanel() {
      if (dmGrid) dmGrid.style.display = 'grid';
      if (dmSubPanel) dmSubPanel.style.display = 'none';
      if (dmPreview) dmPreview.style.display = 'none';
      if (dmConfirm) dmConfirm.style.display = 'none';
      if (dmConfirmInput) dmConfirmInput.value = '';
      if (dmFilterStore) dmFilterStore.style.display = 'none';
      if (dmFilterDate) dmFilterDate.style.display = 'none';
      if (dmFilterStart) dmFilterStart.style.display = 'none';
      if (dmFilterEnd) dmFilterEnd.style.display = 'none';
      currentDmOp = '';
    }

    // Nav click handler
    if (dmNavBtn) {
      dmNavBtn.addEventListener("click", (e) => {
        e.preventDefault();
        openDmModal();
        // Mobile: close sidebar
        if (sidebar && sidebar.classList.contains("active")) {
          sidebar.classList.remove("active");
        }
      });
    }

    // Close DM Modal
    if (dmModalClose) dmModalClose.addEventListener("click", closeDmModal);
    if (dmModalOverlay) {
      dmModalOverlay.addEventListener("click", (e) => {
        if (e.target === dmModalOverlay) closeDmModal();
      });
    }

    // Card click handlers
    const dmCards = dmModalOverlay ? dmModalOverlay.querySelectorAll('.dm-card') : [];
    dmCards.forEach(card => {
      card.addEventListener("click", () => {
        const op = card.getAttribute('data-op');
        if (!op) return;
        openDmSubPanel(op);
      });
    });

    const opTitles = {
      'individual': '🗑️ Delete Individual Record',
      'today': "📅 Delete Today's Data",
      'date': '📆 Delete by Specific Date',
      'date_range': '📊 Delete by Date Range',
      'store': '🏪 Delete Store Data',
      'store_date': '🏪📅 Delete Store + Date',
      'store_range': '🏪📊 Delete Store + Range',
      'all': '⚠️ Delete All Customer Data'
    };

    function openDmSubPanel(op) {
      currentDmOp = op;
      if (dmGrid) dmGrid.style.display = 'none';
      if (dmSubPanel) dmSubPanel.style.display = 'block';
      if (dmSubTitle) dmSubTitle.textContent = opTitles[op] || 'Delete Operation';
      if (dmPreview) dmPreview.style.display = 'none';
      if (dmConfirm) dmConfirm.style.display = 'none';
      if (dmConfirmInput) dmConfirmInput.value = '';

      // Show/hide filter rows based on operation
      if (dmFilterStore) dmFilterStore.style.display = 'none';
      if (dmFilterDate) dmFilterDate.style.display = 'none';
      if (dmFilterStart) dmFilterStart.style.display = 'none';
      if (dmFilterEnd) dmFilterEnd.style.display = 'none';

      // Reset inputs
      if (dmStoreSelect) dmStoreSelect.value = '';
      if (dmDateInput) dmDateInput.value = '';
      if (dmStartInput) dmStartInput.value = '';
      if (dmEndInput) dmEndInput.value = '';

      const showPreviewBtn = dmPreviewBtn;

      if (op === 'individual') {
        // Individual delete is handled from the table rows, not from here
        if (dmSubTitle) dmSubTitle.innerHTML = '🗑️ Delete Individual Record<br><span style="font-size:0.82rem; font-weight:400; color:var(--text-muted); margin-top:8px; display:block;">Individual record deletion is available directly from the Customer Logs table. Click the 🗑️ button on any row to delete that specific entry.</span>';
        if (showPreviewBtn) showPreviewBtn.style.display = 'none';
        return;
      }

      if (showPreviewBtn) showPreviewBtn.style.display = 'inline-flex';

      switch (op) {
        case 'today':
          // No filters needed — just preview/delete
          break;
        case 'date':
          if (dmFilterDate) dmFilterDate.style.display = 'block';
          break;
        case 'date_range':
          if (dmFilterStart) dmFilterStart.style.display = 'block';
          if (dmFilterEnd) dmFilterEnd.style.display = 'block';
          break;
        case 'store':
          if (dmFilterStore) dmFilterStore.style.display = 'block';
          break;
        case 'store_date':
          if (dmFilterStore) dmFilterStore.style.display = 'block';
          if (dmFilterDate) dmFilterDate.style.display = 'block';
          break;
        case 'store_range':
          if (dmFilterStore) dmFilterStore.style.display = 'block';
          if (dmFilterStart) dmFilterStart.style.display = 'block';
          if (dmFilterEnd) dmFilterEnd.style.display = 'block';
          break;
        case 'all':
          // No filters needed
          break;
      }
    }

    // Back button
    if (dmBackBtn) {
      dmBackBtn.addEventListener("click", () => {
        resetDmSubPanel();
        if (dmGrid) dmGrid.style.display = 'grid';
      });
    }

    // Preview button
    if (dmPreviewBtn) {
      dmPreviewBtn.addEventListener("click", async () => {
        if (!currentDmOp) return;

        // Build preview query params
        const params = new URLSearchParams();
        params.append('type', currentDmOp);

        if (['store', 'store_date', 'store_range'].includes(currentDmOp)) {
          const storeVal = dmStoreSelect ? dmStoreSelect.value : '';
          if (!storeVal) {
            showToast("Please select a store.", "warning");
            return;
          }
          params.append('store_id', storeVal);
        }

        if (['date', 'store_date'].includes(currentDmOp)) {
          const dateVal = dmDateInput ? dmDateInput.value : '';
          if (!dateVal) {
            showToast("Please select a date.", "warning");
            return;
          }
          params.append('date', dateVal);
        }

        if (['date_range', 'store_range'].includes(currentDmOp)) {
          const startVal = dmStartInput ? dmStartInput.value : '';
          const endVal = dmEndInput ? dmEndInput.value : '';
          if (!startVal || !endVal) {
            showToast("Please select both start and end dates.", "warning");
            return;
          }
          params.append('start_date', startVal);
          params.append('end_date', endVal);
        }

        dmPreviewBtn.disabled = true;
        dmPreviewBtn.textContent = '⏳ Loading...';

        try {
          const response = await fetch(`/api/admin/delete/preview?${params.toString()}`);
          const result = await response.json();

          if (response.ok && result.success) {
            if (dmPreviewCount) dmPreviewCount.textContent = result.records_count || 0;
            if (dmPreviewStores) dmPreviewStores.textContent = result.stores_affected || 0;
            if (dmPreviewType) {
              const typeLabels = {
                'today': "Today's Records",
                'date': `Date: ${result.date || ''}`,
                'date_range': 'Date Range',
                'store': 'Store Records',
                'store_date': 'Store + Date',
                'store_range': 'Store + Range',
                'all': 'ALL Records'
              };
              dmPreviewType.textContent = typeLabels[currentDmOp] || currentDmOp;
            }
            if (dmPreview) dmPreview.style.display = 'block';

            // Show confirmation if records found
            if (result.records_count > 0) {
              if (dmConfirm) dmConfirm.style.display = 'block';
              if (dmConfirmInput) dmConfirmInput.value = '';
            } else {
              if (dmConfirm) dmConfirm.style.display = 'none';
              showToast("No records found matching the criteria.", "warning");
            }
          } else {
            showToast(result.message || "Preview failed.", "error");
          }
        } catch (error) {
          console.error("DM Preview error:", error);
          showToast("Network error during preview.", "error");
        } finally {
          dmPreviewBtn.disabled = false;
          dmPreviewBtn.textContent = '🔍 Preview';
        }
      });
    }

    // Cancel operation
    if (dmCancelOpBtn) {
      dmCancelOpBtn.addEventListener("click", () => {
        if (dmPreview) dmPreview.style.display = 'none';
        if (dmConfirm) dmConfirm.style.display = 'none';
        if (dmConfirmInput) dmConfirmInput.value = '';
      });
    }

    // Execute delete
    if (dmExecuteBtn) {
      dmExecuteBtn.addEventListener("click", async () => {
        if (!currentDmOp) return;

        // Validate confirmation text
        const confirmText = dmConfirmInput ? dmConfirmInput.value.trim() : '';
        if (confirmText !== 'DELETE') {
          showToast("Please type DELETE to confirm.", "warning");
          if (dmConfirmInput) dmConfirmInput.focus();
          return;
        }

        dmExecuteBtn.disabled = true;
        dmExecuteBtn.textContent = '⏳ Deleting...';

        try {
          let url = '';
          let method = 'DELETE';
          let body = null;
          let headers = {};

          switch (currentDmOp) {
            case 'today':
              url = '/api/admin/delete/today';
              break;
            case 'date':
              url = `/api/admin/delete/date/${dmDateInput ? dmDateInput.value : ''}`;
              break;
            case 'date_range':
              url = '/api/admin/delete/date-range';
              headers = { 'Content-Type': 'application/json' };
              body = JSON.stringify({
                start_date: dmStartInput ? dmStartInput.value : '',
                end_date: dmEndInput ? dmEndInput.value : ''
              });
              break;
            case 'store':
              url = `/api/admin/delete/store/${dmStoreSelect ? dmStoreSelect.value : ''}`;
              break;
            case 'store_date':
              url = '/api/admin/delete/store-date';
              headers = { 'Content-Type': 'application/json' };
              body = JSON.stringify({
                store_id: dmStoreSelect ? dmStoreSelect.value : '',
                date: dmDateInput ? dmDateInput.value : ''
              });
              break;
            case 'store_range':
              url = '/api/admin/delete/store-range';
              headers = { 'Content-Type': 'application/json' };
              body = JSON.stringify({
                store_id: dmStoreSelect ? dmStoreSelect.value : '',
                start_date: dmStartInput ? dmStartInput.value : '',
                end_date: dmEndInput ? dmEndInput.value : ''
              });
              break;
            case 'all':
              url = '/api/admin/delete/all';
              headers = { 'Content-Type': 'application/json' };
              body = JSON.stringify({ confirm: 'DELETE ALL' });
              break;
            default:
              showToast("Unknown operation.", "error");
              return;
          }

          const fetchOptions = { method, headers };
          if (body) fetchOptions.body = body;

          const response = await fetch(url, fetchOptions);
          const result = await response.json();

          if (response.ok && result.success) {
            const count = result.records_deleted || 0;
            showToast(`✅ ${result.message || `Deleted ${count} records.`}`, "success");
            
            // Reset sub-panel and refresh
            resetDmSubPanel();
            if (dmGrid) dmGrid.style.display = 'grid';
            loadDeleteLogs();
            refreshAllData();
          } else {
            showToast(result.message || "Delete operation failed.", "error");
          }
        } catch (error) {
          console.error("DM Execute error:", error);
          showToast("Network error during delete operation.", "error");
        } finally {
          dmExecuteBtn.disabled = false;
          dmExecuteBtn.textContent = '🗑️ Execute Delete';
        }
      });
    }

    // Load Delete Audit Logs
    async function loadDeleteLogs() {
      if (!dmLogsBody) return;

      dmLogsBody.innerHTML = '<tr><td colspan="6" class="table-empty"><div class="icon">⏳</div><div>Loading audit logs...</div></td></tr>';

      try {
        const response = await fetch('/api/admin/delete/logs');
        const result = await response.json();

        if (result.success && Array.isArray(result.data) && result.data.length > 0) {
          dmLogsBody.innerHTML = '';
          result.data.forEach(log => {
            const tr = document.createElement("tr");
            const dateStr = log.created_at
              ? new Date(log.created_at).toLocaleString()
              : 'N/A';
            
            const typeBadgeColors = {
              'individual': '#2563eb',
              'today': '#f59e0b',
              'date': '#8b5cf6',
              'date_range': '#8b5cf6',
              'store': '#10b981',
              'store_date': '#10b981',
              'store_range': '#10b981',
              'all': '#ef4444'
            };
            const badgeColor = typeBadgeColors[log.delete_type] || '#6b7280';

            tr.innerHTML = `
              <td style="white-space: nowrap; font-size: 0.82rem;">${dateStr}</td>
              <td style="font-weight: 500;">${log.user_name || 'N/A'}</td>
              <td><span class="badge" style="background: ${badgeColor}15; color: ${badgeColor};">${log.user_role || 'N/A'}</span></td>
              <td><span class="badge" style="background: ${badgeColor}15; color: ${badgeColor};">${log.delete_type || 'N/A'}</span></td>
              <td style="text-align: center; font-weight: 700;">${log.records_deleted || 0}</td>
              <td class="td-desc" title="${log.details || ''}" style="max-width: 160px;">${log.details || '--'}</td>
            `;
            dmLogsBody.appendChild(tr);
          });
        } else {
          dmLogsBody.innerHTML = '<tr><td colspan="6" class="table-empty"><div class="icon">📭</div><div>No delete logs found.</div></td></tr>';
        }
      } catch (error) {
        console.error("Load delete logs error:", error);
        dmLogsBody.innerHTML = '<tr><td colspan="6" class="table-empty"><div class="icon">⚠️</div><div>Failed to load audit logs.</div></td></tr>';
      }
    }

    // ====================================================
    // DYNAMIC NAVIGATION AND SPA ROUTING
    // ====================================================
    const mainDashboardSections = [
      document.getElementById("overview-section"),
      document.querySelector(".analytics-highlight-grid"),
      document.getElementById("charts-section"),
      document.getElementById("analytics-filter-section"),
      document.querySelector("section.filter-card:not(#analytics-filter-section)"),
      document.getElementById("stores-section"),
      document.getElementById("logs-section")
    ];
    
    const customPages = [
      document.getElementById("user-mgmt-section"),
      document.getElementById("export-center-section"),
      document.getElementById("role-mgmt-section"),
      document.getElementById("printable-reports-section")
    ];

    navItems.forEach(item => {
      item.addEventListener("click", (e) => {
        const targetHref = item.getAttribute("href");
        
        if (item.id === "nav-settings" || item.id === "nav-data-mgmt") {
          e.preventDefault();
          return; // Handled separately
        }
        
        if (targetHref && targetHref.startsWith("#")) {
          const targetId = targetHref.substring(1);
          const customPageIds = ["user-mgmt-section", "export-center-section", "role-mgmt-section", "printable-reports-section"];
          
          if (customPageIds.includes(targetId)) {
            e.preventDefault();
            // Hide main dashboard
            mainDashboardSections.forEach(sec => { if (sec) sec.style.display = "none"; });
            // Hide custom pages
            customPages.forEach(sec => { if (sec) sec.style.display = "none"; });
            
            // Show target custom page
            const targetSec = document.getElementById(targetId);
            if (targetSec) targetSec.style.display = "block";
            
            // Fetch relevant data
            if (targetId === "user-mgmt-section") {
              fetchUsersList();
            } else if (targetId === "role-mgmt-section") {
              fetchAdminAuditLogs();
            } else if (targetId === "printable-reports-section") {
              renderPrintableReport();
            }
          } else {
            // Dashboard section anchor
            mainDashboardSections.forEach(sec => { if (sec) sec.style.display = ""; });
            customPages.forEach(sec => { if (sec) sec.style.display = "none"; });
            
            const targetSec = document.getElementById(targetId);
            if (targetSec) {
              targetSec.scrollIntoView({ behavior: "smooth" });
            }
          }
        }
        
        navItems.forEach(nav => nav.classList.remove("active"));
        item.classList.add("active");
        
        if (sidebar && sidebar.classList.contains("active")) {
          sidebar.classList.remove("active");
        }
      });
    });

    // ====================================================
    // USER MANAGEMENT CRUD MODULE
    // ====================================================
    const userModalOverlay = document.getElementById("userModalOverlay");
    const userModalClose = document.getElementById("userModalClose");
    const userForm = document.getElementById("userForm");
    const userCancelBtn = document.getElementById("userCancelBtn");
    const userModalTitle = document.getElementById("userModalTitle");
    const userSaveBtn = document.getElementById("userSaveBtn");
    
    const userFormId = document.getElementById("userFormId");
    const userEmpId = document.getElementById("userEmpId");
    const userFullName = document.getElementById("userFullName");
    const userUsername = document.getElementById("userUsername");
    const userPassword = document.getElementById("userPassword");
    const userRole = document.getElementById("userRole");
    const userStatus = document.getElementById("userStatus");
    const empIdGroup = document.getElementById("empIdGroup");
    const userPassRequired = document.getElementById("userPassRequired");
    const userPassHelp = document.getElementById("userPassHelp");
    
    const userSearchInput = document.getElementById("userSearchInput");
    const userRoleFilter = document.getElementById("userRoleFilter");
    const userStatusFilter = document.getElementById("userStatusFilter");
    const usersTableBody = document.getElementById("usersTableBody");
    
    const userPrevPageBtn = document.getElementById("userPrevPageBtn");
    const userNextPageBtn = document.getElementById("userNextPageBtn");
    const userPaginationInfo = document.getElementById("userPaginationInfo");
    
    // User Delete modal
    const userDeleteModalOverlay = document.getElementById("userDeleteModalOverlay");
    const userDeleteModalClose = document.getElementById("userDeleteModalClose");
    const userDeleteCancelBtn = document.getElementById("userDeleteCancelBtn");
    const userDeleteConfirmBtn = document.getElementById("userDeleteConfirmBtn");
    
    let userCurrentPage = 1;
    let userPageSize = 10;
    let pendingDeleteUserId = null;
    let userSearchTimeout = null;

    if (document.getElementById("addUserBtn")) {
      document.getElementById("addUserBtn").addEventListener("click", () => openUserModal());
    }
    if (userModalClose) userModalClose.addEventListener("click", closeUserModal);
    if (userCancelBtn) userCancelBtn.addEventListener("click", closeUserModal);
    if (userDeleteModalClose) userDeleteModalClose.addEventListener("click", closeUserDeleteModal);
    if (userDeleteCancelBtn) userDeleteCancelBtn.addEventListener("click", closeUserDeleteModal);

    function openUserModal(user = null) {
      if (!userModalOverlay) return;
      userForm.reset();
      
      if (user) {
        // Edit Mode
        userModalTitle.textContent = "✏️ Edit User Account";
        userFormId.value = user.id;
        userEmpId.value = user.employee_id;
        if (empIdGroup) empIdGroup.style.display = "none"; // Hide employee ID input on edit
        userFullName.value = user.full_name;
        userUsername.value = user.username;
        userPassword.required = false;
        if (userPassRequired) userPassRequired.style.display = "none";
        if (userPassHelp) userPassHelp.style.display = "block";
        userRole.value = user.role;
        userStatus.value = user.status;
        userSaveBtn.textContent = "💾 Save Changes";
      } else {
        // Add Mode
        userModalTitle.textContent = "👥 Add User Account";
        userFormId.value = "";
        if (empIdGroup) empIdGroup.style.display = "block";
        userEmpId.required = true;
        userPassword.required = true;
        if (userPassRequired) userPassRequired.style.display = "inline";
        if (userPassHelp) userPassHelp.style.display = "none";
        userSaveBtn.textContent = "💾 Save User";
      }
      
      userModalOverlay.style.display = "flex";
    }

    function closeUserModal() {
      if (userModalOverlay) userModalOverlay.style.display = "none";
    }

    if (userForm) {
      userForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const userId = userFormId.value;
        const isEdit = userId !== "";
        
        const payload = {
          full_name: userFullName.value.trim(),
          username: userUsername.value.trim(),
          role: userRole.value,
          status: userStatus.value,
          password: userPassword.value
        };
        
        if (!isEdit) {
          payload.employee_id = userEmpId.value.trim();
        }
        
        const url = isEdit ? `/api/users/${userId}` : '/api/users';
        const method = isEdit ? 'PUT' : 'POST';
        
        try {
          const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          const result = await res.json();
          if (res.ok && result.success) {
            showToast(result.message || "Operation successful!");
            closeUserModal();
            fetchUsersList();
          } else {
            alert(result.message || "Failed to save user.");
          }
        } catch (err) {
          console.error("Save user error:", err);
          alert("Error contacting server to save user.");
        }
      });
    }

    async function fetchUsersList() {
      if (!usersTableBody) return;
      
      const search = userSearchInput ? userSearchInput.value.trim() : "";
      const role = userRoleFilter ? userRoleFilter.value : "";
      const status = userStatusFilter ? userStatusFilter.value : "";
      
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (role) params.append("role", role);
      if (status) params.append("status", status);
      params.append("page", userCurrentPage);
      params.append("page_size", userPageSize);
      
      try {
        const res = await fetch(`/api/users?${params.toString()}`);
        if (res.status === 401) {
          handleSessionExpired();
          return;
        }
        if (res.status === 403) {
          usersTableBody.innerHTML = '<tr><td colspan="7" class="table-empty"><div class="icon">⚠️</div><div style="color:var(--color-danger)">Access Denied: Super Admin permissions required.</div></td></tr>';
          return;
        }
        
        const result = await res.json();
        if (result.success && Array.isArray(result.data)) {
          renderUsersTable(result.data, result.total);
        } else {
          usersTableBody.innerHTML = '<tr><td colspan="7" class="table-empty"><div class="icon">⚠️</div><div>Failed to load users list.</div></td></tr>';
        }
      } catch (err) {
        console.error("Fetch users error:", err);
        usersTableBody.innerHTML = '<tr><td colspan="7" class="table-empty"><div class="icon">⚠️</div><div>Error connecting to server.</div></td></tr>';
      }
    }

    function renderUsersTable(users, total) {
      usersTableBody.innerHTML = "";
      
      if (users.length === 0) {
        usersTableBody.innerHTML = '<tr><td colspan="7" class="table-empty"><div class="icon">👤</div><div>No users found.</div></td></tr>';
        if (userPaginationInfo) userPaginationInfo.textContent = "Showing 0-0 of 0 users";
        if (userPrevPageBtn) userPrevPageBtn.disabled = true;
        if (userNextPageBtn) userNextPageBtn.disabled = true;
        return;
      }
      
      users.forEach(user => {
        const tr = document.createElement("tr");
        const dateStr = user.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A";
        
        const statusBadgeClass = user.status === 'Active' ? 'badge-completed' : 'badge-pending';
        const roleLabel = user.role === 'super_admin' ? 'Super Admin' : 'Admin & Store Head';
        
        const isSelf = sessionNameAndDetailsMatchSelf(user.employee_id);
        
        tr.innerHTML = `
          <td><strong>${user.employee_id}</strong></td>
          <td>${user.full_name}</td>
          <td>${user.username}</td>
          <td><span class="badge ${user.role === 'super_admin' ? 'badge-completed' : 'badge-pending'}">${roleLabel}</span></td>
          <td>
            <label class="status-switch">
              <input type="checkbox" class="status-toggle-checkbox" data-id="${user.id}" ${user.status === 'Active' ? 'checked' : ''} ${isSelf ? 'disabled' : ''}>
              <span class="status-slider"></span>
            </label>
            <span style="font-size:0.8rem; margin-left: 5px;" class="status-label">${user.status}</span>
          </td>
          <td>${dateStr}</td>
          <td class="action-cell">
            <button class="action-btn action-btn-edit" title="Edit" data-id="${user.id}">✏️</button>
            <button class="action-btn action-btn-delete" title="Delete" data-id="${user.id}" ${isSelf ? 'disabled style="opacity:0.3; cursor:not-allowed;"' : ''}>🗑️</button>
          </td>
        `;
        
        // Bind Edit
        tr.querySelector(".action-btn-edit").addEventListener("click", () => openUserModal(user));
        
        // Bind Delete
        const delBtn = tr.querySelector(".action-btn-delete");
        if (delBtn && !isSelf) {
          delBtn.addEventListener("click", () => openUserDeleteModal(user.id, user.full_name));
        }
        
        // Bind Status Switch
        const switchInput = tr.querySelector(".status-toggle-checkbox");
        if (switchInput && !isSelf) {
          switchInput.addEventListener("change", (e) => {
            toggleUserStatus(user.id, e.target.checked ? 'Active' : 'Inactive');
          });
        }
        
        usersTableBody.appendChild(tr);
      });
      
      // Pagination state
      const startEntry = (userCurrentPage - 1) * userPageSize + 1;
      const endEntry = Math.min(userCurrentPage * userPageSize, total);
      if (userPaginationInfo) {
        userPaginationInfo.textContent = `Showing ${startEntry}-${endEntry} of ${total} users`;
      }
      
      const totalPages = Math.ceil(total / userPageSize) || 1;
      if (userPrevPageBtn) userPrevPageBtn.disabled = userCurrentPage === 1;
      if (userNextPageBtn) userNextPageBtn.disabled = userCurrentPage === totalPages;
    }

    function sessionNameAndDetailsMatchSelf(empId) {
      const greetingText = document.getElementById("userRoleGreeting") ? document.getElementById("userRoleGreeting").textContent : "";
      const sideNameText = document.getElementById("sideUserName") ? document.getElementById("sideUserName").textContent : "";
      return greetingText.includes(`(${empId})`) || sideNameText.includes(`(${empId})`);
    }

    async function toggleUserStatus(userId, newStatus) {
      try {
        const res = await fetch('/api/users/status', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, status: newStatus })
        });
        const result = await res.json();
        if (res.ok && result.success) {
          showToast(result.message || `User status updated to ${newStatus}`);
          fetchUsersList();
        } else {
          alert(result.message || "Failed to update user status.");
          fetchUsersList();
        }
      } catch (err) {
        console.error("Toggle user status error:", err);
        alert("Error connecting to server to toggle status.");
        fetchUsersList();
      }
    }

    function openUserDeleteModal(userId, fullName) {
      if (!userDeleteModalOverlay) return;
      pendingDeleteUserId = userId;
      document.getElementById("userDeleteModalMessage").innerHTML = `Are you sure you want to delete the user account for <br><strong>${fullName}</strong>? <br><br>This action cannot be undone.`;
      userDeleteModalOverlay.style.display = "flex";
    }

    function closeUserDeleteModal() {
      if (userDeleteModalOverlay) userDeleteModalOverlay.style.display = "none";
      pendingDeleteUserId = null;
    }

    if (userDeleteConfirmBtn) {
      userDeleteConfirmBtn.addEventListener("click", async () => {
        if (!pendingDeleteUserId) return;
        try {
          const res = await fetch(`/api/users/${pendingDeleteUserId}`, { method: 'DELETE' });
          const result = await res.json();
          if (res.ok && result.success) {
            showToast(result.message || "User successfully deleted!");
            closeUserDeleteModal();
            fetchUsersList();
          } else {
            alert(result.message || "Failed to delete user.");
          }
        } catch (err) {
          console.error("Delete user request error:", err);
          alert("Error sending delete request to server.");
        }
      });
    }

    // Bind filters input & pagination buttons
    if (userSearchInput) {
      userSearchInput.addEventListener("input", () => {
        clearTimeout(userSearchTimeout);
        userSearchTimeout = setTimeout(() => {
          userCurrentPage = 1;
          fetchUsersList();
        }, 300);
      });
    }
    if (userRoleFilter) userRoleFilter.addEventListener("change", () => { userCurrentPage = 1; fetchUsersList(); });
    if (userStatusFilter) userStatusFilter.addEventListener("change", () => { userCurrentPage = 1; fetchUsersList(); });
    
    if (userPrevPageBtn) {
      userPrevPageBtn.addEventListener("click", () => {
        if (userCurrentPage > 1) {
          userCurrentPage--;
          fetchUsersList();
        }
      });
    }
    if (userNextPageBtn) {
      userNextPageBtn.addEventListener("click", () => {
        userCurrentPage++;
        fetchUsersList();
      });
    }

    // ====================================================
    // ROLE MANAGEMENT AUDIT LOGS MODULE
    // ====================================================
    async function fetchAdminAuditLogs() {
      const logsBody = document.getElementById("adminAuditLogsBody");
      if (!logsBody) return;
      
      try {
        const res = await fetch("/api/admin/audit-logs");
        if (res.status === 401) {
          handleSessionExpired();
          return;
        }
        
        const result = await res.json();
        if (result.success && Array.isArray(result.data)) {
          renderAuditLogsTable(result.data);
        } else {
          logsBody.innerHTML = '<tr><td colspan="5" class="table-empty"><div class="icon">📜</div><div>No logs could be loaded.</div></td></tr>';
        }
      } catch (err) {
        console.error("Fetch audit logs error:", err);
        logsBody.innerHTML = '<tr><td colspan="5" class="table-empty"><div class="icon">⚠️</div><div>Error connecting to server.</div></td></tr>';
      }
    }

    function renderAuditLogsTable(logs) {
      const logsBody = document.getElementById("adminAuditLogsBody");
      if (!logsBody) return;
      
      logsBody.innerHTML = "";
      if (logs.length === 0) {
        logsBody.innerHTML = '<tr><td colspan="5" class="table-empty"><div class="icon">📜</div><div>No audit logs found.</div></td></tr>';
        return;
      }
      
      logs.forEach(log => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${log.user_name}</strong></td>
          <td>${log.action}</td>
          <td>${log.log_date}</td>
          <td>${log.log_time}</td>
          <td><code>${log.ip_address}</code></td>
        `;
        logsBody.appendChild(tr);
      });
    }

    // ====================================================
    // EXPORT CENTER MODULE
    // ====================================================
    const exportCenterExecuteBtn = document.getElementById("exportCenterExecuteBtn");
    if (exportCenterExecuteBtn) {
      exportCenterExecuteBtn.addEventListener("click", () => {
        const format = document.querySelector('input[name="exportFormatRadio"]:checked').value;
        const storeId = filterStore.value;
        const status = filterStatus.value;
        const search = filterSearch.value.trim();
        const dateVal = filterDate.value;
        
        const params = new URLSearchParams();
        if (storeId) params.append("store_id", storeId);
        if (status) params.append("status", status);
        if (search) params.append("search", search);
        if (dateVal) params.append("date", dateVal);
        
        if (format === 'excel') {
          window.open(`/api/admin/export-excel?${params.toString()}`, '_blank');
        } else {
          window.open(`/api/admin/export?${params.toString()}`, '_blank');
        }
      });
    }

    // ====================================================
    // PRINTABLE REPORTS MODULE
    // ====================================================
    async function renderPrintableReport() {
      const generatedDateSpan = document.getElementById("reportGeneratedDate");
      const totalSubSpan = document.getElementById("reportTotalSubmissions");
      const completedAppsSpan = document.getElementById("reportCompletedApps");
      const issuesSpan = document.getElementById("reportIssuesCount");
      const reportStoresBody = document.getElementById("reportStoresBody");
      
      if (generatedDateSpan) generatedDateSpan.textContent = new Date().toLocaleString();
      
      try {
        const resStores = await fetch("/api/stores");
        const resCustomers = await fetch("/api/admin/customers");
        
        if (!resStores.ok || !resCustomers.ok) {
          if (reportStoresBody) reportStoresBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:15px; color:var(--color-danger);">Error loading report data.</td></tr>';
          return;
        }
        
        const storesData = await resStores.json();
        const customersData = await resCustomers.json();
        
        if (storesData.success && customersData.success) {
          const stores = storesData.data;
          const customers = customersData.data;
          
          const total = customers.length;
          const completed = customers.filter(c => c.app_registration_status === 'Completed').length;
          const issues = customers.filter(c => c.invitation_issue === 'Yes').length;
          
          if (totalSubSpan) totalSubSpan.textContent = total;
          if (completedAppsSpan) completedAppsSpan.textContent = completed;
          if (issuesSpan) issuesSpan.textContent = issues;
          
          const storeStats = {};
          stores.forEach(s => {
            storeStats[s.store_name] = { completed: 0, pending: 0, not_interested: 0, issues: 0, total: 0 };
          });
          
          customers.forEach(c => {
            const storeName = c.store_name;
            if (!storeStats[storeName]) {
              storeStats[storeName] = { completed: 0, pending: 0, not_interested: 0, issues: 0, total: 0 };
            }
            const stats = storeStats[storeName];
            stats.total++;
            if (c.app_registration_status === 'Completed') stats.completed++;
            else if (c.app_registration_status === 'Pending') stats.pending++;
            else if (c.app_registration_status === 'Not Interested') stats.not_interested++;
            
            if (c.invitation_issue === 'Yes') stats.issues++;
          });
          
          if (reportStoresBody) {
            reportStoresBody.innerHTML = "";
            let alternate = false;
            Object.keys(storeStats).sort().forEach(storeName => {
              const stats = storeStats[storeName];
              const tr = document.createElement("tr");
              tr.style.background = alternate ? "#f8fafc" : "#ffffff";
              alternate = !alternate;
              
              tr.innerHTML = `
                <td style="padding: 8px; border: 1px solid #cbd5e1; font-weight:600; text-align:left;">${storeName}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1; text-align:center; color:#16a34a; font-weight:600;">${stats.completed}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1; text-align:center; color:#d97706;">${stats.pending}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1; text-align:center; color:#4b5563;">${stats.not_interested}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1; text-align:center; color:#dc2626; font-weight:600;">${stats.issues}</td>
                <td style="padding: 8px; border: 1px solid #cbd5e1; text-align:center; font-weight:bold;">${stats.total}</td>
              `;
              reportStoresBody.appendChild(tr);
            });
          }
        }
      } catch (err) {
        console.error("Generate printable report error:", err);
      }
    }

    const printReportBtn = document.getElementById("printReportBtn");
    if (printReportBtn) {
      printReportBtn.addEventListener("click", () => {
        window.print();
      });
    }

    // Escape key to close modals
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (dmModalOverlay && dmModalOverlay.style.display !== 'none') closeDmModal();
        if (editModalOverlay && editModalOverlay.style.display !== 'none') closeEditModal();
        if (deleteModalOverlay && deleteModalOverlay.style.display !== 'none') closeDeleteModal();
        if (userModalOverlay && userModalOverlay.style.display !== 'none') closeUserModal();
        if (userDeleteModalOverlay && userDeleteModalOverlay.style.display !== 'none') closeUserDeleteModal();
      }
    });

    // Store Wise Summary Table View Toggle
    const btnSimple = document.getElementById("btnStoreSimpleView");
    const btnFull = document.getElementById("btnStoreFullView");
    const storeTable = document.getElementById("storeSummaryTable");
    
    if (btnSimple && btnFull && storeTable) {
      btnSimple.addEventListener("click", () => {
        btnSimple.classList.add("active");
        btnFull.classList.remove("active");
        storeTable.classList.add("simple-view");
      });
      
      btnFull.addEventListener("click", () => {
        btnFull.classList.add("active");
        btnSimple.classList.remove("active");
        storeTable.classList.remove("simple-view");
      });
    }

    // Initialize fetches sequence
    (async () => {
      await loadStores();
      await fetchDashboardStats();
      await fetchCustomersList();
      await fetchAdvancedStats(new URLSearchParams());
    })();
  }
});
