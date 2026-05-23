import React from 'react';
import LoginForm from '../components/auth/LoginForm';
import '../components/auth/Auth.css';
import logoImage from './logo.png';


const LoginPage = () => {
    return (
        <div className="auth-container">
            <div className="auth-card">
               
                <div className="auth-card-visual">
                    <div className="auth-visual-content">
                        <div className="auth-visual-header">
                            
                            
                            <div className="auth-logo-container">
                                <img src={logoImage} alt="Video-R1 Logo" className="logo-img" />
                            </div>
                            
                            <div className="auth-visual-title">
                                <h1>
                                <span className="primary">VIDEO-R1</span> 
                                <span className="secondary"> SURVEILLANCE</span>
                                </h1>
                                <p>Détection de vols par modèle Vidéo-R1</p>
                            </div>

                            <div className="auth-status">
                                <span className="status-dot"></span>
                                <span>Système Opérationnel</span>
                            </div>
                        </div>
                        
                    </div>
                </div>
                
             
                <div className="auth-card-form-container">
                    <LoginForm />
                </div>
            </div>
        </div>
    );
};

export default LoginPage;