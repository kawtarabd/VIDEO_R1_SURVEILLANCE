import React from 'react';
import './VideoComponents.css';

const ModeSelector = ({ mode, onModeChange, disabled }) => {
    return (
        <div className="mode-selector">
            <h3 className="mode-title">Choisissez le mode d'analyse</h3>
            <div className="mode-options">
                <label className={`mode-option ${mode === 'detect' ? 'active' : ''}`}>
                    <input
                        type="radio"
                        name="mode"
                        value="detect"
                        checked={mode === 'detect'}
                        onChange={(e) => onModeChange(e.target.value)}
                        disabled={disabled}
                    />
                    <div className="mode-content">
                        <div className="mode-icon">🕵️</div>
                        <div className="mode-info">
                            <strong>Détection Automatique</strong>
                            <p>Détection prédéfinie (vol, comportement suspect...)</p>
                        </div>
                    </div>
                </label>

                <label className={`mode-option ${mode === 'analyze' ? 'active' : ''}`}>
                    <input
                        type="radio"
                        name="mode"
                        value="analyze"
                        checked={mode === 'analyze'}
                        onChange={(e) => onModeChange(e.target.value)}
                        disabled={disabled}
                    />
                    <div className="mode-content">
                        <div className="mode-icon">💬</div>
                        <div className="mode-info">
                            <strong>Analyse Libre</strong>
                            <p>Posez votre propre question sur la vidéo</p>
                        </div>
                    </div>
                </label>
            </div>
        </div>
    );
};

export default ModeSelector;