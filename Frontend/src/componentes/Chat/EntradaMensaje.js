import React from 'react';
import { Box, TextField, IconButton, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const EntradaMensaje = ({ valor, alCambiar, alEnviar, deshabilitado }) => {
  const manejarTecla = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      alEnviar();
    }
  };

  return (
    <Box sx={{ display: 'flex', padding: 1, borderTop: '1px solid #ddd' }}>
      <TextField
        multiline
        maxRows={4}
        fullWidth
        placeholder="Escribe tu mensaje..."
        value={valor}
        onChange={alCambiar}
        onKeyDown={manejarTecla}
        disabled={deshabilitado}
      />
      <IconButton color="primary" onClick={alEnviar} disabled={deshabilitado} sx={{ ml: 1 }}>
        {deshabilitado ? <CircularProgress size={24} /> : <SendIcon />}
      </IconButton>
    </Box>
  );
};

export default EntradaMensaje;