import React from 'react'
import { Container } from '@mantine/core';
import { Avatar } from '@mantine/core';
import { Center } from '@mantine/core';

const AvatarSelection = (props) => {
  var tmp = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
  return (
    <div className="bg-neutral-600 overflow-x-auto" >

    <Container className="pt-2 ">
      <Center>
        {tmp.map((object, i) =>
          <Avatar size="xl" radius="xl" className="pl-1 pr-1" />
        )}
      </Center>
    </Container>

    </div>
  )
}

export default AvatarSelection
