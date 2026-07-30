# Comparativo: Transcricao MELO (Whisper local) vs YouTube nativo

## Contexto

No trecho ~7:48-8:29 do mix "Tipico Mix Vol.2 - DJ Phantom Panama"
(https://youtu.be/CoNANz87dTk), a transcricao automatica nativa do
YouTube mostra `[Musica]` repetido de 8:02 a 8:24 - nao capta nenhum
texto real nessa janela.

O MELO (whisper.cpp, modelo small, local) capturou nesse mesmo trecho
uma aproximacao do nome "Arielis Nicole" (variacoes entre sessoes:
"Arelis Nicola", "Arielis Nicole"), posteriormente confirmado como
correto via curadoria manual (tracklist oficial, ver docs/BACKLOG.md).

## Leitura honesta do resultado

Isso NAO prova que o MELO e "melhor que o YouTube" em geral. E um (1)
exemplo pontual, nao uma medicao sistematica de WER (Word Error Rate).
Ambos os sistemas engasgam na mesma janela de tempo, sugerindo que o
problema pode ser o audio em si (vocal baixo na mixagem, predominancia
de instrumental) - nao necessariamente qualidade de modelo.

O que o exemplo mostra, com essa ressalva: em pelo menos 1 caso real,
em espanhol regional de nicho (tipico panameno), o pipeline local do
MELO recuperou um nome proprio que a transcricao automatica do YouTube
nao recuperou.

## Metodologia da comparacao

Captura da transcricao do YouTube feita via recurso nativo "Mostrar
transcricao" do proprio player (uso normal do produto, sem scraping/API
nao autorizada - ver aviso legal do README). Nao ha extracao automatizada
de dados do YouTube neste projeto.

## Proximo passo, se quiser medir WER real

Nao feito ainda: comparacao sistematica (varias faixas, WER calculado
palavra a palavra) entre MELO local e transcricao do YouTube. Ver
scripts/compare_transcripts.py (se existir) ou registrar como item novo
do BACKLOG.
