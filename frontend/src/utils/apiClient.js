/**
 * Enhanced API Client
 * Integrates with session manager for automatic session refresh and retry logic
 */

import sessionManager from "../services/sessionManager.js";

class ApiClient {
    constructor(baseURL = "http://localhost:5001") {
        this.baseURL = baseURL;
    }

    /**
     * Make an API request with session management
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        // Set default options
        const requestOptions = {
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            ...options,
        };

        // Make the request
        const response = await fetch(url, requestOptions);

        // Handle 401 errors with retry logic
        if (response.status === 401) {
            const retryResponse = await sessionManager.handleApiError(
                response,
                () => fetch(url, requestOptions)
            );

            if (retryResponse) {
                return retryResponse;
            } else {
                // Session refresh failed, user will be logged out
                throw new Error("Authentication failed");
            }
        }

        return response;
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, {
            method: "GET",
            ...options,
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data, options = {}) {
        return this.request(endpoint, {
            method: "POST",
            body: JSON.stringify(data),
            ...options,
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data, options = {}) {
        return this.request(endpoint, {
            method: "PUT",
            body: JSON.stringify(data),
            ...options,
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            method: "DELETE",
            ...options,
        });
    }

    /**
     * Handle JSON response
     */
    async handleResponse(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
                errorData.error ||
                    `HTTP ${response.status}: ${response.statusText}`
            );
        }

        return response.json();
    }

    /**
     * Make request and return JSON data
     */
    async getJSON(endpoint, options = {}) {
        const response = await this.get(endpoint, options);
        return this.handleResponse(response);
    }

    async postJSON(endpoint, data, options = {}) {
        const response = await this.post(endpoint, data, options);
        return this.handleResponse(response);
    }

    async putJSON(endpoint, data, options = {}) {
        const response = await this.put(endpoint, data, options);
        return this.handleResponse(response);
    }

    async deleteJSON(endpoint, options = {}) {
        const response = await this.delete(endpoint, options);
        return this.handleResponse(response);
    }
}

// Create singleton instance
const apiClient = new ApiClient();

export default apiClient;
