
import { useState } from "react";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import api from "./services/api";

function UploadDocument({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const allowedExtensions = [
    ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx"
  ];

  const handleFileChange = (selectedFile) => {
    setMessage("");
    setError("");

    if (!selectedFile) return;

    const extension = selectedFile.name
      .substring(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setError("Unsupported file type. Select PDF, PNG, JPG, TXT or DOCX.");
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("File size must not exceed 10 MB.");
      setFile(null);
      return;
    }

    if (selectedFile.size === 0) {
      setError("Empty files cannot be uploaded.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a document first.");
      return;
    }

    setUploading(true);
    setError("");
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post("/documents/upload", formData);

      setMessage(response.data.message);
      setFile(null);

      if (onUploadSuccess) {
        await onUploadSuccess();
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || "Document upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-panel">
      <div className="upload-heading">
        <div className="upload-heading-icon">
          <Upload size={25} />
        </div>
        <h2>Upload Document</h2>
        <p>Securely upload and encrypt your documents.</p>
      </div>

      <label className="upload-dropzone">
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt,.docx"
          hidden
          onChange={(e) => handleFileChange(e.target.files?.[0])}
        />

        <div className="upload-cloud-icon">
          <Upload size={30} />
        </div>

        <h3>Choose a document</h3>
        <p>Click here to browse files from your computer</p>
        <span>PDF, PNG, JPG, JPEG, TXT, DOCX · Maximum 10 MB</span>
      </label>

      {file && (
        <div className="selected-file">
          <FileText size={22} />
          <div>
            <strong>{file.name}</strong>
            <span>{(file.size / 1024).toFixed(2)} KB</span>
          </div>
          <button
            type="button"
            onClick={() => setFile(null)}
            disabled={uploading}
          >
            <X size={18} />
          </button>
        </div>
      )}

      {error && (
        <div className="upload-message error-message">
          <AlertCircle size={17} />
          {error}
        </div>
      )}

      {message && (
        <div className="upload-message success-message">
          <CheckCircle size={17} />
          {message}
        </div>
      )}

      <button
        className="upload-submit-button"
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        <Upload size={18} />
        {uploading ? "Uploading..." : "Upload & Encrypt"}
      </button>

      <div className="upload-security-note">
        <CheckCircle size={15} />
        Documents are encrypted using AES-256-GCM before storage.
      </div>
    </div>
  );
}

export default UploadDocument;
