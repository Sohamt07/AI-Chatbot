import { Box, Typography, Paper } from "@mui/material";

export default function InsightsSection({ eda, insights }) {
  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        📈 Exploratory Data Analysis (EDA)
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography>Shape: {eda.shape.join(" × ")}</Typography>
        <Typography>Columns: {eda.columns.join(", ")}</Typography>
      </Paper>

      <Typography variant="h5" fontWeight="bold" gutterBottom>
        🤖 AI Insights
      </Typography>

      <Paper sx={{ p: 2, whiteSpace: "pre-line", fontSize: 16 }}>
        {insights}
      </Paper>
    </Box>
  );
}
