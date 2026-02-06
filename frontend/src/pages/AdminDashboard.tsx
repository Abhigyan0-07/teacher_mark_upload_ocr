import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiClient } from "../services/api";

interface Student {
  id: string;
  roll_number: string;
  name: string;
}

const AdminDashboard: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get<Student[]>("/api/admin/students");
        setStudents(res.data);
      } catch (e) {
        setError("Failed to load students (make sure you are logged in as admin).");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Admin Dashboard</h1>
      <p className="text-sm text-slate-600 mb-6">
        This is a minimal admin view showing students from the backend. You can extend it to add forms for creating students, teachers, subjects, and exams.
      </p>

      <div className="mb-6">
        <Link 
          to="/teacher/scan" 
          state={{ examId: "demo_exam", studentId: "demo_student" }}
          className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
        >
          Go to Webcam Scanner (Demo)
        </Link>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}
      
      <table className="min-w-full text-sm border border-slate-200 bg-white rounded-md overflow-hidden">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-3 py-2 text-left border-b">Roll No</th>
            <th className="px-3 py-2 text-left border-b">Name</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.id} className="border-b last:border-b-0">
              <td className="px-3 py-2">{s.roll_number}</td>
              <td className="px-3 py-2">{s.name}</td>
            </tr>
          ))}
          {students.length === 0 && !loading && (
            <tr>
              <td colSpan={2} className="px-3 py-3 text-center text-slate-500">
                No students yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminDashboard;

