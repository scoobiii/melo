# BUSINESS PLAN — MELO

> Rascunho inicial gerado a partir do README e da estrutura de código
> existente. Substitui o `BUSINESS_PLAN.md` anterior, que estava vazio
> (0 bytes) desde 21/07. Precisa de validação e números reais antes de
> ser usado externamente (investidores, parceiros).

## 1. Problema

Gêneros musicais regionais (típico panamenho, cumbia, tamborito) têm
correlação estrutural com gêneros regionais brasileiros (forró, pisadinha,
vanerão, sertanejo), mas não existe ferramenta que:

- identifique automaticamente essa correlação,
- adapte uma faixa de um gênero para outro,
- resolva a questão de licenciamento/royalty de forma automatizada.

## 2. O que o MELO faz hoje (validado, com testes)

- Extrai metadados de áudio real (duração, sample rate, canais).
- Transcreve letra via Whisper local (sem depender de API externa paga).
- Estima BPM e calcula correlação de gênero entre panamá e brasil.
- Orquestra esse pipeline numa chamada única.
- Calcula splits de royalty a partir de percentuais negociados
  externamente (o motor não decide o percentual, só aplica).

Isso é uma ferramenta de **análise**, não ainda um produto de **geração**.

## 3. O que falta para virar produto (ver ROADMAP.md)

- Geração/regravação de áudio (instrumental e voz).
- Distribuição e licenciamento automatizado.
- Interface para usuário final não-técnico.

## 4. Modelo de monetização (hipóteses a validar)

Três caminhos possíveis, não mutuamente exclusivos:

1. **B2B / licenciamento de tecnologia**: vender o motor de correlação e
   adaptação (`packages/adaptation` + `packages/pipeline`) para gravadoras
   ou plataformas que já têm catálogo licenciado.
2. **SaaS para produtores/DJs independentes**: cobrar por faixa adaptada,
   com o `packages/publisher` cuidando do split de royalty entre autor
   original e adaptador.
3. **Marketplace de adaptações licenciadas**: MELO como intermediário que
   garante que toda adaptação publicada tem licença mecânica válida,
   cobrando comissão sobre o split.

Nenhuma dessas hipóteses tem validação de mercado ainda — são direções, não
compromissos.

## 4.1 Posicionamento frente a Suno/Udio (revisão 2026-07-25)

Suno e Udio competem em **geração de áudio do zero** (texto → música
completa) e não têm API oficial pública até julho de 2026 — apenas
wrappers de terceiros não-oficiais, com risco de estabilidade e de termos
de uso. MELO **não compete nesse espaço** e não deveria tentar: a vantagem
real é ser o oposto — adaptação de uma faixa **existente e identificada**,
com split de royalty já resolvido tecnicamente (`packages/publisher`), num
nicho de gênero (panamá↔brasil) que essas ferramentas não endereçam.

Isso muda a priorização: perseguir geração de voz própria (Fase 1 do
ROADMAP) só faz sentido se a alternativa de reaproveitar Suno/Udio via API
não for viável — e hoje não é, porque a API deles não é pública. Ou seja,
não há atalho: se quisermos gerar áudio, é preciso construir isso
internamente, o que reforça o tamanho real do investimento da Fase 1.

## 4.2 Oportunidades identificadas (gaps que também são espaço de produto)

- **Tradução simultânea à adaptação de gênero**: extensão barata do
  `packages/ai/adapter.py` já existente — não exige infraestrutura nova,
  só expandir o prompt.
- **Casting de voz por gênero** (escolher cantor local — forró raiz,
  universitário, sofrência, sertanejo, vanerão — um ou vários
  simultaneamente): produto novo, mas de menor risco técnico que geração
  de voz do zero. Depende de resolver persistência primeiro (ver 5.1).
- **Nicho defensável**: por Suno/Udio não terem API pública nem foco em
  adaptação regional, MELO tem uma janela de tempo para se estabelecer
  nesse nicho específico antes que players maiores decidam entrar nele.

## 5. Riscos principais

- **Legal**: qualquer geração de voz que imite artista real sem
  autorização é risco jurídico direto (o próprio README já isola esse
  risco ao proibir extração não licenciada de áudio de streaming).
- **Qualidade**: adaptação de gênero automatizada pode soar artificial;
  sem `packages/score`, não há métrica objetiva de qualidade ainda.
- **Dependência de dados**: correlação de gênero panamá↔brasil precisa de
  dataset representativo; `datasets/` está presente na estrutura mas o
  conteúdo não foi auditado aqui.
- **Ausência de persistência**: não há camada de banco (relacional ou
  vetorial) no projeto hoje — `output/` é só JSON em arquivo. Qualquer
  feature que dependa de "lembrar" dados entre execuções (base de
  cantores, score histórico, catálogo de faixas) precisa dessa camada
  antes de existir.
- **Nenhuma interface de usuário existe ainda**: `apps/web`, `apps/mobile`,
  `apps/cli` são pastas vazias. Não há player nem gerenciador de arquivo —
  qualquer demonstração hoje é via linha de comando.

## 6. Próximos passos concretos

1. Validar Fase 1 do ROADMAP (geração de áudio) com um protótipo mínimo,
   mesmo que de baixa qualidade, para testar se há interesse real.
2. Conversar com pelo menos um titular de catálogo (editora ou artista)
   sobre disposição a licenciar adaptações — sem isso, Fase 3 é
   inviável por design.
3. Definir métrica de qualidade (Fase 2) antes de escalar geração,
   para não publicar adaptações ruins em volume.

## 7. O que este documento não é

Não é um plano financeiro (sem projeção de receita/custo — não há dados
para isso ainda) nem um pitch para investidor. É um ponto de partida para
a próxima pessoa que abrir este arquivo não encontrar 0 bytes.
