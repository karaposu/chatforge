Text-to-Speech AI
Convert text into natural-sounding speech using an API powered by the best of Google’s AI technologies.

New customers get up to $300 in free credits to try Text-to-Speech and other Google Cloud products.

Improve customer interactions with intelligent, lifelike responses

Engage users with voice user interface in your devices and applications

Personalize your communication based on user preference of voice and language

https://texttospeech.googleapis.com/v1beta1/text:synthesize

{
  "audioConfig": {
    "audioEncoding": "LINEAR16",
    "pitch": 0,
    "speakingRate": 1
  },
  "input": {
    "prompt": "Read aloud in a warm, welcoming tone.",
    "text": "Movies, oh my gosh, I just just absolutely love them. They're like time machines taking you to different worlds and landscapes, and um, and I just can't get enough of it."
  },
  "voice": {
    "languageCode": "en-us",
    "modelName": "gemini-2.5-flash-lite-preview-tts",
    "name": "Achernar"
  }
}



Streaming audio synthesis	
Power your AI agents with ultra-low-latency speech for seamless, real-time conversations with streaming audio synthesis.

Long audio synthesis	
Asynchronously synthesize up to 1 million bytes of input with long audio synthesis.

Voice and language selection	
Choose from an extensive selection of 380+ voices across 75+ languages and variants, with more to come soon.

Text and SSML support	
Customize your speech with SSML tags that allow you to add pauses, numbers, date and time formatting, and other pronunciation instructions.

Pitch tuning	
Personalize the pitch of your selected voice, up to 20 semitones more or less than the default.

Speaking rate tuning	
Adjust your speaking rate to be 4x faster or slower than the normal rate.

Volume gain control	
Increase the volume of the output by up to 16 db or decrease the volume up to -96 db.

Integrated REST and gRPC APIs	
Easily integrate with any application or device that can send a REST or gRPC request including phones, PCs, tablets, and IoT devices (for example cars, TVs, speakers).

Audio format flexibility	
Convert text to MP3, Linear16, OGG Opus, and a number of other audio formats.

Audio profiles	
Optimize for the type of speaker from which your speech is intended to play, such as headphones or phone lines.



Create audio from text by using client libraries

bookmark_border
This quickstart walks you through the process of using client libraries to make a request to Cloud TTS, creating audio from text.

To learn more about the fundamental concepts in Cloud Text-to-Speech, read Cloud Text-to-Speech Basics. To see which synthetic voices are available for your language, see the supported voices and languages page.

Before you begin
Before you can send a request to the Cloud Text-to-Speech API, you must have completed the following actions. See the before you begin page for details.

Enable Cloud Text-to-Speech on a Google Cloud project.
Make sure billing is enabled for Cloud Text-to-Speech.
Install the Google Cloud CLI. After installation, initialize the Google Cloud CLI by running the following command:



gcloud init
If you're using an external identity provider (IdP), you must first sign in to the gcloud CLI with your federated identity.

If you're using a local shell, then create local authentication credentials for your user account:



gcloud auth application-default login
You don't need to do this if you're using Cloud Shell.

If an authentication error is returned, and you are using an external identity provider (IdP), confirm that you have signed in to the gcloud CLI with your federated identity.

Before installing the library, make sure you've prepared your environment for Python development.



pip install --upgrade google-cloud-texttospeech

Create audio data
Now you can use Cloud TTS to create an audio file of synthetic human speech. Use the following code to send a synthesize request to the Cloud Text-to-Speech API.

Before running the example, make sure you've prepared your environment for Python development.




"""Synthesizes speech from the input string of text or ssml.
Make sure to be working in a virtual environment.

Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""
from google.cloud import texttospeech

# Instantiates a client
client = texttospeech.TextToSpeechClient()

# Set the text input to be synthesized
synthesis_input = texttospeech.SynthesisInput(text="Hello, World!")

# Build the voice request, select the language code ("en-US") and the ssml
# voice gender ("neutral")
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

# Select the type of audio file you want returned
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

# Perform the text-to-speech request on the text input with the selected
# voice parameters and audio file type
response = client.synthesize_speech(
    input=synthesis_input, voice=voice, audio_config=audio_config
)

# The response's audio_content is binary.
with open("output.mp3", "wb") as out:
    # Write the response to the output file.
    out.write(response.audio_content)
    print('Audio content written to file "output.mp3"')



models

Gemini-TTS is the latest evolution of our Cloud TTS technology that moves beyond natural-sounding speech and provides granular control over generated audio using text-based prompts. Using Gemini-TTS, you can synthesize single or multi-speaker speech from short snippets to long-form narratives, precisely dictating style, accent, pace, tone, and even emotional expression, all steerable through natural-language prompts.


Gemini 2.5 Flash TTS
Gemini 2.5 Flash Lite TTS (Preview)
Gemini 2.5 Pro TTS
Model ID	gemini-2.5-flash-tts
Optimized for	Low latency, controllable, single- and multi-speaker Cloud TTS audio generation for cost-efficient everyday applications
Input and output modalities	
Input: Text
Output: Audio
Speaker number support	Single, multi-speaker
Supported output audio formats	
Unary: LINEAR16 (default), ALAW, MULAW, MP3, OGG_OPUS, PCM
Streaming: PCM (default), ALAW, MULAW, OGG_OPUS


model: "gemini-2.5-flash-tts"
prompt: "Say the following"
text: "[extremely fast] Availability and terms may vary.
       Check our website or your local store for complete
       details and restrictions."
speaker: "Kore"
            

     Model ID	gemini-2.5-flash-lite-preview-tts
Optimized for	Low latency, controllable, single-speaker Cloud TTS audio generation for cost-efficient everyday applications. Note that this model is in Preview.
Input and output modalities	
Input: Text
Output: Audio
Speaker number support	Single
Supported output audio formats	
Unary: LINEAR16 (default), ALAW, MULAW, MP3, OGG_OPUS, PCM
Streaming: PCM (default), ALAW, MULAW, OGG_OPUS

model: "gemini-2.5-flash-lite-preview-tts"
prompt: "Say the following in an elated way"
text: "Congratulations on the recent achievements!"
speaker: "Aoede"


Model ID	gemini-2.5-pro-tts
Optimized for	High control for structured workflows like podcast generation, audiobooks, customer support, and more
Input and output modalities	
Input: Text
Output: Audio
Speaker number support	Single, multi-speaker
Supported output audio formats	
Unary: LINEAR16 (default), ALAW, MULAW, MP3, OGG_OPUS, PCM
Streaming: PCM (default), ALAW, MULAW, OGG_OPUS


model: "gemini-2.5-pro-tts"
prompt: "You are having a casual conversation with a friend.
         Say the following in a friendly and amused way."
text: "hahah I did NOT expect that. Can you believe it!."
speaker: "Callirrhoe"



Additional controls
Additional controls and capabilities include the following:

Natural conversation: Voice interactions of remarkable quality, more appropriate expressivity, and patterns of rhythm are delivered with very low latency so you can converse fluidly.

Style control: Using natural language prompts, you can adapt the delivery within the conversation by steering it to adopt specific accents and produce a range of tones and expressions including a whisper.

Dynamic performance: These models can bring text to life for expressive readings of poetry, newscasts, and engaging storytelling. They can also perform with specific emotions and produce accents when requested.

Enhanced pace and pronunciation control: Controlling delivery speed helps to ensure more accuracy in pronunciation including specific words.



Voice options
Gemini-TTS offers a wide range of voice options similar to our existing Chirp 3: HD Voices, each with distinct characteristics:



Name	Gender	Demo
Achernar	Female	
Achird	Male	
Algenib	Male	
Algieba	Male	
Alnilam	Male	
Aoede	Female	
Autonoe	Female	
Callirrhoe	Female	
Charon	Male	
Despina	Female	
Enceladus	Male	
Erinome	Female	
Fenrir	Male	
Gacrux	Female	
Iapetus	Male	
Kore	Female	
Laomedeia	Female	
Leda	Female	
Orus	Male	
Pulcherrima	Female	
Puck	Male	
Rasalgethi	Male	
Sadachbia	Male	
Sadaltager	Male	
Schedar	Male	
Sulafat	Female	
Umbriel	Male	
Vindemiatrix	Female	
Zephyr	Female	
Zubenelgenubi	Male	



Gemini-TTS supports the following languages:


Language	BCP-47 code	Launch readiness
Arabic (Egypt)	ar-EG	GA
Bangla (Bangladesh)	bn-BD	GA
Dutch (Netherlands)	nl-NL	GA
English (India)	en-IN	GA
English (United States)	en-US	GA
French (France)	fr-FR	GA
German (Germany)	de-DE	GA
Hindi (India)	hi-IN	GA
Indonesian (Indonesia)	id-ID	GA
Italian (Italy)	it-IT	GA
Japanese (Japan)	ja-JP	GA
Korean (South Korea)	ko-KR	GA
Marathi (India)	mr-IN	GA
Polish (Poland)	pl-PL	GA
Portuguese (Brazil)	pt-BR	GA
Romanian (Romania)	ro-RO	GA
Russian (Russia)	ru-RU	GA
Spanish (Spain)	es-ES	GA
Tamil (India)	ta-IN	GA
Telugu (India)	te-IN	GA
Thai (Thailand)	th-TH	GA
Turkish (Turkey)	tr-TR	GA
Ukrainian (Ukraine)	uk-UA	GA
Vietnamese (Vietnam)	vi-VN	GA
Afrikaans (South Africa)	af-ZA	Preview
Albanian (Albania)	sq-AL	Preview
Amharic (Ethiopia)	am-ET	Preview
Arabic (World)	ar-001	Preview
Armenian (Armenia)	hy-AM	Preview
Azerbaijani (Azerbaijan)	az-AZ	Preview
Basque (Spain)	eu-ES	Preview
Belarusian (Belarus)	be-BY	Preview
Bulgarian (Bulgaria)	bg-BG	Preview
Burmese (Myanmar)	my-MM	Preview
Catalan (Spain)	ca-ES	Preview
Cebuano (Philippines)	ceb-PH	Preview
Chinese, Mandarin (China)	cmn-CN	Preview
Chinese, Mandarin (Taiwan)	cmn-tw	Preview
Croatian (Croatia)	hr-HR	Preview
Czech (Czech Republic)	cs-CZ	Preview
Danish (Denmark)	da-DK	Preview
English (Australia)	en-AU	Preview
English (United Kingdom)	en-GB	Preview
Estonian (Estonia)	et-EE	Preview
Filipino (Philippines)	fil-PH	Preview
Finnish (Finland)	fi-FI	Preview
French (Canada)	fr-CA	Preview
Galician (Spain)	gl-ES	Preview
Georgian (Georgia)	ka-GE	Preview
Greek (Greece)	el-GR	Preview
Gujarati (India)	gu-IN	Preview
Haitian Creole (Haiti)	ht-HT	Preview
Hebrew (Israel)	he-IL	Preview
Hungarian (Hungary)	hu-HU	Preview
Icelandic (Iceland)	is-IS	Preview
Javanese (Java)	jv-JV	Preview
Kannada (India)	kn-IN	Preview
Konkani (India)	kok-IN	Preview
Lao (Laos)	lo-LA	Preview
Latin (Vatican City)	la-VA	Preview
Latvian (Latvia)	lv-LV	Preview
Lithuanian (Lithuania)	lt-LT	Preview
Luxembourgish (Luxembourg)	lb-LU	Preview
Macedonian (North Macedonia)	mk-MK	Preview
Maithili (India)	mai-IN	Preview
Malagasy (Madagascar)	mg-MG	Preview
Malay (Malaysia)	ms-MY	Preview
Malayalam (India)	ml-IN	Preview
Mongolian (Mongolia)	mn-MN	Preview
Nepali (Nepal)	ne-NP	Preview
Norwegian, Bokmål (Norway)	nb-NO	Preview
Norwegian, Nynorsk (Norway)	nn-NO	Preview
Odia (India)	or-IN	Preview
Pashto (Afghanistan)	ps-AF	Preview
Persian (Iran)	fa-IR	Preview
Portuguese (Portugal)	pt-PT	Preview
Punjabi (India)	pa-IN	Preview
Serbian (Serbia)	sr-RS	Preview
Sindhi (India)	sd-IN	Preview
Sinhala (Sri Lanka)	si-LK	Preview
Slovak (Slovakia)	sk-SK	Preview
Slovenian (Slovenia)	sl-SI	Preview
Spanish (Latin America)	es-419	Preview
Spanish (Mexico)	es-MX	Preview
Swahili (Kenya)	sw-KE	Preview
Swedish (Sweden)	sv-SE	Preview
Urdu (Pakistan)	ur-PK	Preview



Available regions
Gemini-TTS is available multiple regions, through Cloud Text-to-Speech API or Vertex AI API.

The ML processing for these models occurs within the specific region or multi-region where the request is made. For more information , see Data residency.

For Cloud Text-to-Speech API, the following regions are supported:

Region	Country or Jurisdiction	Available models
global	Global (Non-DRZ)	gemini-2.5-flash-tts
gemini-2.5-pro-tts
gemini-2.5-flash-lite-preview-tts
us	United States	gemini-2.5-flash-tts
gemini-2.5-pro-tts
gemini-2.5-flash-lite-preview-tts
eu	European Union	gemini-2.5-flash-tts
gemini-2.5-pro-tts
gemini-2.5-flash-lite-preview-tts
northamerica-northeast1	Canada	gemini-2.5-flash-tts
gemini-2.5-flash-lite-preview-tts
These regions can be accessed using the following API endpoints: <REGION>-texttospeech.googleapis.com. Note the global region doesn't have a prefix: texttospeech.googleapis.com.



Use Cloud Text-to-Speech API
Note: The size of the text field and the prompt field individually can be at most 4,000 bytes. While the total size of the prompt and text fields can be up to 8,000 bytes, each field must be a maximum of 4000 bytes. The output audio can at most be around 655 seconds. If the input text amounts to audio longer than this limit, the audio will be truncated.
Optionally specify audio formats and sampling rates in "audioConfig" field if non-default options are needed.

Description	Limit	Type
Text field	Less than or equal to 4,000 bytes.	Input
Prompt field	Less than or equal to 4,000 bytes.	Input
Text and prompt fields	Less than or equal to 8,000 bytes.	Input
Duration for the output audio	Approximately 655 seconds. If the input text results in the audio exceeding 655 seconds, the audio is truncated.	Output


Before you begin
Before you can begin using Cloud Text-to-Speech, you must enable the API in the Google Cloud console by following steps:

Enable Cloud Text-to-Speech on a project.
Make sure billing is enabled for Cloud Text-to-Speech.
Set up authentication for your development environment.
Assign aiplatform.endpoints.predict permission for the authenticated user. This permission can be granted with the roles/aiplatform.user role.
Select the correct API endpoint based on Available regions.



import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
TTS_LOCATION = os.getenv("GOOGLE_CLOUD_REGION")

API_ENDPOINT = (
    f"{TTS_LOCATION}-texttospeech.googleapis.com"
    if TTS_LOCATION != "global"
    else "texttospeech.googleapis.com"
)
client = texttospeech.TextToSpeechClient(
    client_options=ClientOptions(api_endpoint=API_ENDPOINT)
)


# google-cloud-texttospeech minimum version 2.29.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize(prompt: str, text: str, output_filepath: str = "output.mp3"):
    """Synthesizes speech from the input text and saves it to an MP3 file.

    Args:
        prompt: Styling instructions on how to synthesize the content in
          the text field.
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
          Defaults to "output.mp3".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

    # Select the voice you want to use.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="Charon",  # Example voice, adjust as needed
        model_name="gemini-2.5-pro-tts"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type.
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")



Perform streaming single-speaker synthesis
Streaming synthesis is suitable for real-time applications where fast response is critical for the user experience. In streaming connection, the API returns audio as it becomes available in small chunks.

As the caller of the API, make sure to consume the audio chunks, passing them down to your clients as they arrive (for example, using socketio for web apps).

Cloud Text-to-Speech API supports multiple request multiple response type streaming. While it's possible to send the input chunks to the API asynchronously as shown in the request_generator, the API only starts synthesizing when the client sends Half-Close as a signal that it won't send any more data to the API.

The prompt field must be set in the first input chunk, because it's ignored in consecutive chunks.


# google-cloud-texttospeech minimum version 2.29.0 is required.

import datetime
import os
import numpy as np
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize(prompt: str, text_chunks: list[str], model: str, voice: str, locale: str):
    """Synthesizes speech from the input text.

    Args:
        prompt: Styling instructions on how to synthesize the content in
          the text field.
        text_chunks: Text chunks to synthesize. Note that The synthesis will 
          start when the client initiates half-close. 
        model: gemini tts model name. gemini-2.5-flash-tts, gemini-2.5-flash-lite-preview-tts, and gemini-2.5-pro-tts
        voice: voice name. Example: leda, kore. Refer to available voices
        locale: locale name. Example: en-us. Refer to available locales. 
    """
    client = texttospeech.TextToSpeechClient()

    config_request = texttospeech.StreamingSynthesizeRequest(
        streaming_config=texttospeech.StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                name=voice,
                language_code=locale,
                model_name=model
            )
        )
    )

    # Example request generator. A function like this can be linked to an LLM
    # text generator and the text can be passed to the TTS API asynchronously.
    def request_generator():
      yield config_request

      for i, text in enumerate(text_chunks):
        yield texttospeech.StreamingSynthesizeRequest(
            input=texttospeech.StreamingSynthesisInput(
              text=text, 
              # Prompt is only supported in the first input chunk.
              prompt=prompt if i == 0 else None,
            )
        )

    request_start_time = datetime.datetime.now()
    streaming_responses = client.streaming_synthesize(request_generator())

    is_first_chunk_received = False
    final_audio_data = np.array([])
    num_chunks_received = 0
    for response in streaming_responses:
        # just a simple progress indicator
        num_chunks_received += 1
        print(".", end="")
        if num_chunks_received % 40 == 0:
            print("")

        # measuring time to first audio
        if not is_first_chunk_received:
            is_first_chunk_received = True
            first_chunk_received_time = datetime.datetime.now()

        # accumulating audio. In a web-server scenario, you would want to 
        # "emit" audio to the frontend as soon as it arrives.
        #
        # For example using flask socketio, you could do the following
        # from flask_socketio import SocketIO, emit
        # emit("audio", response.audio_content)
        # socketio.sleep(0)
        audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
        final_audio_data = np.concatenate((final_audio_data, audio_data))

    time_to_first_audio = first_chunk_received_time - request_start_time
    time_to_completion = datetime.datetime.now() - request_start_time
    audio_duration = len(final_audio_data) / 24_000  # default sampling rate.

    print("\n")
    print(f"Time to first audio: {time_to_first_audio.total_seconds()} seconds")
    print(f"Time to completion: {time_to_completion.total_seconds()} seconds")
    print(f"Audio duration: {audio_duration} seconds")

    return final_audio_data





Perform synchronous multi-speaker synthesis with freeform text input
Note: The combined size of all lines of dialogue can be at most 4,000 bytes. While the total size of the prompt and dialogue can be up to 4,000 bytes, each prompt and dialogue field must be a maximum of 4,000 bytes. Speaker aliases must consist solely of alphanumeric characters, excluding whitespace.


# google-cloud-texttospeech minimum version 2.31.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize_multispeaker_freeform(
    prompt: str,
    text: str,
    output_filepath: str = "output_non_turn_based.wav",
):
    """Synthesizes speech from non-turn-based input and saves it to a WAV file.

    Args:
        prompt: Styling instructions on how to synthesize the content in the
          text field.
        text: The text to synthesize, containing speaker aliases to indicate
          different speakers. Example: "Sam: Hi Bob!\nBob: Hi Sam!"
        output_filepath: The path to save the generated audio file. Defaults to
          "output_non_turn_based.wav".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

    multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
        speaker_voice_configs=[
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker1",
                speaker_id="Kore",
            ),
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker2",
                speaker_id="Charon",
            ),
        ]
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        model_name="gemini-2.5-pro-tts",
        multi_speaker_voice_config=multi_speaker_voice_config,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")





Perform synchronous multi-speaker synthesis with structured text input
Multi-speaker with structured text input enables intelligent verbalization of text in a human-like way. For example, this kind of input is useful for addresses and dates. Freeform text input speaks the text exactly as written.


# google-cloud-texttospeech minimum version 2.31.0 is required.

import os
from google.cloud import texttospeech

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def synthesize_multispeaker_structured(
    prompt: str,
    turns: list[texttospeech.MultiSpeakerMarkup.Turn],
    output_filepath: str = "output_turn_based.wav",
):
    """Synthesizes speech from turn-based input and saves it to a WAV file.

    Args:
        prompt: Styling instructions on how to synthesize the content in the
          text field.
        turns: A list of texttospeech.MultiSpeakerMarkup.Turn objects representing
          the dialogue turns.
        output_filepath: The path to save the generated audio file. Defaults to
          "output_turn_based.wav".
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(
        multi_speaker_markup=texttospeech.MultiSpeakerMarkup(turns=turns),
        prompt=prompt,
    )

    multi_speaker_voice_config = texttospeech.MultiSpeakerVoiceConfig(
        speaker_voice_configs=[
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker1",
                speaker_id="Kore",
            ),
            texttospeech.MultispeakerPrebuiltVoice(
                speaker_alias="Speaker2",
                speaker_id="Charon",
            ),
        ]
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        model_name="gemini-2.5-pro-tts",
        multi_speaker_voice_config=multi_speaker_voice_config,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio content written to file: {output_filepath}")




Perform synchronous single-speaker synthesis


from google import genai
from google.genai import types
import wave
import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
  with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

response = client.models.generate_content(
  model="gemini-2.5-flash-tts",
  contents="Say the following in a curious way: OK, so... tell me about this [uhm] AI thing.",
  config=types.GenerateContentConfig(
      speech_config=types.SpeechConfig(
        language_code="en-in",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
              voice_name='Kore',
            )
        )
      ),
  )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name='output_speech.wav'
wave_file(file_name, data) # Saves the file to current directory



Perform streaming single-speaker synthesis


from google import genai
from google.genai import types
import wave
import os
import datetime

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "global")

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
  with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

def synthesize(text: str, model: str, voice: str, locale: str):
    """Synthesizes speech from the input text.

    Args:
        text: Text to synthesize.
        model: gemini tts model name. gemini-2.5-flash-tts, gemini-2.5-flash-lite-preview-tts, and gemini-2.5-pro-tts
        voice: voice name. Example: leda, kore. Refer to available voices
        locale: locale name. Example: en-us. Refer to available locales.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    generate_content_config=types.GenerateContentConfig(
        speech_config=types.SpeechConfig(
          language_code=locale,
          voice_config=types.VoiceConfig(
              prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=voice,
              )
          )
        ),
    )

    request_start_time = datetime.datetime.now()
    is_first_chunk_received = False
    final_audio_data = bytes()
    num_chunks_received = 0

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=text,
        config=generate_content_config,
    ):
        # just a simple progress indicator
        num_chunks_received += 1
        print(".", end="")
        if num_chunks_received % 40 == 0:
            print("")
        # measuring time to first audio
        if not is_first_chunk_received:
            is_first_chunk_received = True
            first_chunk_received_time = datetime.datetime.now()

        if (
            chunk.candidates is None
            or not chunk.candidates
            or chunk.candidates[0].content is None
            or not chunk.candidates[0].content.parts
        ):
            continue
        part = chunk.candidates[0].content.parts[0]
        if part.inline_data and part.inline_data.data:
          # accumulating audio. In a web-server scenario, you would want to
          # "emit" audio to the frontend as soon as it arrives.
          #
          # For example using flask socketio, you could do the following
          # from flask_socketio import SocketIO, emit
          # emit("audio", chunk.candidates[0].content.parts[0].inline_data.data)
          # socketio.sleep(0)
          final_audio_data += chunk.candidates[0].content.parts[0].inline_data.data

    time_to_first_audio = first_chunk_received_time - request_start_time
    time_to_completion = datetime.datetime.now() - request_start_time

    print("\n")
    print(f"Time to first audio: {time_to_first_audio.total_seconds()} seconds")
    print(f"Time to completion: {time_to_completion.total_seconds()} seconds")

    return final_audio_data

audio_data = synthesize(
    "Say the following in a curious way: Radio Bakery is a New York City gem, celebrated for its exceptional and creative baked goods. The pistachio croissant is often described as a delight with perfect sweetness. The rhubarb custard croissant is a lauded masterpiece of flaky pastry and tart filling. The brown butter corn cake stands out with its crisp edges and rich flavor. Despite the bustle, the staff consistently receives praise for being friendly and helpful.",
    "gemini-2.5-flash-tts",
    "Kore",
    "en-in")
file_name='output_speech.wav'
wave_file(file_name, audio_data)

Audio("output_speech.wav")




Perform synchronous multi-speaker synthesi

# Make sure to install gcloud cli, and sign in to your project.
# Make sure to use your PROJECT_ID value.
# The available models are gemini-2.5-flash-tts, gemini-2.5-flash-lite-preview-tts, and gemini-2.5-pro-tts.
# To parse the JSON output and use it directly see the last line of the command.
# Requires JQ and ffplay library to be installed.
PROJECT_ID=YOUR_PROJECT_ID
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: $PROJECT_ID" \
  -H "Content-Type: application/json" \
-d '{
  "contents": {
    "role": "user",
    "parts": { "text": "Say the following as a conversation between friends: Sam: Hi Bob, how are you?\\nBob: I am doing well, and you?" }
  },
  "generation_config": {
    "speech_config": {
      "language_code": "en-in",
      "multi_speaker_voice_config": {
        "speaker_voice_configs": [{
          "speaker": "Sam",
          "voice_config": {
            "prebuilt_voice_config": {
              "voice_name": "Aoede"
            }
          }
        },{
          "speaker": "Bob",
          "voice_config": {
            "prebuilt_voice_config": {
              "voice_name": "Algieba"
            }
          }
        }]
      }
    }
  }
  }' \
  https://aiplatform.googleapis.com/v1beta1/projects/$PROJECT_ID/locations/us-central1/publishers/google/models/gemini-2.5-flash-tts:generateContent \
  | jq -r '.candidates[0].content.parts[0].inlineData.data' \
  | base64 -d | ffmpeg -f s16le -ar 24k -ac 1 -i - output_speech.wav
            