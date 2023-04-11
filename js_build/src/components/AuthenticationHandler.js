import React, { useState } from 'react';
import { Stack, Button } from '@mantine/core';
import TokenRequest from './TokenRequest'
import AuthenticateButton from './AuthenticateButton'

async function getWebAccessToken (spDcCookie) {
  const res = await fetch('https://open.spotify.com/get_access_token?reason=transport&productType=web_player', {
    headers: {

      Cookie: `sp_dc=AQA8IOxL3CtidbX_hOykrNsKlfACXBA8O2Xs72rBX6zZP6l6rR6MhfCgV5H63qC9WBqPdJ1qF0t3nZHoYHneAuwZWH0kwHEqO0nVNq_VpJFBd_DlCTQOQA22OjRlb3oxmA3NtaIYpgvxZsaMGExMfllv6NXK0h8`
    }
  })
  return res.json()

}

const AuthenticationHandler = ({accessToken}) => {
  // var SpotifyWebApi = require('spotify-web-api-node');

  const [sp_Dc, set_sp_Dc] = useState()


  function getFriendsList(){
    getWebAccessToken(sp_Dc).then((res) => {
      console.log(res)
    })
  }

  var authenticated = false
  if (accessToken === null ){
    authenticated = false
  }
  else{
    authenticated = true
  }

  return (
    <Stack>
      <AuthenticateButton authenticated={authenticated} />

      <TokenRequest sp_Dc={sp_Dc} set_sp_Dc={set_sp_Dc} getFriendsList={getFriendsList}/>
      <Button variant="outline">1</Button>
      <Button variant="outline">2</Button>
      <Button variant="outline">3</Button>
    </Stack>
  )
}

export default AuthenticationHandler
