import UploadDocument from "./Upload";
import ShareDocument from "./ShareDocument";
import { useState, useEffect, useCallback } from "react";
import {
  ShieldCheck,
  LockKeyhole,
  FileText,
  Upload,
  Users,
  Activity,
  LayoutDashboard,
  Settings,
  LogOut,
  Search,
  Bell,
  Menu,
  Download,
  RefreshCw,
  Share2 ,
} from "lucide-react";

import Login from "./Login";

import {
  getCurrentUser,
  getDocuments,
  logoutUser,
  downloadDocument,
  getAuditLogs,
} from "./services/api";
import "./App.css";

function App() {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activePage, setActivePage] = useState("Dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const loadDocuments = useCallback(async () => {
  const data = await getDocuments();
  setDocuments(data.items || []);
}, []);

const loadAuditLogs = useCallback(async () => {
  try {
    const data = await getAuditLogs();
    setAuditLogs(data.items || []);
  } catch (error) {
    console.error("Failed to load audit logs:", error);
  }
}, []);

  useEffect(() => {
    const initializeApp = async () => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    setLoading(false);
    return;
  }

  try {
    const currentUser = await getCurrentUser();
    setUser(currentUser);
    await loadDocuments();

    if (currentUser.role === "admin") {
      await loadAuditLogs();
    }
  } catch {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
  } finally {
    setLoading(false);
  }
};

    initializeApp();
  }, [loadDocuments]);

  const handleLogin = async (loggedInUser) => {
    setUser(loggedInUser);
    setLoading(true);

    try {
      await loadDocuments();
    } catch {
      setError("Login successful, but documents could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    }

    setUser(null);
    setDocuments([]);
    setActivePage("Dashboard");
  };

  if (loading) {
    return (
      <div className="app-loading">
        <ShieldCheck size={38} />
        <h2>TrustVault</h2>
        <p>Securing your workspace...</p>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  const isAdmin = user.role === "admin";
  const myDocuments = documents.filter(
    (doc) => doc.access?.is_owner
  );
  const sharedDocuments = documents.filter(
    (doc) => !doc.access?.is_owner
  );

  const visibleDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(search.toLowerCase())
  );

  const menuItems = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "My Documents", icon: FileText },
  { name: "Upload Document", icon: Upload },
  { name: "Share Document", icon: Share2 },
  { name: "Shared Documents", icon: Users },
  ...(isAdmin
    ? [{ name: "Audit Logs", icon: Activity }]
    : []),
  { name: "Settings", icon: Settings },
];
  const handleRefresh = async () => {
    setError("");
    try {
      await loadDocuments();
    } catch {
      setError("Unable to refresh documents.");
    }
  };

  const renderDocuments = (items) => {
    if (items.length === 0) {
      return (
        <div className="empty-state">
          <div className="empty-icon">
            <FileText size={30} />
          </div>
          <h3>No documents found</h3>
          <p>Documents will appear here when available.</p>
        </div>
      );
    }

    return (
      <div className="document-list">
        {items.map((doc) => (
          <div className="document-row" key={doc.document_id}>
            <div className="document-info">
              <div className="document-icon">
                <FileText size={21} />
              </div>
              <div>
                <strong>{doc.filename}</strong>
                <span>
                  {(doc.file_size / 1024).toFixed(2)} KB ·{" "}
                  {doc.encryption}
                </span>
              </div>
            </div>

            <div className="permission-tags">
              {doc.access?.is_owner ? (
                <span className="tag owner-tag">Owner</span>
              ) : (
                <span className="tag shared-tag">Shared</span>
              )}
              {doc.access?.can_edit && (
                <span className="tag edit-tag">Edit</span>
              )}
              {doc.access?.can_download && (
                <span className="tag download-tag">Download</span>
              )}
            </div>

            {doc.access?.can_download && (
              <button
                className="download-button"
                title="Download document"
                onClick={async () => {
  try {
    await downloadDocument(doc.document_id, doc.filename);
  } catch (error) {
    setError(
      error.response?.status === 403
        ? "You do not have permission to download this document."
        : "Document download failed. Please try again."
    );
  }
}}
              >
                <Download size={17} />
              </button>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={27} />
          </div>
          <div>
            <h2>TrustVault</h2>
            <span>SECURE DOCUMENTS</span>
          </div>
        </div>

        <div className="nav-heading">WORKSPACE</div>

        <nav>
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                className={`nav-item ${
                  activePage === item.name ? "active" : ""
                }`}
                onClick={() => setActivePage(item.name)}
              >
                <Icon size={19} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="security-status">
            <LockKeyhole size={18} />
            <div>
              <strong>Security Active</strong>
              <span>AES-256-GCM Encryption</span>
            </div>
          </div>

          <button className="nav-item" onClick={handleLogout}>
            <LogOut size={19} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu">
            <Menu size={22} />
          </button>

          <div className="breadcrumb">
            Workspace / <strong>{activePage}</strong>
          </div>

          <div className="topbar-right">
            <button className="icon-button" onClick={handleRefresh}>
              <RefreshCw size={18} />
            </button>
            <button className="icon-button">
              <Bell size={19} />
            </button>

            <div className="profile">
              <div className="avatar">
                {user.name?.charAt(0).toUpperCase()}
              </div>
              <div>
                <strong>{user.name}</strong>
                <span>{user.role}</span>
              </div>
            </div>
          </div>
        </header>

        <section className="page-content">
          {error && <div className="app-error">{error}</div>}

          <div className="welcome-section">
            <div>
              <span className="eyebrow">SECURE WORKSPACE</span>
              <h1>{activePage}</h1>
              <p>Manage and protect your important documents securely.</p>
            </div>
          </div>

          {activePage === "Dashboard" && (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon purple">
                    <FileText />
                  </div>
                  <span>Visible Documents</span>
                  <h2>{documents.length}</h2>
                  <small>Available to your account</small>
                </div>

                <div className="stat-card">
                  <div className="stat-icon blue">
                    <Users />
                  </div>
                  <span>Shared Documents</span>
                  <h2>{sharedDocuments.length}</h2>
                  <small>Shared with your account</small>
                </div>

                <div className="stat-card">
                  <div className="stat-icon green">
                    <LockKeyhole />
                  </div>
                  <span>Encryption</span>
                  <h2>AES-256</h2>
                  <small>GCM authenticated encryption</small>
                </div>

                <div className="stat-card">
                  <div className="stat-icon orange">
                    <Activity />
                  </div>
                  <span>Account Role</span>
                  <h2>{user.role}</h2>
                  <small>Access-controlled account</small>
                </div>
              </div>

              <div className="documents-panel">
                <div className="panel-header">
                  <div>
                    <h2>Recent Documents</h2>
                    <p>Documents available in your workspace</p>
                  </div>
                  <button
                    className="secondary-button"
                    onClick={() => setActivePage("My Documents")}
                  >
                    View All
                  </button>
                </div>
                {renderDocuments(documents.slice(0, 5))}
              </div>
            </>
          )}

          {activePage === "My Documents" && (
            <div className="documents-panel">
              <div className="panel-header">
                <div>
                  <h2>My Documents</h2>
                  <p>Documents owned by you: {myDocuments.length}</p>
                </div>
              </div>
              {renderDocuments(myDocuments)}
            </div>
          )}

          {activePage === "Shared Documents" && (
            <div className="documents-panel">
              <div className="panel-header">
                <div>
                  <h2>Shared Documents</h2>
                  <p>Documents shared with you: {sharedDocuments.length}</p>
                </div>
              </div>
              {renderDocuments(sharedDocuments)}
            </div>
          )}
          {activePage === "Upload Document" && (
  <UploadDocument
    onUploadSuccess={loadDocuments}
  />
)}
{activePage === "Share Document" && (
  <ShareDocument documents={myDocuments} />
)}
          {activePage === "Audit Logs" && isAdmin && (
  <div className="documents-panel audit-logs-panel">
    <div className="panel-header audit-header">
      <div>
        <h2>Audit Logs</h2>
        <p>Monitor document activity and security events</p>
      </div>

      <button
        onClick={loadAuditLogs}
        className="audit-refresh-button"
      >
        ↻ Refresh
      </button>
    </div>

    <div className="audit-summary">
      <div>
        <span>Total Events</span>
        <strong>{auditLogs.length}</strong>
      </div>
      <div>
        <span>Uploads</span>
        <strong>{auditLogs.filter(log => log.action === "UPLOAD").length}</strong>
      </div>
      <div>
        <span>Downloads</span>
        <strong>{auditLogs.filter(log => log.action === "DOWNLOAD").length}</strong>
      </div>
      <div>
        <span>Access Changes</span>
        <strong>
          {auditLogs.filter(log =>
            ["GRANT", "REVOKE"].includes(log.action)
          ).length}
        </strong>
      </div>
    </div>

    <div className="audit-table-container">
      <table className="audit-logs-table">
        <thead>
          <tr>
            <th>Action</th>
            <th>User ID</th>
            <th>Document ID</th>
            <th>Timestamp</th>
          </tr>
        </thead>

        <tbody>
          {auditLogs.length > 0 ? (
            auditLogs.map((log, index) => (
              <tr key={log.id || index}>
                <td>
                  <span className={`audit-action ${String(log.action || "").toLowerCase()}`}>
                    {log.action || "UNKNOWN"}
                  </span>
                </td>
                <td title={log.user_id || ""}>
                  {log.user_id || "N/A"}
                </td>
                <td title={log.document_id || ""}>
                  {log.document_id || "N/A"}
                </td>
                <td>
                  {log.created_at
                    ? new Date(log.created_at).toLocaleString()
                    : "N/A"}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="4" className="audit-empty">
                No audit records found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </div>
)}

          {activePage === "Settings" && (
            <div className="documents-panel">
              <h2>Account Settings</h2>
              <p className="page-placeholder">
                <strong>{user.name}</strong><br />
                {user.email}<br />
                Account role: {user.role}
              </p>
            </div>
          )}

          <footer>
            <ShieldCheck size={16} />
            TrustVault · Secure Document Management
            <span>Protected with AES-256-GCM</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
