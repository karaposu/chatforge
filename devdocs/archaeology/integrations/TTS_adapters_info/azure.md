What is text to speech?
In this overview, you learn about the benefits and capabilities of the text to speech feature of the Speech service, which is part of Foundry Tools.

Text to speech enables your applications, tools, or devices to convert text into human like synthesized speech. The text to speech capability is also known as speech synthesis. Use human like standard voices out of the box, or create a custom voice that's unique to your product or brand. For a full list of supported voices, languages, and locales, see Language and voice support for the Speech service.

Core features
Text to speech includes the following features:

Feature	Summary	Demo
Standard voice (called Neural on the pricing page)	Highly natural out-of-the-box voices. Create an Azure subscription and Speech resource, and then use the Speech SDK or visit the Speech Studio portal and select standard voices to get started. Check the pricing details.	Check the Voice Gallery and determine the right voice for your business needs.
Custom voice	Easy-to-use self-service for creating a natural brand voice, with limited access for responsible use. Create an Azure subscription and Microsoft Foundry resource and then apply to use custom voice. After you're granted access, go to the professional voice fine-tuning documentation to get started. Check the pricing details.	Check the voice samples.
More about neural text to speech features
Text to speech uses deep neural networks to make the voices of computers nearly indistinguishable from the recordings of people. With the clear articulation of words, neural text to speech significantly reduces listening fatigue when users interact with AI systems.

The patterns of stress and intonation in spoken language are called prosody. Traditional text to speech systems break down prosody into separate linguistic analysis and acoustic prediction steps governed by independent models. That can result in muffled, buzzy voice synthesis.

Here's more information about neural text to speech features in the Speech service, and how they overcome the limits of traditional text to speech systems:

Real-time speech synthesis: Use the Speech SDK or REST API to convert text to speech by using standard voices or custom voices.

Asynchronous synthesis of long audio: Use the batch synthesis API to asynchronously synthesize text to speech files longer than 10 minutes (for example, audio books or lectures). Unlike synthesis performed via the Speech SDK or Speech to text REST API, responses aren't returned in real-time. The expectation is that requests are sent asynchronously, responses are polled for, and synthesized audio is downloaded when the service makes it available.

Standard voices: Azure Speech in Foundry Tools uses deep neural networks to overcome the limits of traditional speech synthesis regarding stress and intonation in spoken language. Prosody prediction and voice synthesis happen simultaneously, which results in more fluid and natural-sounding outputs. Each standard voice model is available at 24 kHz and high-fidelity 48 kHz. You can use neural voices to:

Make interactions with chatbots and voice assistants more natural and engaging.
Convert digital texts such as e-books into audiobooks.
Enhance in-car navigation systems.
For a full list of standard Azure Speech in Foundry Tools neural voices, see Language and voice support for the Speech service.

Improve text to speech output with SSML: Speech Synthesis Markup Language (SSML) is an XML-based markup language used to customize text to speech outputs. With SSML, you can adjust pitch, add pauses, improve pronunciation, change speaking rate, adjust volume, and attribute multiple voices to a single document.

You can use SSML to define your own lexicons or switch to different speaking styles. With the multilingual voices, you can also adjust the speaking languages via SSML. To improve the voice output for your scenario, see Improve synthesis with Speech Synthesis Markup Language and Speech synthesis with the Audio Content Creation tool.

Visemes: Visemes are the key poses in observed speech, including the position of the lips, jaw, and tongue in producing a particular phoneme. Visemes have a strong correlation with voices and phonemes.

By using viseme events in Speech SDK, you can generate facial animation data. This data can be used to animate faces in lip-reading communication, education, entertainment, and customer service. Viseme is currently supported only for the en-US (US English) neural voices.

 Note

In addition to Azure Speech neural (non HD) voices, you can also use Azure Speech high definition (HD) voices and Azure OpenAI neural (HD and non HD) voices. The HD voices provide a higher quality for more versatile scenarios.

Some voices don't support all Speech Synthesis Markup Language (SSML) tags. This includes neural text to speech HD voices, personal voices, and embedded voices.

For Azure Speech high definition (HD) voices, check the SSML support here.
For personal voice, you can find the SSML support here.
For embedded voices, check the SSML support here.

Quickstart: Convert text to speech
Choose a programming language or tool
Reference documentation | Package (PyPi) | Additional samples on GitHub

With Azure Speech in Foundry Tools, you can run an application that synthesizes a human-like voice to read text. You can change the voice, enter text to be spoken, and listen to the output on your computer's speaker.

 Tip

You can try text to speech in the Speech Studio Voice Gallery without signing up or writing any code.

 Tip

Try out the Azure Speech Toolkit to easily build and run samples on Visual Studio Code.

Prerequisites
An Azure subscription. You can create one for free.
Create an AI Services resource for Speech in the Azure portal.
Get the Speech resource key and endpoint. After your Speech resource is deployed, select Go to resource to view and manage keys.
Set up the environment
The Speech SDK for Python is available as a Python Package Index (PyPI) module. The Speech SDK for Python is compatible with Windows, Linux, and macOS.

On Windows, install the Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017, 2019, and 2022 for your platform. Installing this package might require a restart.
On Linux, you must use the x64 target architecture.
Install a version of Python from 3.7 or later. For any requirements, see Install the Speech SDK.

Set environment variables
You need to authenticate your application to access Foundry Tools. This article shows you how to use environment variables to store your credentials. You can then access the environment variables from your code to authenticate your application. For production, use a more secure way to store and access your credentials.

 Important

We recommend Microsoft Entra ID authentication with managed identities for Azure resources to avoid storing credentials with your applications that run in the cloud.

Use API keys with caution. Don't include the API key directly in your code, and never post it publicly. If using API keys, store them securely in Azure Key Vault, rotate the keys regularly, and restrict access to Azure Key Vault using role based access control and network access restrictions. For more information about using API keys securely in your apps, see API keys with Azure Key Vault.

For more information about AI services security, see Authenticate requests to Azure AI services.

To set the environment variables for your Speech resource key and endpoint, open a console window, and follow the instructions for your operating system and development environment.

To set the SPEECH_KEY environment variable, replace your-key with one of the keys for your resource.
To set the ENDPOINT environment variable, replace your-endpoint with one of the endpoints for your resource.
Windows
Linux
macOS
Bash
Edit your .bashrc file, and add the environment variables:

Bash
export SPEECH_KEY=your-key
export ENDPOINT=your-endpoint
After you add the environment variables, run source ~/.bashrc from your console window to make the changes effective.

Create the application
Follow these steps to create a console application.

Open a command prompt window in the folder where you want the new project. Create a file named speech_synthesis.py.

Run this command to install the Speech SDK:

Console
pip install azure-cognitiveservices-speech
Copy the following code into speech_synthesis.py:

Python
import os
import azure.cognitiveservices.speech as speechsdk

# This example requires environment variables named "SPEECH_KEY" and "ENDPOINT"
# Replace with your own subscription key and endpoint, the endpoint is like : "https://YourServiceRegion.api.cognitive.microsoft.com"
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), endpoint=os.environ.get('ENDPOINT'))
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The neural multilingual voice can speak different languages based on the input text.
speech_config.speech_synthesis_voice_name='en-US-Ava:DragonHDLatestNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Get text from the console and synthesize to the default speaker.
print("Enter some text that you want to speak >")
text = input()

speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized for text [{}]".format(text))
elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = speech_synthesis_result.cancellation_details
    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        if cancellation_details.error_details:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and endpoint values?")
To change the speech synthesis language, replace en-US-Ava:DragonHDLatestNeural with another supported voice.

All neural voices are multilingual and fluent in their own language and English. For example, if the input text in English is I'm excited to try text to speech and you set es-ES-Ximena:DragonHDLatestNeural, the text is spoken in English with a Spanish accent. If the voice doesn't speak the language of the input text, the Speech service doesn't output synthesized audio.

Run your new console application to start speech synthesis to the default speaker.

Console
python speech_synthesis.py
 Important

Make sure that you set the SPEECH_KEY and ENDPOINT environment variables. If you don't set these variables, the sample fails with an error message.

Enter some text that you want to speak. For example, type I'm excited to try text to speech. Select the Enter key to hear the synthesized speech.

Console
Enter some text that you want to speak > 
I'm excited to try text to speech
Remarks
More speech synthesis options
This quickstart uses the speak_text_async operation to synthesize a short block of text that you enter. You can also use long-form text from a file and get finer control over voice styles, prosody, and other settings.

See how to synthesize speech and Speech Synthesis Markup Language (SSML) overview for information about speech synthesis from a file and finer control over voice styles, prosody, and other settings.
See batch synthesis API for text to speech for information about synthesizing long-form text to speech.
OpenAI text to speech voices in Azure Speech in Foundry Tools
OpenAI text to speech voices are also supported. See OpenAI text to speech voices in Azure Speech and multilingual voices. You can replace en-US-Ava:DragonHDLatestNeural with a supported OpenAI voice name such as en-US-FableMultilingualNeural.

Clean up resources
You can use the Azure portal or Azure Command Line Interface (CLI) to remove the Speech resource you created.




What is the Speech SDK?
The Speech SDK (software development kit) exposes many of the Speech service capabilities, so you can develop speech-enabled applications. The Speech SDK is available in many programming languages and across platforms. The Speech SDK is ideal for both real-time and non-real-time scenarios, by using local devices, files, Azure Blob Storage, and input and output streams.

In some cases, you can't or shouldn't use the Speech SDK. In those cases, you can use REST APIs to access the Speech service. For example, use the Speech to text REST API for batch transcription and custom speech model management.



https://github.com/Azure-Samples/cognitive-services-speech-sdk
