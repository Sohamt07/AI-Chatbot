import { useState } from "react";
import { Box, TextField, Button, Paper, Typography } from "@mui/material";
import { API } from "../api";
import { marked } from "marked";

export default function ChatBox() {
  const [query, setQuery] = useState("");
  const [log, setLog] = useState([]);

  const sendQuery = async () => {
    if (!query.trim()) return;

    setLog((prev) => [...prev, { sender: "user", text: query }]);

    const res = await API.get("/ask", { params: { query } });

    setLog((prev) => [...prev, { sender: "bot", text: res.data.response }]);
    setQuery("");
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        💬 Ask Questions About the Data
      </Typography>

      <Paper sx={{ p: 2, mb: 2, height: 250, overflowY: "auto" }}>
        {log.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              textAlign: msg.sender === "user" ? "right" : "left",
              mb: 1,
            }}
          >
            <Typography
              sx={{
                display: "inline-block",
                p: 1,
                borderRadius: 2,
                bgcolor: msg.sender === "user" ? "primary.main" : "grey.300",
                color: msg.sender === "user" ? "white" : "black",
              }}
            >
              <span
                dangerouslySetInnerHTML={{ __html: marked.parse(msg.text) }}
              />
            </Typography>
          </Box>
        ))}
      </Paper>

      <Box sx={{ display: "flex", gap: 2 }}>
        <TextField
          fullWidth
          label="Ask something..."
          variant="outlined"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="contained" onClick={sendQuery}>
          Send
        </Button>
      </Box>
    </Box>
  );
}
