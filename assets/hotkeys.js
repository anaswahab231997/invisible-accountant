/**
 * Invisible Accountant — High-Performance Ergonomic Keyboard Engine (hotkeys.js)
 * Designed for UK Chartered Accountants & Ledger Power Users.
 * 
 * Features:
 * - 0ms perceived latency optimistic row execution (Ctrl+Enter)
 * - Row navigation with J/K or Up/Down arrows
 * - Slide-over inspection drawer toggle (Space / E / Esc)
 * - Date shorthand parser (t, +0, +30, 1410 -> YYYY-MM-DD)
 * - 1p VAT rounding hotkey (Alt+R)
 * - Global instant search focus (/ or Ctrl+K)
 */

(function () {
    'use strict';

    let activeRowIndex = 0;
    const ROW_SELECTOR = 'tr.triage-row';

    function getRows() {
        return Array.from(document.querySelectorAll(ROW_SELECTOR)).filter(r => !r.classList.contains('hidden') && r.offsetParent !== null);
    }

    function setActiveRow(index, scrollIntoView = true) {
        const rows = getRows();
        if (rows.length === 0) return;

        if (index < 0) index = 0;
        if (index >= rows.length) index = rows.length - 1;

        rows.forEach((r, idx) => {
            if (idx === index) {
                r.classList.add('active-row', 'ring-2', 'ring-blue-600', 'ring-inset', 'bg-blue-50/60');
                r.setAttribute('aria-selected', 'true');
                if (scrollIntoView) {
                    r.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                }
            } else {
                r.classList.remove('active-row', 'ring-2', 'ring-blue-600', 'ring-inset', 'bg-blue-50/60');
                r.setAttribute('aria-selected', 'false');
            }
        });

        activeRowIndex = index;
    }

    function getActiveRow() {
        const rows = getRows();
        return rows[activeRowIndex] || rows[0] || null;
    }

    // Optimistic Row Approval & Advance
    window.optimisticApprove = function (rowElement) {
        if (!rowElement) return;

        // Visual flash
        rowElement.classList.add('bg-emerald-100', 'transition-all', 'duration-150');
        
        // Find release button and trigger HTMX request
        const releaseBtn = rowElement.querySelector('[data-action="release"]');
        if (releaseBtn) {
            releaseBtn.click();
        }

        // Animate off DOM and advance focus
        setTimeout(() => {
            const nextIndex = activeRowIndex;
            rowElement.style.opacity = '0';
            rowElement.style.transform = 'translateX(20px)';
            rowElement.style.transition = 'all 0.15s ease-out';
            
            setTimeout(() => {
                rowElement.remove();
                setActiveRow(nextIndex, true);
                updateSummaryBadge(-1);
            }, 150);
        }, 50);
    };

    function updateSummaryBadge(delta) {
        const activeTabBadge = document.querySelector('nav a.active-tab span');
        if (activeTabBadge) {
            const current = parseInt(activeTabBadge.textContent.trim(), 10) || 0;
            const updated = Math.max(0, current + delta);
            activeTabBadge.textContent = updated;
        }
    }

    // Drawer Management
    let currentZoom = 1.0;
    let currentRotate = 0;
    let isThermalEnhanced = false;

    window.receiptZoom = function (delta) {
        const img = document.getElementById('active-receipt-img');
        if (!img) return;
        currentZoom = Math.min(3.0, Math.max(0.5, currentZoom + delta));
        applyReceiptTransform();
    };

    window.receiptRotate = function () {
        const img = document.getElementById('active-receipt-img');
        if (!img) return;
        currentRotate = (currentRotate + 90) % 360;
        applyReceiptTransform();
    };

    window.receiptToggleThermal = function () {
        const img = document.getElementById('active-receipt-img');
        if (!img) return;
        isThermalEnhanced = !isThermalEnhanced;
        if (isThermalEnhanced) {
            img.style.filter = 'contrast(190%) grayscale(100%) brightness(92%)';
        } else {
            img.style.filter = 'none';
        }
    };

    window.receiptReset = function () {
        currentZoom = 1.0;
        currentRotate = 0;
        isThermalEnhanced = false;
        const img = document.getElementById('active-receipt-img');
        if (img) img.style.filter = 'none';
        applyReceiptTransform();
    };

    function applyReceiptTransform() {
        const img = document.getElementById('active-receipt-img');
        if (img) {
            img.style.transform = `scale(${currentZoom}) rotate(${currentRotate}deg)`;
        }
    }

    window.openDrawer = function (contentHtml) {
        const drawer = document.getElementById('inspect-drawer');
        const overlay = document.getElementById('drawer-overlay');
        if (drawer) {
            drawer.classList.remove('translate-x-full');
            drawer.classList.add('translate-x-0');
        }
        if (overlay) {
            overlay.classList.remove('hidden');
        }
        window.receiptReset();
    };

    window.closeDrawer = function () {
        const drawer = document.getElementById('inspect-drawer');
        const overlay = document.getElementById('drawer-overlay');
        if (drawer) {
            drawer.classList.remove('translate-x-0');
            drawer.classList.add('translate-x-full');
        }
        if (overlay) {
            overlay.classList.add('hidden');
        }
    };

    window.toggleDrawer = function () {
        const drawer = document.getElementById('inspect-drawer');
        if (drawer && drawer.classList.contains('translate-x-0')) {
            window.closeDrawer();
        } else {
            const activeRow = getActiveRow();
            if (activeRow) {
                const inspectBtn = activeRow.querySelector('[data-action="inspect"]');
                if (inspectBtn) inspectBtn.click();
            }
        }
    };

    // Date Shorthand Parsing Engine
    window.parseDateShorthand = function (input) {
        const val = input.value.trim().toLowerCase();
        if (!val) return;

        const now = new Date();
        const yyyy = now.getFullYear();
        let targetDate = null;

        if (val === 't' || val === '+0' || val === 'today') {
            targetDate = now;
        } else if (val.startsWith('+') && !isNaN(parseInt(val.substring(1), 10))) {
            const days = parseInt(val.substring(1), 10);
            targetDate = new Date();
            targetDate.setDate(now.getDate() + days);
        } else if (/^\d{4}$/.test(val)) {
            // E.g. 1410 -> 14th Oct current year; 1402 -> 14th Feb current year
            const day = parseInt(val.substring(0, 2), 10);
            const month = parseInt(val.substring(2, 4), 10) - 1;
            targetDate = new Date(yyyy, month, day);
        }

        if (targetDate && !isNaN(targetDate.getTime())) {
            const y = targetDate.getFullYear();
            const m = String(targetDate.getMonth() + 1).padStart(2, '0');
            const d = String(targetDate.getDate()).padStart(2, '0');
            input.value = `${y}-${m}-${d}`;
        }
    };

    // Global Key Listener Matrix
    document.addEventListener('keydown', function (e) {
        const activeEl = document.activeElement;
        const isInput = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'SELECT' || activeEl.tagName === 'TEXTAREA');

        // Esc: Always closes drawer or cancels search
        if (e.key === 'Escape') {
            window.closeDrawer();
            if (isInput) activeEl.blur();
            return;
        }

        // Global Slash / Ctrl+K: Focus instant search
        if ((e.key === '/' && !isInput) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')) {
            e.preventDefault();
            const searchInput = document.getElementById('table-search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
            return;
        }

        // Ctrl+Enter: Instant Approve / Release
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const activeRow = getActiveRow();
            if (activeRow) {
                window.optimisticApprove(activeRow);
            }
            return;
        }

        // If user is actively typing in a text field, do not hijack standard keystrokes
        if (isInput) {
            // Check for Alt+R (1p Rounding)
            if (e.altKey && e.key.toLowerCase() === 'r') {
                e.preventDefault();
                const roundInput = document.getElementById('vat-rounding-line');
                if (roundInput) {
                    roundInput.value = '0.01';
                    roundInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
            return;
        }

        // TABLE NAVIGATION HOTKEYS (When NOT typing)
        switch (e.key) {
            case 'j':
            case 'ArrowDown':
                e.preventDefault();
                setActiveRow(activeRowIndex + 1);
                break;

            case 'k':
            case 'ArrowUp':
                e.preventDefault();
                setActiveRow(activeRowIndex - 1);
                break;

            case ' ':
                e.preventDefault();
                window.toggleDrawer();
                break;

            case 'e':
            case 't':
                e.preventDefault();
                const activeRow = getActiveRow();
                if (activeRow) {
                    const inspectBtn = activeRow.querySelector('[data-action="inspect"]');
                    if (inspectBtn) inspectBtn.click();
                }
                break;

            case 'Delete':
            case 'Backspace':
                e.preventDefault();
                const rowToDelete = getActiveRow();
                if (rowToDelete) {
                    const rejectBtn = rowToDelete.querySelector('[data-action="reject"]');
                    if (rejectBtn) {
                        rowToDelete.classList.add('bg-rose-100');
                        setTimeout(() => rejectBtn.click(), 100);
                    }
                }
                break;

            case 'r':
                // Refresh table
                const refreshBtn = document.getElementById('btn-refresh');
                if (refreshBtn) refreshBtn.click();
                break;
        }
    });

    // Client-side quick filter
    window.filterTable = function (query) {
        const q = (query || '').toLowerCase().trim();
        const rows = document.querySelectorAll(ROW_SELECTOR);
        rows.forEach(r => {
            const text = r.textContent.toLowerCase();
            if (!q || text.includes(q)) {
                r.classList.remove('hidden');
            } else {
                r.classList.add('hidden');
            }
        });
        setActiveRow(0);
    };

    // Attach date shorthands to dynamically loaded date fields
    document.addEventListener('focusout', function (e) {
        if (e.target && e.target.type === 'date' || (e.target.dataset && e.target.dataset.type === 'date')) {
            window.parseDateShorthand(e.target);
        }
    });

    // Initial load setup
    document.addEventListener('DOMContentLoaded', function () {
        setActiveRow(0, false);
    });

    // Handle HTMX DOM swaps to re-initialize active row
    document.addEventListener('htmx:afterSwap', function () {
        setActiveRow(activeRowIndex, false);
    });
})();
