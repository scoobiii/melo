# Gaps de Negócio — MELO

> Domínios sem dono técnico até 2026-07-25: CRM/Mkt, ERP/Gestão,
> Financeiro além do split, Legal/Contratos, Web3. Decisões registradas
> abaixo à medida que foram tomadas.

## Decisão por domínio

| Domínio | Estratégia | Motivo |
|---|---|---|
| CRM/Mkt (básico) | **Interno** — `packages/catalog/partners.py`, SQLite existente | Volume atual (0 parceiros validados) não justifica infra externa |
| ERP/Gestão (fatura/contabilidade formal) | Adiado — integrar Odoo **só quando houver faturamento real** | BUSINESS_PLAN: nenhuma hipótese validada com titular de catálogo ainda |
| Financeiro (split royalty) | **Interno** — `packages/publisher` | Já é o diferencial de produto |
| Financeiro (fatura/pagamento real) | Integrar externo (Odoo Invoicing), quando ativado | Emissão fiscal não é competência central |
| Legal (schema de licença) | Interno fino — extensão futura de `packages/catalog` | Específico do domínio (ECAD, licença mecânica panamá↔brasil) |
| Legal (assinatura) | Integrar externo (DocuSign ou similar), quando necessário | Assinatura eletrônica é problema resolvido |
| Web3 | Não fazer | Nenhum caso de uso validado em nenhum doc do projeto |

## Estrutura criada

```
packages/catalog/partners.py     # CRM básico: parceiros_negocio (lead → negociação → contrato → ativo)
packages/integrations/
├── crm/            # reservado — não ativado
├── erp/            # client JSON-RPC Odoo pronto (packages/integrations/erp/client.py), não ativado
└── legal_signing/  # reservado — não ativado
```

## Por que Odoo não roda no A23

Servidor Odoo requer PostgreSQL + wkhtmltopdf + assets Node — inviável em
Termux ARM64. MELO no A23 seria só cliente HTTP do Odoo (JSON-RPC via
`requests`, mesmo padrão de `packages/ai/adapter.py`), com o servidor
hospedado em Odoo Online, VPS, ou outra máquina. Não ativado ainda por
falta de faturamento real a declarar.

## Não decidido ainda

- Qual ferramenta exata de CRM/ERP externo (Odoo vs HubSpot vs outro),
  quando chegar a hora — depende de custo e de já ter conta em algum.
- Schema de licença dentro de `packages/catalog` (novo, ainda não desenhado).

## O que isso NÃO muda

Núcleo técnico do MELO (audio/lyrics/adaptation/pipeline/publisher/ai/
prompts/score/voices) continua 100% independente disso — os adapters
consomem eventos do pipeline, não o contrário.
