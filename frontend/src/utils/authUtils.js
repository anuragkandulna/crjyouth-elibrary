/**
 * Authentication Utilities
 * Centralized functions for authentication-related tasks
 */

import apiClient from "./apiClient.js";

export const checkAuthStatus = async () => {
    try {
        const response = await apiClient.get("/api/v1/session/info");
        return response.ok;
    } catch (error) {
        console.error("Auth status check failed:", error);
        return false;
    }
};

export const getCurrentUser = async () => {
    try {
        const data = await apiClient.getJSON("/api/v1/session/info");
        return data.user || null;
    } catch (error) {
        console.error("Get user info failed:", error);
        return null;
    }
};

export const refreshSession = async () => {
    try {
        const data = await apiClient.postJSON("/api/v1/auth/refresh");
        return data;
    } catch (error) {
        console.error("Session refresh failed:", error);
        throw error;
    }
};
