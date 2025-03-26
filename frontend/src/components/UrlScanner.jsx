import React, { useState } from "react";
import ScoreChart from "./ScoreChart";
import LoadingSpinner from "./LoadingSpinner";

const UrlScanner = () => {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScan = async () => {
    if (!url.trim()) {
      setError("⚠️ Please enter a valid URL.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error("❌ Failed to scan URL.");
      }

      const data = await response.json();
      setResult(data);
    } catch  {
      setError("❌ Error scanning the URL.");
    }

    setLoading(false);
  };

  return (
    <div className="p-6 max-w-lg mx-auto bg-white shadow-md rounded-lg">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">🔍 URL Scanner</h2>
      
      <input
        type="text"
        className="w-full p-3 border border-gray-300 rounded-md text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Enter URL (e.g., https://example.com)"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      
      <button
        onClick={handleScan}
        className={`mt-4 w-full py-2 rounded-md font-semibold text-white ${
          loading ? "bg-blue-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
        }`}
        disabled={loading}
      >
        {loading ? "Scanning..." : "Scan URL"}
      </button>

      {loading && <LoadingSpinner />}

      {error && <p className="mt-3 text-red-500 text-sm">{error}</p>}

      {result && (
        <div className="mt-6 p-4 border rounded-lg bg-gray-50 text-gray-800 shadow-sm">
          <h3 className="text-lg font-semibold">📊 Scan Results</h3>
          <p className="mt-2">
            <strong>📊 Prediction:</strong> {result.prediction}
          </p>
          <p>
            <strong>✅ WHOIS Domain Age:</strong> {result.domain_age} years
          </p>
          <p>
            <strong>🔐 SSL Certificate:</strong> {result.ssl_valid ? "Valid ✅" : "Invalid ❌"}
          </p>
          <p>⚡ Confidence Score: {result.confidence_score !== undefined ? `${result.confidence_score}%` : "N/A"}</p>


          <ScoreChart scores={result.scores} />
        </div>
      )}
    </div>
  );
};

export default UrlScanner;
