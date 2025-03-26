import React from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js";

// Register necessary chart components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const ScoreChart = ({ scores, prediction }) => {
  // Override scores if the final prediction is Benign due to SSL & WHOIS
  const adjustedScores = prediction === "Benign" ? { benign: 100, phishing: 0, defacement: 0 } : scores;

  const data = {
    labels: ["Benign", "Phishing", "Defacement"],
    datasets: [
      {
        label: "Confidence Score (%)",
        data: [adjustedScores.benign, adjustedScores.phishing, adjustedScores.defacement],
        backgroundColor: ["#4CAF50", "#FF5733", "#FFC107"], // Green for safe, Red for phishing, Yellow for defacement
      },
    ],
  };

  const options = {
    responsive: true,
    scales: {
      y: { beginAtZero: true, max: 100 },
    },
  };

  return (
    <div className="mt-4 p-4 bg-white shadow-md rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800">📊 Confidence Scores</h3>
      <Bar data={data} options={options} />
    </div>
  );
};

export default ScoreChart;
