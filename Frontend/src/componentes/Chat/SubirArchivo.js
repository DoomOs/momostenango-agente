import React, { useState } from 'react';
import { getDocument } from 'pdfjs-dist';
import { 
  Button, 
  LinearProgress, 
  Typography, 
  Box,
  Fade,
  Alert,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { 
  AttachFile as AttachFileIcon,
  CloudUpload as CloudUploadIcon,
  CheckCircle as CheckCircleIcon 
} from '@mui/icons-material';

/**
 * Función auxiliar para extraer texto de un PDF usando PDF.js
 * @param {File} file - Archivo PDF
 * @returns {Promise<string>} Texto extraído
 */
async function extraerTextoPDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await getDocument({ data: arrayBuffer }).promise;
  let texto = '';
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const strings = content.items.map(item => item.str);
    texto += strings.join(' ') + '\n\n';
  }
  return texto;
}

/**
 * Componente mejorado para subir archivos PDF con diseño moderno.
 *
 * Ahora extrae el texto en el cliente y lo envía como JSON al endpoint /chat.
 *
 * Props:
 * - tokenSesion: token de sesión para autenticación.
 * - ciudadanoId: id del ciudadano.
 * - onArchivoSubido: callback cuando el chat responde.
 */
const SubirArchivo = ({ tokenSesion, ciudadanoId, onArchivoSubido }) => {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [nombreArchivo, setNombreArchivo] = useState('');
  const [progreso, setProgreso] = useState(0);
  
  const tema = useTheme();
  const esPantallaPequena = useMediaQuery(tema.breakpoints.down('sm'));

  const manejarCambioArchivo = async (e) => {
    if (e.target.files.length === 0) return;
    const archivo = e.target.files[0];
    setNombreArchivo(archivo.name);
    setError(null);
    setCargando(true);
    setProgreso(0);

    try {
      // 1) Extraer texto en cliente
      const texto = await extraerTextoPDF(archivo);

      // 2) Simular barra de progreso rápida
      const interval = setInterval(() => {
        setProgreso(prev => Math.min(prev + 20, 100));
      }, 100);

      // 3) Enviar al endpoint /chat con JSON
      const resp = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pregunta: texto,
          token_sesion: tokenSesion,
          ciudadano_id: ciudadanoId
        })
      });
      clearInterval(interval);
      setProgreso(100);

      if (!resp.ok) {
        throw new Error(`Error en el servidor: ${resp.status}`);
      }

      const data = await resp.json();
      onArchivoSubido(data);

      // Reset UI
      setTimeout(() => {
        setCargando(false);
        setNombreArchivo('');
        setProgreso(0);
      }, 2000);
    } catch (err) {
      setError(err.message || 'Error procesando PDF');
      setCargando(false);
      setProgreso(0);
    } finally {
      // Liberar input
      e.target.value = '';
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 200 }}>
      <Button 
        variant="outlined" 
        component="label" 
        disabled={cargando}
        startIcon={cargando ? <CloudUploadIcon /> : <AttachFileIcon />}
        sx={{ /* estilos omitidos por brevedad, mantén los tuyos */ }}
      >
        {cargando ? 'Procesando...' : 'Adjuntar PDF'}
        <input 
          type="file" 
          hidden 
          accept="application/pdf" 
          onChange={manejarCambioArchivo}
          disabled={cargando}
        />
      </Button>

      {nombreArchivo && (
        <Typography variant="body2">{nombreArchivo}</Typography>
      )}

      {cargando && (
        <LinearProgress variant="determinate" value={progreso} />
      )}

      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default SubirArchivo;
