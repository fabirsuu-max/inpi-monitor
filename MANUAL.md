# INPI Monitor — Manual do Usuário

## 1. Introdução

O **INPI Monitor** é uma ferramenta desktop para pesquisar e monitorar marcas registradas no Instituto Nacional da Propriedade Industrial (INPI). Permite:

- Pesquisar processos de marcas a partir do arquivo XML da Revista da Propriedade Industrial (RPI)
- Buscar marcas diretamente no portal online do INPI
- Monitorar termos de interesse e verificar ocorrências na RPI carregada

---

## 2. Como Iniciar

### Via terminal

```bash
cd "/home/user_1/ai/Marcas Projeto"
./iniciar.sh
```

### Carregando XML automaticamente

```bash
./iniciar.sh RM2878.xml
```

### Via gerenciador de arquivos

Clique duas vezes em `iniciar.sh` (certifique-se de que o gerenciador executa scripts shell, não os abre como texto).

---

## 3. Aba: Pesquisa RPI (XML)

Esta aba pesquisa processos no arquivo XML da RPI carregado localmente.

### 3.1 Abrir arquivo XML

1. Clique em **Abrir XML...** ou use o menu **Arquivo → Abrir XML da RPI...** (Ctrl+O)
2. Selecione o arquivo `.xml` da RPI (ex: `RM2878.xml`)
3. Uma barra de progresso aparece durante o carregamento — para arquivos grandes (36.000+ processos) isso pode levar alguns segundos
4. Ao concluir, o total de processos carregados é exibido

### 3.2 Filtros de pesquisa

| Campo | Descrição |
|---|---|
| **Nome** | Nome da marca (parcial, sem diferença de maiúsculas) |
| **Titular** | Nome do titular ou razão social (parcial) |
| **Classe Nice** | Número da classe (ex: `35`, `42`, `09`) |
| **Despacho** | Código ou nome do despacho (ex: `Concessão`, `IPAS158`, `oposição`) |
| **Apresentação** | Tipo da marca: Nominativa, Mista, Figurativa, Tridimensional |
| **Natureza** | Natureza: Produtos e/ou Serviço, Coletiva, Certificação |
| **Nº Processo** | Número exato ou parcial do processo |

Todos os filtros de texto funcionam como busca parcial (contém) por padrão. Pressione **Enter** em qualquer campo ou clique em **Pesquisar** para executar.

### 3.3 Modo Regex

Marque a opção **Usar Regex** para ativar expressões regulares nos campos de texto.

Exemplos:
- `^CAFE` — marcas que começam com "CAFE"
- `CAFE|COFFEE` — marcas que contêm "CAFE" ou "COFFEE"
- `\bNATURA\b` — palavra exata "NATURA"
- `^[0-9]{9}$` — número de processo com exatamente 9 dígitos

### 3.4 Botões de ação

- **Pesquisar** — aplica os filtros sobre os processos carregados
- **Limpar Filtros** — apaga todos os campos de filtro
- **Mostrar Todos** — remove filtros e exibe todos os processos carregados

### 3.5 Tabela de resultados

Colunas exibidas: **Processo, Nome da Marca, Titular, Classes, Despacho, Apresentação, Depósito, Concessão, Vigência**

**Cores por tipo de despacho:**

| Cor | Significado |
|---|---|
| Verde claro | Concessão / Deferido |
| Vermelho claro | Indeferido / Extinção / Caducidade |
| Amarelo claro | Arquivado |
| Azul claro | Oposição |
| Cinza claro | Publicação |

- Clique no **cabeçalho de uma coluna** para ordenar (clique novamente para inverter)
- **Duplo clique** em uma linha abre os detalhes completos do processo
- **Botão direito** em uma linha abre o menu de contexto

### 3.6 Menu de contexto (botão direito)

- **Copiar número do processo** — copia o número para a área de transferência
- **Copiar nome da marca** — copia o nome da marca
- **Copiar linha completa** — copia todos os campos separados por tabulação (útil para colar no Excel)
- **Ver detalhes** — abre o dialog de detalhes

### 3.7 Dialog de detalhes

Exibe todas as informações do processo: número, datas, titular(es), despachos, classes Nice com especificações, procurador e apresentação/natureza da marca.

---

## 4. Aba: Pesquisa Online

Busca diretamente no portal **busca.inpi.gov.br**. Requer conexão com a internet.

### 4.1 Parâmetros de busca

| Campo | Descrição |
|---|---|
| **Nome** | Nome ou parte do nome da marca |
| **Titular** | Nome do titular |
| **Nº Processo** | Número do processo |
| **Classe** | Classe Nice (ex: `35`) |
| **Página** | Número da página de resultados (começa em 1) |

Informe ao menos um parâmetro antes de buscar. Pressione **Enter** em qualquer campo ou clique em **Buscar Online**.

### 4.2 Navegar entre páginas

Após uma busca bem-sucedida, o botão **Próxima Página →** fica disponível e avança automaticamente para a página seguinte com os mesmos parâmetros.

Também é possível alterar manualmente o campo **Página** e clicar em **Buscar Online**.

---

## 5. Aba: Monitoramento

Permite salvar termos de interesse e verificar se aparecem na RPI carregada. Os dados são persistidos em banco SQLite (`app/data/monitor.db`).

> **Requisito:** É necessário ter um XML carregado na aba "Pesquisa RPI" antes de verificar marcas.

### 5.1 Adicionar monitoramento

1. Clique em **+ Adicionar**
2. Preencha o formulário:
   - **Termo**: texto a monitorar
   - **Tipo de busca**: `nome` (busca no nome da marca), `titular` (busca no titular), `regex` (expressão regular no nome)
   - **Observação**: campo livre para anotações
   - **Ativo**: desmarcado = monitoramento pausado (não verificado em "Verificar Todas")
3. Clique em **OK**

### 5.2 Verificar ocorrências

- **Verificar Selecionada** — verifica apenas o monitoramento atualmente selecionado na lista
- **Verificar Todas** — verifica todas as marcas ativas em sequência

Os resultados são exibidos na tabela à direita e salvos no histórico.

### 5.3 Ver resultados

Clique em um monitoramento na lista para ver os processos encontrados na última verificação. Duplo clique em um processo abre os detalhes.

### 5.4 Editar monitoramento

Selecione um item na lista e clique em **Editar** para alterar termo, tipo, observação ou status ativo/inativo.

### 5.5 Remover monitoramento

Selecione um item e clique em **Remover**. Uma confirmação é solicitada. O histórico associado também é apagado.

### 5.6 Indicadores na lista

Cada item exibe: `✓ [tipo] termo` (ativo) ou `✗ [tipo] termo` (inativo).

---

## 6. Dicas e Atalhos

| Ação | Como fazer |
|---|---|
| Abrir XML | `Ctrl+O` ou menu Arquivo → Abrir XML |
| Pesquisar | `Enter` em qualquer campo de filtro |
| Sair | `Ctrl+Q` ou menu Arquivo → Sair |
| Ver detalhes | Duplo clique na linha da tabela |
| Copiar dados | Botão direito → opção de cópia |
| Ordenar tabela | Clique no cabeçalho da coluna |
| Múltiplos critérios | Preencha vários filtros ao mesmo tempo (todos são aplicados juntos) |

---

## 7. Solução de Problemas

### Aplicativo não abre

Verifique o log de erros:

```bash
cat "/home/user_1/ai/Marcas Projeto/app/logs/erro.log"
```

Causas comuns:
- Dependências não instaladas: rode `uv sync` dentro de `app/`
- `uv` não encontrado: o script usa `/home/user_1/.local/bin/uv` como caminho fixo

### XML demora para carregar

É normal para arquivos grandes. A RPI 2878 tem 36.501 processos — o carregamento pode levar 5–15 segundos dependendo do hardware. Uma barra de progresso indica o andamento.

### Busca online não retorna resultados

- Verifique sua conexão com a internet
- O portal do INPI pode estar temporariamente indisponível
- Tente novamente em alguns minutos

### Busca online retorna erro de conexão

O portal `busca.inpi.gov.br` pode bloquear requisições automáticas. O erro é exibido em um dialog. O log em `app/logs/erro.log` pode conter detalhes adicionais.

### Monitoramento não encontra nada

- Confirme que um XML foi carregado na aba "Pesquisa RPI"
- A verificação usa apenas os dados do XML carregado, não o portal online
- Para busca mais ampla, use a aba "Pesquisa Online"
