import re
from lxml import etree
from .models import Processo, Titular, ClasseNice


def parse_xml(filepath: str, progress_callback=None) -> list[Processo]:
    """Parse RPI XML file returning list of Processo."""
    processos = []
    total = 0

    # Count total for progress
    for _, elem in etree.iterparse(filepath, events=("end",), tag="processo"):
        total += 1
        elem.clear()

    count = 0
    context = etree.iterparse(filepath, events=("end",), tag="processo")

    for _, elem in context:
        processo = _parse_processo(elem)
        processos.append(processo)
        elem.clear()
        count += 1
        if progress_callback and count % 500 == 0:
            progress_callback(count, total)

    if progress_callback:
        progress_callback(total, total)

    return processos


def _parse_processo(elem) -> Processo:
    p = Processo(numero=elem.get("numero", ""))
    p.data_deposito = elem.get("data-deposito", "")
    p.data_concessao = elem.get("data-concessao", "")
    p.data_vigencia = elem.get("data-vigencia", "")

    despachos = elem.find("despachos")
    if despachos is not None:
        despacho = despachos.find("despacho")
        if despacho is not None:
            p.despacho_codigo = despacho.get("codigo", "")
            p.despacho_nome = despacho.get("nome", "")

    titulares_elem = elem.find("titulares")
    if titulares_elem is not None:
        for t in titulares_elem.findall("titular"):
            p.titulares.append(Titular(
                nome=t.get("nome-razao-social", ""),
                pais=t.get("pais", ""),
                uf=t.get("uf", ""),
            ))

    marca = elem.find("marca")
    if marca is not None:
        p.marca_apresentacao = marca.get("apresentacao", "")
        p.marca_natureza = marca.get("natureza", "")
        nome_elem = marca.find("nome")
        if nome_elem is not None and nome_elem.text:
            p.marca_nome = nome_elem.text.strip()

    lista_nice = elem.find("lista-classe-nice")
    if lista_nice is not None:
        for cn in lista_nice.findall("classe-nice"):
            espec_elem = cn.find("especificacao")
            status_elem = cn.find("status")
            p.classes_nice.append(ClasseNice(
                codigo=cn.get("codigo", ""),
                especificacao=espec_elem.text.strip() if espec_elem is not None and espec_elem.text else "",
                status=status_elem.text.strip() if status_elem is not None and status_elem.text else "",
            ))

    proc_elem = elem.find("procurador")
    if proc_elem is not None and proc_elem.text:
        p.procurador = proc_elem.text.strip()

    return p


def _build_match_fn(value_str: str, use_regex: bool):
    """
    Build a match function for a field value.
    Supports OR / AND operators between terms (case-insensitive keywords).
    With use_regex=True the whole value is compiled as a regex (OR/AND ignored).
    """
    if use_regex:
        try:
            pattern = re.compile(value_str, re.IGNORECASE)
            return lambda s, p=pattern: bool(p.search(s))
        except re.error:
            pass  # fall through to literal match

    if re.search(r'\bOR\b', value_str, re.IGNORECASE):
        tokens = [t.strip() for t in re.split(r'\bOR\b', value_str, flags=re.IGNORECASE) if t.strip()]
        return lambda s, toks=tokens: any(t.lower() in s.lower() for t in toks)

    if re.search(r'\bAND\b', value_str, re.IGNORECASE):
        tokens = [t.strip() for t in re.split(r'\bAND\b', value_str, flags=re.IGNORECASE) if t.strip()]
        return lambda s, toks=tokens: all(t.lower() in s.lower() for t in toks)

    return lambda s, v=value_str: v.lower() in s.lower()


def filtrar(processos: list[Processo], **kwargs) -> list[Processo]:
    """
    Filter list of Processo by criteria (all fields combined with AND).
    Within each field supports OR / AND operators between terms.
    Supports: nome, titular, classe_nice, despacho_codigo, despacho_nome,
              apresentacao, natureza, numero, use_regex (bool)
    """
    use_regex = kwargs.pop("use_regex", False)
    results = processos

    for field, value in kwargs.items():
        if not value:
            continue
        value_str = str(value).strip()
        if not value_str:
            continue

        match_fn = _build_match_fn(value_str, use_regex)

        if field == "nome":
            results = [p for p in results if match_fn(p.marca_nome)]
        elif field == "titular":
            results = [p for p in results if any(match_fn(t.nome) for t in p.titulares)]
        elif field == "classe_nice":
            results = [p for p in results if any(match_fn(c.codigo) for c in p.classes_nice)]
        elif field == "despacho_codigo":
            results = [p for p in results if match_fn(p.despacho_codigo)]
        elif field == "despacho_nome":
            results = [p for p in results if match_fn(p.despacho_nome)]
        elif field == "apresentacao":
            results = [p for p in results if match_fn(p.marca_apresentacao)]
        elif field == "natureza":
            results = [p for p in results if match_fn(p.marca_natureza)]
        elif field == "numero":
            results = [p for p in results if match_fn(p.numero)]

    return results
