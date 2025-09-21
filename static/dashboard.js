class DashboardManager {
    constructor(config) {
        this.config = config;
        this.dashboard = null;
        this.isInitialized = false;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async initialize() {
        this.showLoadingState();

        try {
            const { DatabricksDashboard } = await import("https://cdn.jsdelivr.net/npm/@databricks/aibi-client@0.0.0-alpha.7/+esm");

            const container = document.getElementById("dashboard-content");

            this.dashboard = new DatabricksDashboard({
                instanceUrl: this.config.instanceUrl,
                workspaceId: this.config.workspaceId,
                dashboardId: this.config.dashboardId,
                token: this.config.token,
                container: container
            });

            this.hideLoadingState();

            await this.dashboard.initialize();

            this.isInitialized = true;

            setTimeout(() => {
                this.hideLoadingState();
                const container = document.getElementById('dashboard-content');
                const stillLoading = container.querySelector('.loading-container');
                if (stillLoading) {
                    container.removeChild(stillLoading);
                }
            }, 2000);

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.handleInitializationError(error);
        }
    }

    showLoadingState() {
        const container = document.getElementById('dashboard-content');
        container.innerHTML = `
            <div class="loading-container" id="loading-state">
                <div class="loading-spinner"></div>
                <div class="loading-text">Carregando Dashboard</div>
                <div class="loading-subtext">Conectando com Databricks Analytics...</div>
            </div>
        `;
    }

    hideLoadingState() {
        const loadingElements = document.querySelectorAll('.loading-container, #loading-state');
        loadingElements.forEach(element => {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });

        const container = document.getElementById('dashboard-content');
        const loadingInContainer = container.querySelector('.loading-container');
        if (loadingInContainer) {
            container.removeChild(loadingInContainer);
        }
    }

    handleInitializationError(error) {
        const container = document.getElementById('dashboard-content');

        container.innerHTML = `
            <div class="error-container">
                <div class="error-icon">!</div>
                <div class="error-title">Erro ao Carregar Dashboard</div>
                <div class="error-message">
                    ${this.getErrorMessage(error)}
                    ${this.retryCount < this.maxRetries ? '<br><br>Tentando novamente...' : ''}
                </div>
            </div>
        `;

        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            setTimeout(() => {
                this.initialize();
            }, 3000);
        }
    }

    getErrorMessage(error) {
        if (error.message.includes('token')) {
            return 'Erro de autenticação. Verifique as credenciais.';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
            return 'Erro de conexão. Verifique sua conexão com a internet.';
        } else if (error.message.includes('dashboard')) {
            return 'Dashboard não encontrado. Verifique o ID do dashboard.';
        } else {
            return `Erro inesperado: ${error.message}`;
        }
    }

    refresh() {
        if (this.isInitialized && this.dashboard) {
            this.dashboard.refresh();
        } else {
            this.initialize();
        }
    }
}

function setupRefreshButton() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (window.dashboardManager) {
                window.dashboardManager.refresh();
            }
        });
    }
}

function initializeTheme() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
        document.body.classList.add('dark-theme');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    setupRefreshButton();

    window.forceRemoveLoading = () => {
        const loadingElements = document.querySelectorAll('.loading-container, #loading-state');
        loadingElements.forEach(element => {
            if (element && element.parentNode) {
                element.parentNode.removeChild(element);
            }
        });
    };

    setTimeout(() => {
        window.forceRemoveLoading();
    }, 5000);
});

window.addEventListener('error', (event) => {
    console.error('Unhandled error:', event.error);
});

window.addEventListener('online', () => {
    if (window.dashboardManager && !window.dashboardManager.isInitialized) {
        window.dashboardManager.initialize();
    }
});

window.addEventListener('offline', () => {
    // Network connection lost - could implement additional logic here if needed
});

window.DashboardManager = DashboardManager;