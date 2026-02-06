import { Route, Routes, Navigate, Link } from "react-router-dom";
import { AuthProvider, useAuth } from "../hooks/useAuth";
import { ProtectedRoute } from "../components/ProtectedRoute";
import LoginPage from "./LoginPage";
import AdminDashboard from "./AdminDashboard";
import TeacherDashboard from "./TeacherDashboard";
import WebcamScannerPage from "./WebcamScannerPage";
import OCRReviewPage from "./OCRReviewPage";

const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold text-slate-800">
            Marks OCR System
          </Link>
          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-slate-600">
                {user.full_name || user.username} ({user.role})
              </span>
            )}
            {user ? (
              <button
                onClick={logout}
                className="px-3 py-1 rounded-md text-sm bg-slate-800 text-white hover:bg-slate-900"
              >
                Logout
              </button>
            ) : (
              <Link
                to="/login"
                className="px-3 py-1 rounded-md text-sm bg-slate-800 text-white hover:bg-slate-900"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-6">{children}</div>
      </main>
    </div>
  );
};

const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <Shell>
            <Home />
          </Shell>
        </ProtectedRoute>
      }
    />
    <Route
      path="/admin"
      element={
        <ProtectedRoute roles={["admin"]}>
          <Shell>
            <AdminDashboard />
          </Shell>
        </ProtectedRoute>
      }
    />
    <Route
      path="/teacher"
      element={
        <ProtectedRoute roles={["teacher", "admin"]}>
          <Shell>
            <TeacherDashboard />
          </Shell>
        </ProtectedRoute>
      }
    />
    <Route
      path="/teacher/scan"
      element={
        <ProtectedRoute roles={["teacher", "admin"]}>
          <Shell>
            <WebcamScannerPage />
          </Shell>
        </ProtectedRoute>
      }
    />
    <Route
      path="/teacher/review"
      element={
        <ProtectedRoute roles={["teacher", "admin"]}>
          <Shell>
            <OCRReviewPage />
          </Shell>
        </ProtectedRoute>
      }
    />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

const Home: React.FC = () => {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Welcome</h1>
      <div className="flex gap-4">
        {user.role === "admin" && (
          <Link
            to="/admin"
            className="px-4 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-900"
          >
            Go to Admin Dashboard
          </Link>
        )}
        {user.role === "teacher" && (
          <Link
            to="/teacher"
            className="px-4 py-2 rounded-md bg-slate-800 text-white hover:bg-slate-900"
          >
            Go to Teacher Dashboard
          </Link>
        )}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
};

export default App;

