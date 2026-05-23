import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, setUnauthorizedCallback } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    
    useEffect(() => {
        setUnauthorizedCallback(() => {
            setUser(null);
            navigate('/login', { replace: true });
        });
    }, [navigate]);

    
    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        const token = sessionStorage.getItem('access_token');
        if (!token) {
            setLoading(false);
            return;
        }
        try {
            const response = await authAPI.getCurrentUser();
            setUser(response.data);
        } catch (err) {
        console.error('Failed to load user:', err);
        sessionStorage.removeItem('access_token');
        setUser(null);
        } finally {
        setLoading(false);
        }
    };

    // Login
    const login = async (username, password) => {
    try {
        setError(null);
        const response = await authAPI.login({ username, password });
        sessionStorage.setItem('access_token', response.data.access_token); 
        await loadUser();
        return { success: true };
    } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Login failed';
        setError(errorMsg);
        return { success: false, error: errorMsg };
    }
};

    // Register
    const register = async (userData) => {
        try {
            setError(null);
            await authAPI.register(userData);
            return { success: true };
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Registration failed';
            setError(errorMsg);
            return { success: false, error: errorMsg };
        }
    };

    // Logout
    const logout = async () => {
    try {
        await authAPI.logout();
    } catch (err) {
        console.error('Logout error:', err);
    } finally {
        sessionStorage.removeItem('access_token'); 
        setUser(null);
        navigate('/login', { replace: true });
    }
};

    const value = {
        user,
        loading,
        error,
        login,
        register,
        logout,
        isAuthenticated: !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
};
