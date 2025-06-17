import React from 'react';
import { Box, Typography } from '@mui/material';

const Mensaje = ({ texto, esUsuario, esSistema }) => {
  return (
    <Box
      sx={{
        maxWidth: '75%',
        margin: '8px',
        padding: '10px 15px',
        borderRadius: '20px',
        backgroundColor: esSistema ? '#e0e0e0' : esUsuario ? '#1976d2' : '#f1f0f0',
        color: esSistema ? '#333' : esUsuario ? 'white' : 'black',
        alignSelf: esUsuario ? 'flex-end' : 'flex-start',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      <Typography variant="body1">{texto}</Typography>
    </Box>
  );
};

export default Mensaje;