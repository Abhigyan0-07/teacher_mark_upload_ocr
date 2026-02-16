import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import ReactCrop, { Crop, PixelCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";
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
    
    // Excel State
    const [excelFile, setExcelFile] = useState<File | null>(null);
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
    const [excelInfo, setExcelInfo] = useState<string | null>(null);
    const [rows, setRows] = useState(4);
    const [cols, setCols] = useState(2);
    
    // Mode State
    const [mode, setMode] = useState<"auto" | "manual">("auto");
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [crop, setCrop] = useState<Crop>();
    const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
    const imgRef = useRef<HTMLImageElement>(null);

    const navigate = useNavigate();
    const location = useLocation();
    const state = (location.state || {}) as Partial<LocationState>;

    // ... (useEffect for stream remains same) ...
    useEffect(() => {
        const start = async () => {
        try {
            const media = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1920 }, 
                    height: { ideal: 1080 } 
                } 
            });
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

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const fullImage = canvas.toDataURL("image/png");
        
        if (mode === "manual") {
            setCapturedImage(fullImage);
            return fullImage;
        }

        // For Auto Mode:
        // PREVIOUSLY: We cropped to the center 2/3.
        // PROBLEM: If the user wasn't perfectly aligned, we cut off numbers.
        // FIX: Send the FULL video frame. The backend's "Smart Sort" is robust enough 
        // to find the grid structure in the full image, provided the background isn't full of numbers.
        return fullImage;
    };

    const fileToBase64 = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (error) => reject(error);
        });
    };

    // ... handleFileUpload remains same ...
    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
        setExcelFile(e.target.files[0]);
        setDownloadUrl(null); // Reset download link on new upload
        setExcelInfo("Loaded custom Excel file.");
        }
    };

    // AUTO MODE SCAN
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
            rows: rows,
            cols: cols
        });
        
        handleExcelResponse(res.data);
        } catch (e: any) {
             const msg = e.response?.data?.detail || "Failed to scan grid. Check backend logs.";
             setError(msg);
        } finally {
             setLoading(false);
        }
    };

    // MANUAL CROP HELPER
    const getCroppedImg = async (imageSrc: string, crop: PixelCrop): Promise<string> => {
        const image = new Image();
        image.src = imageSrc;
        await new Promise(resolve => image.onload = resolve);
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) return "";
        
        const scaleX = image.naturalWidth / image.width;
        const scaleY = image.naturalHeight / image.height;
        
        canvas.width = crop.width;
        canvas.height = crop.height;
        
        ctx.drawImage(
            image,
            crop.x * scaleX,
            crop.y * scaleY,
            crop.width * scaleX,
            crop.height * scaleY,
            0,
            0,
            crop.width,
            crop.height
        );
        
        return canvas.toDataURL('image/png');
    }

    // MANUAL SCAN ACTION
    const handleManualCropScan = async () => {
        if (!capturedImage || !completedCrop) {
            setError("Please capture an image and select a region first.");
            return;
        }
        
        setLoading(true);
        setError(null);
        
        try {
            // 1. Get cropped image base64
            // Note: completedCrop refers to the display size. We need to scale to actual image size.
            // But we can do this via a helper or just rely on the imgRef
            
            if (!imgRef.current) throw new Error("Image not loaded");
            
            const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
            const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
            
            const canvas = document.createElement('canvas');
            canvas.width = completedCrop.width * scaleX;
            canvas.height = completedCrop.height * scaleY;
            const ctx = canvas.getContext('2d');
            
            if (!ctx) throw new Error("No context");
            
            ctx.drawImage(
                imgRef.current,
                completedCrop.x * scaleX,
                completedCrop.y * scaleY,
                completedCrop.width * scaleX,
                completedCrop.height * scaleY,
                0,
                0,
                completedCrop.width * scaleX,
                completedCrop.height * scaleY,
            );
            
            const cropBase64 = canvas.toDataURL('image/png');
            
            // 2. Send to backend
            let excelBase64: string | null = null;
            if (excelFile) {
                excelBase64 = await fileToBase64(excelFile);
            }

            const res = await apiClient.post("/api/teacher/scan-crop-excel", {
                image_base64: cropBase64,
                excel_file: excelBase64
            });
            
            handleExcelResponse(res.data);
            setCapturedImage(null); // Reset after success? Or keep it? Let's reset.
            
        } catch (e: any) {
            console.error(e);
            setError("Failed to scan crop. " + (e.response?.data?.detail || e.message));
        } finally {
            setLoading(false);
        }
    }

    const handleExcelResponse = (data: any) => {
        const { marks, total, excel_file } = data;

        // Convert returned base64 back to file
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
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-slate-800">Scan Marks</h1>
                  <p className="text-slate-500 text-sm">
                      {mode === "auto" ? "Point camera at the grid." : "Take a photo and select a box."}
                  </p>
                </div>
                
                <div className="flex gap-4 items-center">
                    {/* Mode Toggle */}
                    <div className="bg-slate-100 p-1 rounded-lg flex text-sm font-medium">
                        <button 
                            onClick={() => { setMode("auto"); setCapturedImage(null); }}
                            className={`px-3 py-1.5 rounded-md transition ${mode === "auto" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                        >
                            Auto Grid
                        </button>
                        <button 
                            onClick={() => setMode("manual")}
                            className={`px-3 py-1.5 rounded-md transition ${mode === "manual" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                        >
                            Manual Crop
                        </button>
                    </div>
                    
                    <Link to="/teacher" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                        &larr; Exit
                    </Link>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-700 text-sm rounded-md border border-red-100">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Config */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Excel Config (Always visible) */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
                        <h2 className="text-lg font-semibold text-slate-800 mb-4">Excel Sheet</h2>
                         <div className="space-y-4">
                            <input 
                                type="file" 
                                accept=".xlsx, .xls"
                                onChange={handleFileUpload}
                                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-slate-50 file:text-slate-700 hover:file:bg-slate-100"
                            />
                            {/* Download Link area */}
                            <div className="pt-4 border-t border-slate-100">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-slate-600">Current File:</span>
                                    <span className={`text-xs font-mono py-0.5 px-2 rounded ${excelFile ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}`}>
                                        {excelFile ? excelFile.name : "New File"}
                                    </span>
                                </div>
                                {downloadUrl && (
                                    <a href={downloadUrl} download={excelFile?.name || "marks.xlsx"} className="block w-full text-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition">
                                        Download Updated File
                                    </a>
                                )}
                            </div>
                         </div>
                    </div>

                    {/* Auto Grid Config (Only in Auto Mode) */}
                    {mode === "auto" && (
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
                            <h2 className="text-lg font-semibold text-slate-800 mb-4">Grid Layout</h2>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Rows</label>
                                    <input type="number" min="1" max="10" value={rows} onChange={(e) => setRows(parseInt(e.target.value) || 4)} className="w-full px-3 py-2 border rounded-md" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Cols</label>
                                    <input type="number" min="1" max="6" value={cols} onChange={(e) => setCols(parseInt(e.target.value) || 2)} className="w-full px-3 py-2 border rounded-md" />
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {/* Manual Mode Instructions */}
                    {mode === "manual" && (
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-sm text-blue-800">
                            <strong>How to use:</strong>
                            <ol className="list-decimal ml-4 mt-2 space-y-1">
                                <li>Click "Capture Image" to freeze the camera.</li>
                                <li>Draw a box around the digit you want to scan.</li>
                                <li>Click "Scan Selection".</li>
                                <li>It will be added to the Excel sheet.</li>
                            </ol>
                        </div>
                    )}
                </div>

                {/* Right Column: Viewport (Camera or Image) */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="bg-slate-900 rounded-lg overflow-hidden shadow-lg border border-slate-800 relative aspect-video flex items-center justify-center">
                        {/* 
                            VIEWPORT LOGIC:
                            1. If Manual & Captured => Show Image with Crop
                            2. Else => Show Video Feed
                        */}
                        {mode === "manual" && capturedImage ? (
                            <ReactCrop 
                                crop={crop} 
                                onChange={(c) => setCrop(c)} 
                                onComplete={(c) => setCompletedCrop(c)}
                                aspect={undefined} // Free aspect ratio
                                className="max-h-[60vh]"
                            >
                                <img ref={imgRef} src={capturedImage} className="max-h-[60vh] w-auto object-contain" alt="Capture" />
                            </ReactCrop>
                        ) : (
                            <>
                                <video ref={videoRef} autoPlay playsInline className="w-full h-full object-contain" />
                                {/* Overlay for Auto Mode */}
                                {mode === "auto" && (
                                    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                                         <div className="w-2/3 h-2/3 border-4 border-green-400 rounded-lg shadow-[0_0_15px_rgba(74,222,128,0.5)]">
                                             {/* Grid Lines Visual */}
                                            <div className="absolute inset-0 flex flex-col">
                                                {Array.from({ length: rows - 1 }).map((_, i) => (
                                                    <div key={i} className="flex-1 border-b border-green-400/30 border-dashed"></div>
                                                ))}
                                                <div className="flex-1"></div>
                                            </div>
                                            <div className="absolute inset-0 flex">
                                                {Array.from({ length: cols - 1 }).map((_, i) => (
                                                    <div key={i} className="flex-1 border-r border-green-400/30 border-dashed"></div>
                                                ))}
                                                <div className="flex-1"></div>
                                            </div>
                                         </div>
                                    </div>
                                )}
                            </>
                        )}
                        
                        {loading && (
                            <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-20 backdrop-blur-sm">
                                <div className="text-white font-medium">Processing...</div>
                            </div>
                        )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4">
                        {mode === "auto" ? (
                             <button
                                onClick={handleScanToExcel}
                                disabled={loading}
                                className="flex-1 px-6 py-3 bg-slate-800 text-white font-semibold rounded-lg shadow hover:bg-slate-900 transition flex items-center justify-center gap-2"
                            >
                                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                                Auto Scan Grid
                            </button>
                        ) : (
                            <>
                                {!capturedImage ? (
                                    <button
                                        onClick={() => captureFrame()}
                                        className="flex-1 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow hover:bg-blue-700 transition"
                                    >
                                        Capture Image
                                    </button>
                                ) : (
                                    <>
                                        <button
                                            onClick={() => setCapturedImage(null)}
                                            className="px-6 py-3 bg-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-300 transition"
                                        >
                                            Retake
                                        </button>
                                        <button
                                            onClick={handleManualCropScan}
                                            disabled={!completedCrop || completedCrop.width === 0 || loading}
                                            className="flex-1 px-6 py-3 bg-purple-600 text-white font-semibold rounded-lg shadow-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            </svg>
                                            Scan Selected Box
                                        </button>
                                    </>
                                )}
                            </>
                        )}
                    </div>
                    
                    {excelInfo && (
                        <div className="bg-green-100 border-2 border-green-500 text-green-900 px-6 py-4 rounded-xl shadow-lg flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4">
                            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div className="font-semibold text-lg">{excelInfo}</div>
                        </div>
                    )}
                </div>
            </div>
            
            <canvas ref={canvasRef} className="hidden" />
        </div>
    );
};

export default WebcamScannerPage;

