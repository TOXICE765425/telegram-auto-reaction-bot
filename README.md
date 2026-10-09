# Telegram Auto Reaction Bot — Vercel

GitHub-ready, webhook-based Telegram bot for Vercel.

## Features

- Random ❤️ 🔥 👍 😍 reaction
- Private chat messages (including `/start`)
- Group and supergroup messages
- Channel posts
- Five rotating welcome videos from direct MP4 URLs
- Welcome name + bot description
- Add to Group/Channel button
- Language selector
- Indian + international languages
- Admin `/broadcast message`
- Admin `/broadcast USER_ID message`
- Admin `/user`
- Persistent user records with Upstash Redis
- Timed intro-video gate; successful unlock lasts 24 hours and is stored in Upstash Redis
- Localized welcome, buttons, status, and gate instructions for all 32 listed languages

## Repository videos

Put your five MP4 files here:

```text
videos/welcome1.mp4
videos/welcome2.mp4
videos/welcome3.mp4
videos/welcome4.mp4
videos/welcome5.mp4
```

Do NOT add `WELCOME_VIDEOS` to Vercel environment variables.

The bot builds the deployed Vercel URL automatically and sends each video in rotation.

## Environment Variables

Only these are needed:

```text
BOT_TOKEN=your_bot_token
ADMIN_ID=your_numeric_telegram_id
BOT_USERNAME=your_bot_username
UPSTASH_REDIS_REST_URL=your_upstash_rest_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_rest_token
```

`BOT_USERNAME` is optional; the bot can call `getMe` if it is empty.

## Important: video size

GitHub/Vercel is not intended for large video hosting. Keep the five repository videos small enough for your deployment limits. If the videos are large, use a CDN/object-storage host instead.

## Deploy

1. Upload this repository to GitHub.
2. Import the repository into Vercel.
3. Add the environment variables.
4. Deploy.
5. Make sure the five files exist under `/videos/`.
6. Set the Telegram webhook.

Example webhook:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR-PROJECT.vercel.app/api&allowed_updates=["message","callback_query","channel_post"]
```

Check it:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

## Private-chat reactions

The bot also attempts to react to messages in the user's private chat, including the `/start` message. If Telegram rejects a particular reaction or the chat/message type does not allow it, the bot silently continues and still sends the normal reply.

## Telegram permissions

Add the bot to the target group/channel and give it the Telegram permissions required for reactions.

A bot cannot read a user's personal list of every group/channel they belong to. The Add button opens Telegram's add flow; it cannot enumerate the user's account.

## Admin commands

```text
/broadcast Hello everyone
/broadcast 123456789 Hello this is a direct message
/user
```

## Security

Never upload `BOT_TOKEN`, `UPSTASH_REDIS_REST_TOKEN`, or other secrets to GitHub.


## Intro video gate (56 seconds)

In `api/index.py`, set `START_GATE_VIDEO_URL` to your direct MP4 URL. This video is sent first when a user sends `/start`; the regular rotating 5-video welcome and existing bot features remain after the Continue button is unlocked. `START_GATE_SECONDS = 56` controls the wait duration.

**Telegram limitation:** the bot cannot verify actual video playback or automatically detect when a user finishes watching. The button is time-gated: clicking before 56 seconds shows a locked notice; after 56 seconds, clicking Continue opens the welcome menu. A user could wait without watching.


## Intro-video gate

The bot sends `START_GATE_VIDEO_URL` on `/start` when the user's unlock has expired.
The Continue button becomes available after `START_GATE_SECONDS` (currently 65).
After Continue succeeds, the user can skip the gate for 24 hours. The expiry is
stored in Upstash Redis, so it survives Vercel redeploys. Configure both
`UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` for persistent behavior.

Telegram does not provide a reliable signal that a user actually watched a video;
this gate checks elapsed time, not playback progress.


## Language files

Translations are stored separately in `api/languages/`, one JSON file per language code (for example `en.json`, `hi.json`, `bn.json`). To edit a translation, update the matching JSON file and redeploy. Each file includes every supported text key; keys not yet translated use English fallback text.
