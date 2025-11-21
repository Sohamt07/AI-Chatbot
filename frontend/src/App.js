import { Container, Box, Typography, Divider } from "@mui/material";
import UploadSection from "./components/UploadSection";
import InsightsSection from "./components/InsightsSection";
import PlotGallery from "./components/PlotGallery";
import ChatBox from "./components/ChatBox";
import { useState } from "react";

function App() {
  const [eda, setEda] = useState(null);
  const [insights, setInsights] = useState("");
  const [plots, setPlots] = useState([]);

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          📊 AI Data Analyst (Gemini)
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload a CSV → Get Automatic EDA → AI Insights → Ask Questions
        </Typography>

        <Divider sx={{ my: 3 }} />

        {/* Upload */}
        <UploadSection setEda={setEda} setInsights={setInsights} setPlots={setPlots} />

        {eda && (
          <>
            <Divider sx={{ my: 4 }} />

            {/* EDA + Insights */}
            <InsightsSection eda={eda} insights={insights} />

            {/* Plots */}
            <PlotGallery plots={plots} />

            <Divider sx={{ my: 4 }} />

            {/* Ask AI */}
            <ChatBox />
          </>
        )}
      </Box>
    </Container>
  );
}

export default App;