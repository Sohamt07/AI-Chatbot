import { Box, Typography, Grid, Card, CardMedia } from "@mui/material";

export default function PlotGallery({ plots }) {
  if (!plots.length) return null;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        📊 Generated Plots
      </Typography>

      <Grid container spacing={2}>
        {plots.map((url, i) => (
          <Grid item xs={12} sm={6} md={4} key={i}>
            <Card>
              <CardMedia
                component="img"
                image={`http://localhost:8000${url}`}
                alt="plot"
              />
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
