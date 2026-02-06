import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { apiClient } from "../services/api";

interface LocationState {
  examId: string;
  studentId: string;
}

const WebcamScannerPage: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [excelInfo, setExcelInfo] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as Partial<LocationState>;

  useEffect(() => {
    const start = async () => {
      try {
        const media = await navigator.mediaDevices.getUserMedia({ video: true });
        setStream(media);
        if (videoRef.current) {
          videoRef.current.srcObject = media;
        }
      } catch (e) {
        setError("Unable to access webcam. Please allow camera permission.");
      }
    };
    start();
    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Draw video frame into canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL("image/png");
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = (error) => reject(error);
    });
  };

  const handleScan = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setError(null);
    setLoading(true);
    const dataUrl = captureFrame();

    try {
      const res = await apiClient.post("/api/teacher/scan", {
        image_base64: dataUrl,
      });
      const entries = res.data.entries || [];
      navigate("/teacher/review", {
        state: {
          examId: state.examId,
          studentId: state.studentId,
          entries,
        },
      });
    } catch (e) {
      setError("Failed to run OCR. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const handleScanToExcel = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setError(null);
    setExcelInfo(null);
    setLoading(true);
    const dataUrl = captureFrame();

    try {
      let excelBase64: string | null = null;
      if (excelFile) {
        excelBase64 = await fileToBase64(excelFile);
      }

      const res = await apiClient.post("/api/teacher/scan-grid-excel", {
        image_base64: dataUrl,
        excel_file: excelBase64,
      });
      
      const { marks, total, excel_file } = res.data as {
        marks: number[];
        total: number;
        excel_file: string; // Base64 returned from backend
      };

      // Convert returned base64 back to file for next state
      const byteCharacters = atob(excel_file);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      const newFile = new File([blob], excelFile?.name || "marks.xlsx", { type: blob.type });
      
      setExcelFile(newFile);
      setDownloadUrl(URL.createObjectURL(blob));

      setExcelInfo(`Added row. Marks: [${marks.join(", ")}], Total: ${total}`);
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Failed to scan grid and write to Excel. Check backend logs.";
      setError(msg);
      console.error(e);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setExcelFile(e.target.files[0]);
      setDownloadUrl(null); // Reset download link on new upload
      setExcelInfo("Loaded custom Excel file.");
    }
  };

  if (!state.examId || !state.studentId) {
    return (
      <div className="p-6">
        <p className="text-red-600 text-sm mb-4">
          Missing exam or student selection. Go back to Teacher Dashboard.
        </p>
        <button
          onClick={() => navigate("/teacher")}
          className="px-4 py-2 rounded-md bg-slate-800 text-white text-sm hover:bg-slate-900"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="text-2xl font-bold text-slate-800">Live Mark Scanner</h1>
           <p className="text-slate-500 text-sm">Scan physical marks and update your Excel sheet in real-time.</p>
        </div>
        <Link 
            to="/teacher" 
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
        >
            &larr; Back to Dashboard
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 text-sm rounded-md border border-red-100">
            {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Excel Management */}
        <div className="lg:col-span-1 space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
                <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                    <span className="bg-green-100 text-green-700 p-1.5 rounded text-xs">1</span>
                    Excel Configuration
                </h2>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Master Excel Sheet</label>
                        <p className="text-xs text-slate-500 mb-3">
                            Upload an existing sheet to append marks to, or start fresh.
                        </p>
                        <input 
                            type="file" 
                            accept=".xlsx, .xls"
                            onChange={handleFileUpload}
                            className="block w-full text-sm text-slate-500
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-md file:border-0
                                file:text-sm file:font-semibold
                                file:bg-slate-50 file:text-slate-700
                                hover:file:bg-slate-100
                            "
                        />
                    </div>

                    <div className="pt-4 border-t border-slate-100">
                         <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-slate-600">Current File:</span>
                            <span className={`text-xs font-mono py-0.5 px-2 rounded ${excelFile ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}`}>
                                {excelFile ? excelFile.name : "System Default (New)"}
                            </span>
                         </div>
                         
                         {downloadUrl && (
                            <a 
                                href={downloadUrl} 
                                download={excelFile?.name || "marks.xlsx"}
                                className="block w-full text-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition"
                            >
                                Download Updated File
                            </a>
                         )}
                         {!downloadUrl && excelFile && (
                            <p className="text-xs text-center text-slate-400 mt-2">
                                Updates will be available for download after scanning.
                            </p>
                         )}
                    </div>
                </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-sm text-blue-800">
                <strong>Tip:</strong> Position the camera so the grid of marks is clearly visible inside the box.
            </div>
        </div>

        {/* Right Column: Scanner */}
        <div className="lg:col-span-2">
            <div className="bg-black rounded-lg overflow-hidden shadow-lg relative aspect-video bg-slate-900 border border-slate-800">
                <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    className="w-full h-full object-contain" 
                />
                
                {/* ROI Overlay */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-2/3 h-1/2 border-4 border-green-400 rounded-lg shadow-[0_0_15px_rgba(74,222,128,0.5)] bg-transparent">
                        <div className="absolute -top-8 left-0 right-0 text-center">
                            <span className="bg-black/70 text-white text-xs px-2 py-1 rounded">
                                Align Marks Grid Here
                            </span>
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10 backdrop-blur-sm">
                        <div className="text-white font-medium flex flex-col items-center">
                            <div className="w-8 h-8 border-2 border-white/30 border-t-white rounded-full animate-spin mb-2" />
                            Processing...
                        </div>
                    </div>
                )}
            </div>

            <div className="mt-4 flex flex-col md:flex-row gap-4 items-start justify-between">
                <button
                    onClick={handleScanToExcel}
                    disabled={loading}
                    className="flex-1 w-full md:w-auto px-6 py-3 bg-slate-800 text-white font-semibold rounded-lg shadow hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                >
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    Scan & Update Excel
                </button>
                
                {excelInfo && (
                     <div className="flex-1 bg-emerald-50 border border-emerald-100 text-emerald-800 px-4 py-3 rounded-md text-sm animate-in fade-in slide-in-from-top-1">
                        {excelInfo}
                     </div>
                )}
            </div>
        </div>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
};

export default WebcamScannerPage;

