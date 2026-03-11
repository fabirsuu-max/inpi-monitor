import requests
from bs4 import BeautifulSoup
from .models import Processo, Titular, ClasseNice

BASE_URL = "https://busca.inpi.gov.br/pePI/servlet/MarcasServletController"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def buscar_marcas(
    nome: str = "",
    titular: str = "",
    numero: str = "",
    classe: str = "",
    pagina: int = 1,
    timeout: int = 15,
) -> tuple[list[Processo], int]:
    """
    Search INPI online.
    Returns (list of Processo, total_results).
    """
    params = {
        "Action": "SearchBasica",
        "Tipo": "",
        "Txt_Numero": numero,
        "Txt_Titular": titular,
        "Txt_Marca": nome,
        "classe": "",
        "Txt_Classe": classe,
        "Txt_Estado": "",
        "Txt_Pais": "",
        "pagina": pagina,
    }

    try:
        resp = SESSION.get(BASE_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        return _parse_results(resp.text)
    except requests.RequestException as e:
        raise ConnectionError(f"Erro ao conectar ao INPI: {e}")


def _parse_results(html: str) -> tuple[list[Processo], int]:
    soup = BeautifulSoup(html, "lxml")
    processos = []
    total = 0

    # Try to extract total count
    total_tag = soup.find(string=lambda t: t and "resultado" in t.lower() and "encontrado" in t.lower())
    if total_tag:
        import re
        nums = re.findall(r"\d+", total_tag)
        if nums:
            total = int(nums[0])

    # Find results table
    table = soup.find("table", {"class": lambda c: c and "resultado" in c.lower()})
    if table is None:
        table = soup.find("table", id=lambda i: i and "resultado" in (i or "").lower())
    if table is None:
        # Try to find any table with process data
        tables = soup.find_all("table")
        for t in tables:
            if t.find("td", string=lambda s: s and len(s) >= 7 and s.strip().isdigit()):
                table = t
                break

    if table is None:
        return processos, total

    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        texts = [c.get_text(strip=True) for c in cols]

        p = Processo(numero=texts[0] if texts else "")
        if len(texts) > 1:
            p.marca_nome = texts[1]
        if len(texts) > 2:
            p.titulares = [Titular(nome=texts[2], pais="", uf="")]
        if len(texts) > 3:
            p.despacho_nome = texts[3]
        if len(texts) > 4:
            p.classes_nice = [ClasseNice(codigo=texts[4], especificacao="", status="")]

        processos.append(p)

    if not total:
        total = len(processos)

    return processos, total


def buscar_detalhe(numero_processo: str, timeout: int = 15) -> dict:
    """Fetch detail page for a specific process number."""
    params = {
        "Action": "Visualizar",
        "Txt_Numero": numero_processo,
    }
    try:
        resp = SESSION.get(BASE_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        return _parse_detalhe(resp.text)
    except requests.RequestException as e:
        raise ConnectionError(f"Erro ao buscar detalhes: {e}")


def _parse_detalhe(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    dados = {}

    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).rstrip(":")
            val = cols[1].get_text(strip=True)
            if key:
                dados[key] = val

    return dados
