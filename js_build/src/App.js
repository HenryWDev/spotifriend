import './App.css';
import React, { useState, useEffect } from 'react';
import MainScreenHandler from './components/MainScreenHandler'
import AuthenticationHandler from './components/AuthenticationHandler'
import { MantineProvider } from '@mantine/core';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [accessToken, setAccessToken] = useState()

  useEffect(() => {
    var get_access_token = new URLSearchParams(window.location.hash).get('#access_token');
    console.log("access token", get_access_token)
    setAccessToken(get_access_token)
  }, []);

  return (
    <MantineProvider theme={{ colorScheme: 'dark' }} withGlobalStyles withNormalizeCSS>
      {authenticated ?
        <MainScreenHandler/>
      :
        <AuthenticationHandler accessToken={accessToken} />
      }
    </MantineProvider>

  );
}

export default App;
