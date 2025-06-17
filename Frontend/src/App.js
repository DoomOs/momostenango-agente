import React, { useState } from 'react';
import FormularioLogin from './componentes/Login/FormularioLogin';
import VentanaChat from './componentes/Chat/VentanaChat';
import { CssBaseline, Box } from '@mui/material';
import './estilos/global.css';

function App() {
  const [usuario, setUsuario] = useState(null); // { ciudadanoId, tokenSesion }

  const manejarLogin = async (datosLogin) => {
  try {
    const response = await fetch('http://localhost:8000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosLogin),
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error en login:', errorText);
      alert('Error en login: ' + errorText);
      return;
    }
    const data = await response.json();
    setUsuario({ ciudadanoId: data.ciudadano_id, tokenSesion: data.token_sesion });
  } catch (error) {
    console.error('Error de conexión al servidor:', error);
    alert('Error de conexión al servidor. Revisa la consola para más detalles.');
  }
};

  const cerrarSesion = () => {
    setUsuario(null);
  };

  return (
    <>
      <CssBaseline />
      <Box sx={{ height: '100vh', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        {!usuario ? (
          <FormularioLogin onLogin={manejarLogin} />
        ) : (
          <VentanaChat
            ciudadanoId={usuario.ciudadanoId}
            tokenSesion={usuario.tokenSesion}
            alCerrarSesion={cerrarSesion}
          />
        )}
      </Box>
    </>
  );
}

export default App;