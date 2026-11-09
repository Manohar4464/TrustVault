
import { useState, useEffect } from "react";
import {
  Share2,
  ShieldCheck,
  AlertCircle,
  CheckCircle,
  Users,
  RefreshCw,
  XCircle,
} from "lucide-react";
import api from "./services/api";

function ShareDocument({ documents = [] }) {
  const [selectedDocument, setSelectedDocument] = useState("");
  const [userId, setUserId] = useState("");
  const [canRead, setCanRead] = useState(true);
  const [canEdit, setCanEdit] = useState(false);
  const [canDownload, setCanDownload] = useState(true);
  const [sharing, setSharing] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const [loadingPermissions, setLoadingPermissions] = useState(false);
  const [revokingUser, setRevokingUser] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadPermissions = async (documentId) => {
    if (!documentId) {
      setPermissions([]);
      return;
    }

    setLoadingPermissions(true);

    try {
      const response = await api.get(`/permissions/${documentId}`);
      setPermissions(response.data);
    } catch (err) {
      setPermissions([]);
      setError(
        err.response?.data?.detail ||
          "Unable to load sharing permissions."
      );
    } finally {
      setLoadingPermissions(false);
    }
  };

  useEffect(() => {
    loadPermissions(selectedDocument);
  }, [selectedDocument]);

  const handleShare = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!selectedDocument || !userId.trim()) {
      setError("Select a document and enter the receiver's User ID.");
      return;
    }

    if (!canRead && (canEdit || canDownload)) {
      setError("Read permission is required for edit or download.");
      return;
    }

    setSharing(true);

    try {
      await api.post("/permissions/grant", {
        document_id: selectedDocument,
        user_id: userId.trim(),
        can_read: canRead,
        can_edit: canEdit,
        can_download: canDownload,
      });

      setMessage("Document shared successfully!");
      setUserId("");
      await loadPermissions(selectedDocument);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to share the document."
      );
    } finally {
      setSharing(false);
    }
  };

  const handleRevoke = async (receiverId) => {
    if (!window.confirm("Are you sure you want to revoke this user's access?")) {
      return;
    }

    setMessage("");
    setError("");
    setRevokingUser(receiverId);

    try {
      await api.delete(
        `/permissions/revoke/${selectedDocument}/${receiverId}`
      );

      setMessage("Document access revoked successfully!");
      await loadPermissions(selectedDocument);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to revoke access."
      );
    } finally {
      setRevokingUser("");
    }
  };

  return (
    <div className="share-document-page">
      <div className="share-document-header">
        <div>
          <h2>Share Document</h2>
          <p>Securely share and manage document access.</p>
        </div>

        <div className="share-document-icon">
          <Share2 size={28} />
        </div>
      </div>

      <form className="share-document-card" onSubmit={handleShare}>
        <label>Select Document</label>

        <select
          value={selectedDocument}
          onChange={(e) => {
            setSelectedDocument(e.target.value);
            setMessage("");
            setError("");
          }}
          required
        >
          <option value="">Choose a document</option>

          {documents.map((doc) => (
            <option key={doc.document_id} value={doc.document_id}>
              {doc.filename}
            </option>
          ))}
        </select>

        <label>Receiver User ID</label>

        <input
          type="text"
          placeholder="Enter registered user's ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          required
        />

        <h3>Access Permissions</h3>

        <label className="share-permission-option">
          <input
            type="checkbox"
            checked={canRead}
            onChange={(e) => setCanRead(e.target.checked)}
          />
          <span>Read Document</span>
        </label>

        <label className="share-permission-option">
          <input
            type="checkbox"
            checked={canDownload}
            onChange={(e) => setCanDownload(e.target.checked)}
            disabled={!canRead}
          />
          <span>Download Document</span>
        </label>

        <label className="share-permission-option">
          <input
            type="checkbox"
            checked={canEdit}
            onChange={(e) => setCanEdit(e.target.checked)}
            disabled={!canRead}
          />
          <span>Edit Document</span>
        </label>

        {message && (
          <p className="success-message">
            <CheckCircle size={17} />
            {message}
          </p>
        )}

        {error && (
          <p className="error-message">
            <AlertCircle size={17} />
            {error}
          </p>
        )}

        <button
          type="submit"
          className="share-submit-button"
          disabled={sharing}
        >
          <Share2 size={17} />
          {sharing ? "Sharing..." : "Share Securely"}
        </button>

        <p className="share-security-note">
          <ShieldCheck size={16} />
          Only registered TrustVault users can receive shared documents.
        </p>
      </form>

      <div className="share-document-card access-management-card">
        <div className="access-management-heading">
          <div>
            <h3>Manage Shared Access</h3>
            <p>View and revoke access granted to other users.</p>
          </div>
          <Users size={24} />
        </div>

        {!selectedDocument ? (
          <p className="page-placeholder">
            Select a document above to manage its access.
          </p>
        ) : loadingPermissions ? (
          <p className="page-placeholder">
            <RefreshCw size={16} /> Loading permissions...
          </p>
        ) : permissions.filter((p) => p.is_active).length === 0 ? (
          <p className="page-placeholder">
            No active users have access to this document.
          </p>
        ) : (
          <div className="shared-user-list">
            {permissions
              .filter((permission) => permission.is_active)
              .map((permission) => (
                <div className="shared-user-row" key={permission.id}>
                  <div className="shared-user-info">
                    <strong>{permission.user_id}</strong>
                    <span>
                      {[
                        permission.can_read && "Read",
                        permission.can_download && "Download",
                        permission.can_edit && "Edit",
                      ]
                        .filter(Boolean)
                        .join(" · ") || "No permissions"}
                    </span>
                  </div>

                  <button
                    type="button"
                    className="revoke-access-button"
                    onClick={() => handleRevoke(permission.user_id)}
                    disabled={revokingUser === permission.user_id}
                  >
                    <XCircle size={16} />
                    {revokingUser === permission.user_id
                      ? "Revoking..."
                      : "Revoke"}
                  </button>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ShareDocument;
