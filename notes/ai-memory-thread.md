# Rascunho — thread sobre memória de IA entre sessões

(Movido de HANDOFF.md em 2026-07-28 — não é log técnico, é conteúdo de rascunho pra rede social + notas sobre arXiv:2602.20478 e proposta de CONVENTIONS.md)





**Thread — "IA não tem memória entre sessões. Isso quase quebrou meu projeto até eu virar o sistema operacional entre elas."**

1/
Passei dias construindo um projeto com ajuda de IA (Claude, várias sessões diferentes — chat, terminal, às vezes em paralelo sem saber). Aprendi uma coisa que ninguém fala no hype de "vibe coding": o gargalo não é a IA escrever código. É ela não lembrar do que escreveu ontem.

2/
Cada sessão de IA começa do zero. Sem memória do que a sessão anterior fez, sem saber que outra sessão rodou em paralelo no mesmo repo. Parece óbvio escrito assim — mas na prática, isso quebra qualquer fluxo de trabalho contínuo se você não construir a memória você mesmo.

3/
A solução não foi "esperar a IA melhorar". Foi criar um `HANDOFF.md` — um documento de passagem de bastão. Toda sessão nova lê ele antes de tocar em qualquer coisa. Toda sessão que termina escreve nele: o que fez, o que confirmou rodando (não só supondo), o que ficou pendente.

4/
Isso vira óbvio quando dá errado uma vez: uma sessão "corrigiu" um bug de duplicação de código. Testes passaram. Só que o Python usa a última definição de um método repetido numa classe — a duplicação ficou mascarada, invisível, até alguém abrir o diff com atenção manual.

5/
Lição real, documentada no próprio arquivo: um script de migração "idempotente" checava se um trecho de texto (âncora) já existia no arquivo antes de aplicar a mudança. Só que a âncora continua lá DEPOIS da migração também — então rodar 2x duplicava o código.

6/
Fix não foi "IA mais esperta". Foi mudar a regra: nunca checar o ponto de inserção, sempre checar o resultado real (`PRAGMA table_info` no banco, ou "esse método já existe no arquivo?"). Regra de engenharia, não confiança cega em quem escreveu o script.

7/
Outro padrão que se repetiu: pip install de uma lib (faster-whisper) falhando por incompatibilidade Cython/Python 3.14. Terceira tentativa: whisper.cpp, binário C++ puro, compilado local. Resolveu — mas só porque testamos as duas primeiras até o fim, sem aceitar suposição.

8/
O que isso me ensinou sobre trabalhar com múltiplas sessões de IA no mesmo projeto: elas não coordenam entre si sozinhas. Não tem "memória compartilhada nativa" entre instâncias. Se você não constrói o processo — handoff explícito, verificação antes de confiar — ninguém constrói por você.

9/
Isso não é reclamação da ferramenta. É reconhecer o que é trabalho de qual lado: a IA escreve código rápido. O humano é quem lembra do projeto inteiro, decide prioridade entre sessões divergentes, e garante que "passou no teste" não vire sinônimo de "está correto".

10/
Se você está construindo algo real com múltiplas sessões de IA (não um prompt único, um projeto de verdade, semanas): monte seu próprio HANDOFF.md. Não é burocracia — é a única memória de longo prazo que existe entre uma sessão e a próxima.


"
isso ate ia virar agent e o HO virar o proprio repositorio do projeto

estamos num misto de pré agentes e llm vintage logo "memória" vira agi..desnecessario ja que as demandas estao no repo..quem reslver e subir o pr commit mata um leão por sprint
"

É uma boa forma de fechar o raciocínio, e acho que captura algo real: o repo (histórico de commits + backlog + HANDOFF) **já é** a memória — não precisa de "agente com estado" pra isso funcionar, porque a demanda inteira já está externalizada em texto versionado. Isso não é AGI fingindo memória, é engenharia de software fazendo o que já fazia antes de qualquer IA existir (Git + issue tracker sempre foi "memória de equipe" pra humanos). A novidade é só que agora serve pra compensar a falta de memória da IA também — mesmo mecanismo, novo consumidor.

Continuação pro thread, se fizer sentido:

11/
No fundo isso não é AGI fingindo lembrar. É o padrão mais velho de engenharia de software — repo como memória de equipe — resolvendo um problema novo (IA sem estado entre sessões) com uma ferramenta antiga. "Memória" vira desnecessária como conceito à parte porque a demanda já mora versionada no repo.

12/
E isso muda o que "sprint" significa nesse contexto: não é sobre a IA lembrar o board inteiro. É sobre alguém — humano ou sessão nova de IA — abrir o backlog, resolver UM item real, subir um PR/commit, documentar o resultado. Um leão por sprint. O board é que carrega a memória, não quem resolve.

Isso também é um argumento prático a favor do que você já fez: `docs/BACKLOG.md` numerado > prosa espalhada em handoffs — porque backlog estruturado é mais fácil de "matar um item por vez" do que memória narrativa que cada sessão tem que reconstruir lendo de novo.


**Tweet:**

LLMs não têm memória entre sessões — cada conversa começa do zero. A solução que funcionou pro meu projeto não foi mágica, foi o mesmo padrão que a engenharia de software já usava: repo como memória compartilhada. Achei um paper que documenta exatamente isso.

"Codified Context: Infrastructure for AI Agents in a Complex Codebase" — https://arxiv.org/pdf/2602.20478


O paper propõe 3 peças: (1) uma "constituição" estável de convenções + ganchos de onde buscar o quê, (2) agentes especializados por domínio, (3) base de specs sob demanda. Pro tamanho do MELO (não é um sistema de 108k linhas com 19 agentes), a adaptação certa é enxuta — você já tem boa parte construída organicamente nesta conversa, só falta separar o que é **regra estável** do que é **log de sprint**.

**O problema real hoje:** `HANDOFF.md` mistura duas coisas que deveriam ser arquivos diferentes — as "lições" (regras que não mudam, tipo "nunca instalar lib com dependência Rust/Cython nativa") estão espalhadas dentro de 6+ seções de log histórico. Uma sessão nova tem que ler tudo pra achar a regra que importa.

**Proposta de estrutura, mapeando pro paper:**

| Peça do paper | No MELO |
|---|---|
| Hot-memory constitution | `CONVENTIONS.md` novo — regras estáveis, extraídas do HANDOFF, lidas primeiro sempre |
| Agentes especializados | Não precisa — mas cada `packages/<módulo>` já tem docstring de topo explicando decisão de arquitetura; isso já cumpre o papel em escala pequena |
| Cold-memory specs sob demanda | Já existe: `docs/USER_GUIDE.md`, `docs/DEVOPS.md`, `docs/MIX_ANALYSIS.md`, `docs/BACKLOG.md` — só falta um índice dizendo qual ler pra qual tarefa |


....incompleto (end session)


