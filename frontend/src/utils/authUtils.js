/**
 * Authentication utility functions
 */

/**
 * Check if user is authenticated by calling the session info endpoint
 * @returns {Promise<boolean>} True if authenticated, false otherwise
 */
export const checkAuthStatus = async () => {
    try {
        const response = await fetch(
            "http://localhost:5001/api/v1/session/info",
            {
                method: "GET",
                credentials: "include", // Include session cookie
            }
        );

        if (response.ok) {
            const data = await response.json();
            return data.user_id ? true : false;
        }
        return false;
    } catch (error) {
        console.error("Auth check failed:", error);
        return false;
    }
};

/**
 * Get current user info from session
 * @returns {Promise<Object|null>} User object or null if not authenticated
 */
export const getCurrentUser = async () => {
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
            return data.user || null;
        }
        return null;
    } catch (error) {
        console.error("Get user info failed:", error);
        return null;
    }
};
