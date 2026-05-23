import React, { useState } from 'react';
import './VideoComponents.css';

const DetectMode = ({ video, onDetect, isProcessing }) => {
    const [config, setConfig] = useState({
        detection_type: 'shoplifting',
        frames: 64,
        resolution: 672,
        smart: true,
        cumulative: true,
        multipass: false,
        overlap: 16,
        span: null,
        start: null,
        end: null,
        start_frame: null,
        end_frame: null,
        pass1_frames: 16,
        pass2_frames: 64,
        pass2_window: 8.0,
    });

    const handleChange = (field, value) => {
        setConfig({ ...config, [field]: value });
    };

    const handleLaunch = () => {
        if (!video) {
            alert('Veuillez d\'abord uploader une vidéo');
            return;
        }
        onDetect(config);
    };

    return (
        <div className="detect-mode">
            <h3 className="section-title">🕵️ Configuration Détection Automatique</h3>

            <div className="config-form">
               
                <div className="form-group">
                    <label>Type de détection</label>
                    <select
                        value={config.detection_type}
                        onChange={(e) => handleChange('detection_type', e.target.value)}
                        disabled={isProcessing}
                        className="form-select"
                    >
                        <option value="shoplifting">🛒 Shoplifting (Vol à l'étalage)</option>
                        <option value="suspicious_behavior">👀 Suspicious Behavior</option>
                        <option value="checkout_interactions">💳 Checkout Interactions</option>
                        <option value="timeline">⏱️ Timeline</option>
                        <option value="crowd_analysis">👥 Crowd Analysis</option>
                        <option value="general">📝 General</option>
                    </select>
                </div>

                
                <div className="form-group">
                    <label>
                        Frames par segment: <strong>{config.frames}</strong>
                    </label>
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
                        <option value="448">448px (Rapide)</option>
                        <option value="560">560px (Équilibré)</option>
                        <option value="672">672px (Haute qualité)</option>
                    </select>
                </div>

          
                <div className="form-group-row">
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={config.smart}
                            onChange={(e) => handleChange('smart', e.target.checked)}
                            disabled={isProcessing}
                        />
                        <span>🧠 Smart Mode</span>
                    </label>

                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={config.cumulative}
                            onChange={(e) => handleChange('cumulative', e.target.checked)}
                            disabled={isProcessing}
                        />
                        <span>📚 Cumulative</span>
                    </label>

                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={config.multipass}
                            onChange={(e) => handleChange('multipass', e.target.checked)}
                            disabled={isProcessing}
                        />
                        <span>🔍 Multi-Pass</span>
                    </label>
                </div>

                
                <details className="advanced-params">
                    <summary>⚙️ Paramètres avancés</summary>
                    
                    <div className="advanced-grid">
                       
                        <div className="form-group">
                            <label>Overlap: <strong>{config.overlap}</strong></label>
                            <input
                                type="range"
                                min="0"
                                max="64"
                                step="4"
                                value={config.overlap}
                                onChange={(e) => handleChange('overlap', parseInt(e.target.value))}
                                disabled={isProcessing}
                                className="form-slider"
                            />
                        </div>



                
                         <div className="form-group">
                              <label>Span (secondes)</label>
                              <input
                                   type="number"
                                   min="0"
                                   step="1"
                                   value={config.span || ''}
                                   onChange={(e) => handleChange('span', e.target.value ? parseFloat(e.target.value) : null)}
                                   placeholder="Ex: 10 (répartir frames sur 10s)"
                                   disabled={isProcessing}
                                   className="form-input"
                            />
                                   <small className="form-hint">
                                    💡 Répartir les frames sur une durée spécifique
                                   </small>
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
                </details>

                {config.multipass && (
                    <div className="multipass-config">
                        <h4>🔍 Configuration Multi-Pass</h4>
                        <p className="multipass-description">
                            Pass 1: Scan rapide pour détecter les moments suspects<br/>
                            Pass 2: Analyse détaillée des moments détectés
                        </p>
                        
                        <div className="advanced-grid">
                            
                            <div className="form-group">
                                <label>Pass 1 Frames: <strong>{config.pass1_frames}</strong></label>
                                <div className="input-with-slider">
                                    <input
                                        type="range"
                                        min="8"
                                        max="32"
                                        value={config.pass1_frames}
                                        onChange={(e) => handleChange('pass1_frames', parseInt(e.target.value))}
                                        disabled={isProcessing}
                                        className="form-slider"
                                    />
                                    <input
                                        type="number"
                                        min="8"
                                        max="32"
                                        value={config.pass1_frames}
                                        onChange={(e) => handleChange('pass1_frames', parseInt(e.target.value) || 16)}
                                        disabled={isProcessing}
                                        className="form-number-small"
                                    />
                                </div>
                                <small className="form-hint">🚀 Scan rapide initial</small>
                            </div>

                            
                            <div className="form-group">
                                <label>Pass 2 Frames: <strong>{config.pass2_frames}</strong></label>
                                <div className="input-with-slider">
                                    <input
                                        type="range"
                                        min="32"
                                        max="128"
                                        value={config.pass2_frames}
                                        onChange={(e) => handleChange('pass2_frames', parseInt(e.target.value))}
                                        disabled={isProcessing}
                                        className="form-slider"
                                    />
                                    <input
                                        type="number"
                                        min="32"
                                        max="128"
                                        value={config.pass2_frames}
                                        onChange={(e) => handleChange('pass2_frames', parseInt(e.target.value) || 64)}
                                        disabled={isProcessing}
                                        className="form-number-small"
                                    />
                                </div>
                                <small className="form-hint">🔍 Analyse détaillée</small>
                            </div>

                       
                            <div className="form-group">
                                <label>Pass 2 Window (secondes)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="30"
                                    step="0.5"
                                    value={config.pass2_window}
                                    onChange={(e) => handleChange('pass2_window', parseFloat(e.target.value) || 8.0)}
                                    disabled={isProcessing}
                                    className="form-input"
                                />
                                <small className="form-hint">⏱️ Fenêtre temporelle de focus</small>
                            </div>
                        </div>
                    </div>
                )}

              
                <button
                    onClick={handleLaunch}
                    disabled={!video || isProcessing}
                    className="btn-launch"
                >
                    {isProcessing ? (
                        <>
                            <span className="spinner"></span>
                            Analyse en cours...
                        </>
                    ) : (
                        <>
                            ▶️ Lancer la Détection
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default DetectMode;