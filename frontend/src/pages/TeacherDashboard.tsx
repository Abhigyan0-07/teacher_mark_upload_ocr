import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../services/api";

interface Exam {
  id: string;
  name: string;
}

interface Student {
  id: string;
  roll_number: string;
  name: string;
}

const TeacherDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [exams, setExams] = useState<Exam[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>("");
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const examsRes = await apiClient.get<Exam[]>("/api/teacher/exams");
        setExams(examsRes.data);
        const studentsRes = await apiClient.get<Student[]>("/api/teacher/students");
        setStudents(studentsRes.data);
      } catch (e) {
        setError("Failed to load exams or students. Make sure backend is running and you are logged in as teacher.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredStudents = students.filter(
    (s) =>
      s.roll_number.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase()),
  );

  const canStartScan = !!selectedExamId && !!selectedStudentId;

  const handleStartScan = () => {
    if (!canStartScan) return;
    navigate("/teacher/scan", {
      state: {
        examId: selectedExamId,
        studentId: selectedStudentId,
      },
    });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-800">Teacher Dashboard</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <h2 className="text-lg font-medium text-slate-800">Select Exam</h2>
          <select
            value={selectedExamId}
            onChange={(e) => setSelectedExamId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 bg-white"
          >
            <option value="">-- Choose exam --</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-medium text-slate-800">Select Student</h2>
          <input
            placeholder="Search by roll no or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 mb-2"
          />
          <div className="max-h-52 overflow-auto border border-slate-200 rounded-md bg-white">
            {filteredStudents.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setSelectedStudentId(s.id)}
                className={`w-full text-left px-3 py-1.5 text-sm border-b last:border-b-0 hover:bg-slate-50 ${
                  selectedStudentId === s.id ? "bg-slate-800 text-white hover:bg-slate-900" : ""
                }`}
              >
                {s.roll_number} - {s.name}
              </button>
            ))}
            {filteredStudents.length === 0 && (
              <div className="px-3 py-2 text-sm text-slate-500">No students found.</div>
            )}
          </div>
        </div>
      </div>

      <div>
        <button
          disabled={!canStartScan}
          onClick={handleStartScan}
          className="px-4 py-2 rounded-md bg-slate-800 text-white text-sm font-medium hover:bg-slate-900 disabled:opacity-60"
        >
          Go to Webcam Scanner
        </button>
      </div>
    </div>
  );
};

export default TeacherDashboard;

