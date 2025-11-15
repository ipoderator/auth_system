// API utility functions
const API_BASE_URL = '/api';

class AuthAPI {
    static async request(url, options = {}) {
        const token = localStorage.getItem('auth_token');
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };
        
        if (token) {
            headers['Authorization'] = `Token ${token}`;
        }
        
        const config = {
            ...options,
            headers,
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}${url}`, config);
            
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            if (!response.ok) {
                // Handle different error formats
                let errorMessage = `HTTP error! status: ${response.status}`;
                let errorData = null;
                
                if (typeof data === 'object') {
                    // Check for common error fields
                    if (data.error) {
                        errorMessage = data.error;
                    } else if (data.detail) {
                        errorMessage = data.detail;
                    } else if (data.message) {
                        errorMessage = data.message;
                    } else if (Array.isArray(data)) {
                        errorMessage = data.join(', ');
                    } else {
                        // Check if it's field errors object (like {email: [...], password: [...]})
                        const keys = Object.keys(data);
                        if (keys.length > 0) {
                            // Check if all values are arrays (field errors)
                            const isFieldErrors = keys.every(
                                key => Array.isArray(data[key])
                            );
                            if (isFieldErrors) {
                                // Return the error object for field-level handling
                                errorData = data;
                                // Create a general message from first error
                                const firstKey = keys[0];
                                errorMessage = Array.isArray(data[firstKey])
                                    ? data[firstKey][0]
                                    : data[firstKey];
                            } else {
                                // Try to extract first error message
                                const firstError = data[keys[0]];
                                errorMessage = Array.isArray(firstError)
                                    ? firstError[0]
                                    : firstError;
                            }
                        }
                    }
                } else if (typeof data === 'string') {
                    errorMessage = data;
                }
                
                const error = new Error(errorMessage);
                if (errorData) {
                    error.data = errorData;
                }
                throw error;
            }
            
            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                errorData: error.data || null
            };
        }
    }
    
    static async register(userData) {
        return this.request('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }
    
    static async login(email, password) {
        const result = await this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        
        if (result.success && result.data.token) {
            localStorage.setItem('auth_token', result.data.token);
            localStorage.setItem('user', JSON.stringify(result.data.user));
        }
        
        return result;
    }
    
    static async logout() {
        const result = await this.request('/auth/logout/', {
            method: 'POST',
        });
        
        if (result.success) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
        }
        
        return result;
    }
    
    static async getProfile() {
        return this.request('/auth/profile/me/');
    }
    
    static async updateProfile(profileData) {
        return this.request('/auth/profile/update_profile/', {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    }
    
    static async deleteAccount() {
        const result = await this.request('/auth/profile/delete_account/', {
            method: 'DELETE',
        });
        
        if (result.success) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
        }
        
        return result;
    }
    
    static isAuthenticated() {
        return !!localStorage.getItem('auth_token');
    }
    
    static getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }
}

