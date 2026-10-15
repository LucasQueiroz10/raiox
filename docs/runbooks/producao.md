# Roteiro de operação: produção no Google Cloud

Passos manuais do ambiente de produção (ADR 0007). Versão inicial: a criação do projeto, do banco e
do deploy entra aqui com o PR do deploy.

Nada deste roteiro guarda segredo: senhas e tokens ficam só no Secret Manager. Os valores entre `<>`
são preenchidos na hora, no terminal, e nunca vão para o repositório.

---

## 1. Provedor de identidade do GitHub (Workload Identity Federation)

O GitHub Actions entra no Google Cloud sem chave de conta de serviço (ADR 0007, seção 6). O provedor
aceita só o repositório `LucasQueiroz10/raiox`, conferido pelo nome e pelo número interno do
repositório e do dono no GitHub, que não mudam se o repositório for renomeado e não são
reaproveitados. A conta `rx-deploy` aceita só os jobs do ambiente `producao` do GitHub.

**1.1. Números internos do repositório e do dono** (com o GitHub CLI logado na conta do Lucas):

```bash
gh api repos/LucasQueiroz10/raiox --jq '.id, .owner.id'
```

**1.2. Pool e provedor**, com a condição que recusa qualquer outro repositório:

```bash
PROJETO=<id-do-projeto>
ID_REPOSITORIO=<primeiro número do passo 1.1>
ID_DONO=<segundo número do passo 1.1>

gcloud iam workload-identity-pools create github \
  --project="$PROJETO" --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc raiox \
  --project="$PROJETO" --location=global --workload-identity-pool=github \
  --display-name="Repositório raiox" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.environment=assertion.environment" \
  --attribute-condition="assertion.repository == 'LucasQueiroz10/raiox' && assertion.repository_id == '$ID_REPOSITORIO' && assertion.repository_owner_id == '$ID_DONO'"
```

**1.3. Só o ambiente `producao` pode usar a conta `rx-deploy`:**

```bash
NUMERO_PROJETO=$(gcloud projects describe "$PROJETO" --format='value(projectNumber)')

gcloud iam service-accounts add-iam-policy-binding "rx-deploy@$PROJETO.iam.gserviceaccount.com" \
  --project="$PROJETO" --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/$NUMERO_PROJETO/locations/global/workloadIdentityPools/github/subject/repo:LucasQueiroz10/raiox:environment:producao"
```

O GitHub identifica cada job de um ambiente como `repo:LucasQueiroz10/raiox:environment:producao`;
nenhum outro job, nem do mesmo repositório, recebe a conta.

**1.4. No GitHub:** criar o ambiente `producao` (Settings → Environments), com o Lucas como revisor
obrigatório e só a branch `main` autorizada. O workflow de deploy declara `environment: producao` e
`permissions: id-token: write`.

**1.5. Conferir:**

```bash
gcloud iam workload-identity-pools providers describe raiox \
  --project="$PROJETO" --location=global --workload-identity-pool=github \
  --format='value(attributeCondition)'
```

A saída precisa trazer as três condições do passo 1.2.

---

## 2. DNS do `sagitalapp.com.br`

O domínio já existe e já tem e-mail. O site passa a ser servido pelo Firebase Hosting sem tocar no
e-mail.

1. **Antes de qualquer mudança, salvar a zona atual do DNS:** exportar o arquivo de zona no painel do
   provedor de DNS (ou, se ele não exportar, registrar todos os registros com tipo, nome, valor e TTL).
   Guardar com a data na pasta compartilhada do projeto, fora do repositório.
2. **Não alterar os registros de e-mail:** MX, o TXT do SPF (`v=spf1 ...`), os TXT do DKIM
   (`<seletor>._domainkey`) e o TXT do DMARC (`_dmarc`). Também não apagar registros de verificação de
   outros serviços.
3. No console do Firebase Hosting, adicionar `sagitalapp.com.br` e `www.sagitalapp.com.br` como
   domínios personalizados e criar **só** os registros que o console indicar (o TXT de verificação e
   os de apontamento). Se já houver um registro A ou AAAA no domínio raiz (por exemplo, de uma página
   de estacionamento do registrador), trocar só esse.
4. Esperar o certificado do Firebase, que pode levar algumas horas.
5. **Conferir depois:**
   - o site abre em `https://sagitalapp.com.br` e em `https://www.sagitalapp.com.br`;
   - os registros de e-mail continuam iguais aos da zona salva no passo 1;
   - um e-mail de teste é enviado e recebido pelo endereço do projeto.

---

## 3. Primeiro deploy: conferências

Fazer com pedidos nossos, nunca com dados de usuários.

1. **Saúde pelo domínio:** `curl -i https://sagitalapp.com.br/api/saude` responde 200.
2. **IP do cliente** (ADR 0007, seção 3; DT-17): chamar a medição `GET /interno/ip-do-cliente`
   pelo domínio e direto ao endereço `run.app` do serviço, com o segredo do aquecimento no
   cabeçalho `x-rx-aquecimento`. A resposta traz os endereços do `X-Forwarded-For`, na ordem, só
   para quem chamou, e a API não os registra em log. Nos dois casos, registrar no ADR 0007, seção
   3, só a estrutura: quantos endereços vêm e em que posição está o IP da máquina que fez o teste.
   Nunca anotar os IPs. Acertar `RX_PROXIES_CONFIAVEIS` no deploy pela posição do caminho pelo
   domínio.
3. **Limite por IP:** confirmar que o limite conta o IP da máquina do teste nos dois caminhos e
   registrar o resultado. Pelo `run.app`, o limite pode ser driblado (DT-11): o registro serve para o
   P3 saber o tamanho do risco.
4. **Aquecimento** (ADR 0007, seção 3):
   - `POST` em `<run.app>/interno/aquecer` sem o cabeçalho do segredo responde 404;
   - `https://sagitalapp.com.br/interno/aquecer` não chega à API (o Firebase não encaminha);
   - o job do Cloud Scheduler que chama o aquecimento termina com sucesso.
5. **Remover a medição** (DT-17): depois de registrar as posições no ADR 0007 e acertar
   `RX_PROXIES_CONFIAVEIS`, remover o endpoint `/interno/ip-do-cliente` (`app/api/interno.py`),
   seus testes (`test_medicao_ip.py`) e o trecho no `backend/CLAUDE.md`, num PR próprio, e fechar
   a DT-17. No mesmo PR, o `scripts/testar_imagem.sh`, que hoje confere pela medição que a
   aplicação lê o `X-Forwarded-For`, passa a conferir pelo limite por IP: com
   `RX_PROXIES_CONFIAVEIS=2`, 20 análises com o mesmo penúltimo endereço e um primeiro endereço
   forjado diferente em cada uma; a 21ª recebe 429, e uma com outro penúltimo endereço recebe 200.

---

## 4. Rotinas manuais do M1

Combinadas na aprovação da carga da CVM (ADR 0008, seção 7):

- **Uma vez por mês:** olhar a página do CDA no portal de dados abertos da CVM em busca de avisos de
  mudança de arquivo (como a troca de `cda_fiim` para `cda_fie` em 15/11/2025). A carga também para e
  avisa sozinha quando o nome ou as colunas mudam (ADR 0008, etapa 3).
- **A cada 6 meses:** rever os termos de uso das fontes da matriz de dados (`docs/matriz_de_dados.md`).
