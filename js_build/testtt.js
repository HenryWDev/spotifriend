// must be node-fetch@2.6.6, or at least not the most recent
const fetch = require('node-fetch')


async function main () {
  let spDcCookie = ""

  const { accessToken } = await getWebAccessToken(spDcCookie)
  console.log(accessToken)
  const friendActivity = await getFriendActivity(accessToken)

  // console.log(JSON.stringify(friendActivity, null, 2))
}

main()


async function getWebAccessToken (spDcCookie) {
  const res = await fetch('https://open.spotify.com/get_access_token?reason=transport&productType=web_player', {
    headers: {
      Cookie: `sp_dc=${spDcCookie}`
    }
  })
  return res.json()
}

async function getFriendActivity (webAccessToken) {
  // Looks like the app now uses `https://spclient.wg.spotify.com/presence-view/v1/buddylist`
  // but both endpoints appear to be identical in the kind of token they accept
  // and the response format.
  console.log(webAccessToken)
  const res = await
    fetch('https://spclient.wg.spotify.com/user-profile-view/v3/profile/sws2obne5rwglf9x7podxy3nb/following', {
    headers: {
      Authorization: `Bearer ${webAccessToken}`
    }
  })

  return res.json()
}
