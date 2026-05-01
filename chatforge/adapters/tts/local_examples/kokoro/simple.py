# pip install kokoro>=0.9.4 soundfile
# apt-get install espeak-ng
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='a')
# text = '''
# [Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) can be deployed anywhere from production environments to personal projects.
# '''

text = '''
benim adım siluet, minik tırtılım. Nasılsın ne yapıyorsun
'''


generator = pipeline(text, voice='af_heart')
audio_chunks = []
for i, (gs, ps, audio) in enumerate(generator):
    print(i, gs, ps)
    audio_chunks.append(audio)

import numpy as np
full_audio = np.concatenate(audio_chunks)
sf.write('test-kokoro.wav', full_audio, 24000)
print("Done. Saved test-kokoro.wav")