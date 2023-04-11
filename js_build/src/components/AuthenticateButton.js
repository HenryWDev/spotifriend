import React from 'react'
import { Button } from '@mantine/core';

const AuthenticateButton = ({authenticated}) => {
  var clientId = '9b5e5952eb0e4c7bb4c35e3d89e28466'
  var redirectUri = 'http://localhost:3000/'
  var scope = 'user-modify-playback-state'
  var url = 'https://accounts.spotify.com/authorize';
  url += '?response_type=token';
  url += '&client_id=' + encodeURIComponent(clientId);
  url += '&scope=' + encodeURIComponent(scope);
  url += '&redirect_uri=' + encodeURIComponent(redirectUri);

  return (
    <>
    {authenticated ?

      <Button
        component="a"
        target="_blank"
        rel="noopener noreferrer"
        disabled
        variant="outline" className="mt-10" href={url}>
        Authenticated!
      </Button>

      :

      <Button
        component="a"
        target="_blank"
        rel="noopener noreferrer"
        variant="outline" className="mt-10" href={url}>
        Authenticateee
      </Button>
    }
    </>
  )
}

export default AuthenticateButton
