import React, { useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  IconButton, 
  CircularProgress,
  useTheme,
  useMediaQuery,
  Fade
} from '@mui/material';
import { 
  Send as SendIcon,
  Mic as MicIcon 
} from '@mui/icons-material';

/**
 * Componente mejorado para entrada de texto con botón de enviar.
 * Soporta enviar con Enter (sin Shift) y diseño moderno.
 *
 * Props:
 * - valor: texto actual.
 * - alCambiar: función para actualizar texto.
 * - alEnviar: función para enviar mensaje.
 * - deshabilitado: boolean para deshabilitar entrada y botón.
 */
const EntradaMensaje = ({ valor, alCambiar, alEnviar, deshabilitado }) => {
  const tema = useTheme();
  const esPantallaPequena = useMediaQuery(tema.breakpoints.down('sm'));
  const inputRef = useRef(null);

  // Auto-focus en el input cuando se habilita
  useEffect(() => {
    if (!deshabilitado && inputRef.current) {
      inputRef.current.focus();
    }
  }, [deshabilitado]);

  const manejarTecla = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      alEnviar();
    }
  };

  const puedeEnviar = valor.trim().length > 0 && !deshabilitado;

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'flex-end',
        gap: 1,
        position: 'relative'
      }}
    >
      <TextField
        inputRef={inputRef}
        multiline
        maxRows={4}
        fullWidth
        placeholder={deshabilitado ? "Esperando respuesta..." : "Escribe tu mensaje aquí..."}
        value={valor}
        onChange={alCambiar}
        onKeyDown={manejarTecla}
        disabled={deshabilitado}
        variant="outlined"
        sx={{
          '& .MuiOutlinedInput-root': {
            borderRadius: '20px',
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
            paddingRight: '8px',
            minHeight: '48px',
            fontSize: esPantallaPequena ? '0.9rem' : '1rem',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: 'rgba(0, 0, 0, 0.04)',
            },
            '&.Mui-focused': {
              backgroundColor: 'white',
              boxShadow: '0 0 0 2px rgba(102, 126, 234, 0.2)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#667eea',
                borderWidth: '2px'
              }
            },
            '&.Mui-disabled': {
              backgroundColor: 'rgba(0, 0, 0, 0.06)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'rgba(0, 0, 0, 0.1)'
              }
            }
          },
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s ease-in-out'
          },
          '& .MuiInputBase-input': {
            padding: '12px 16px',
            '&::placeholder': {
              color: 'rgba(0, 0, 0, 0.4)',
              opacity: 1
            }
          }
        }}
      />

      {/* Botón de Enviar */}
      <Fade in={true}>
        <IconButton 
          color="primary" 
          onClick={alEnviar} 
          disabled={!puedeEnviar}
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: puedeEnviar 
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : 'rgba(0, 0, 0, 0.12)',
            color: puedeEnviar ? 'white' : 'rgba(0, 0, 0, 0.26)',
            boxShadow: puedeEnviar ? '0 4px 12px rgba(102, 126, 234, 0.4)' : 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              background: puedeEnviar 
                ? 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)'
                : 'rgba(0, 0, 0, 0.12)',
              transform: puedeEnviar ? 'translateY(-1px) scale(1.05)' : 'none',
              boxShadow: puedeEnviar ? '0 6px 16px rgba(102, 126, 234, 0.5)' : 'none'
            },
            '&:active': {
              transform: puedeEnviar ? 'translateY(0) scale(0.98)' : 'none'
            },
            '&.Mui-disabled': {
              background: 'rgba(0, 0, 0, 0.12)',
              color: 'rgba(0, 0, 0, 0.26)'
            }
          }}
        >
          {deshabilitado ? (
            <CircularProgress 
              size={20} 
              thickness={6}
              sx={{ color: 'rgba(102, 126, 234, 0.6)' }}
            />
          ) : (
            <SendIcon sx={{ fontSize: '1.2rem' }} />
          )}
        </IconButton>
      </Fade>

      {/* Contador de caracteres (opcional) */}
      {valor.length > 200 && (
        <Box
          sx={{
            position: 'absolute',
            bottom: -20,
            right: 60,
            fontSize: '0.75rem',
            color: valor.length > 500 ? 'error.main' : 'text.secondary',
            backgroundColor: 'white',
            padding: '2px 6px',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}
        >
          {valor.length}/1000
        </Box>
      )}
    </Box>
  );
};

export default EntradaMensaje;