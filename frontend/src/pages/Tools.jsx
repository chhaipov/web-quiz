import { useState } from 'react';
import { toolsApi } from '../api';
import { useToast } from '../context/ToastContext';
import ProtectedRoute from '../components/ProtectedRoute';

function ToolsContent() {
  const toast = useToast();

  const [template, setTemplate] = useState('Hello {{ user.username }}!');
  const [previewResult, setPreviewResult] = useState(null);
  const [previewing, setPreviewing] = useState(false);

  const [imageUrl, setImageUrl] = useState('');
  const [imageResult, setImageResult] = useState(null);
  const [validating, setValidating] = useState(false);

  const [filePath, setFilePath] = useState('');

  const handlePreview = (e) => {
    e.preventDefault();
    if (!template.trim()) return;
    setPreviewing(true);
    setPreviewResult(null);
    toolsApi
      .previewTemplate(template)
      .then((data) => setPreviewResult(data))
      .catch((e) => setPreviewResult({ error: e.response?.data?.error || 'Preview failed' }))
      .finally(() => setPreviewing(false));
  };

  const handleValidate = (e) => {
    e.preventDefault();
    if (!imageUrl.trim()) return;
    setValidating(true);
    setImageResult(null);
    toolsApi
      .validateImage(imageUrl.trim())
      .then((data) => setImageResult(data))
      .catch((e) => setImageResult({ error: e.response?.data?.error || 'Validation failed' }))
      .finally(() => setValidating(false));
  };

  const handleDownload = (e) => {
    e.preventDefault();
    if (!filePath.trim()) return;
    const url = toolsApi.downloadFile(filePath.trim());
    window.open(url, '_blank');
    toast.info('Download started');
  };

  return (
    <div className="page">
      <h1>Developer Tools</h1>
      <p className="subtitle">Utilities for testing and development</p>

      <div className="tools-grid">
        {/* Template Preview */}
        <section className="card tool-card">
          <h2>Template Preview</h2>
          <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>
            Preview dynamic templates before using them. Supports Django template syntax.
          </p>
          <form onSubmit={handlePreview} className="tool-form">
            <div className="form-group">
              <label htmlFor="template-input">Template String</label>
              <textarea
                id="template-input"
                rows="3"
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                placeholder="Hello {{ user.username }}!"
                disabled={previewing}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={previewing || !template.trim()}>
              {previewing ? 'Rendering…' : 'Preview'}
            </button>
          </form>
          {previewResult && (
            <div className={`tool-result ${previewResult.error ? 'tool-result-error' : ''}`}>
              <strong>{previewResult.error ? 'Error:' : 'Result:'}</strong>
              <pre>{previewResult.error || previewResult.rendered}</pre>
            </div>
          )}
        </section>

        {/* Image URL Validator */}
        <section className="card tool-card">
          <h2>Image URL Validator</h2>
          <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>
            Check if an image URL is valid and accessible before linking it.
          </p>
          <form onSubmit={handleValidate} className="tool-form">
            <div className="form-group">
              <label htmlFor="image-url">Image URL</label>
              <input
                id="image-url"
                type="text"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/image.png"
                disabled={validating}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={validating || !imageUrl.trim()}>
              {validating ? 'Validating…' : 'Validate URL'}
            </button>
          </form>
          {imageResult && (
            <div className={`tool-result ${imageResult.error || !imageResult.valid ? 'tool-result-error' : ''}`}>
              {imageResult.error ? (
                <p><strong>Error:</strong> {imageResult.error}</p>
              ) : (
                <>
                  <p><strong>Valid:</strong> {imageResult.valid ? 'Yes' : 'No'}</p>
                  <p><strong>Status:</strong> {imageResult.status_code}</p>
                  <p><strong>Content-Type:</strong> {imageResult.content_type}</p>
                  <p><strong>Size:</strong> {imageResult.content_length} bytes</p>
                </>
              )}
            </div>
          )}
        </section>

        {/* File Download */}
        <section className="card tool-card">
          <h2>File Download</h2>
          <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>
            Download files from the media storage. Enter the file path relative to the media directory.
          </p>
          <form onSubmit={handleDownload} className="tool-form">
            <div className="form-group">
              <label htmlFor="file-path">File Path</label>
              <input
                id="file-path"
                type="text"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="items/image.png"
                disabled={false}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={!filePath.trim()}>
              Download
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default function Tools() {
  return (
    <ProtectedRoute>
      <ToolsContent />
    </ProtectedRoute>
  );
}
