/**
 * Session Manager Service
 * Handles session refresh, retry logic, and API interceptors
 */

const SESSION_REFRESH_CONFIG = {
    EXPIRY_THRESHOLD: 120000, // 120 seconds (2 minutes)
    COOLDOWN_PERIOD: 300000, // 5 minutes between proactive refreshes
    RETRY_BACKOFF: [250, 1000, 2000], // 250ms, 1s, 2s
    MAX_RETRIES: 3,
};

class SessionManager {
    constructor() {
        this.lastRefreshTime = 0;
        this.isRefreshing = false;
        this.refreshPromise = null;
    }

    /**
     * Check if session needs refresh and perform if needed
     */
    async checkAndRefreshSession() {
        // Respect cooldown period
        const now = Date.now();
        if (
            now - this.lastRefreshTime <
            SESSION_REFRESH_CONFIG.COOLDOWN_PERIOD
        ) {
            return false;
        }

        try {
            const response = await fetch(
                "http://localhost:5001/api/v1/session/info",
                {
                    method: "GET",
                    credentials: "include",
                }
            );

            if (response.ok) {
                const data = await response.json();
                if (data.expires_at) {
                    const expiresAt = new Date(data.expires_at).getTime();
                    const timeUntilExpiry = expiresAt - now;

                    if (
                        timeUntilExpiry <=
                        SESSION_REFRESH_CONFIG.EXPIRY_THRESHOLD
                    ) {
                        return await this.refreshSession();
                    }
                }
            }
        } catch (error) {
            console.error("Failed to check session status:", error);
        }

        return false;
    }

    /**
     * Refresh the current session
     */
    async refreshSession() {
        if (this.isRefreshing) {
            return this.refreshPromise;
        }

        this.isRefreshing = true;
        this.refreshPromise = this._performRefresh();

        try {
            const result = await this.refreshPromise;
            this.lastRefreshTime = Date.now();
            return result;
        } finally {
            this.isRefreshing = false;
            this.refreshPromise = null;
        }
    }

    async _performRefresh() {
        try {
            const response = await fetch(
                "http://localhost:5001/api/v1/auth/refresh",
                {
                    method: "POST",
                    credentials: "include",
                }
            );

            if (response.ok) {
                const data = await response.json();
                console.log("Session refreshed successfully:", data);
                return true;
            } else {
                console.error("Session refresh failed:", response.status);
                return false;
            }
        } catch (error) {
            console.error("Session refresh error:", error);
            return false;
        }
    }

    /**
     * Handle API errors with retry logic
     */
    async handleApiError(response, originalRequest) {
        if (response.status === 401) {
            // Try to refresh session
            const refreshSuccess = await this.refreshSession();

            if (refreshSuccess) {
                // Retry original request with backoff
                return await this.retryWithBackoff(originalRequest);
            } else {
                // Refresh failed, logout user
                this.logoutUser();
                return null;
            }
        }

        return response;
    }

    /**
     * Retry request with exponential backoff
     */
    async retryWithBackoff(requestFn, attempt = 0) {
        if (attempt >= SESSION_REFRESH_CONFIG.MAX_RETRIES) {
            console.error("Max retries reached");
            this.logoutUser();
            return null;
        }

        try {
            const delay =
                SESSION_REFRESH_CONFIG.RETRY_BACKOFF[attempt] ||
                SESSION_REFRESH_CONFIG.RETRY_BACKOFF[
                    SESSION_REFRESH_CONFIG.RETRY_BACKOFF.length - 1
                ];

            await new Promise((resolve) => setTimeout(resolve, delay));

            const response = await requestFn();

            if (response.status === 401) {
                // Still getting 401, try again
                return await this.retryWithBackoff(requestFn, attempt + 1);
            }

            return response;
        } catch (error) {
            console.error(`Retry attempt ${attempt + 1} failed:`, error);
            return await this.retryWithBackoff(requestFn, attempt + 1);
        }
    }

    /**
     * Logout user and redirect to login
     */
    logoutUser() {
        // Clear Redux state
        if (window.store) {
            window.store.dispatch({ type: "user/logoutUser" });
        }

        // Clear any stored data
        localStorage.removeItem("user");
        sessionStorage.clear();

        // Redirect to login
        window.location.href = "/login";
    }

    /**
     * Logout from all sessions
     */
    async logoutAllSessions() {
        try {
            const response = await fetch(
                "http://localhost:5001/api/v1/logout-all",
                {
                    method: "POST",
                    credentials: "include",
                }
            );

            if (response.ok) {
                const data = await response.json();
                console.log("Logged out from all sessions:", data);
                this.logoutUser();
                return true;
            } else {
                console.error("Logout all failed:", response.status);
                return false;
            }
        } catch (error) {
            console.error("Logout all error:", error);
            return false;
        }
    }
}

// Create singleton instance
const sessionManager = new SessionManager();

export default sessionManager;
