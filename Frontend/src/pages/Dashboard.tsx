import React from 'react';
import { Box, Typography } from '@mui/material';

export const Dashboard: React.FC = () => {
  return (
    <Box p={4}>
      <Typography variant="h2">Dashboard</Typography>
      <Typography variant="body1" mt={2}>
        Dashboard page
      </Typography>
    </Box>
  );
};

export default Dashboard; 