import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { videoAPI } from '../services/api';
import { chatService } from '../services/chatService';
import VideoUpload from '../components/video/VideoUpload';
import DetectMode from '../components/video/DetectMode';
import AnalyzeMode from '../components/video/AnalyzeMode';
import ResultsDisplay from '../components/video/ResultsDisplay';
import './DashboardPage.css';
import logoImage from './logo.png'

const DashboardPage = () => {
    const { user, logout } = useAuth();

    
    // ÉTAT DE L'APPLICATION
    
    const [conversations, setConversations] = useState([]);
    const [currentConversation, setCurrentConversation] = useState(null);
    const [mode, setMode] = useState('detect'); // Mode détection auto ou question libre
    const [uploadedVideo, setUploadedVideo] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [allDetections, setAllDetections] = useState([]);
    const [selectedDetection, setSelectedDetection] = useState(null);
    const [showHistory, setShowHistory] = useState(false);
    
    const [error, setError] = useState(null);
    
    const pollIntervalRef = useRef(null);
    
    

    
    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                console.log(' Polling arrêté - composant démonté');
            }
        };
    }, []);
    
    
    // CHARGEMENT DES CONVERSATIONS AU DÉMARRAGE
    
    useEffect(() => {
        loadConversations();
    }, []);

    const loadConversations = async () => {
        try {
            const data = await chatService.getConversations();
            setConversations(data);
        } catch (err) {
            console.error('Impossible de charger les conversations:', err);
        }
    };

    
    // CHARGER TOUTES LES DÉTECTIONS D'UNE VIDÉO
    
    const loadDetections = async (videoId) => {
    try {
        console.log('Chargement détections pour video_id:', videoId);

        const response = await videoAPI.getDetections(videoId);
        const detections = response.data || [];

        console.log('Détections reçues:', detections.length);

        setAllDetections(detections);

        if (detections.length > 0) {
            setSelectedDetection(detections[0]);
            console.log('Détection sélectionnée:', detections[0].id);
        } else {
            setSelectedDetection(null);
        }

        return detections;

    } catch (err) {
        console.error('Erreur chargement détections:', err);
        return [];
    }
};

    
    // CRÉER UNE NOUVELLE CONVERSATION
    
    const handleNewConversation = async () => {
    try {
        const title = `Analyse ${new Date().toLocaleString('fr-FR')}`;
        const newConv = await chatService.createConversation(title);

        setConversations(prev => [newConv, ...prev]);
        setCurrentConversation(newConv.id);

        setUploadedVideo(null);
        setAllDetections([]);
        setSelectedDetection(null);
        setError(null);

        return newConv.id;
    } catch (err) {
        console.error('Erreur lors de la création:', err);
        return null;
    }
};

    
    // SÉLECTIONNER UNE CONVERSATION EXISTANTE
    
    const handleSelectConversation = async (convId) => {
        setCurrentConversation(convId);
        setError(null);
        
        try {
            // Récupère tous les messages de la conversation
            const messages = await chatService.getMessages(convId);
            
            const videoMessage = messages.find(m => 
                m.role === 'system' && m.content.includes('video_uploaded')
            );
            
            if (videoMessage) {
                try {
                    // Récupère les données structurées (JSON)
                    const data = JSON.parse(videoMessage.content);
                    const videoResponse = await videoAPI.getVideo(data.video_id);
                    setUploadedVideo(videoResponse.data);
                    
                    // Charge TOUTES les détections de cette vidéo
                    await loadDetections(data.video_id);
                    
                } catch (parseError) {
                    console.error('Erreur lors du parsing des données vidéo:', parseError);
                    setUploadedVideo(null);
                    setAllDetections([]);
                    setSelectedDetection(null);
                }
            } else {
                // Pas de vidéo dans cette conversation
                setUploadedVideo(null);
                setAllDetections([]);
                setSelectedDetection(null);
            }
            
        } catch (err) {
            console.error('Erreur lors du chargement:', err);
            setError('Impossible de charger cette conversation');
        }
    };

    
    // SUPPRIMER UNE CONVERSATION
    
    const handleDeleteConversation = async (convId) => {
    if (!window.confirm('Voulez-vous vraiment supprimer cette conversation ?')) {
        return;
    }

    try {
        await chatService.deleteConversation(convId);

        setConversations(prev => prev.filter(c => c.id !== convId));

        if (currentConversation === convId) {
            setCurrentConversation(null);
            setUploadedVideo(null);
            setAllDetections([]);
            setSelectedDetection(null);
        }
    } catch (err) {
        console.error('Erreur lors de la suppression:', err);
    }
};

    
    // UPLOAD D'UNE VIDÉO
    
    const handleVideoUpload = async (file) => {
        setIsUploading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await videoAPI.upload(formData);
            setUploadedVideo(response.data);
            
            await loadDetections(response.data.id);
            
            if (!currentConversation) {
                const title = `Analyse ${response.data.original_filename}`;
                const newConv = await chatService.createConversation(title);
                setConversations(prev => [newConv, ...prev]);
                setCurrentConversation(newConv.id);
                
                // Sauvegarde les infos de la vidéo en JSON structuré
                await chatService.addMessage(
                    newConv.id,
                    'system', 
                    JSON.stringify({
                        type: 'video_uploaded',
                        video_id: response.data.id,
                        filename: response.data.original_filename,
                        duration: response.data.duration,
                        resolution: response.data.resolution,
                        uploaded_at: new Date().toISOString()
                    })
                );
            } else {
                await chatService.addMessage(
                    currentConversation,
                    'system',
                    JSON.stringify({
                        type: 'video_uploaded',
                        video_id: response.data.id,
                        filename: response.data.original_filename
                    })
                );
            }
        } catch (err) {
            setError('Erreur lors de l\'upload de la vidéo');
            console.error(err);
        } finally {
            setIsUploading(false);
        }
    };

    
    // LANCER UNE DÉTECTION AUTOMATIQUE
    
    const handleDetect = async (config) => {
    if (!uploadedVideo) {
        setError('Veuillez d\'abord uploader une vidéo');
        return;
    }

    let convId = currentConversation;

    if (!convId) {
        const title = `Analyse ${uploadedVideo.original_filename}`;
        const newConv = await chatService.createConversation(title);
        setConversations(prev => [newConv, ...prev]);
        setCurrentConversation(newConv.id);
        convId = newConv.id;

        await chatService.addMessage(
            convId,
            'system',
            JSON.stringify({
                type: 'video_uploaded',
                video_id: uploadedVideo.id,
                filename: uploadedVideo.original_filename,
                duration: uploadedVideo.duration,
                resolution: uploadedVideo.resolution,
                uploaded_at: new Date().toISOString()
            })
        );
    }

    setIsProcessing(true);
    setError(null);

    try {
        await videoAPI.detect({
            video_id: uploadedVideo.id,
            ...config
        });

        await pollResults(uploadedVideo.id, convId);
    } catch (err) {
        setError('Erreur lors de la détection');
        console.error(err);
        setIsProcessing(false);
    }
};

    
    
    const handleAnalyze = async (question, config) => {
    if (!uploadedVideo) {
        setError('Veuillez d\'abord uploader une vidéo');
        return;
    }

    let convId = currentConversation;

    if (!convId) {
        const title = `Analyse ${uploadedVideo.original_filename}`;
        const newConv = await chatService.createConversation(title);
        setConversations(prev => [newConv, ...prev]);
        setCurrentConversation(newConv.id);
        convId = newConv.id;

        await chatService.addMessage(
            convId,
            'system',
            JSON.stringify({
                type: 'video_uploaded',
                video_id: uploadedVideo.id,
                filename: uploadedVideo.original_filename,
                duration: uploadedVideo.duration,
                resolution: uploadedVideo.resolution,
                uploaded_at: new Date().toISOString()
            })
        );
    }

    setIsProcessing(true);
    setError(null);

    try {
        await chatService.addMessage(
            convId,
            'user',
            question
        );

        await videoAPI.detect({
            video_id: uploadedVideo.id,
            detection_type: 'general',
            custom_question: question,
            ...config
        });

        await pollResults(uploadedVideo.id, convId);
    } catch (err) {
        setError('Erreur lors de l\'analyse');
        console.error(err);
        setIsProcessing(false);
    }
};
    
    
    const pollResults = async (videoId, convId = currentConversation) => { 
    const maxAttempts = 60; 
    let attempts = 0;

    return new Promise((resolve, reject) => {
        pollIntervalRef.current = setInterval(async () => {
            attempts++;

            try {
                const videoResponse = await videoAPI.getVideo(videoId);
                const video = videoResponse.data;

                if (video.status === 'completed') {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    console.log('✅ Analyse terminée!');

                    const detections = await loadDetections(videoId);

                    if (convId && detections.length > 0) {
                        const latest = detections[0];
                        const summary = typeof latest.result?.answer === 'string'
                            ? latest.result.answer.substring(0, 300)
                            : JSON.stringify(latest.result).substring(0, 300);

                        await chatService.addMessage(
                            convId,
                            'assistant',
                            `✅ Analyse terminée\n\n${summary}...`
                        );
                    }

                    setIsProcessing(false);
                    resolve();
                    return;
                }

                if (video.status === 'failed') {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    setError('L\'analyse a échoué');
                    setIsProcessing(false);
                    reject(new Error('Analysis failed'));
                    return;
                }

                if (attempts >= maxAttempts) {
                    clearInterval(pollIntervalRef.current);
                    pollIntervalRef.current = null;

                    setError('L\'analyse prend trop de temps');
                    setIsProcessing(false);
                    reject(new Error('Timeout'));
                    return;
                }
            } catch (err) {
                console.error('Erreur lors de la vérification:', err);
            }
        }, 5000);
    });
};
    
    
    const handleSelectDetection = (detection) => {
        console.log('🎯 Sélection détection:', detection.id);
        setSelectedDetection(detection);
    };

    return (
        <div className="dashboard-page">
           
            <header className="dashboard-header">

                <div className="header-content">
                    <div className="header-brand">
        <img src={logoImage} alt="Video-R1 Logo" className="header-logo" />
        <h1>Video-R1 Surveillance</h1>
    </div>
                    <div className="header-right">
                        <div className="user-info">
                            <div className="user-avatar">
                                {user?.username?.charAt(0).toUpperCase()}
                            </div>
                            <span>{user?.username}</span>
                        </div>
                        <button onClick={logout} className="btn-logout">
                            🚪
                        </button>
                    </div>
                </div>
            </header>

         
            <div className="dashboard-main">
                <aside className="conversations-sidebar">
                    <div className="sidebar-header">
                        <h2>💬 Historique</h2>
                        <button 
                            onClick={handleNewConversation}
                            className="btn-new-conv"
                            title="Nouvelle conversation"
                        >
                            ➕
                        </button>
                    </div>

                    <div className="conversations-list">
                        {conversations.length === 0 ? (
                            <div className="no-conversations">
                                <p>Aucune conversation</p>
                            </div>
                        ) : (
                            conversations.map(conv => (
                                <div
                                    key={conv.id}
                                    className={`conversation-item ${currentConversation === conv.id ? 'active' : ''}`}
                                    onClick={() => handleSelectConversation(conv.id)}
                                >
                                    <div className="conv-info">
                                        <h3>{conv.title}</h3>
                                        <span className="conv-date">
                                            {new Date(conv.created_at).toLocaleDateString('fr-FR')}
                                        </span>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteConversation(conv.id);
                                        }}
                                        className="btn-delete-conv"
                                        title="Supprimer"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </aside>

                <main className="main-area">
                    <VideoUpload
                        video={uploadedVideo}
                        onUpload={handleVideoUpload}
                        isUploading={isUploading}
                    />

                    <div className="mode-toggle">
                        <button
                            onClick={() => setMode('detect')}
                            className={`mode-btn ${mode === 'detect' ? 'active' : ''}`}
                            disabled={isProcessing}
                        >
                            🕵️ Détection Auto
                        </button>
                        <button
                            onClick={() => setMode('analyze')}
                            className={`mode-btn ${mode === 'analyze' ? 'active' : ''}`}
                            disabled={isProcessing}
                        >
                            💬 Question Libre
                        </button>
                    </div>

                    {error && (
                        <div className="error-banner">
                            ❌ {error}
                            <button onClick={() => setError(null)}>✕</button>
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

               
{allDetections.length > 0 && (
    <div className="history-toggle-container">
        <button 
            onClick={() => setShowHistory(!showHistory)}
            className="btn-toggle-history"
        >
            {showHistory ? '🔽 Masquer l\'historique' : '📊 Afficher l\'historique'} 
            ({allDetections.length})
        </button>
    </div>
)}


{showHistory && allDetections.length > 0 && (
    <div className="history-container">
        <h3 className="history-title">📊 Historique des Analyses ({allDetections.length})</h3>
        
        <div className="history-grid">
            {allDetections.map((detection) => (
                <div
                    key={detection.id}
                    onClick={() => handleSelectDetection(detection)}
                    className={`history-card ${selectedDetection?.id === detection.id ? 'selected' : ''}`}
                >
                    <div className="history-info">
                        <strong>
                            {detection.detection_type === 'general' ? '💬 Question Libre' : `🎯 ${detection.detection_type}`}
                        </strong>
                        <span>
                            {new Date(detection.created_at).toLocaleString('fr-FR')}
                        </span>
                    </div>
                    
                    {detection.confidence && (
                        <span 
                            className="confidence-badge"
                            style={{
                                backgroundColor: 
                                    detection.confidence === 'HIGH' ? '#059669' : 
                                    detection.confidence === 'MEDIUM' ? '#d97706' : '#dc2626'
                            }}
                        >
                            {detection.confidence}
                        </span>
                    )}
                </div>
            ))}
        </div>
    </div>
)}
                                  

                    {selectedDetection && (
                        <div style={{ marginTop: '24px' }}>
                            <ResultsDisplay
                                result={selectedDetection.result}
                                mode={mode}
                            />
                        </div>
                    )}

                    {isProcessing && (
                        <div className="processing-banner">
                            <div className="spinner"></div>
                            <div>
                                <strong>Analyse en cours...</strong>
                                <p>Cela peut prendre quelques minutes</p>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default DashboardPage;