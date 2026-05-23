import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Auth.css';

const LoginForm = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const result = await login(username, password);
            if (result.success) {
                navigate('/dashboard');
            } else {
                setError(result.error);
            }
        } catch (err) {
            setError('Erreur serveur. Réessayez.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-form">
            <div className="auth-header">
                <h1>
                <span className="primary">SE</span> 
                <span className="secondary"> CONNECTER</span>
                 </h1>
                <h2>Connectez-vous au centre de contrôle</h2>
                
            </div>

            {error && (
                <div className="alert alert-error">
                    ❌ {error}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        disabled={isLoading}
                        placeholder="user@example.com"
                        autoComplete="username"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password"> Password </label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={isLoading}
                        placeholder="••••••••"
                        autoComplete="current-password"
                    />
                </div>

                <button 
                    type="submit" 
                    className="btn btn-primary" 
                    disabled={isLoading}
                >
                    {isLoading && <span className="spinner"></span>}
                    {isLoading ? 'Authentification...' : 'Accéder au Système'}
                </button>
            </form>

            <p className="auth-footer">
                Nouveau sur Video-R1? <a href="/register">Créer un Compte</a>
            </p>
        </div>
    );
};

export default LoginForm;