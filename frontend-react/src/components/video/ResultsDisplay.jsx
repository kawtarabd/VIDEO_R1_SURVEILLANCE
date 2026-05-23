import React from 'react';
import './VideoComponents.css';

const ResultsDisplay = ({ result, mode }) => {
    if (!result) return null;

    const handleExportJSON = () => {
        const dataStr = JSON.stringify(result, null, 2);
        const dataUri =
            'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

        const exportFileDefaultName = `${mode}_result_${Date.now()}.json`;

        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    };

    /*
      IMPORTANT:
      On analyse uniquement la réponse finale / segments.answer,
      pas le thinking, car le raisonnement peut contenir des hésitations
      ou des contradictions.
    */
    const getAnalysisText = () => {
        if (result.segments && result.segments.length > 0) {
            return result.segments
                .map((segment) => segment.answer || '')
                .join(' ');
        }

        if (result.answer) return result.answer;
        if (result.raw_output) return result.raw_output;

        return JSON.stringify(result);
    };

    const extractConfidence = () => {
        const text = getAnalysisText().toUpperCase();

        if (
            text.includes('CONFIDENCE: HIGH') ||
            text.includes('HIGH (CLEAR THEFT)') ||
            text.includes('CLEAR THEFT')
        ) {
            return 'HIGH';
        }

        if (
            text.includes('CONFIDENCE: MEDIUM') ||
            text.includes('MEDIUM')
        ) {
            return 'MEDIUM';
        }

        if (
            text.includes('CONFIDENCE: LOW') ||
            text.includes('LOW')
        ) {
            return 'LOW';
        }

        return 'UNKNOWN';
    };

    const extractDecision = () => {
        const text = getAnalysisText().toLowerCase();

        const hasDetection =
            text.includes('confidence: high') ||
            text.includes('high (clear theft)') ||
            text.includes('clear theft') ||
            text.includes('possibly concealing') ||
            text.includes('concealing it') ||
            text.includes('concealment') ||
            text.includes('shoplifting') ||
            text.includes('theft') ||
            text.includes('suspicious') ||
            text.includes('comportement suspect');

        const hasNoDetection =
            text.includes('no shoplifting detected') ||
            text.includes('no suspicious activity detected') ||
            text.includes('no theft') ||
            text.includes('aucun vol détecté') ||
            text.includes('normal shopping behavior');

        if (hasDetection) {
            return 'Événement suspect détecté';
        }

        if (hasNoDetection) {
            return 'Aucun vol détecté';
        }

        return 'Analyse générale';
    };

    const extractMainAnswer = () => {
        if (result.segments && result.segments.length > 0) {
            return result.segments
                .map((segment, index) => {
                    return `Segment ${segment.segment || index + 1} (${segment.time_range || 'temps non défini'}):\n${segment.answer || 'Aucune réponse'}`;
                })
                .join('\n\n');
        }

        if (result.answer) return result.answer;
        if (result.raw_output) return result.raw_output;

        return JSON.stringify(result, null, 2);
    };

    const handleExportReport = () => {
        const confidence = extractConfidence();
        const decision = extractDecision();
        const answer = extractMainAnswer();

        const report = `
RAPPORT D'ANALYSE VIDÉO
========================

Date de génération : ${new Date().toLocaleString('fr-FR')}
Mode d'analyse : ${mode === 'detect' ? 'Détection automatique' : 'Analyse libre'}

Résumé de décision :
- Décision principale : ${decision}
- Niveau de confiance : ${confidence}

Réponse du modèle :
${answer}

Limite :
Ce rapport est généré automatiquement par un modèle d'intelligence artificielle.
Les résultats doivent être interprétés comme une aide à l'analyse et validés par un humain.
`;

        const blob = new Blob([report], {
            type: 'text/plain;charset=utf-8',
        });

        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `rapport_analyse_${Date.now()}.txt`;
        link.click();

        URL.revokeObjectURL(url);
    };

    const confidence = extractConfidence();
    const decision = extractDecision();

    const confidenceClass =
        confidence === 'HIGH'
            ? 'confidence-high'
            : confidence === 'MEDIUM'
            ? 'confidence-medium'
            : confidence === 'LOW'
            ? 'confidence-low'
            : 'confidence-unknown';

    return (
        <div className="results-display">
            <div className="results-header">
                <h3>
                    {mode === 'detect'
                        ? '🕵️ Résultats Détection'
                        : '💬 Résultat Analyse'}
                </h3>

                <div className="results-actions">
                    <button onClick={handleExportJSON} className="btn-export">
                        💾 Export JSON
                    </button>

                    <button onClick={handleExportReport} className="btn-export">
                        📄 Rapport TXT
                    </button>
                </div>
            </div>

            <div className="decision-card">
                <h4>🧾 Résumé de décision</h4>

                <div className="decision-grid">
                    <div>
                        <span className="decision-label">
                            Décision principale
                        </span>
                        <strong>{decision}</strong>
                    </div>

                    <div>
                        <span className="decision-label">
                            Niveau de confiance
                        </span>
                        <span className={`confidence-badge ${confidenceClass}`}>
                            {confidence}
                        </span>
                    </div>

                    <div>
                        <span className="decision-label">
                            Type d'analyse
                        </span>
                        <strong>
                            {mode === 'detect'
                                ? 'Détection automatique'
                                : 'Question libre'}
                        </strong>
                    </div>
                </div>

                <p className="decision-warning">
                    ⚠️ Résultat généré automatiquement. Une validation humaine
                    reste nécessaire.
                </p>
            </div>

            <div className="results-content">
                {result.thinking && (
                    <div className="result-section">
                        <h4>💭 Raisonnement</h4>

                        <div className="thinking-box">
                            {result.thinking.length > 500 ? (
                                <>
                                    <p>
                                        {result.thinking.substring(0, 500)}...
                                    </p>

                                    <details>
                                        <summary>
                                            Voir le raisonnement complet
                                        </summary>
                                        <p>{result.thinking}</p>
                                    </details>
                                </>
                            ) : (
                                <p>{result.thinking}</p>
                            )}
                        </div>
                    </div>
                )}

                {result.answer && (
                    <div className="result-section">
                        <h4>📋 Réponse</h4>

                        <div className="answer-box">
                            {result.answer.split('\n').map((line, i) => (
                                <p key={i}>{line}</p>
                            ))}
                        </div>
                    </div>
                )}

                {mode === 'detect' &&
                    result.segments &&
                    result.segments.length > 0 && (
                        <div className="result-section">
                            <h4>
                                📊 Segments Analysés ({result.segments.length})
                            </h4>

                            <div className="segments-list">
                                {result.segments.map((segment, idx) => {
                                    let timeRange = segment.time_range;

                                    if (!timeRange && segment.answer) {
                                        const match = segment.answer.match(
                                            /\((\d+\.?\d*s - \d+\.?\d*s)\)/
                                        );

                                        if (match) {
                                            timeRange = match[1];
                                        }
                                    }

                                    const answerText =
                                        segment.answer?.toLowerCase() || '';

                                    const isDetected =
                                        segment.answer &&
                                        !answerText.includes(
                                            'no shoplifting detected'
                                        ) &&
                                        !answerText.includes(
                                            'no suspicious activity detected'
                                        ) &&
                                        (
                                            answerText.includes(
                                                'confidence: high'
                                            ) ||
                                            answerText.includes(
                                                'high (clear theft)'
                                            ) ||
                                            answerText.includes(
                                                'clear theft'
                                            ) ||
                                            answerText.includes(
                                                'possibly concealing'
                                            ) ||
                                            answerText.includes(
                                                'concealing it'
                                            ) ||
                                            answerText.includes(
                                                'concealment'
                                            ) ||
                                            answerText.includes(
                                                'shoplifting'
                                            ) ||
                                            answerText.includes('theft') ||
                                            answerText.includes(
                                                'suspicious'
                                            )
                                        );

                                    return (
                                        <div
                                            key={idx}
                                            className={`segment-item ${
                                                isDetected ? 'detected' : ''
                                            }`}
                                        >
                                            <div className="segment-number">
                                                #{segment.segment || idx + 1}

                                                {isDetected && (
                                                    <span className="detection-badge">
                                                        ⚠️ DÉTECTÉ
                                                    </span>
                                                )}
                                            </div>

                                            <div className="segment-details">
                                                {timeRange && (
                                                    <div className="segment-time">
                                                        ⏱️ {timeRange}
                                                    </div>
                                                )}

                                                {segment.start_frame !==
                                                    undefined &&
                                                    segment.end_frame !==
                                                        undefined && (
                                                        <div className="segment-frames">
                                                            🎞️ Frames:{' '}
                                                            {
                                                                segment.start_frame
                                                            }{' '}
                                                            →{' '}
                                                            {segment.end_frame}
                                                        </div>
                                                    )}

                                                {segment.answer && (
                                                    <div className="segment-answer">
                                                        <strong>
                                                            📋 Réponse:
                                                        </strong>

                                                        <div className="segment-answer-text">
                                                            {segment.answer}
                                                        </div>
                                                    </div>
                                                )}

                                                {segment.thinking &&
                                                    segment.thinking.length >
                                                        100 && (
                                                        <details className="segment-thinking">
                                                            <summary>
                                                                💭 Voir le
                                                                raisonnement
                                                                complet
                                                            </summary>

                                                            <div className="thinking-content">
                                                                {
                                                                    segment.thinking
                                                                }
                                                            </div>
                                                        </details>
                                                    )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                {result.metadata && (
                    <div className="result-section">
                        <h4>ℹ️ Métadonnées</h4>

                        <div className="metadata-grid">
                            {Object.entries(result.metadata).map(
                                ([key, value]) => (
                                    <div
                                        key={key}
                                        className="metadata-item"
                                    >
                                        <span className="metadata-key">
                                            {key}:
                                        </span>

                                        <span className="metadata-value">
                                            {JSON.stringify(value)}
                                        </span>
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                )}

                {result.error && (
                    <div className="result-section error">
                        <h4>❌ Erreur</h4>

                        <div className="error-box">
                            {result.error}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ResultsDisplay;