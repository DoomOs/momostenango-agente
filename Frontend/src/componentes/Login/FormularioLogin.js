import React from 'react';
import { useForm } from 'react-hook-form';
import { Box, TextField, Button, Typography } from '@mui/material';

const FormularioLogin = ({ onLogin }) => {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();

  const enviarFormulario = async (datos) => {
    await onLogin(datos);
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(enviarFormulario)}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        padding: 3,
        width: '100%',
        maxWidth: 400,
        margin: 'auto',
      }}
    >
      <Typography variant="h5" align="center">Iniciar Sesión / Registro</Typography>

      <TextField
        label="Nombre completo"
        {...register('nombre', { required: 'El nombre es obligatorio' })}
        error={!!errors.nombre}
        helperText={errors.nombre?.message}
      />

      <TextField
        label="Correo electrónico"
        type="email"
        {...register('email', {
          required: 'El correo es obligatorio',
          pattern: {
            value: /^\S+@\S+$/i,
            message: 'Correo inválido',
          },
        })}
        error={!!errors.email}
        helperText={errors.email?.message}
      />

      <TextField
        label="Teléfono (opcional)"
        {...register('telefono')}
      />

      <Button type="submit" variant="contained" disabled={isSubmitting}>
        {isSubmitting ? 'Procesando...' : 'Entrar'}
      </Button>
    </Box>
  );
};

export default FormularioLogin;