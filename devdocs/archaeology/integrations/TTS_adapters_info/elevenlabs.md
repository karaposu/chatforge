Introduction

Copy page

Explore the ElevenLabs API reference with comprehensive guides, code examples, and endpoint documentation
Installation
You can interact with the API through HTTP or Websocket requests from any language, via our official Python bindings or our official Node.js libraries.

To install the official Python bindings, run the following command:

pip install elevenlabs


To install the official Node.js library, run the following command in your Node.js project directory:

npm install @elevenlabs/elevenlabs-js


Tracking generation costs
Access response headers to retrieve generation metadata including character costs.


Python

JavaScript


from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key="your_api_key")
# Get raw response with headers
response = client.text_to_speech.with_raw_response.convert(
    text="Hello, world!",
    voice_id="voice_id"
)
# Access character cost from headers
char_cost = response.headers.get("x-character-count")
request_id = response.headers.get("request-id")
audio_data = response.data
The raw response provides access to:

Response data - The actual API response content
HTTP headers - Metadata including character costs and request IDs

API Authentication

Copy page

Learn how to authenticate your ElevenLabs API requests
API Keys
The ElevenLabs API uses API keys for authentication. Every request to the API must include your API key, used to authenticate your requests and track usage quota.

Each API key can be scoped to one of the following:

Scope restriction: Set access restrictions by limiting which API endpoints the key can access.
Credit quota: Define custom credit limits to control usage.
Remember that your API key is a secret. Do not share it with others or expose it in any client-side code (browsers, apps).

All API requests should include your API key in an xi-api-key HTTP header as follows:

xi-api-key: ELEVENLABS_API_KEY


Making requests
You can paste the command below into your terminal to run your first API request. Make sure to replace $ELEVENLABS_API_KEY with your secret API key.

curl 'https://api.elevenlabs.io/v1/models' \
  -H 'Content-Type: application/json' \
  -H 'xi-api-key: $ELEVENLABS_API_KEY'


Example with the elevenlabs Python package:

from elevenlabs.client import ElevenLabs
elevenlabs = ElevenLabs(
  api_key='YOUR_API_KEY',
)


Example with the elevenlabs Node.js package:

import { ElevenLabsClient } from '@elevenlabs/elevenlabs-js';
const elevenlabs = new ElevenLabsClient({
  apiKey: 'YOUR_API_KEY',
});


Single use tokens
For certain endpoints, you can use single use tokens to authenticate your requests. These tokens are valid for a limited time and can be used to connect to the API without exposing your API key, for example from the client side.

See the Single use tokens documentation for more information.


Streaming

Copy page

Learn how to stream real-time audio from the ElevenLabs API using chunked transfer encoding

The ElevenLabs API supports real-time audio streaming for select endpoints, returning raw audio bytes (e.g., MP3 data) directly over HTTP using chunked transfer encoding. This allows clients to process or play audio incrementally as it is generated.

Our official Node and Python libraries include utilities to simplify handling this continuous audio stream.

Streaming is supported for the Text to Speech API, Voice Changer API & Audio Isolation API. This section focuses on how streaming works for requests made to the Text to Speech API.

In Python, a streaming request looks like:

from elevenlabs import stream
from elevenlabs.client import ElevenLabs
elevenlabs = ElevenLabs()
audio_stream = elevenlabs.text_to_speech.stream(
    text="This is a test",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2"
)
# option 1: play the streamed audio locally
stream(audio_stream)
# option 2: process the audio bytes manually
for chunk in audio_stream:
    if isinstance(chunk, bytes):
        print(chunk)


In Node / Typescript, a streaming request looks like:

import { ElevenLabsClient, stream } from '@elevenlabs/elevenlabs-js';
import { Readable } from 'stream';
const elevenlabs = new ElevenLabsClient();
async function main() {
  const audioStream = await elevenlabs.textToSpeech.stream('JBFqnCBsd6RMkjVDRZzb', {
    text: 'This is a test',
    modelId: 'eleven_multilingual_v2',
  });
  // option 1: play the streamed audio locally
  await stream(Readable.from(audioStream));
  // option 2: process the audio manually
  for await (const chunk of audioStream) {
    console.log(chunk);
  }
}
main();


Creative Platform
Text to Speech
WebSocket

Copy page

WSS

wss://api.elevenlabs.io
/v1/text-to-speech/:voice_id/stream-input
Handshake
URL	wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input
Method	GET
Status	101 Switching Protocols
Try it
Messages

{ "text": " ", "voice_settings": { "speed": 1, "stability": 0.5, "similarity_boost": 0.8 }, "xi_api_key": "<YOUR_API_KEY>" }
publish


{ "text": "Hello World ", "try_trigger_generation": true }
publish


{ "text": "" }
publish


{ "audio": "Y3VyaW91cyBtaW5kcyB0aGluayBhbGlrZSA6KQ==", "isFinal": false, "normalizedAlignment": { "charStartTimesMs": [ 0, 3, 7, 9, 11, 12, 13, 15, 17, 19, 21 ], "charDurationsMs": [ 3, 4, 2, 2, 1, 1, 2, 2, 2, 2, 3 ], "chars": [ "H", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d" ] }, "alignment": { "charStartTimesMs": [ 0, 3, 7, 9, 11, 12, 13, 15, 17, 19, 21 ], "charDurationsMs": [ 3, 4, 2, 2, 1, 1, 2, 2, 2, 2, 3 ], "chars": [ "H", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d" ] } }
subscribe

The Text-to-Speech WebSockets API is designed to generate audio from partial text input while ensuring consistency throughout the generated audio. Although highly flexible, the WebSockets API isn’t a one-size-fits-all solution. It’s well-suited for scenarios where:

The input text is being streamed or generated in chunks.
Word-to-audio alignment information is required.
However, it may not be the best choice when:

The entire input text is available upfront. Given that the generations are partial, some buffering is involved, which could potentially result in slightly higher latency compared to a standard HTTP request.
You want to quickly experiment or prototype. Working with WebSockets can be harder and more complex than using a standard HTTP API, which might slow down rapid development and testing.
Handshake
WSS

wss://api.elevenlabs.io
/v1/text-to-speech/:voice_id/stream-input

Headers
xi-api-key
string
Required
Path parameters
voice_id
string
Required
The unique identifier for the voice to use in the TTS process.
Query parameters
authorization
string
Optional
Your authorization bearer token.
model_id
string
Optional
The model ID to use.
language_code
string
Optional
The ISO 639-1 language code (for specific models).

enable_logging
boolean
Optional
Defaults to true
Whether to enable logging of the request.
enable_ssml_parsing
boolean
Optional
Defaults to false
Whether to enable SSML parsing.
output_format
enum
Optional
The output audio format

Show 18 enum values
inactivity_timeout
integer
Optional
Defaults to 20
Timeout for inactivity before a context is closed (seconds), can be up to 180 seconds.

sync_alignment
boolean
Optional
Defaults to false
Whether to include timing data with every audio chunk.
auto_mode
boolean
Optional
Defaults to false
Reduces latency by disabling chunk schedule and buffers. Recommended for full sentences/phrases.

apply_text_normalization
enum
Optional
Defaults to auto
This parameter controls text normalization with three modes - ‘auto’, ‘on’, and ‘off’. When set to ‘auto’, the system will automatically decide whether to apply text normalization (e.g., spelling out numbers). With ‘on’, text normalization will always be applied, while with ‘off’, it will be skipped. For ‘eleven_turbo_v2_5’ and ‘eleven_flash_v2_5’ models, text normalization can only be enabled with Enterprise plans. Defaults to ‘auto’.

Allowed values:
auto
on
off
seed
integer
Optional
0-4294967295
If specified, system will best-effort sample deterministically. Integer between 0 and 4294967295.

Send
initializeConnection
object
Required

Show 6 properties
OR
sendText
object
Required

Show 5 properties
OR
closeConnection
object
Required

Show 1 properties





Multi-Context WebSocket


Copy page

WSS

wss://api.elevenlabs.io
/v1/text-to-speech/:voice_id/multi-stream-input
Handshake
URL	wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/multi-stream-input
Method	GET
Status	101 Switching Protocols
Try it
Messages

{ "text": " ", "voice_settings": { "stability": 0.5, "similarity_boost": 0.8 }, "context_id": "conv_1" }
publish


{ "text": "Hello from conversation one. ", "context_id": "conv_1" }
publish


{ "text": "This is added to the buffer of text to flush. ", "context_id": "conv_1", "flush": true }
publish


{ "audio": "Y3VyaW91cyBtaW5kcyB0aGluayBhbGlrZSA6KQ==", "is_final": false, "normalizedAlignment": { "charStartTimesMs": [ 0, 3, 7, 9, 11, 12, 13, 15, 17, 19, 21 ], "charDurationsMs": [ 3, 4, 2, 2, 1, 1, 2, 2, 2, 2, 3 ], "chars": [ "H", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d" ] }, "alignment": { "charStartTimesMs": [ 0, 3, 7, 9, 11, 12, 13, 15, 17, 19, 21 ], "charDurationsMs": [ 3, 4, 2, 2, 1, 1, 2, 2, 2, 2, 3 ], "chars": [ "H", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d" ] }, "contextId": "conv_1" }
subscribe


{ "text": "Hi this is a new context with different settings! ", "context_id": "interruption_context", "voice_settings": { "stability": 0.2, "similarity_boost": 0.9 } }
publish


{ "context_id": "conv_1", "close_context": true }
publish


{ "context_id": "interruption_context", "flush": true }
publish


{ "audio": "Y3VyaW91cyBtaW5kcyB0aGluayBhbGlrZSA6KQ==", "is_final": false, "contextId": "interruption_context" }
subscribe


{ "is_final": true, "contextId": "interruption_context" }
subscribe


{ "context_id": "interruption_context", "text": "" }
publish


{ "close_socket": true }
publish

The Multi-Context Text-to-Speech WebSockets API allows for generating audio from text input while managing multiple independent audio generation streams (contexts) over a single WebSocket connection. This is useful for scenarios requiring concurrent or interleaved audio generations, such as dynamic conversational AI applications.

Each context, identified by a context id, maintains its own state. You can send text to specific contexts, flush them, or close them independently. A close_socket message can be used to terminate the entire connection gracefully.

For more information on best practices for how to use this API, please see the multi context websocket guide.

Handshake
WSS

wss://api.elevenlabs.io
/v1/text-to-speech/:voice_id/multi-stream-input

Headers
xi-api-key
string
Required
Path parameters
voice_id
string
Required
The unique identifier for the voice to use in the TTS process.
Query parameters
authorization
string
Optional
Your authorization bearer token.
model_id
string
Optional
The model ID to use.
language_code
string
Optional
The ISO 639-1 language code (for specific models).

enable_logging
boolean
Optional
Defaults to true
Whether to enable logging of the request.
enable_ssml_parsing
boolean
Optional
Defaults to false
Whether to enable SSML parsing.
output_format
enum
Optional
The output audio format

Show 18 enum values
inactivity_timeout
integer
Optional
Defaults to 20
Timeout for inactivity before a context is closed (seconds), can be up to 180 seconds.

sync_alignment
boolean
Optional
Defaults to false
Whether to include timing data with every audio chunk.
auto_mode
boolean
Optional
Defaults to false
Reduces latency by disabling chunk schedule and buffers. Recommended for full sentences/phrases.

apply_text_normalization
enum
Optional
Defaults to auto
This parameter controls text normalization with three modes - ‘auto’, ‘on’, and ‘off’. When set to ‘auto’, the system will automatically decide whether to apply text normalization (e.g., spelling out numbers). With ‘on’, text normalization will always be applied, while with ‘off’, it will be skipped. For ‘eleven_turbo_v2_5’ and ‘eleven_flash_v2_5’ models, text normalization can only be enabled with Enterprise plans. Defaults to ‘auto’.

Allowed values:
auto
on
off
seed
integer
Optional
0-4294967295
If specified, system will best-effort sample deterministically. Integer between 0 and 4294967295.

Send
initializeConnectionMulti
object
Required

Show 7 properties
OR
initialiseContext
object
Required

Show 7 properties
OR
sendTextMulti
object
Required

Show 3 properties
OR
flushContextClient
object
Required

Show 3 properties
OR
closeContextClient
object
Required

Show 2 properties
OR
closeSocketClient
object
Required

Show 1 properties
OR
keepContextAlive
object
Required

Show 2 properties
Receive
audioOutputMulti
object
Required

Show 4 properties
OR
finalOutputMulti
object
Required




Text to Speech

Copy page

Learn how to turn text into lifelike spoken audio with ElevenLabs.
Overview
ElevenLabs Text to Speech (TTS) API turns text into lifelike audio with nuanced intonation, pacing and emotional awareness. Our models adapt to textual cues across 32 languages and multiple voice styles and can be used to:

Narrate global media campaigns & ads
Produce audiobooks in multiple languages with complex emotional delivery
Stream real-time audio from text



Get started
Developer quickstart

Copy page

Learn how to make your first ElevenLabs API request.
The ElevenLabs API provides a simple interface to state-of-the-art audio models and features. Follow this guide to learn how to create lifelike speech with our Text to Speech API. See the developer guides for more examples with our other products.

Using the Text to Speech API
1
Create an API key
Create an API key in the dashboard here, which you’ll use to securely access the API.

Store the key as a managed secret and pass it to the SDKs either as a environment variable via an .env file, or directly in your app’s configuration depending on your preference.

.env


ELEVENLABS_API_KEY=<your_api_key_here>
2
Install the SDK
We’ll also use the dotenv library to load our API key from an environment variable.


Python

TypeScript


pip install elevenlabs
pip install python-dotenv
To play the audio through your speakers, you may be prompted to install MPV and/or ffmpeg.

3
Make your first request
Create a new file named example.py or example.mts, depending on your language of choice and add the following code:


Python

TypeScript


from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
load_dotenv()
elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)
audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)
play(audio)
4
Run the code

Python

TypeScript


python example.py
You should hear the audio play through your speakers.

Eleven v3 (alpha)
This model is currently in alpha and is subject to change. Eleven v3 is not made for real-time applications like Agents Platform. When integrating Eleven v3 into your application, consider generating several generations and allowing the user to select the best one.

Eleven v3 is our latest and most advanced speech synthesis model. It is a state-of-the-art model that produces natural, life-like speech with high emotional range and contextual understanding across multiple languages.

This model works well in the following scenarios:

Character Discussions: Excellent for audio experiences with multiple characters that interact with each other.
Audiobook Production: Perfect for long-form narration with complex emotional delivery.
Emotional Dialogue: Generate natural, lifelike dialogue with high emotional range and contextual understanding.
With Eleven v3 comes a new Text to Dialogue API, which allows you to generate natural, lifelike dialogue with high emotional range and contextual understanding across multiple languages. Eleven v3 can also be used with the Text to Speech API to generate natural, lifelike speech with high emotional range and contextual understanding across multiple languages.

Read more about the Text to Dialogue API here.

Supported languages
The Eleven v3 model supports 70+ languages, including:

Afrikaans (afr), Arabic (ara), Armenian (hye), Assamese (asm), Azerbaijani (aze), Belarusian (bel), Bengali (ben), Bosnian (bos), Bulgarian (bul), Catalan (cat), Cebuano (ceb), Chichewa (nya), Croatian (hrv), Czech (ces), Danish (dan), Dutch (nld), English (eng), Estonian (est), Filipino (fil), Finnish (fin), French (fra), Galician (glg), Georgian (kat), German (deu), Greek (ell), Gujarati (guj), Hausa (hau), Hebrew (heb), Hindi (hin), Hungarian (hun), Icelandic (isl), Indonesian (ind), Irish (gle), Italian (ita), Japanese (jpn), Javanese (jav), Kannada (kan), Kazakh (kaz), Kirghiz (kir), Korean (kor), Latvian (lav), Lingala (lin), Lithuanian (lit), Luxembourgish (ltz), Macedonian (mkd), Malay (msa), Malayalam (mal), Mandarin Chinese (cmn), Marathi (mar), Nepali (nep), Norwegian (nor), Pashto (pus), Persian (fas), Polish (pol), Portuguese (por), Punjabi (pan), Romanian (ron), Russian (rus), Serbian (srp), Sindhi (snd), Slovak (slk), Slovenian (slv), Somali (som), Spanish (spa), Swahili (swa), Swedish (swe), Tamil (tam), Telugu (tel), Thai (tha), Turkish (tur), Ukrainian (ukr), Urdu (urd), Vietnamese (vie), Welsh (cym).

Multilingual v2
Eleven Multilingual v2 is our most advanced, emotionally-aware speech synthesis model. It produces natural, lifelike speech with high emotional range and contextual understanding across multiple languages.

The model delivers consistent voice quality and personality across all supported languages while maintaining the speaker’s unique characteristics and accent.

This model excels in scenarios requiring high-quality, emotionally nuanced speech:

Character Voiceovers: Ideal for gaming and animation due to its emotional range.
Professional Content: Well-suited for corporate videos and e-learning materials.
Multilingual Projects: Maintains consistent voice quality across language switches.
Stable Quality: Produces consistent, high-quality audio output.
While it has a higher latency & cost per character than Flash models, it delivers superior quality for projects where lifelike speech is important.

Our multilingual v2 models support 29 languages:

English (USA, UK, Australia, Canada), Japanese, Chinese, German, Hindi, French (France, Canada), Korean, Portuguese (Brazil, Portugal), Italian, Spanish (Spain, Mexico), Indonesian, Dutch, Turkish, Filipino, Polish, Swedish, Bulgarian, Romanian, Arabic (Saudi Arabia, UAE), Czech, Greek, Finnish, Croatian, Malay, Slovak, Danish, Tamil, Ukrainian & Russian.

Flash v2.5
Eleven Flash v2.5 is our fastest speech synthesis model, designed for real-time applications and Agents Platform. It delivers high-quality speech with ultra-low latency (~75ms†) across 32 languages.

The model balances speed and quality, making it ideal for interactive applications while maintaining natural-sounding output and consistent voice characteristics across languages.

This model is particularly well-suited for:

Agents Platform: Perfect for real-time voice agents and chatbots.
Interactive Applications: Ideal for games and applications requiring immediate response.
Large-Scale Processing: Efficient for bulk text-to-speech conversion.
With its lower price point and 75ms latency, Flash v2.5 is the cost-effective option for anyone needing fast, reliable speech synthesis across multiple languages.

Flash v2.5 supports 32 languages - all languages from v2 models plus:

Hungarian, Norwegian & Vietnamese

† Excluding application & network latency


Turbo v2.5
Eleven Turbo v2.5 is our high-quality, low-latency model with a good balance of quality and speed.

This model is an ideal choice for all scenarios where you’d use Flash v2.5, but where you’re willing to trade off latency for higher quality voice generation.


Character limits
The maximum number of characters supported in a single text-to-speech request varies by model.

Model ID	Character limit	Approximate audio duration
eleven_v3	5,000	~5 minutes
eleven_flash_v2_5	40,000	~40 minutes
eleven_flash_v2	30,000	~30 minutes
eleven_turbo_v2_5	40,000	~40 minutes
eleven_turbo_v2	30,000	~30 minutes
eleven_multilingual_v2	10,000	~10 minutes
eleven_multilingual_v1	10,000	~10 minutes
eleven_english_sts_v2	10,000	~10 minutes
eleven_english_sts_v1	10,000	~10 minutes



Scribe v1
Scribe v1 is our state-of-the-art speech recognition model designed for accurate transcription across 99 languages. It provides precise word-level timestamps and advanced features like speaker diarization and dynamic audio tagging.

This model excels in scenarios requiring accurate speech-to-text conversion:

Transcription Services: Perfect for converting audio/video content to text
Meeting Documentation: Ideal for capturing and documenting conversations
Content Analysis: Well-suited for audio content processing and analysis
Multilingual Recognition: Supports accurate transcription across 99 languages
Key features:

Accurate transcription with word-level timestamps
Speaker diarization for multi-speaker audio
Dynamic audio tagging for enhanced context
Support for 99 languages
Read more about Scribe v1 here.

Scribe v2 Realtime
Scribe v2 Realtime, our fastest and most accurate live speech recognition model, delivers state-of-the-art accuracy in over 90 languages with an ultra-low 150ms of latency.

This model excels in conversational use cases:

Live meeting transcription: Perfect for realtime transcription
AI Agents: Ideal for live conversations
Multilingual Recognition: Supports accurate transcription across 99 languages with automatic language recognition
Key features:

Ultra-low latency: Get partial transcriptions in ~150 milliseconds
Streaming support: Send audio in chunks while receiving transcripts in real-time
Multiple audio formats: Support for PCM (8kHz to 48kHz) and μ-law encoding
Voice Activity Detection (VAD): Automatic speech segmentation based on silence detection
Manual commit control: Full control over when to finalize transcript segments
Read more about Scribe v2 Realtime here.


