import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../services/api";

interface Entry {
  question_label: string;
  marks: number;
}

interface LocationState {
  examId: string;
  studentId: string;
  entries: Entry[];
}

const OCRReviewPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as Partial<LocationState>;
  const [rows, setRows] = useState<Entry[]>(state.entries || []);
  const [maxMarks, setMaxMarks] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!state.examId) return;
    apiClient
      .get(`/api/admin/exams`)
      .then((res) => {
        const exam = (res.data as any[]).find((e) => e.id === state.examId);
        if (exam) setMaxMarks(exam.max_marks);
      })
      .catch(() => {
        // non-fatal
      });
  }, [state.examId]);

  const total = useMemo(
    () => rows.reduce((sum, r) => sum + (Number.isFinite(r.marks) ? r.marks : 0), 0),
    [rows],
  );

  const handleChange = (index: number, field: keyof Entry, value: string) => {
    setRows((prev) =>
      prev.map((r, i) =>
        i === index
          ? {
              ...r,
              [field]: field === "marks" ? Number(value || 0) : value,
            }
          : r,
      ),
    );
  };

  const handleAddRow = () => {
    setRows((prev) => [...prev, { question_label: "", marks: 0 }]);
  };

  const handleDeleteRow = (index: number) => {
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!state.examId || !state.studentId) return;
    setSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      const cleaned = rows.filter((r) => r.question_label.trim() !== "");
      await apiClient.post("/api/teacher/submit-marks", {
        exam_id: state.examId,
        student_id: state.studentId,
        entries: cleaned,
      });
      setMessage("Marks submitted successfully.");
    } catch (e) {
      setError("Failed to submit marks. Check backend logs.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!state.examId || !state.studentId) {
    return (
      <div>
        <p className="text-red-600 text-sm mb-4">
          Missing exam or student context. Go back to Teacher Dashboard.
        </p>
        <button
          onClick={() => navigate("/teacher")}
          className="px-4 py-2 rounded-md bg-slate-800 text-white text-sm hover:bg-slate-900"
        >
          Back to Teacher Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Review OCR Marks</h1>
      <p className="text-sm text-slate-600">
        Edit labels or marks, add missing rows, and delete incorrect ones. Then submit to save.
      </p>

      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left border-b">Question Label</th>
              <th className="px-3 py-2 text-left border-b">Marks</th>
              <th className="px-3 py-2 text-left border-b w-16"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className="border-b last:border-b-0">
                <td className="px-3 py-2">
                  <input
                    value={row.question_label}
                    onChange={(e) => handleChange(idx, "question_label", e.target.value)}
                    className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-slate-800"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    min={0}
                    value={row.marks}
                    onChange={(e) => handleChange(idx, "marks", e.target.value)}
                    className="w-24 rounded-md border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-slate-800"
                  />
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => handleDeleteRow(idx)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={3} className="px-3 py-3 text-center text-slate-500">
                  No entries. Add rows manually or go back and rescan.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <div className="space-y-1 text-sm">
          <p>
            <span className="font-medium">Total marks:</span> {total}
          </p>
          {maxMarks !== null && total > maxMarks && (
            <p className="text-xs text-amber-600">
              Warning: total exceeds max marks ({maxMarks}).
            </p>
          )}
        </div>
        <div className="space-x-2">
          <button
            type="button"
            onClick={handleAddRow}
            className="px-3 py-2 rounded-md border border-slate-300 text-sm hover:bg-slate-50"
          >
            Add Row
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={handleSubmit}
            className="px-4 py-2 rounded-md bg-slate-800 text-white text-sm font-medium hover:bg-slate-900 disabled:opacity-60"
          >
            {submitting ? "Submitting..." : "Submit Marks"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OCRReviewPage;

