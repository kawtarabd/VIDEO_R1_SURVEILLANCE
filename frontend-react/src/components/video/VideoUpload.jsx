import React from 'react';
import './VideoComponents.css';

const VideoUpload = ({ video, onUpload, isUploading }) => {
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            onUpload(file);
        }
    };

    return (
        <div className="video-upload-section">
            <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                disabled={isUploading}
                id="video-upload-input"
                style={{ display: 'none' }}
            />
            
            {!video ? (
                <label 
                    htmlFor="video-upload-input" 
                    className={`upload-button ${isUploading ? 'uploading' : ''}`}
                >
                    <span className="upload-icon">📹</span>
                    <div className="upload-text">
                        <strong>{isUploading ? 'Upload en cours...' : 'Cliquez pour uploader une vidéo'}</strong>
                        <small>MP4, AVI, MOV, MKV</small>
                    </div>
                </label>
            ) : (
                <div className="video-info-card">
                    <div className="video-icon">✅</div>
                    <div className="video-details">
                        <strong>{video.original_filename}</strong>
                        <div className="video-meta">
                            <span>⏱️ {video.duration?.toFixed(1)}s</span>
                            <span>📐 {video.resolution}</span>
                            <span>🎞️ {video.fps?.toFixed(0)} fps</span>
                        </div>
                    </div>
                    <label 
                        htmlFor="video-upload-input" 
                        className="change-video-btn"
                        title="Changer de vidéo"
                    >
                        🔄
                    </label>
                </div>
            )}
        </div>
    );
};

export default VideoUpload;