# API Fluig Demo - Fornecedores

Extensao da API de colaboradores para uma demonstracao empresarial de fornecedores. Usa os fontes atuais de `anderson-simoes-code/api-fluig-demo`, consultados durante esta solicitacao, e acrescenta o recurso de fornecedores. Este pacote foi preparado e testado localmente; nao foi enviado ao seu GitHub, publicado no Render nem importado no seu Fluig.

## O que esta pronto

- 15 fornecedores inteiramente ficticios: 10 homologados e 5 nao homologados.
- Colunas: codigo, razaoSocial, categoria, cidade, uf, email e homologado.
- `homologado` e booleano no JSON: `true` ou `false`, sem aspas.
- GET `/fornecedores`: todos os 15 registros.
- GET `/fornecedores?homologado=true`: somente os 10 homologados.
- GET `/fornecedores?homologado=false`: somente os 5 nao homologados.
- Basic Auth, Swagger 2.0, suporte a HTTPS no Render e execucao local.
- Os endpoints de colaboradores e autenticacao continuam disponiveis.

O estado de homologacao e ilustrativo, sem representar uma avaliacao real das empresas. Todos os nomes foram criados para o exemplo e todos os emails usam example.com.

## Executar no computador

Requer Python 3.8 ou superior. Nao precisa instalar bibliotecas.

```console
python api_demo_fluig.py
```

No Windows, voce tambem pode usar `py -3 api_demo_fluig.py`. Mantenha a janela aberta enquanto testar.

URLs locais:

| Uso | Endereco |
| --- | --- |
| Health, publico | http://localhost:8765/health |
| Swagger, publico | http://localhost:8765/swagger.json |
| Validar Basic Auth | http://localhost:8765/basic-auth |
| Listar fornecedores | http://localhost:8765/fornecedores |
| Listar homologados | http://localhost:8765/fornecedores?homologado=true |

Usuario ficticio: `fluig`. Senha ficticia: `123456`. Esses valores sao os padroes do exemplo, nao credenciais de uma conta real. Se voce ja configurou `DEMO_API_USER` e `DEMO_API_PASSWORD` no Render, os valores configurados continuam sendo utilizados. O Swagger e o health sao publicos; as consultas de dados exigem autenticacao.

## Atualizar o repositorio e o Render

1. Substitua `api_demo_fluig.py` no repositorio pela versao deste pacote.
2. Adicione `fornecedores.json` na mesma pasta do arquivo Python.
3. Mantenha `colaboradores.json` nessa pasta. A copia incluida veio do repositorio atual.
4. O arquivo `fluig/dsFornecedoresHomologados.js` sera usado dentro do Fluig. Pode ficar na pasta fluig do repositorio, mas nao e executado pelo Render.
5. Grave o commit e acompanhe a publicacao no Render. Se o deploy automatico estiver desligado, publique o commit mais recente pelo painel.

O comando de inicializacao continua o mesmo:

```console
python api_demo_fluig.py --host 0.0.0.0 --port $PORT
```

Build Command: `python -m py_compile api_demo_fluig.py`.

O protocolo do Swagger agora acompanha `X-Forwarded-Proto`: HTTP localmente e HTTPS quando o Render encaminha a chamada HTTPS. Nao precisa editar schemes manualmente.

Depois da publicacao no servico existente, os enderecos esperados serao:

- https://api-fluig-demo.onrender.com/swagger.json
- https://api-fluig-demo.onrender.com/fornecedores
- https://api-fluig-demo.onrender.com/fornecedores?homologado=true

Os novos endpoints so estarao disponiveis depois dessa atualizacao. Para acrescentar registros, edite fornecedores.json no GitHub e publique o novo commit. A API nao possui POST de cadastro.

## 1. Cadastrar o servico no Fluig

Pode cadastrar um servico separado para facilitar a demonstracao:

| Campo | Preenchimento apos publicar no Render existente |
| --- | --- |
| Servico | REST |
| Nome | RestFornecedoresDemo |
| Descricao | Consulta de fornecedores ficticios |
| Arquivo Swagger | https://api-fluig-demo.onrender.com/swagger.json |
| Dominio | https://api-fluig-demo.onrender.com |
| Tipo de Autenticacao | Basic |
| Usuario | fluig, ou o valor configurado no Render |
| Senha | 123456, ou o valor configurado no Render |
| URL para teste de Servico | /basic-auth |

Salve e teste o servico. Se for usar outro servico do Render, substitua o dominio em todos os campos. O servidor Fluig precisa conseguir acessar o endereco escolhido.

## 2. Criar o dataset simples

Em Painel de Controle > Desenvolvimento > Datasets > Novo Dataset > Simples:

| Campo | Valor |
| --- | --- |
| Codigo | dsFornecedores |
| Descricao | Consulta de todos os fornecedores |
| Servico | RestFornecedoresDemo |
| Operacao | GET /fornecedores, listarFornecedores |
| Parametro homologado | Atribuicao Valor, conteudo vazio |

O parametro de consulta foi descrito como texto opcional, com valor padrao vazio, para o assistente nao assumir false quando voce quiser todos. A coluna homologado da resposta continua sendo booleana.

Salve/publique conforme sua interface e consulte o dataset. O retorno esperado sao 15 linhas. Confirme o codigo exato `dsFornecedores` antes de prosseguir.

Se o codigo gerado contiver a configuracao abaixo, mantenha o valor vazio:

```javascript
"inputValues": {
    "homologado": ""
}
```

Se deixar o parametro preenchido com true, o simples ja retornara somente homologados, eliminando a comparacao de 15 contra 10 na demonstracao.

## 3. Criar o dataset avancado

Crie outro dataset, do tipo Avancado, com codigo `dsFornecedoresHomologados`. Cole o conteudo completo de `fluig/dsFornecedoresHomologados.js` e publique.

O trecho principal e:

```javascript
var filtroHomologado = DatasetFactory.createConstraint(
    "homologado",
    "true",
    "true",
    ConstraintType.MUST
);
```

O avancado consulta `dsFornecedores`, passando essa constraint. O simples gerado pelo assistente interpreta o parametro e monta `/fornecedores?homologado=true`. A API aplica o filtro e retorna as 10 linhas homologadas.

O fluxo depende de o simples tratar a constraint. No codigo de integracao que voce compartilhou, isso ja ocorre em verifyConstraints e mountPath. Constraints nao aplicam, sozinhas, filtros a qualquer dataset customizado. Este exemplo utiliza igualdade com true e MUST; nao implementa faixas, LIKE ou combinacoes de SHOULD/MUST_NOT.

O avancado e uma visao fixa de homologados e nao encaminha filtros arbitrarios que o chamador envie. A filtragem e realizada na API, sem carregar os 15 registros no Fluig para descartar cinco depois.

## 4. Conferir o resultado

| Consulta | Resultado esperado |
| --- | --- |
| dsFornecedores, parametro vazio | 15 fornecedores |
| dsFornecedoresHomologados | 10 fornecedores, todos com homologado=true |
| API com homologado=false | 5 fornecedores nao homologados |
| API sem autenticacao ou com senha incorreta | HTTP 401 |
| API com homologado=talvez | HTTP 400 |

Se o avancado informar null, consulte o simples diretamente e confirme se seu codigo e exatamente `dsFornecedores`. Se a API retornar erro de autenticacao, confira o servico e as variaveis no Render. O teste no seu Fluig continua necessario.

### Observacao sobre o filtro false no gerador de datasets

O exemplo principal usa true. Se voce quiser consultar false via constraint no simples, verifique o if da funcao mountPath do codigo gerado. Um teste `if (value)` descarta o booleano false depois de JSON.parse. Para preservar false, a condicao de presenca deve ser:

```javascript
if (value !== null && typeof value !== "undefined" && String(value) !== "") {
    // restante do bloco original que monta os parametros
}
```

Editar o codigo gerado converte esse dataset em avancado; para a demonstracao simples versus avancado proposta, mantenha o fluxo com true e o simples inalterado.

## Trecho de fala sugerido

Primeiro, criamos um dataset simples para consultar o cadastro de fornecedores. Ele retorna todos os registros e informa quais fornecedores estao homologados. Agora, no dataset avancado, vamos reaproveitar essa consulta e enviar uma constraint para trazer somente os homologados. O simples encaminha esse parametro ao servico, e a API devolve apenas os fornecedores que atendem ao criterio. Assim, demonstramos reaproveitamento e filtragem na origem.

## Verificacao dos fontes

Os testes incluidos verificam a API e as respostas HTTP em memoria, sem acessar contas externas. O teste JavaScript usa mocks das interfaces DatasetFactory e ConstraintType: confirma a constraint true/MUST e o nome do dataset de origem, mas nao substitui a publicacao no Fluig.

```console
python -m unittest discover -s tests -p "test_*.py"
node tests/test_dataset.js
```
