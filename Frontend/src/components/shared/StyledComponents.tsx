import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";

export const HeaderBox = styled(Box)({
  borderBottom: "1px solid #E0E0E0",
  marginBottom: "20px",
  paddingBottom: "12px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
});

export const HeaderText = styled(Typography)({
  color: "#C00000",
  fontWeight: 600,
  fontSize: "24px",
}); 