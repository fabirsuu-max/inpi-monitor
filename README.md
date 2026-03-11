# INPI Monitor

Ferramenta desktop para pesquisar e monitorar marcas registradas no [INPI](https://www.gov.br/inpi) (Instituto Nacional da Propriedade Industrial).

## Funcionalidades

- Pesquisar processos no arquivo XML da Revista da Propriedade Industrial (RPI)
- Buscar marcas diretamente no portal online do INPI
- Monitorar termos de interesse e verificar ocorrências na RPI

## Como iniciar

```bash
./iniciar.sh
```

Para carregar um XML automaticamente:

```bash
./iniciar.sh RM2878.xml
```

## Documentação

Consulte o [MANUAL.md](MANUAL.md) para instruções detalhadas de uso.

## Requisitos

- Python 3.x (gerenciado via [uv](https://github.com/astral-sh/uv) no diretório `app/`)
- Arquivo XML da RPI (opcional, para pesquisa local)
