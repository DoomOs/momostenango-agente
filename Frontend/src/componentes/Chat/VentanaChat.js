import React, { useState, useEffect, useRef } from 'react';
import Mensaje from './Mensaje';
import EntradaMensaje from './EntradaMensaje';
import SubirArchivo from './SubirArchivo';
import { 
  Box, 
  Button, 
  Typography, 
  Alert, 
  CircularProgress,
  Paper,
  Divider,
  useTheme,
  useMediaQuery,
  Fade,
  Chip
} from '@mui/material';
import { 
  Clear as ClearIcon, 
  ExitToApp as ExitIcon,
  SmartToy as BotIcon 
} from '@mui/icons-material';

const VentanaChat = ({ ciudadanoId, tokenSesion, alCerrarSesion }) => {
  const [mensajes, setMensajes] = useState([]);
  const [entrada, setEntrada] = useState('');
  const [cargando, setCargando] = useState(false);
  const [derivadoHumano, setDerivadoHumano] = useState(false);
  const [errorGlobal, setErrorGlobal] = useState(null);
  const [mostrarBienvenida, setMostrarBienvenida] = useState(true);
  const mensajesFinRef = useRef(null);
  const areaContenedorRef = useRef(null);
  
  const tema = useTheme();
  const esPantallaPequena = useMediaQuery(tema.breakpoints.down('md'));

  // Scroll automático al final
  useEffect(() => {
    if (mensajesFinRef.current) {
      mensajesFinRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [mensajes]);

  // Ocultar mensaje de bienvenida cuando hay mensajes
  useEffect(() => {
    if (mensajes.length > 0) {
      setMostrarBienvenida(false);
    }
  }, [mensajes]);

  // Enviar mensaje al backend con streaming real
  const enviarMensaje = async () => {
    if (!entrada.trim() || cargando || derivadoHumano) return;

    const textoUsuario = entrada.trim();
    setMensajes((prev) => [...prev, { texto: textoUsuario, esUsuario: true }]);
    setEntrada('');
    setCargando(true);
    setErrorGlobal(null);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pregunta: textoUsuario,
          ciudadano_id: ciudadanoId,
          token_sesion: tokenSesion,
        }),
      });

      if (!response.body) throw new Error('No se pudo obtener el stream');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let respuestaTexto = '';
      let derivarHumanoDetectado = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        respuestaTexto += chunk;
        setMensajes((prev) => {
          const msgs = [...prev];
          if (msgs.length === 0 || msgs[msgs.length - 1].esUsuario) {
            msgs.push({ texto: chunk, esUsuario: false });
          } else {
            msgs[msgs.length - 1].texto += chunk;
          }
          return msgs;
        });

        if (respuestaTexto.includes('Uno de nuestros colaboradores se pondrá en contacto')) {
          derivarHumanoDetectado = true;
          setDerivadoHumano(true);
        }
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

      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Error al subir archivo');

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
    setMostrarBienvenida(true);
    try {
      await fetch('http://localhost:8000/limpiar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ciudadano_id: ciudadanoId,
          token_sesion: tokenSesion,
        }),
      });
    } catch {
      // Ignorar errores en limpieza
    }
  };

  return (
    <Paper 
      elevation={8}
      sx={{ 
        height: esPantallaPequena ? '100vh' : 'calc(100vh - 40px)',
        width: '100%',
        maxWidth: esPantallaPequena ? '100%' : '900px',
        margin: 'auto',
        borderRadius: esPantallaPequena ? 0 : 3,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        position: 'relative'
      }}
    >
      {/* Header del Chat */}
      <Box
        sx={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
          padding: '16px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <BotIcon sx={{ color: 'white', fontSize: 32 }} />
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'white', 
                fontWeight: 600,
                fontSize: esPantallaPequena ? '1.1rem' : '1.25rem'
              }}
            >
              Asistente Virtual
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '0.85rem'
              }}
            >
              {derivadoHumano ? 'Derivado a humano' : 'En línea'}
            </Typography>
          </Box>
        </Box>
        {derivadoHumano && (
          <Chip 
            label="Derivado" 
            size="small" 
            sx={{ 
              backgroundColor: 'rgba(255, 193, 7, 0.9)',
              color: 'rgba(0, 0, 0, 0.87)',
              fontWeight: 600
            }} 
          />
        )}
      </Box>

      {/* Área de Mensajes */}
      <Box
        ref={areaContenedorRef}
        sx={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(5px)',
          minHeight: 0, // Importante para flex scroll
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(0, 0, 0, 0.1)',
            borderRadius: '10px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '10px',
            '&:hover': {
              background: 'rgba(0, 0, 0, 0.5)',
            },
          },
        }}
      >
        {/* Mensaje de Bienvenida */}
        {mostrarBienvenida && mensajes.length === 0 && (
          <Fade in={mostrarBienvenida} timeout={800}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
                opacity: 0.7,
                py: 4
              }}
            >
              <BotIcon sx={{ fontSize: 64, color: tema.palette.primary.main, mb: 2 }} />
              <Typography 
                variant="h5" 
                gutterBottom 
                sx={{ 
                  fontWeight: 600,
                  color: tema.palette.text.primary,
                  mb: 1
                }}
              >
                ¡Hola! Soy tu asistente virtual
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  color: tema.palette.text.secondary,
                  maxWidth: 400,
                  lineHeight: 1.6
                }}
              >
                Estoy aquí para ayudarte. Puedes hacerme preguntas, subir archivos o solicitar información. ¿En qué puedo asistirte hoy?
              </Typography>
            </Box>
          </Fade>
        )}

        {/* Mensaje de Error Global */}
        {errorGlobal && (
          <Fade in={Boolean(errorGlobal)}>
            <Alert 
              severity="error" 
              onClose={() => setErrorGlobal(null)} 
              sx={{ 
                mb: 2,
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  alignItems: 'center'
                }
              }}
            >
              {errorGlobal}
            </Alert>
          </Fade>
        )}

        {/* Lista de Mensajes */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {mensajes.map((msg, idx) => (
            <Fade in={true} key={idx} timeout={300} style={{ transitionDelay: `${idx * 50}ms` }}>
              <div>
                <Mensaje
                  texto={msg.texto}
                  esUsuario={msg.esUsuario}
                  esSistema={msg.esSistema}
                />
              </div>
            </Fade>
          ))}
          <div ref={mensajesFinRef} />
        </Box>

        {/* Indicador de Carga */}
        {cargando && (
          <Fade in={cargando}>
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2,
                padding: '12px 20px',
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: '20px',
                alignSelf: 'flex-start',
                mb: 1
              }}
            >
              <CircularProgress size={16} thickness={6} />
              <Typography 
                variant="body2" 
                sx={{ 
                  color: tema.palette.text.secondary,
                  fontStyle: 'italic'
                }}
              >
                Escribiendo...
              </Typography>
            </Box>
          </Fade>
        )}
      </Box>

      <Divider sx={{ opacity: 0.3 }} />

      {/* Panel de Controles */}
      <Box
        sx={{
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(10px)',
          padding: '16px 20px',
          flexShrink: 0,
          borderTop: '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        {/* Entrada de Mensaje */}
        <EntradaMensaje
          valor={entrada}
          alCambiar={manejarCambioEntrada}
          alEnviar={enviarMensaje}
          deshabilitado={cargando || derivadoHumano}
        />

        {/* Controles Adicionales */}
        <Box 
          sx={{ 
            mt: 2,
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            flexWrap: esPantallaPequena ? 'wrap' : 'nowrap',
            gap: 1
          }}
        >
         {/* funcionalidad retirada por problemas tecnicos
         
         <SubirArchivo
            tokenSesion={tokenSesion}
            ciudadanoId={ciudadanoId}
            onArchivoSubido={manejarSeleccionArchivo}
          />*/}
          
          <Box 
            sx={{ 
              display: 'flex', 
              gap: 1,
              flexWrap: esPantallaPequena ? 'wrap' : 'nowrap'
            }}
          >
            <Button 
              variant="outlined" 
              color="error" 
              onClick={limpiarChat} 
              disabled={cargando}
              startIcon={<ClearIcon />}
              size={esPantallaPequena ? 'small' : 'medium'}
              sx={{
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 500,
                minWidth: esPantallaPequena ? 'auto' : '140px'
              }}
            >
              {esPantallaPequena ? 'Limpiar' : 'Limpiar Chat'}
            </Button>
            
            <Button 
              variant="contained" 
              color="primary" 
              onClick={alCerrarSesion} 
              disabled={cargando}
              startIcon={<ExitIcon />}
              size={esPantallaPequena ? 'small' : 'medium'}
              sx={{
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 500,
                minWidth: esPantallaPequena ? 'auto' : '140px',
                background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #5a6fd8 30%, #6a4190 90%)',
                }
              }}
            >
              {esPantallaPequena ? 'Salir' : 'Cerrar Sesión'}
            </Button>
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};

export default VentanaChat;