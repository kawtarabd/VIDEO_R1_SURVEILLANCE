import React, { useState } from 'react';
import './VideoComponents.css';

const AnalyzeMode = ({ video, onAnalyze, isProcessing }) => {
    const [question, setQuestion] = useState('');
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [config, setConfig] = useState({
    frames: 64,
    resolution: 672,
    smart: true,
    multipass: false,        
    cumulative: false,       
    overlap: 0,              
    span: null,
    start: null,
    end: null,
    start_frame: null,
    end_frame: null,
    pass1_frames: 16,        
    pass2_frames: 64,        
    pass2_window: 8.0        
});

    const handleChange = (field, value) => {
        setConfig({ ...config, [field]: value });
    };

    const handleLaunch = () => {
        if (!video) {
            alert('Veuillez d\'abord uploader une vidéo');
            return;
        }
        if (!question.trim()) {
            alert('Veuillez entrer une question');
            return;
        }
        onAnalyze(question, config);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleLaunch();
        }
    };

    return (
        <div className="analyze-mode">
            <h3 className="section-title">💬 Analyse Libre - Posez votre Question</h3>

            <div className="analyze-form">
                {/* Question Input */}
                <div className="form-group">
                    <label>Votre question (obligatoire)</label>
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ex: Combien de personnes sont dans la vidéo?&#10;Ex: Y a-t-il un vol?&#10;Ex: Décris ce qui se passe entre 00:10 et 00:30"
                        disabled={isProcessing}
                        className="question-textarea"
                        rows="4"
                    />
                    <small className="form-hint">
                        💡 Astuce: Appuyez sur Ctrl+Enter pour lancer
                    </small>
                </div>

               
                <div className="quick-questions">
                    <label>Exemples rapides:</label>
                    <div className="question-chips">
                        <button
                            onClick={() => setQuestion("Y a-t-il un vol dans cette vidéo?")}
                            disabled={isProcessing}
                            className="chip"
                        >
                            Y a-t-il un vol?
                        </button>
                        <button
                            onClick={() => setQuestion("Combien de personnes sont visibles?")}
                            disabled={isProcessing}
                            className="chip"
                        >
                            Combien de personnes?
                        </button>
                        <button
                            onClick={() => setQuestion("Décris tous les événements dans la vidéo")}
                            disabled={isProcessing}
                            className="chip"
                        >
                            Décris les événements
                        </button>
                        <button
                            onClick={() => setQuestion("Quels comportements suspects sont détectés?")}
                            disabled={isProcessing}
                            className="chip"
                        >
                            Comportements suspects
                        </button>
                    </div>
                </div>

               
                <div className="advanced-toggle">
                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        disabled={isProcessing}
                        className="toggle-btn"
                    >
                        {showAdvanced ? '▼' : '▶'} Paramètres avancés (optionnel)
                    </button>
                </div>

                
                {showAdvanced && (
                    <div className="advanced-params-box">
                        <div className="advanced-grid">
                            {/* Frames */}
                            <div className="form-group">
                                <label>Frames: <strong>{config.frames}</strong></label>
                                <div className="input-with-slider">
                                    <input
                                        type="range"
                                        min="16"
                                        max="128"
                                        value={config.frames}
                                        onChange={(e) => handleChange('frames', parseInt(e.target.value))}
                                        disabled={isProcessing}
                                        className="form-slider"
                                    />
                                    <input
                                        type="number"
                                        min="16"
                                        max="128"
                                        value={config.frames}
                                        onChange={(e) => handleChange('frames', parseInt(e.target.value) || 16)}
                                        disabled={isProcessing}
                                        className="form-number-small"
                                    />
                                </div>
                            </div>

                           
                            <div className="form-group">
                                <label>Résolution</label>
                                <select
                                    value={config.resolution}
                                    onChange={(e) => handleChange('resolution', parseInt(e.target.value))}
                                    disabled={isProcessing}
                                    className="form-select"
                                >
                                    <option value="448">448px</option>
                                    <option value="560">560px</option>
                                    <option value="672">672px</option>
                                </select>
                            </div>

                          
                            <div className="form-group">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={config.smart}
                                        onChange={(e) => handleChange('smart', e.target.checked)}
                                        disabled={isProcessing}
                                    />
                                    <span>🧠 Smart Mode</span>
                                </label>
                            </div>

                            
                            <div className="form-group">
                                <label>Début (secondes)</label>
                                <input
                                    type="number"
                                    min="0"
                                    step="0.5"
                                    value={config.start || ''}
                                    onChange={(e) => handleChange('start', e.target.value ? parseFloat(e.target.value) : null)}
                                    placeholder="Ex: 10"
                                    disabled={isProcessing}
                                    className="form-input"
                                />
                            </div>

                            <div className="form-group">
                                <label>Fin (secondes)</label>
                                <input
                                    type="number"
                                    min="0"
                                    step="0.5"
                                    value={config.end || ''}
                                    onChange={(e) => handleChange('end', e.target.value ? parseFloat(e.target.value) : null)}
                                    placeholder="Ex: 30"
                                    disabled={isProcessing}
                                    className="form-input"
                                />
                            </div>
                        </div>
                    </div>
                )}

                
                <button
                    onClick={handleLaunch}
                    disabled={!video || !question.trim() || isProcessing}
                    className="btn-launch"
                >
                    {isProcessing ? (
                        <>
                            <span className="spinner"></span>
                            Analyse en cours...
                        </>
                    ) : (
                        <>
                            ▶️ Lancer l'Analyse
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default AnalyzeMode;