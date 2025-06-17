import React, { useState } from 'react';
import { Button, LinearProgress, Typography } from '@mui/material';
import axios from 'axios';

const SubirArchivo = ({ tokenSesion, ciudadanoId, onArchivoSubido }) => {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const manejarCambioArchivo = async (e) => {
    if (e.target.files.length === 0) return;
    const archivo = e.target.files[0];
    setError(null);
    setCargando(true);

    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('token_sesion', tokenSesion);
    formData.append('ciudadano_id', ciudadanoId);

    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onArchivoSubido(response.data);
    } catch (err) {
      setError('Error al subir archivo.');
    } finally {
      setCargando(false);
    }
  };

  return (
    <>
      <Button variant="outlined" component="label" sx={{ mt: 1 }}>
        Adjuntar archivo
        <input type="file" hidden onChange={manejarCambioArchivo} />
      </Button>
      {cargando && <LinearProgress sx={{ mt: 1 }} />}
      {error && <Typography color="error" variant="body2" sx={{ mt: 1 }}>{error}</Typography>}
    </>
  );
};

export default SubirArchivo;