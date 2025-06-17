import React from 'react';
import { Box, Typography, Avatar, useTheme, useMediaQuery } from '@mui/material';
import { 
  Person as PersonIcon, 
  SmartToy as BotIcon,
  Info as InfoIcon 
} from '@mui/icons-material';

/**
 * Componente para mostrar un mensaje en el chat con diseño moderno.
 *
 * Props:
 * - texto: contenido del mensaje.
 * - esUsuario: boolean, si es mensaje del usuario.
 * - esSistema: boolean, si es mensaje del sistema.
 */
const Mensaje = ({ texto, esUsuario, esSistema }) => {
  const tema = useTheme();
  const esPantallaPequena = useMediaQuery(tema.breakpoints.down('sm'));

  const obtenerEstilosMensaje = () => {
    if (esSistema) {
      return {
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        color: tema.palette.info.dark,
        border: `1px solid ${tema.palette.info.light}`,
        alignSelf: 'center',
        maxWidth: '90%'
      };
    }
    
    if (esUsuario) {
      return {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        alignSelf: 'flex-end',
        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
      };
    }
    
    return {
      backgroundColor: 'white',
      color: tema.palette.text.primary,
      alignSelf: 'flex-start',
      border: `1px solid ${tema.palette.divider}`,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
    };
  };

  const obtenerIcono = () => {
    if (esSistema) return <InfoIcon />;
    if (esUsuario) return <PersonIcon />;
    return <BotIcon />;
  };

  const obtenerColorAvatar = () => {
    if (esSistema) return tema.palette.info.main;
    if (esUsuario) return '#667eea';
    return tema.palette.primary.main;
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: esPantallaPequena ? 1 : 1.5,
        margin: '8px 0',
        flexDirection: esUsuario ? 'row-reverse' : 'row',
        maxWidth: '100%'
      }}
    >
      {/* Avatar */}
      <Avatar
        sx={{
          width: esPantallaPequena ? 32 : 40,
          height: esPantallaPequena ? 32 : 40,
          backgroundColor: obtenerColorAvatar(),
          flexShrink: 0,
          '& .MuiSvgIcon-root': {
            fontSize: esPantallaPequena ? '1rem' : '1.2rem'
          }
        }}
      >
        {obtenerIcono()}
      </Avatar>

      {/* Mensaje */}
      <Box
        sx={{
          ...obtenerEstilosMensaje(),
          maxWidth: esSistema ? '90%' : '75%',
          minWidth: 'fit-content',
          padding: esPantallaPequena ? '10px 14px' : '12px 18px',
          borderRadius: esSistema ? '12px' : esUsuario ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          position: 'relative',
          backdropFilter: esSistema ? 'blur(5px)' : 'none',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: esSistema 
              ? '0 4px 12px rgba(33, 150, 243, 0.2)' 
              : esUsuario 
                ? '0 6px 16px rgba(102, 126, 234, 0.5)'
                : '0 4px 12px rgba(0, 0, 0, 0.15)'
          }
        }}
      >
        <Typography 
          variant="body1" 
          sx={{
            fontSize: esPantallaPequena ? '0.9rem' : '1rem',
            lineHeight: 1.5,
            fontWeight: esSistema ? 500 : 400,
            '& strong': {
              fontWeight: 600
            },
            '& em': {
              fontStyle: 'italic',
              opacity: 0.9
            }
          }}
        >
          {texto}
        </Typography>
        
        {/* Timestamp */}
        <Typography 
          variant="caption" 
          sx={{
            display: 'block',
            textAlign: esUsuario ? 'right' : 'left',
            marginTop: '4px',
            opacity: 0.7,
            fontSize: '0.75rem',
            color: esUsuario ? 'rgba(255, 255, 255, 0.8)' : tema.palette.text.secondary
          }}
        >
          {new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </Typography>
      </Box>
    </Box>
  );
};

export default Mensaje;