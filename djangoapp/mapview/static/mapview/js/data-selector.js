class DataSelector {
    constructor() {
        this.modelSelect = document.getElementById('model-select');
        this.startDateInput = document.getElementById('start-date');
        this.endDateInput = document.getElementById('end-date');
        this.loadButton = document.getElementById('load-button');
        this.errorMessage = document.getElementById('error-message');
        this.dataTable = document.getElementById('data-table');
        this.tableBody = document.getElementById('table-body');
        this.loading = document.getElementById('loading');
        this.recordCount = document.getElementById('record-count');
        this.paginationContainer = document.getElementById('pagination');

        this.selectionHeader = document.getElementById('selection-header');
        this.selectionContent = document.getElementById('selection-content');
        this.selectionToggle = this.selectionHeader.querySelector('.section-toggle');

        this.previewHeader = document.getElementById('preview-header');
        this.previewContent = document.getElementById('preview-content');
        this.previewToggle = this.previewHeader.querySelector('.section-toggle');

        this.allData = [];
        this.currentPage = 1;
        this.rowsPerPage = 10;
        this.totalPages = 0;
        this.isSelectionExpanded = false;
        this.isPreviewExpanded = false;

        this.initializeDefaults();
        this.attachEventListeners();
    }

    initializeDefaults() {
        // TODO: Fix default values, maybe read one row from the database and set initial values accordingly
        this.startDateInput.value = '2025-01-01';
        this.endDateInput.value = '2025-01-01';
    }

    attachEventListeners() {
        this.loadButton.addEventListener('click', () => this.handleLoadData());
        this.startDateInput.addEventListener('change', () => this.clearErrorOnChange());
        this.endDateInput.addEventListener('change', () => this.clearErrorOnChange());
        this.selectionHeader.addEventListener('click', () => this.toggleSelection());
        this.previewHeader.addEventListener('click', () => this.togglePreview());
    }

    validateDateRange() {
        const startDate = new Date(this.startDateInput.value);
        const endDate = new Date(this.endDateInput.value);

        if (!this.startDateInput.value || !this.endDateInput.value) {
            this.showError('Please select both start and end dates');
            return false;
        }

        if (startDate > endDate) {
            this.showError('Start date must be before or equal to end date');
            return false;
        }

        const daysDifference = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24));
        if (daysDifference > 7) {
            this.showError('Date range cannot exceed 7 days');
            return false;
        }

        this.clearError();
        return true;
    }

    async handleLoadData() {
        if (!this.validateDateRange()) {
            return;
        }

        this.loading.style.display = 'block';
        this.loadButton.disabled = true;

        try {
            const response = await fetch(
                `/api/data/?model=${this.modelSelect.value}&`
                + `start_date=${this.startDateInput.value}&`
                + `end_date=${this.endDateInput.value}`
            );

            if (!response.ok) {
                this.showError(`HTTP error! status: ${response.status}`);
                return;
            }

            this.allData = await response.json();
            this.currentPage = 1;
            this.displayCurrentPage();

            if (!this.isPreviewExpanded) {
                this.togglePreview();
            }
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Error loading data. Please try again.');
        } finally {
            this.loading.style.display = 'none';
            this.loadButton.disabled = false;
        }
    }

    displayCurrentPage() {
        this.tableBody.innerHTML = '';

        if (!this.allData || this.allData.length === 0) {
            this.dataTable.classList.remove('show');
            this.recordCount.textContent = 'No records found';
            this.paginationContainer.innerHTML = '';
            return;
        }

        this.totalPages = Math.ceil(this.allData.length / this.rowsPerPage);
        const startIndex = (this.currentPage - 1) * this.rowsPerPage;
        const endIndex = Math.min(startIndex + this.rowsPerPage, this.allData.length);
        const pageData = this.allData.slice(startIndex, endIndex);

        pageData.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.date}</td>
                <td>${record.hour}</td>
                <td>${record.source}</td>
                <td>${record.destination}</td>
                <td>${record.passengers}</td>
            `;
            this.tableBody.appendChild(row);
        });

        this.dataTable.classList.add('show');
        this.updateRecordCount();
        this.renderPagination();
    }

    updateRecordCount() {
        this.recordCount.textContent = `Total: ${this.allData.length} record(s)`;
    }

    renderPagination() {
        this.paginationContainer.innerHTML = '';

        if (this.totalPages <= 1) {
            return;
        }

        const prevButton = document.createElement('button');
        prevButton.textContent = '← Previous';
        prevButton.className = 'pagination-btn';
        prevButton.disabled = this.currentPage === 1;
        prevButton.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.displayCurrentPage();
                this.scrollToTop();
            }
        });
        this.paginationContainer.appendChild(prevButton);

        const pageInputContainer = document.createElement('div');
        pageInputContainer.className = 'page-input-container';

        const pageInput = document.createElement('input');
        pageInput.type = 'number';
        pageInput.className = 'page-input';
        pageInput.min = '1';
        pageInput.max = this.totalPages;
        pageInput.value = this.currentPage;
        pageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handlePageInputChange(pageInput);
            }
        });
        pageInput.addEventListener('blur', () => {
            pageInput.value = this.currentPage;
        });

        const pageLabel = document.createElement('span');
        pageLabel.className = 'page-label';
        pageLabel.textContent = `of ${this.totalPages}`;

        pageInputContainer.appendChild(pageInput);
        pageInputContainer.appendChild(pageLabel);
        this.paginationContainer.appendChild(pageInputContainer);

        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next →';
        nextButton.className = 'pagination-btn';
        nextButton.disabled = this.currentPage === this.totalPages;
        nextButton.addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
                this.displayCurrentPage();
                this.scrollToTop();
            }
        });
        this.paginationContainer.appendChild(nextButton);
    }

    handlePageInputChange(pageInput) {
        const pageNumber = parseInt(pageInput.value, 10);

        if (isNaN(pageNumber)) {
            pageInput.value = this.currentPage;
            return;
        }

        if (pageNumber < 1 || pageNumber > this.totalPages) {
            pageInput.value = this.currentPage;
            return;
        }

        this.currentPage = pageNumber;
        this.displayCurrentPage();
        this.scrollToTop();
    }

    toggleSelection() {
        this.isSelectionExpanded = !this.isSelectionExpanded;
        
        if (this.isSelectionExpanded) {
            this.selectionContent.classList.add('expanded');
            this.selectionToggle.textContent = '▼';
        } else {
            this.selectionContent.classList.remove('expanded');
            this.selectionToggle.textContent = '▶';
        }
    }

    togglePreview() {
        this.isPreviewExpanded = !this.isPreviewExpanded;
        
        if (this.isPreviewExpanded) {
            this.previewContent.classList.add('expanded');
            this.previewToggle.textContent = '▼';
        } else {
            this.previewContent.classList.remove('expanded');
            this.previewToggle.textContent = '▶';
        }
    }

    scrollToTop() {
        const sidePanel = document.getElementById('side-panel');
        if (sidePanel) {
            sidePanel.scrollTop = sidePanel.scrollHeight - sidePanel.clientHeight;
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
    }

    clearError() {
        this.errorMessage.style.display = 'none';
    }

    clearErrorOnChange() {
        if (this.errorMessage.style.display !== 'none') {
            this.validateDateRange();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DataSelector();
});