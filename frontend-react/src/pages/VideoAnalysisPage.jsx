import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { videoAPI } from '../services/api';
import ModeSelector from '../components/video/ModeSelector';
import VideoUpload from '../components/video/VideoUpload';
import DetectMode from '../components/video/DetectMode';
import AnalyzeMode from '../components/video/AnalyzeMode';
import ResultsDisplay from '../components/video/ResultsDisplay';
import './VideoAnalysisPage.css';

const VideoAnalysisPage = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    
    // ÉTAT DE L'APPLICATION
   
    const [mode, setMode] = useState('detect'); // Mode détection ou analyse
    const [uploadedVideo, setUploadedVideo] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
   
    
   
    const pollIntervalRef = useRef(null);
    
    const isMountedRef = useRef(true);
    
    
    
    useEffect(() => {
    isMountedRef.current = true;

    return () => {
        isMountedRef.current = false;

        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            console.log('Polling arrêté - page fermée');
        }
    };
}, []);

    
    // GÉRER L'UPLOAD D'UNE VIDÉO
    
    const handleVideoUpload = async (file) => {
        setIsUploading(true);
        setError(null);

        try {
            
            const formData = new FormData();
            formData.append('file', file);

            
            const response = await videoAPI.upload(formData);
            setUploadedVideo(response.data);
            
          
            setResult(null);
        } catch (err) {
            setError(err.response?.data?.detail || 'Erreur lors de l\'upload');
            console.error('Erreur upload:', err);
        } finally {
            setIsUploading(false);
        }
    };

    
    // GÉRER LA DÉTECTION
    
    const handleDetect = async (config) => {
         if (!uploadedVideo) {
    setError("Veuillez d'abord uploader une vidéo");
    return;
  }

    setIsProcessing(true);
    setError(null);  
    setResult(null);

    try {
        const detectResponse = await videoAPI.detect({
            video_id: uploadedVideo.id,
            ...config
        });

        console.log('Détection lancée:', detectResponse.data);

      
        await pollResults(uploadedVideo.id);

    } catch (err) {
        
        setError(err.response?.data?.detail || 'Erreur lors de la détection');
        console.error('Erreur détection:', err);
        setIsProcessing(false);
    }
};

    
    // GÉRER L'ANALYSE (Mode question libre)
    
    const handleAnalyze = async (question, config) => {
    if (!uploadedVideo) {
        setError("Veuillez d'abord uploader une vidéo");
        return;
    }

    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
        const analyzeResponse = await videoAPI.detect({
            video_id: uploadedVideo.id,
            detection_type: 'general',
            custom_question: question,
            ...config
        });

        console.log('Analyse lancée:', analyzeResponse.data);
        await pollResults(uploadedVideo.id);

    } catch (err) {
        setError(err.response?.data?.detail || 'Erreur lors de l\'analyse');
        console.error('Erreur analyse:', err);
        setIsProcessing(false);
    }
};
    
  
   
const pollResults = async (videoId) => {
    const maxAttempts = 120;
    let attempts = 0;

    return new Promise((resolve, reject) => {
        pollIntervalRef.current = setInterval(async () => {
            attempts++;

    
            if (!isMountedRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
                return;
            }

            try {
                const videoResponse = await videoAPI.getVideo(videoId);
                const video = videoResponse.data;

                if (video.status === 'completed') {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    try {
                        const detectionsResponse = await videoAPI.getDetections(videoId);
                        const detections = detectionsResponse.data;

                        
                        if (!isMountedRef.current) return;

                        if (detections && detections.length > 0) {
                            setResult(detections[0].result);  
                            setError(null);                    
                        } else {
                            setError('Aucun résultat trouvé'); 
                        }
                    } catch {
                        if (!isMountedRef.current) return;
                        setError('Erreur récupération');       
                    }

                    if (!isMountedRef.current) return;
                    setIsProcessing(false);                    
                    resolve();

                                } else if (video.status === 'failed') {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    if (!isMountedRef.current) return;
                    setError("L'analyse a échoué");
                    setIsProcessing(false);
                    reject(new Error('Analyse échouée'));

                } else if (attempts >= maxAttempts) {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    if (!isMountedRef.current) return;
                    setError("L'analyse prend trop de temps");
                    setIsProcessing(false);
                    reject(new Error('Timeout'));
                }

            } catch (err) {
                if (attempts >= 3) {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    if (!isMountedRef.current) return;
                    setError('Erreur de connexion');       
                    setIsProcessing(false);                   
                    reject(err);
                }
            }
        }, 5000);
    });
};
    
    // GÉRER LE CHANGEMENT DE MODE
    
    const handleModeChange = (newMode) => {
        setMode(newMode);
        // Efface les résultats lors du changement de mode
        setResult(null);
        setError(null);
    };

    return (
        <div className="video-analysis-page">
            
            <header className="page-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1>🎯 Video-R1 Surveillance</h1>
                        <p className="header-subtitle">
                            Analyse intelligente de vidéos par IA
                        </p>
                    </div>
                    <div className="header-right">
                        <div className="user-info">
                            <div className="user-avatar">
                                {user?.username?.charAt(0).toUpperCase()}
                            </div>
                            <span className="user-name">{user?.username}</span>
                        </div>
                        {user?.is_admin && (
                         <button onClick={() => navigate('/admin')} className="admin-btn" >
                             ⚙️ Admin
                         </button>
                           )}
                        <button onClick={logout} className="btn-logout-header">
                            🚪 Déconnexion
                        </button>
                    </div>
                </div>
            </header>

           
            <main className="page-main">
                <div className="content-container">
                    
                  
                    <VideoUpload
                        video={uploadedVideo}
                        onUpload={handleVideoUpload}
                        isUploading={isUploading}
                    />

                  
                    <ModeSelector
                        mode={mode}
                        onModeChange={handleModeChange}
                        disabled={isProcessing}
                    />

                    
                    {error && (
                        <div className="error-banner">
                            <span className="error-icon">❌</span>
                            <span className="error-message">{error}</span>
                            <button 
                                onClick={() => setError(null)}
                                className="error-close"
                            >
                                ✕
                            </button>
                        </div>
                    )}

                    
                    {mode === 'detect' ? (
                        <DetectMode
                            video={uploadedVideo}
                            onDetect={handleDetect}
                            isProcessing={isProcessing}
                        />
                    ) : (
                        <AnalyzeMode
                            video={uploadedVideo}
                            onAnalyze={handleAnalyze}
                            isProcessing={isProcessing}
                        />
                    )}

                    
                    {result && (
                        <ResultsDisplay
                            result={result}
                            mode={mode}
                        />
                    )}

                    {isProcessing && (
                        <div className="processing-banner">
                            <div className="processing-content">
                                <div className="processing-spinner"></div>
                                <div className="processing-text">
                                    <strong>Analyse en cours...</strong>
                                    <p>Cela peut prendre quelques minutes</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default VideoAnalysisPage;