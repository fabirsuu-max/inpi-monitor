import re
import requests
from bs4 import BeautifulSoup
from .models import Processo, Titular, ClasseNice

BASE_URL = "https://busca.inpi.gov.br/pePI"
SEARCH_URL = BASE_URL + "/servlet/MarcasServletController"
LOGIN_URL = BASE_URL + "/servlet/LoginController"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
_logged_in = False


def _ensure_login(timeout: int = 15) -> None:
    """Login anonymously to the INPI pePI portal to get a valid session."""
    global _logged_in
    if _logged_in:
        return
    SESSION.post(
        LOGIN_URL,
        data={"T_Login": "", "T_Senha": "", "action": "login"},
        timeout=timeout,
    )
    _logged_in = True


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
    Returns (list of Processo, total_pages).
    """
    try:
        _ensure_login(timeout)

        if pagina > 1:
            # Navigate to a specific page (requires an active search in session)
            resp = SESSION.get(
                SEARCH_URL,
                params={"Action": "nextPageMarca", "page": pagina},
                timeout=timeout,
            )
            resp.raise_for_status()
            return _parse_results(resp.text)

        if numero:
            referer = BASE_URL + "/jsp/marcas/Pesquisa_num_processo.jsp"
            data = {
                "Action": "searchMarca",
                "tipoPesquisa": "BY_NUM_PROC",
                "NumPedido": numero,
                "NumGRU": "",
                "NumProtocolo": "",
                "NumInscricaoInternacional": "",
            }
        elif titular:
            # Step 1: get list of matching titulars
            referer = BASE_URL + "/jsp/marcas/Pesquisa_titular.jsp"
            step1 = SESSION.post(
                SEARCH_URL,
                data={
                    "Action": "searchNome",
                    "tipoPesquisa": "BY_CNPJ_NOME",
                    "nomeTitular": titular,
                    "cpf_cgc_numINPI": "",
                    "precisao": "aproximacao",
                    "registerPerPage": "20",
                },
                timeout=timeout,
                headers={"Referer": referer},
            )
            step1.raise_for_status()
            # Step 2: follow the best match link (pos=0) to get their marks
            soup1 = BeautifulSoup(step1.text, "lxml")
            titular_link = soup1.find("a", href=re.compile(r"BY_CNPJ_NOME.*pos=0"))
            if titular_link:
                href = titular_link["href"]
                if not href.startswith("http"):
                    href = "https://busca.inpi.gov.br" + href
                resp = SESSION.get(href, timeout=timeout)
                resp.raise_for_status()
                return _parse_results(resp.text)
            # No titular found
            return [], 0
        else:
            referer = BASE_URL + "/jsp/marcas/Pesquisa_classe_basica.jsp"
            data = {
                "Action": "searchMarca",
                "tipoPesquisa": "BY_MARCA_CLASSIF_BASICA",
                "marca": nome,
                "classeInter": classe,
                "buscaExata": "nao",
                "registerPerPage": "20",
            }

        resp = SESSION.post(
            SEARCH_URL,
            data=data,
            timeout=timeout,
            headers={"Referer": referer},
        )
        resp.raise_for_status()
        return _parse_results(resp.text)

    except requests.RequestException as e:
        raise ConnectionError(f"Erro ao conectar ao INPI: {e}")


def _parse_results(html: str) -> tuple[list[Processo], int]:
    soup = BeautifulSoup(html, "lxml")
    processos = []
    total_pages = 1

    # Results are in the 3rd table (index 2)
    tables = soup.find_all("table")
    if len(tables) < 3:
        return processos, total_pages

    table = tables[2]
    rows = table.find_all("tr")

    for row in rows[1:]:  # skip header row
        cols = row.find_all("td")
        if len(cols) < 6:
            # Check if this is the pagination row
            text = row.get_text()
            if "Páginas de Resultados" in text:
                nums = re.findall(r"\.\.\.(\d+)", text) or re.findall(r"page=(\d+)", text)
                if nums:
                    total_pages = max(int(n) for n in nums)
            continue

        texts = [c.get_text(strip=True) for c in cols]
        # Columns: 0=Número, 1=Prioridade, 2=(img), 3=Marca, 4=(img), 5=Situação, 6=Titular, 7=Classe
        numero = texts[0]
        if not numero or not numero[0].isdigit():
            continue  # skip non-data rows (header, alto renome labels, etc.)

        p = Processo(numero=numero)
        p.data_deposito = texts[1] if len(texts) > 1 else ""
        p.marca_nome = texts[3] if len(texts) > 3 else ""
        p.despacho_nome = texts[5] if len(texts) > 5 else ""
        if len(texts) > 6 and texts[6]:
            p.titulares = [Titular(nome=texts[6], pais="", uf="")]
        if len(texts) > 7 and texts[7]:
            # Format: "25 : 20" → extract code
            classe_str = texts[7].split(":")[0].strip()
            p.classes_nice = [ClasseNice(codigo=classe_str, especificacao="", status="")]

        processos.append(p)

    if not total_pages:
        total_pages = 1

    return processos, total_pages


def buscar_detalhe(numero_processo: str, timeout: int = 15) -> dict:
    """Fetch detail page for a specific process number."""
    try:
        _ensure_login(timeout)
        # Search by process number to get the detail link
        data = {
            "Action": "searchMarca",
            "tipoPesquisa": "BY_NUM_PROC",
            "NumPedido": numero_processo,
            "NumGRU": "",
            "NumProtocolo": "",
            "NumInscricaoInternacional": "",
        }
        resp = SESSION.post(
            SEARCH_URL,
            data=data,
            timeout=timeout,
            headers={"Referer": BASE_URL + "/jsp/marcas/Pesquisa_num_processo.jsp"},
        )
        resp.raise_for_status()

        # Try to find a detail link in the results
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.find_all("a", href=re.compile(r"detalhe|visualizar|processo", re.I))
        if links:
            href = links[0].get("href", "")
            if not href.startswith("http"):
                href = "https://busca.inpi.gov.br" + href
            r2 = SESSION.get(href, timeout=timeout)
            r2.raise_for_status()
            return _parse_detalhe(r2.text)

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
