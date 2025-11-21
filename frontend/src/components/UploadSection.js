import { useState } from "react";
import { Box, Button, LinearProgress, Typography } from "@mui/material";
import { API } from "../api";

export default function UploadSection({ setEda, setInsights, setPlots }) {
  const [loading, setLoading] = useState(false);

  const uploadCSV = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await API.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setEda(res.data.eda);
      setInsights(res.data.insights);
      setPlots(res.data.plots);
    } catch (err) {
      alert("Upload failed: " + err.response?.data?.detail);
    }

    setLoading(false);
  };

  return (
    <Box>
      <Button variant="contained" component="label">
        Upload CSV
        <input hidden type="file" accept=".csv" onChange={uploadCSV} />
      </Button>

      {loading && <LinearProgress sx={{ mt: 2 }} />}

      <Typography variant="body2" sx={{ mt: 1 }}>
        Supported: CSV files only
      </Typography>
    </Box>
  );
}
