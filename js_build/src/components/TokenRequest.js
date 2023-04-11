import React from 'react';
import { TextInput, Container, Button } from '@mantine/core';

const TokenRequest = ({sp_Dc, set_sp_Dc, getFriendsList}) => {

  return (
    <Container className="mt-10 w-screen rounded-md border-solid border-2 border-sky-500">
    <TextInput
      className="pt-10 pl-10 pr-10"
      placeholder="Enter your sp_Dc cookie"
      label="sp_Dc Cookie"
      value={sp_Dc}
      onChange={(event) => set_sp_Dc(event.currentTarget.value)}
    />
    <Button
      variant="outline" className="ml-10 mt-2 mb-10"
      onClick={getFriendsList}
    >
      Get Friends List
    </Button>
    </Container>
  )
}

export default TokenRequest
