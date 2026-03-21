import type { ForecastResponse } from "@/lib/api";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export async function exportExcel(result: ForecastResponse) {
  const wb = XLSX.utils.book_new();

  // Forecast sheet
  const forecastData = result.forecast.map((f, i) => ({
    Langkah: `t+${i + 1}`,
    Prediksi: parseFloat(f.toFixed(4)),
    "Batas Bawah": parseFloat(result.forecast_lower[i].toFixed(4)),
    "Batas Atas": parseFloat(result.forecast_upper[i].toFixed(4)),
  }));
  const forecastSheet = XLSX.utils.json_to_sheet(forecastData);
  XLSX.utils.book_append_sheet(wb, forecastSheet, "Forecast");

  // Validation sheet
  const valData = result.val_actual.map((a, i) => ({
    Index: i,
    Aktual: parseFloat(a.toFixed(4)),
    Prediksi: parseFloat(result.val_predictions[i].toFixed(4)),
    Error: parseFloat((a - result.val_predictions[i]).toFixed(4)),
  }));
  const valSheet = XLSX.utils.json_to_sheet(valData);
  XLSX.utils.book_append_sheet(wb, valSheet, "Validasi");

  // Profile sheet
  const profileData = [{
    Trend: result.profile.trend_strength,
    Seasonal: result.profile.seasonal_strength,
    Noise: result.profile.noise_level,
    Period: result.profile.seasonal_period,
    Stationarity: result.profile.stationarity,
    "Data Length": result.profile.data_length,
  }];
  const profileSheet = XLSX.utils.json_to_sheet(profileData);
  XLSX.utils.book_append_sheet(wb, profileSheet, "Profil Data");

  // Fitness history sheet
  const fitnessData = result.fitness_history.map((h) => ({
    Generasi: h.gen,
    "Best Fitness": h.best,
    "Avg Fitness": h.avg,
    Diversity: h.diversity,
    Metric: h.metric,
    "Avg Mutation": h.avg_mutation,
  }));
  const fitnessSheet = XLSX.utils.json_to_sheet(fitnessData);
  XLSX.utils.book_append_sheet(wb, fitnessSheet, "Fitness History");

  // Model weights sheet
  const weightData = Object.entries(result.final_weights).map(([model, weight]) => ({
    Model: model,
    Bobot: weight,
    "Bobot (%)": parseFloat((weight * 100).toFixed(1)),
  }));
  const weightSheet = XLSX.utils.json_to_sheet(weightData);
  XLSX.utils.book_append_sheet(wb, weightSheet, "Bobot Model");

  XLSX.writeFile(wb, `forecast_report_${Date.now()}.xlsx`);
}

export async function exportPDF(chartContainerId: string, result: ForecastResponse) {
  const pdf = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  const pageW = pdf.internal.pageSize.getWidth();

  // Title
  pdf.setFontSize(16);
  pdf.text("Adaptive Forecasting Engine — Report", 14, 15);

  pdf.setFontSize(9);
  pdf.text(`Generated: ${new Date().toLocaleString("id-ID")}`, 14, 22);

  // Profile summary
  let y = 30;
  pdf.setFontSize(11);
  pdf.text("Profil Data", 14, y);
  y += 6;
  pdf.setFontSize(9);
  const p = result.profile;
  pdf.text(`Trend: ${(p.trend_strength * 100).toFixed(1)}%  |  Seasonal: ${(p.seasonal_strength * 100).toFixed(1)}% (T=${p.seasonal_period})  |  Noise: ${(p.noise_level * 100).toFixed(1)}%`, 14, y);
  y += 5;
  pdf.text(`RMSE: ${Math.sqrt(result.val_mse).toFixed(4)}  |  Confidence: ${(result.confidence * 100).toFixed(1)}%  |  Drift Events: ${result.drift_events.length}`, 14, y);
  y += 5;

  // Model weights
  const weights = Object.entries(result.final_weights)
    .map(([m, w]) => `${m}: ${(w * 100).toFixed(1)}%`)
    .join("  |  ");
  pdf.text(`Bobot Model: ${weights}`, 14, y);
  y += 8;

  // Capture chart as image
  const container = document.getElementById(chartContainerId);
  if (container) {
    try {
      const canvas = await html2canvas(container, {
        backgroundColor: null,
        scale: 2,
      });
      const imgData = canvas.toDataURL("image/png");
      const imgW = pageW - 28;
      const imgH = (canvas.height / canvas.width) * imgW;
      pdf.addImage(imgData, "PNG", 14, y, imgW, Math.min(imgH, 120));
      y += Math.min(imgH, 120) + 5;
    } catch {
      // skip chart if capture fails
    }
  }

  // Forecast table
  if (y > 160) {
    pdf.addPage();
    y = 15;
  }
  pdf.setFontSize(11);
  pdf.text("Tabel Forecast", 14, y);
  y += 6;
  pdf.setFontSize(8);

  // table header
  pdf.text("Langkah", 14, y);
  pdf.text("Prediksi", 50, y);
  pdf.text("Batas Bawah", 80, y);
  pdf.text("Batas Atas", 115, y);
  y += 4;

  for (let i = 0; i < result.forecast.length; i++) {
    if (y > 190) {
      pdf.addPage();
      y = 15;
    }
    pdf.text(`t+${i + 1}`, 14, y);
    pdf.text(result.forecast[i].toFixed(2), 50, y);
    pdf.text(result.forecast_lower[i].toFixed(2), 80, y);
    pdf.text(result.forecast_upper[i].toFixed(2), 115, y);
    y += 4;
  }

  pdf.save(`forecast_report_${Date.now()}.pdf`);
}
