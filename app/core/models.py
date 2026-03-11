from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClasseNice:
    codigo: str
    especificacao: str
    status: str


@dataclass
class Titular:
    nome: str
    pais: str
    uf: str


@dataclass
class Processo:
    numero: str
    data_deposito: str = ""
    data_concessao: str = ""
    data_vigencia: str = ""
    despacho_codigo: str = ""
    despacho_nome: str = ""
    titulares: list[Titular] = field(default_factory=list)
    marca_nome: str = ""
    marca_apresentacao: str = ""
    marca_natureza: str = ""
    classes_nice: list[ClasseNice] = field(default_factory=list)
    procurador: str = ""

    @property
    def titular_principal(self) -> str:
        if self.titulares:
            return self.titulares[0].nome
        return ""

    @property
    def classes_nice_str(self) -> str:
        return ", ".join(c.codigo for c in self.classes_nice)

    @property
    def especificacoes_str(self) -> str:
        return " | ".join(c.especificacao for c in self.classes_nice)


@dataclass
class MarcaMonitorada:
    id: Optional[int]
    termo: str
    tipo_busca: str  # "nome", "titular", "regex"
    observacao: str = ""
    ativo: bool = True
