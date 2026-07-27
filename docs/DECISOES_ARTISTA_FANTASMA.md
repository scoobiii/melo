# Localização no repo: docs/DECISOES_ARTISTA_FANTASMA.md

Perguntas de negócio desta sessão, traduzidas em regra de código —
"se não respondermos no código não temos projeto":

| Pergunta | Resposta em código |
|---|---|
| Cadê o artista, se o DJ não creditou? | `mix_tracks.status_identificacao = 'nao_identificado'` — estado explícito, não null silencioso |
| E se ninguém nunca identificar? | `POST /mix-tracks/{id}/escrow` — reserva 100% pra `escrow_titular_desconhecido`, nunca paga DJ/MELO enquanto não identificado |
| Como sai do escrow quando aparecer titular? | `POST /mix-tracks/{id}/identify` com `source_artist_id` real — a partir daí, próximo cálculo de royalty já usa o titular certo, não mais escrow |
| Vale perguntar pro DJ? | Sim — não é ação de código, é outreach; mas o campo `mixes.plataformas_distribuicao` já existe pra registrar o que ele responder |
| Isso expõe MELO a risco por perguntar? | Não codificado como bloqueio — perguntar não é o ato de risco; o conteúdo sem licença já é o risco, existente antes da pergunta |

Isso substitui a resposta em prosa da sessão anterior. Se uma pergunta de
negócio não tiver linha correspondente nesta tabela, ela ainda não foi
resolvida — não finge que foi.
