#!/data/data/com.termux/files/usr/bin/bash
set -e

mkdir -p requirements

printf "numpy\nscipy\npydantic\npython-dotenv\npyyaml\ntqdm\nrequests\n" > requirements/base.txt

printf -- "-r base.txt\nffmpeg-python\nmutagen\nlibrosa\nsoundfile\naudioread\npydub\nmatplotlib\n" > requirements/audio.txt

printf -- "-r base.txt\ntorch\ntorchaudio\ntransformers\naccelerate\nsentencepiece\nopenai-whisper\nfaster-whisper\n" > requirements/ai.txt

printf -- "-r audio.txt\nbasic-pitch\npretty-midi\nmido\nmusic21\n" > requirements/music.txt

printf "pytest\npytest-cov\ncoverage\npytest-mock\n" > requirements/test.txt

printf -- "-r audio.txt\n-r ai.txt\n-r music.txt\n-r test.txt\nruff\nblack\nmypy\npre-commit\nmkdocs\nmkdocs-material\n" > requirements/dev.txt

printf -- "-r audio.txt\nrich\nclick\n" > requirements/termux.txt

printf -- "-r dev.txt\njupyter\nipywidgets\ngoogle-colab\n" > requirements/colab.txt

echo "requirements criado:"
ls -1 requirements
