import React, { useState, useEffect, useRef } from 'react';
import Mensaje from './Mensaje';
import EntradaMensaje from './EntradaMensaje';
import SubirArchivo from './SubirArchivo';
import { Box, Button, Typography, Alert, Grid } from '@mui/material';
import axios from 'axios';

const VentanaChat = ({ ciudadanoId, tokenSesion, alCerrarSesion }) => {
  const [mensajes, setMensajes] = useState([]);
  const [entrada, setEntrada] = useState('');
  const [cargando, setCargando] = useState(false);
  const [derivadoHumano, setDerivadoHumano] = useState(false);
  const [errorGlobal, setErrorGlobal] = useState(null);
  const mensajesFinRef = useRef(null);

  // Scroll automático al final
  useEffect(() => {
    mensajesFinRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  // Enviar mensaje al backend
  const enviarMensaje = async () => {
    if (!entrada.trim() || cargando || derivadoHumano) return;

    const textoUsuario = entrada.trim();
    setMensajes((prev) => [...prev, { texto: textoUsuario, esUsuario: true }]);
    setEntrada('');
    setCargando(true);
    setErrorGlobal(null);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        pregunta: textoUsuario,
        ciudadano_id: ciudadanoId,
        token_sesion: tokenSesion,
      }, {
        responseType: 'text',
      });

      const respuestaTexto = response.data;

      // Detectar mensaje de derivación a humano
      if (respuestaTexto.includes('Uno de nuestros colaboradores se pondrá en contacto')) {
        setMensajes((prev) => [...prev, { texto: respuestaTexto, esSistema: true }]);
        setDerivadoHumano(true);
      } else {
        setMensajes((prev) => [...prev, { texto: respuestaTexto, esUsuario: false }]);
      }
    } catch (error) {
      setErrorGlobal('Error al comunicarse con el servidor.');
      setMensajes((prev) => [...prev, { texto: 'Error al comunicarse con el servidor.', esSistema: true }]);
    } finally {
      setCargando(false);
    }
  };

  const manejarCambioEntrada = (e) => setEntrada(e.target.value);

  const manejarSeleccionArchivo = async (archivo) => {
    setErrorGlobal(null);
    setCargando(true);
    try {
      const formData = new FormData();
      formData.append('archivo', archivo);
      formData.append('token_sesion', tokenSesion);
      formData.append('ciudadano_id', ciudadanoId);

      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setMensajes((prev) => [...prev, { texto: 'Archivo subido correctamente.', esSistema: true }]);
    } catch (error) {
      setErrorGlobal('Error al subir archivo.');
    } finally {
      setCargando(false);
    }
  };

  const limpiarChat = async () => {
    setMensajes([]);
    setDerivadoHumano(false);
    setErrorGlobal(null);
    try {
      await axios.post('http://localhost:8000/limpiar', {
        ciudadano_id: ciudadanoId,
        token_sesion: tokenSesion,
      });
    } catch {
      // Ignorar errores en limpieza
    }
  };

  return (
    <Grid container direction="column" sx={{ height: '100%' }}>
      <Grid item xs sx={{ overflowY: 'auto', padding: 2, backgroundColor: '#fafafa' }}>
        {errorGlobal && (
          <Alert severity="error" onClose={() => setErrorGlobal(null)} sx={{ mb: 1 }}>
            {errorGlobal}
          </Alert>
        )}
        {mensajes.map((msg, idx) => (
          <Mensaje
            key={idx}
            texto={msg.texto}
            esUsuario={msg.esUsuario}
            esSistema={msg.esSistema}
          />
        ))}
        <div ref={mensajesFinRef} />
      </Grid>

      <Grid item>
        <EntradaMensaje
          valor={entrada}
          alCambiar={manejarCambioEntrada}
          alEnviar={enviarMensaje}
          deshabilitado={cargando || derivadoHumano}
        />
        <SubirArchivo
          tokenSesion={tokenSesion}
          ciudadanoId={ciudadanoId}
          onArchivoSubido={manejarSeleccionArchivo}
        />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, px: 1 }}>
          <Button variant="text" color="error" onClick={limpiarChat} disabled={cargando}>
            Borrar chat y continuar
          </Button>
          <Button variant="outlined" color="primary" onClick={alCerrarSesion} disabled={cargando}>
            Cerrar sesión
          </Button>
        </Box>
      </Grid>
    </Grid>
  );
};

export default VentanaChat;