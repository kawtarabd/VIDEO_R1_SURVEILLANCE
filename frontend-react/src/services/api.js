import axios from 'axios';

// Base URL
const API_URL = 'http://localhost:8000';

// Creation axios 
const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
});


let onUnauthorized = null;

export const setUnauthorizedCallback = (callback) => {
    onUnauthorized = callback;
};


api.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle 401
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            sessionStorage.removeItem('access_token');
            if (onUnauthorized) {
                onUnauthorized(); // React Router navigation
            } else {
                window.location.href = '/login'; 
            }
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    register: (userData) => api.post('/auth/register', userData),
    login: (credentials) => api.post('/auth/login', credentials),
    getCurrentUser: () => api.get('/auth/me'),
    logout: () => api.post('/auth/logout'), //  call backend
};

// Video API
export const videoAPI = {
    upload: (formData, conversationId = null) => {
        const url = conversationId ? `/video/upload?conversation_id=${conversationId}` : '/video/upload';
        return api.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    getVideos: (params) => api.get('/video/videos', { params }),
    getVideo: (id) => api.get(`/video/videos/${id}`),
    detect: (data) => api.post('/video/detect', data),
    getDetections: (videoId) => api.get(`/video/videos/${videoId}/detections`),
    deleteVideo: (id) => api.delete(`/video/videos/${id}`), //  delete video
};

export default api;
