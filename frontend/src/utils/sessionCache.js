/**
 * Session Cache Utility
 * Manages session state locally to reduce API calls and improve performance
 */

class SessionCache {
    constructor() {
        this.sessionData = null;
        this.lastRefresh = 0;
        this.refreshThreshold = 2 * 60 * 1000; // 2 minutes before expiry
        this.cacheKey = "crjyouth_session_cache";
        this.loadFromStorage();
    }

    /**
     * Load cached session data from localStorage
     */
    loadFromStorage() {
        try {
            const cached = localStorage.getItem(this.cacheKey);
            if (cached) {
                const data = JSON.parse(cached);
                // Check if cache is still valid
                if (data.expiresAt && data.expiresAt > Date.now()) {
                    this.sessionData = data;
                    this.lastRefresh = data.lastRefresh || 0;
                } else {
                    // Cache expired, clear it
                    this.clear();
                }
            }
        } catch (error) {
            console.error("Failed to load session cache:", error);
            this.clear();
        }
    }

    /**
     * Save session data to cache and localStorage
     */
    setSession(sessionData) {
        try {
            const cacheData = {
                user: sessionData.user,
                sessionId: sessionData.sessionId,
                expiresAt: sessionData.expiresAt
                    ? new Date(sessionData.expiresAt).getTime()
                    : null,
                lastRefresh: Date.now(),
                deviceId: sessionData.deviceId,
            };

            this.sessionData = cacheData;
            this.lastRefresh = cacheData.lastRefresh;

            // Save to localStorage
            localStorage.setItem(this.cacheKey, JSON.stringify(cacheData));

            console.log("Session cached successfully");
        } catch (error) {
            console.error("Failed to cache session:", error);
        }
    }

    /**
     * Get cached session data
     */
    getSession() {
        return this.sessionData;
    }

    /**
     * Get cached user data
     */
    getCachedUser() {
        return this.sessionData?.user || null;
    }

    /**
     * Check if session needs refresh
     */
    needsRefresh() {
        if (!this.sessionData || !this.sessionData.expiresAt) {
            return true;
        }

        const now = Date.now();
        const timeUntilExpiry = this.sessionData.expiresAt - now;

        // Refresh if within threshold or already expired
        return timeUntilExpiry <= this.refreshThreshold || timeUntilExpiry <= 0;
    }

    /**
     * Check if session is valid (not expired)
     */
    isValid() {
        if (!this.sessionData || !this.sessionData.expiresAt) {
            return false;
        }
        return this.sessionData.expiresAt > Date.now();
    }

    /**
     * Update session expiry time
     */
    updateExpiry(newExpiresAt) {
        if (this.sessionData) {
            this.sessionData.expiresAt = new Date(newExpiresAt).getTime();
            this.lastRefresh = Date.now();
            this.saveToStorage();
        }
    }

    /**
     * Save current cache to localStorage
     */
    saveToStorage() {
        try {
            if (this.sessionData) {
                localStorage.setItem(
                    this.cacheKey,
                    JSON.stringify(this.sessionData)
                );
            }
        } catch (error) {
            console.error("Failed to save session cache:", error);
        }
    }

    /**
     * Clear session cache
     */
    clear() {
        this.sessionData = null;
        this.lastRefresh = 0;
        localStorage.removeItem(this.cacheKey);
        console.log("Session cache cleared");
    }

    /**
     * Get time until session expires (in milliseconds)
     */
    getTimeUntilExpiry() {
        if (!this.sessionData || !this.sessionData.expiresAt) {
            return 0;
        }
        return Math.max(0, this.sessionData.expiresAt - Date.now());
    }

    /**
     * Check if session is near expiry (within 5 minutes)
     */
    isNearExpiry() {
        const timeUntilExpiry = this.getTimeUntilExpiry();
        return timeUntilExpiry > 0 && timeUntilExpiry <= 5 * 60 * 1000; // 5 minutes
    }
}

// Create singleton instance
const sessionCache = new SessionCache();

export default sessionCache;
