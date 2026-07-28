# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

## [Não lançado]

### Corrigido
- `packages/catalog/store.py`: `claim_handle()` não impedia `@` duplicado
  entre cadastros diferentes na mesma tabela — o `UPDATE` era executado
  sem nenhuma verificação de unicidade, apesar do docstring prometer
  `sqlite3.IntegrityError` em colisão. Adicionado `CREATE UNIQUE INDEX`
  por tabela em `_ensure_handle_columns` (`source_artists`,
  `destination_artists`, `produtores`). Múltiplos `NULL` continuam
  permitidos (cadastros que ainda não reivindicaram `@`).
  Teste de regressão: `test_claim_handle_rejects_duplicate` em
  `tests/unit/test_catalog_store.py`.
