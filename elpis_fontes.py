# -*- coding: utf-8 -*-
# Élpis — motores de busca de vagas (v21)
# © 2026 INOVHIA Desenvolvimento Tecnológico. Todos os direitos reservados.
# Contato: Jeferson Alexandre — +55 31 99484-8343
# É proibida a reprodução, total ou parcial, sem autorização prévia.
from __future__ import annotations

import json
import os
import re
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutTimeout
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from html import unescape
from typing import Callable
from urllib.parse import parse_qsl, quote, quote_plus, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

try:  # opcional: melhora muito a taxa de sucesso (impersonação de TLS do Chrome)
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover
    curl_requests = None

UTC = timezone.utc
MIN_DATA = datetime(1970, 1, 1, tzinfo=UTC)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}
_tl = threading.local()

# ======================================================================
# Diagnóstico: cada fonte registra "notas" (HTTP, URL, o que deu errado)
# ======================================================================
def nota(msg) -> None:
    lst = getattr(_tl, "notas", None)
    if lst is not None and len(lst) < 14:
        lst.append(str(msg)[:220])


# ======================================================================
# HTTP (sessão por thread, com fallback para requests puro)
# ======================================================================
def _sessao(forcar_requests=False):
    chave = "s_req" if forcar_requests else "s"
    s = getattr(_tl, chave, None)
    if s is None:
        if curl_requests is not None and not forcar_requests:
            s = curl_requests.Session(impersonate="chrome")
        else:
            s = requests.Session()
        setattr(_tl, chave, s)
    return s


def obter(url, params=None, headers=None, timeout=10, metodo="GET", json_body=None):
    h = dict(HEADERS)
    h.update(headers or {})
    r, falha = None, None
    for forcar in ((False, True) if curl_requests is not None else (True,)):
        try:
            r = _sessao(forcar).request(metodo, url, params=params, headers=h, json=json_body, timeout=timeout)
            break
        except Exception as e:  # tenta o outro cliente HTTP
            falha = e
    if r is None:
        nota(f"sem resposta de {urlparse(url).netloc}: {type(falha).__name__}")
        raise falha
    p = urlparse(url)
    nota(f"HTTP {r.status_code} {p.netloc}{p.path[:42]} ({len(r.content) // 1024} KB)")
    return r


def obter_json(url, **kw):
    r = obter(url, **kw)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    try:
        return r.json()
    except Exception:
        raise RuntimeError("resposta não é JSON (rota mudou ou o site bloqueou)")


def obter_html(url, **kw):
    r = obter(url, **kw)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    return BeautifulSoup(r.text, "html.parser")


def paralelo(fn: Callable, itens: list, workers: int = 6) -> list:
    """Executa fn(item) em paralelo, mantendo as notas de diagnóstico.
    Levanta erro só se TODAS falharem."""
    pai = getattr(_tl, "notas", None)

    def run(i):
        _tl.notas = pai
        try:
            return fn(i)
        finally:
            _tl.notas = None

    ok, erros = [], []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(itens)))) as p:
        for f in [p.submit(run, i) for i in itens]:
            try:
                ok.append(f.result())
            except Exception as e:
                erros.append(e)
                nota(f"parte falhou: {str(e)[:70]}")
    if not ok and erros:
        raise erros[0]
    return ok


def verificar_rede() -> dict:
    """Teste rápido de conectividade (em paralelo). Ajuda a separar 'sem internet/proxy' de 'site mudou'."""
    alvos = {"Internet (google.com)": "https://www.google.com/generate_204",
             "Sólides": "https://vagas.solides.com.br/",
             "Jobicy": "https://jobicy.com/api/v2/remote-jobs?count=1"}

    def um(item):
        nome, url = item
        try:
            return nome, f"HTTP {obter(url, timeout=6).status_code}"
        except Exception as e:
            return nome, f"{type(e).__name__}: {str(e)[:90]}"

    with ThreadPoolExecutor(max_workers=3) as pool:
        res = dict(pool.map(um, alvos.items()))
    proxies = [k for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy") if os.getenv(k)]
    res["Proxy no ambiente"] = ", ".join(proxies) if proxies else "nenhum"
    return res


# ======================================================================
# Texto, datas, links
# ======================================================================
def norm(t) -> str:
    return unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()


def slug(t) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(t)).strip("-")


def limpa(t) -> str:
    if t is None:
        return ""
    s = str(t)
    if s.lower() in {"nan", "none", "nat", "null"}:
        return ""
    s = re.sub(r"<[^>]+>", " ", unescape(s))
    return re.sub(r"\s+", " ", s).strip()


def eh_http(u) -> bool:
    try:
        return urlparse(str(u)).scheme in ("http", "https") and bool(urlparse(str(u)).netloc)
    except Exception:
        return False


_TRACK = {"trackingid", "refid", "trk", "trkemail", "position", "pagenum", "gclid", "fbclid", "ref", "from", "src", "origin"}


def limpar_link(u: str) -> str:
    p = urlparse(u.strip())
    if "linkedin.com" in p.netloc:
        return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith("utm") and k.lower() not in _TRACK]
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), ""))


_REL = (
    (r"(\d+)\s*\+?\s*(?:minutos?|minutes?|mins?)\b", "minutes", 1),
    (r"(\d+)\s*\+?\s*(?:horas?|hours?|hrs?)\b", "hours", 1),
    (r"(\d+)\s*\+?\s*(?:dias?|days?)\b", "days", 1),
    (r"(\d+)\s*\+?\s*(?:semanas?|weeks?)\b", "days", 7),
    (r"(\d+)\s*\+?\s*(?:mes|meses|months?)\b", "days", 30),
)


def parse_data(v):
    """Devolve datetime com fuso ou None (nunca uma data falsa)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if v != v:
            return None
        x = float(v)
        x = x / 1000 if x > 1e12 else x
        return datetime.fromtimestamp(x, UTC) if x > 1e8 else None
    s = str(v).strip()
    if s.lower() in {"", "nan", "nat", "none", "null"}:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=UTC)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day, tzinfo=UTC)
    t = s.lower()
    try:
        d = datetime.fromisoformat(t.replace("z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except ValueError:
        pass
    for f in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(t[:10], f).replace(tzinfo=UTC)
        except ValueError:
            pass
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except Exception:
        pass
    n = norm(t)
    agora = datetime.now(UTC)
    if re.search(r"\b(hoje|today|agora|just now)\b", n):
        return agora
    if re.search(r"\b(ontem|yesterday)\b", n):
        return agora - timedelta(days=1)
    for padrao, unidade, mult in _REL:
        m = re.search(padrao, n)
        if m:
            return agora - timedelta(**{unidade: int(m.group(1)) * mult})
    return None


def idade_dias(d):
    if not isinstance(d, datetime) or d <= MIN_DATA:
        return None
    return max(0, (datetime.now(UTC) - d).days)


# ======================================================================
# Relevância (genérica: sinônimos PT/EN + radical, sem acento)
# ======================================================================
SINONIMOS = [
    ("auditor", "auditora", "auditoria", "auditores", "auditorias", "audit", "auditing"),
    ("interno", "interna", "internos", "internas", "internal"),
    ("desenvolvedor", "desenvolvedora", "developer", "programador", "programmer"),
    ("contador", "contadora", "contabil", "contabilidade", "accountant", "accounting"),
    ("financeiro", "financeira", "financas", "finance", "financial"),
    ("controller", "controladoria", "controllership"),
    ("juridico", "advogado", "advogada", "legal", "lawyer", "counsel"),
    ("dados", "data"),
    ("engenheiro", "engenheira", "engenharia", "engineer", "engineering"),
    ("vendas", "vendedor", "vendedora", "sales", "comercial"),
    ("compras", "comprador", "procurement", "purchasing", "suprimentos"),
    ("seguranca", "security"),
    ("qualidade", "quality"),
    ("projetos", "projeto", "project"),
    ("produto", "product"),
    ("risco", "riscos", "risk"),
    ("fiscal", "tributario", "tax"),
    ("logistica", "logistics"),
    ("rh", "recursos", "people", "talent", "talentos"),
]
IGNORAR = {"qualquer", "analista", "especialista", "coordenador", "gerente", "diretor", "vp", "de", "da", "do",
           "das", "dos", "e", "em", "para", "a", "o", "na", "no", "com", "pleno", "senior", "junior", "sr", "jr"}


class Matcher:
    def __init__(self, termo: str):
        self.grupos: list[tuple[str, ...]] = []
        for t in re.findall(r"[a-z0-9]+", norm(termo)):
            if t in IGNORAR:
                continue
            alias = next((g for g in SINONIMOS if t in g or t.rstrip("s") in g), None)
            self.grupos.append(alias or ((t[:-1] if len(t) >= 7 else t),))

    def score(self, texto) -> int:
        if not self.grupos:
            return 1
        palavras = re.findall(r"[a-z0-9]+", norm(texto))
        ok = sum(1 for g in self.grupos
                 if any(w == a or (len(a) >= 4 and w.startswith(a)) for w in palavras for a in g))
        if ok == len(self.grupos):
            return 140 + 20 * ok
        return 45 if ok else 0


@lru_cache(maxsize=128)
def matcher(termo: str) -> Matcher:
    return Matcher(termo)


def relevancia_vaga(titulo, termo) -> int:
    return matcher(termo or "").score(titulo)


_NIVEIS = {
    "especialista": ["especialista", "senior", "specialist"],
    "analista": ["analista", "analyst"],
    "coordenador": ["coordenador", "coordenacao", "coordinator"],
    "gerente": ["gerente", "manager"],
    "diretor": ["diretor", "director"],
    "vp": ["vp", "vice president", "vice-presidente"],
}


def pontuar_nivel(titulo, nivel) -> int:
    if not nivel or nivel == "(qualquer)":
        return 0
    t, n = norm(titulo), norm(nivel)
    return 25 if any(a in t for a in _NIVEIS.get(n, [n])) else 0


_GENERICOS = {"", "brasil", "brazil", "global", "qualquer", "mundo", "remoto", "remote", "todo o brasil",
              "nao informado", "100% remoto", "worldwide", "anywhere"}


def local_generico(local) -> bool:
    return norm(local).strip(" -,.") in _GENERICOS


def local_ok(local_vaga, local_busca) -> bool:
    if local_generico(local_busca):
        return True
    lb, lv = norm(local_busca).strip(), norm(local_vaga)
    return lb in lv or any(k in lv for k in ("remot", "anywhere", "worldwide", "home office"))


def eh_remoto(v) -> bool:
    txt = norm(f"{v.get('local', '')} {v.get('titulo', '')} {v.get('resumo', '')[:200]}")
    return any(k in txt for k in ("remot", "home office", "anywhere", "worldwide", "teletrabalho"))


def nova_vaga(titulo, empresa, local, data, link, origem, resumo="", relevancia=0, **extra):
    titulo, link = limpa(titulo), str(link or "").strip()
    if not titulo or not eh_http(link):
        return None
    v = {
        "titulo": titulo,
        "empresa": limpa(empresa) or "Empresa não informada",
        "local": limpa(local) or "Não informado",
        "data": parse_data(data),
        "link": limpar_link(link),
        "origem": origem,
        "resumo": limpa(resumo)[:400],
        "relevancia": relevancia,
    }
    v.update(extra)
    return v


# ======================================================================
# Cache TTL (processo inteiro; vale para todas as sessões do Streamlit)
# ======================================================================
_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()


def cache_get(chave, ttl=900):
    with _CACHE_LOCK:
        item = _CACHE.get(chave)
        return item[1] if item and time.time() - item[0] < ttl else None


def cache_set(chave, valor):
    with _CACHE_LOCK:
        _CACHE[chave] = (time.time(), valor)
        if len(_CACHE) > 400:
            for k in sorted(_CACHE, key=lambda k: _CACHE[k][0])[:100]:
                _CACHE.pop(k, None)


# ======================================================================
# Registro de fontes + execução paralela com prazo global
# ======================================================================
@dataclass
class Fonte:
    nome: str
    grupo: str
    fn: Callable
    exige: tuple = ()
    beta: bool = False


@dataclass
class Resultado:
    nome: str
    grupo: str
    itens: list = field(default_factory=list)
    erro: str | None = None
    ms: int = 0
    notas: list = field(default_factory=list)
    timeout: bool = False

    @property
    def status(self) -> str:
        if self.timeout:
            return "timeout"
        if self.erro:
            return "erro"
        return "ok" if self.itens else "vazio"


FONTES: dict[str, Fonte] = {}


def fonte(nome, grupo, exige=(), beta=False):
    def deco(fn):
        FONTES[nome] = Fonte(nome, grupo, fn, tuple(exige), beta)
        return fn
    return deco


def disponiveis() -> list[str]:
    return [n for n, f in FONTES.items() if all(os.getenv(k) for k in f.exige)]


def indisponiveis() -> dict[str, tuple]:
    return {n: f.exige for n, f in FONTES.items() if not all(os.getenv(k) for k in f.exige)}


def _cronometrar(nome, termo, local) -> Resultado:
    f = FONTES[nome]
    chave = (nome, norm(termo), norm(local))
    em_cache = cache_get(chave)
    if em_cache is not None:
        return Resultado(nome, f.grupo, [dict(v) for v in em_cache], None, 0, ["resultado em cache (15 min)"])
    _tl.notas = []
    t0, itens, erro = time.perf_counter(), [], None
    try:
        itens = f.fn(termo, local) or []
    except Exception as e:
        erro = f"{type(e).__name__}: {str(e)[:140]}"
    for v in itens:
        v["grupo"] = f.grupo
        v["origem"] = v.get("origem") or nome
    if itens and not erro:
        cache_set(chave, [dict(v) for v in itens])
    r = Resultado(nome, f.grupo, itens, erro, int((time.perf_counter() - t0) * 1000), list(_tl.notas))
    _tl.notas = None
    return r


def executar(nomes, termo, local, prazo=20):
    """Gerador: entrega cada Resultado assim que a fonte termina.
    Ao estourar o prazo, as fontes pendentes viram 'timeout' (não travam a tela)."""
    nomes = [n for n in nomes if n in FONTES]
    if not nomes:
        return
    pool = ThreadPoolExecutor(max_workers=min(24, len(nomes)))
    futs = {pool.submit(_cronometrar, n, termo, local): n for n in nomes}
    prontos = set()
    try:
        for f in as_completed(futs, timeout=prazo):
            r = f.result()
            prontos.add(r.nome)
            yield r
    except FutTimeout:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    for n in nomes:
        if n not in prontos:
            yield Resultado(n, FONTES[n].grupo, [], "tempo esgotado", int(prazo * 1000),
                            [f"sem resposta em {prazo}s"], timeout=True)


def consolidar(vagas, nivel="(qualquer)", limite=60, min_exatas=5):
    """Remove duplicatas (link e título+empresa+cidade), ordena por relevância e data."""
    por_link, por_chave = set(), {}
    for v in vagas:
        if not v.get("titulo") or not eh_http(v.get("link")) or v["link"] in por_link:
            continue
        por_link.add(v["link"])
        v["nivel_relevancia"] = pontuar_nivel(v["titulo"], nivel)
        cidade = re.split(r"[,\-/(]", v.get("local", ""))[0]
        k = (slug(v["titulo"]), slug(v.get("empresa", "")), slug(cidade))
        atual = por_chave.get(k)
        if atual is None:
            v["tambem"] = []
            por_chave[k] = v
            continue
        melhor, outro = (v, atual) if (v.get("data") is not None, len(v.get("resumo", ""))) > \
                                      (atual.get("data") is not None, len(atual.get("resumo", ""))) else (atual, v)
        melhor["tambem"] = sorted(set(melhor.get("tambem", []) + outro.get("tambem", []) + [outro["origem"]])
                                  - {melhor["origem"]})
        por_chave[k] = melhor
    lista = list(por_chave.values())
    exatas = [v for v in lista if v.get("relevancia", 0) >= 140]
    if len(exatas) >= min_exatas:  # já há resultados suficientes com o cargo completo: some o "ruído" parcial
        lista = exatas
    lista.sort(key=lambda v: (v.get("relevancia", 0) + v.get("nivel_relevancia", 0), v.get("data") or MIN_DATA),
               reverse=True)
    return lista[:limite]


# ======================================================================
# Geocodificação: tabela offline (instantânea) + Nominatim limitado
# ======================================================================
CIDADES = {
    "rio branco": (-9.9747, -67.81, "AC"), "maceio": (-9.6658, -35.7353, "AL"), "macapa": (0.0349, -51.0664, "AP"),
    "manaus": (-3.119, -60.0217, "AM"), "salvador": (-12.9777, -38.5016, "BA"), "fortaleza": (-3.7319, -38.5267, "CE"),
    "brasilia": (-15.7939, -47.8828, "DF"), "vitoria": (-20.3155, -40.3128, "ES"), "goiania": (-16.6869, -49.2648, "GO"),
    "sao luis": (-2.5307, -44.3068, "MA"), "cuiaba": (-15.6014, -56.0979, "MT"), "campo grande": (-20.4697, -54.6201, "MS"),
    "belo horizonte": (-19.9167, -43.9345, "MG"), "belem": (-1.4558, -48.4902, "PA"), "joao pessoa": (-7.1195, -34.845, "PB"),
    "curitiba": (-25.4284, -49.2733, "PR"), "recife": (-8.0476, -34.877, "PE"), "teresina": (-5.0892, -42.8019, "PI"),
    "rio de janeiro": (-22.9068, -43.1729, "RJ"), "natal": (-5.7945, -35.211, "RN"), "porto alegre": (-30.0346, -51.2177, "RS"),
    "porto velho": (-8.7612, -63.9039, "RO"), "boa vista": (2.8235, -60.6758, "RR"), "florianopolis": (-27.5954, -48.548, "SC"),
    "sao paulo": (-23.5505, -46.6333, "SP"), "aracaju": (-10.9472, -37.0731, "SE"), "palmas": (-10.184, -48.3336, "TO"),
    "campinas": (-22.9099, -47.0626, "SP"), "guarulhos": (-23.4543, -46.5337, "SP"), "santos": (-23.9608, -46.3336, "SP"),
    "uberlandia": (-18.9186, -48.2772, "MG"), "juiz de fora": (-21.7642, -43.3503, "MG"), "contagem": (-19.9319, -44.0539, "MG"),
    "betim": (-19.9668, -44.1983, "MG"), "vespasiano": (-19.6911, -43.9239, "MG"), "nova lima": (-19.9856, -43.8467, "MG"),
    "ribeirao preto": (-21.1775, -47.8103, "SP"), "osasco": (-23.5329, -46.7917, "SP"), "barueri": (-23.5106, -46.8761, "SP"),
    "joinville": (-26.3045, -48.8487, "SC"), "blumenau": (-26.9194, -49.0661, "SC"), "londrina": (-23.3045, -51.1696, "PR"),
    "maringa": (-23.4205, -51.9331, "PR"), "sorocaba": (-23.5015, -47.4526, "SP"), "niteroi": (-22.8832, -43.1034, "RJ"),
    "sao jose dos campos": (-23.2237, -45.9009, "SP"), "santo andre": (-23.6639, -46.5383, "SP"),
    "sao bernardo do campo": (-23.6914, -46.5646, "SP"), "caxias do sul": (-29.1678, -51.1794, "RS"),
    "united states": (39.8, -98.6, ""), "estados unidos": (39.8, -98.6, ""), "usa": (39.8, -98.6, ""),
    "canada": (56.1, -106.3, ""), "portugal": (39.4, -8.2, ""), "united kingdom": (54.0, -2.0, ""), "uk": (54.0, -2.0, ""),
    "germany": (51.2, 10.4, ""), "alemanha": (51.2, 10.4, ""), "spain": (40.4, -3.7, ""), "espanha": (40.4, -3.7, ""),
    "argentina": (-38.4, -63.6, ""), "mexico": (23.6, -102.5, ""), "italy": (41.9, 12.6, ""), "france": (46.2, 2.2, ""),
    "netherlands": (52.1, 5.3, ""), "ireland": (53.4, -8.2, ""), "india": (20.6, 79.0, ""),
}
UF_NOME = {"AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
           "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
           "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
           "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
           "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
           "SE": "Sergipe", "TO": "Tocantins"}
_CIDADES_ORD = sorted(CIDADES, key=len, reverse=True)


def _achar_cidade(local):
    t = norm(local)
    for nome in _CIDADES_ORD:
        if re.search(rf"(?<![a-z]){re.escape(nome)}(?![a-z])", t):
            return nome
    return None


def geo_offline(local):
    nome = _achar_cidade(local)
    return (CIDADES[nome][0], CIDADES[nome][1]) if nome else None


def cidade_uf(local):
    nome = _achar_cidade(local)
    if nome and CIDADES[nome][2]:
        return nome, CIDADES[nome][2]
    return None, None


def geo_nominatim(consulta):
    chave = ("geo", norm(consulta))
    c = cache_get(chave, ttl=86400)
    if c is not None:
        return c or None
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", timeout=4,
                         params={"q": consulta, "format": "json", "limit": 1},
                         headers={"User-Agent": "ElpisVagas/21 (INOVHIA Desenvolvimento Tecnologico)"})
        d = r.json() if r.status_code == 200 else []
        if d:
            pos = (float(d[0]["lat"]), float(d[0]["lon"]))
            cache_set(chave, pos)
            return pos
    except Exception:
        pass  # falha transitória NÃO é guardada em cache
    return None


# ======================================================================
# Extratores genéricos (sites sem API: JSON-LD / __NEXT_DATA__ / links)
# ======================================================================
def _iter_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for x in obj.values():
            yield from _iter_dicts(x)
    elif isinstance(obj, list):
        for x in obj:
            yield from _iter_dicts(x)


def _lista_json(soup, chave):
    """Procura {chave: {"data": [...]}} nos <script> JSON (ex.: initialJobList da Gupy)."""
    for bloco in soup.select("script#__NEXT_DATA__, script[type='application/json']"):
        try:
            dados = json.loads(bloco.string or bloco.get_text())
        except Exception:
            continue
        for d in _iter_dicts(dados):
            alvo = d.get(chave)
            if isinstance(alvo, dict) and isinstance(alvo.get("data"), list):
                return alvo["data"]
    return []


def extrair_generico(soup, base, origem, termo, local, hints, minimo_link=140, limite=40):
    M, out, vistos, n_ld = matcher(termo), [], set(), 0
    for sc in soup.select('script[type="application/ld+json"]'):  # 1) JobPosting estruturado
        try:
            dados = json.loads(sc.string or sc.get_text())
        except Exception:
            continue
        for d in _iter_dicts(dados):
            if d.get("@type") != "JobPosting":
                continue
            n_ld += 1
            s_ = M.score(d.get("title"))
            loc = d.get("jobLocation")
            loc = (loc[0] if isinstance(loc, list) and loc else loc) or {}
            addr = loc.get("address", {}) if isinstance(loc, dict) else {}
            local_v = ", ".join(x for x in (addr.get("addressLocality"), addr.get("addressRegion")) if x) or local
            org = d.get("hiringOrganization")
            v = nova_vaga(d.get("title"), org.get("name") if isinstance(org, dict) else org, local_v,
                          d.get("datePosted"), urljoin(base, d.get("url") or ""), origem, d.get("description"), s_)
            if v and s_ and v["link"] not in vistos:
                vistos.add(v["link"]); out.append(v)
    todos = soup.select("a[href]")
    com_padrao = [a for a in todos if any(h in a["href"] for h in hints)]
    nota(f"{len(todos)} links na página; {len(com_padrao)} com padrão de vaga; {n_ld} JSON-LD JobPosting")

    def aceitar(a, minimo):
        titulo = limpa(a.get_text(" "))
        s_ = M.score(titulo)
        link = urljoin(base, a["href"])
        if len(titulo) < 6 or s_ < minimo or link in vistos:
            return
        v = nova_vaga(titulo, "", local or "Brasil", None, link, origem, "", s_)
        if v:
            vistos.add(link); out.append(v)

    for a in com_padrao:  # 2) links com padrão conhecido
        aceitar(a, minimo_link)
    if not out:  # 3) plano B: link com ID numérico longo (típico de vaga) e cargo completo no título
        for a in todos:
            if re.search(r"\d{5,}", a["href"]):
                aceitar(a, minimo_link)
    if not out:
        ex = [a["href"][:80] for a in todos if M.score(a.get_text(" ")) >= 100][:3]
        nota("nenhuma vaga extraída" + (f"; links com o cargo: {' ; '.join(ex)}" if ex else "; nenhum link com o cargo no HTML (provável carga via JavaScript)"))
    return out[:limite]


def extrair_next_data(soup, base, origem, termo, local):
    M, out, vistos = matcher(termo), [], set()
    bloco = soup.select_one("script#__NEXT_DATA__")
    if not bloco:
        nota("página sem __NEXT_DATA__ (renderiza via JavaScript; sem dados no HTML)")
        return out
    for d in _iter_dicts(json.loads(bloco.string or bloco.get_text())):
        titulo = d.get("title") or d.get("jobTitle") or d.get("name")
        url = d.get("url") or d.get("jobUrl") or d.get("link") or d.get("applyUrl")
        if not isinstance(titulo, str) or not isinstance(url, str):
            continue
        s = M.score(titulo)
        emp = d.get("company") or d.get("companyName") or ""
        emp = emp.get("name", "") if isinstance(emp, dict) else emp
        v = nova_vaga(titulo, emp, d.get("location") or local or "Remoto", d.get("publishedAt") or d.get("createdAt"),
                      urljoin(base, url), origem, d.get("description"), s)
        if v and s and v["link"] not in vistos:
            vistos.add(v["link"]); out.append(v)
    return out


# ======================================================================
# FONTES — BRASIL
# ======================================================================
@fonte("Gupy", "Brasil")
def gupy(termo, local):
    # Busca nacional devolve poucos itens (≈12) e o filtro de cidade os descartava. O portal aceita state= e city=.
    M = matcher(termo)
    cidade_txt = "" if local_generico(local) else re.split(r"[,\-/]", local)[0].strip()
    _, uf = cidade_uf(local)
    base = f"https://portal.gupy.io/job-search/term={quote_plus(slug(termo))}"
    urls = []
    if cidade_txt and uf:
        urls.append(f"{base}&state={quote(UF_NOME[uf])}&city={quote(cidade_txt)}")
    if uf:
        urls.append(f"{base}&state={quote(UF_NOME[uf])}")
    urls.append(base)
    try:
        lotes = paralelo(lambda u: _lista_json(obter_html(u, timeout=12), "initialJobList"), urls)
    except Exception as e:
        lotes = []
        nota(f"portal público falhou: {str(e)[:70]}")
    respondeu, dados, vistos = bool(lotes), [], set()
    for lote in lotes:
        for d in lote:
            chave = d.get("jobUrl") or d.get("id")
            if chave not in vistos:
                vistos.add(chave); dados.append(d)
    falhas = []
    if not dados:  # API pública (rotas alternativas)
        hdr = {"Origin": "https://portal.gupy.io", "Referer": "https://portal.gupy.io/", "Accept": "application/json"}
        for url, p in (("https://portal.api.gupy.io/api/job", {"name": termo, "limit": 50, "offset": 0}),
                       ("https://portal.api.gupy.io/api/v1/jobs", {"name": termo, "limit": 50})):
            try:
                j = obter_json(url, params=p, headers=hdr, timeout=10)
                dados = j.get("data") or [] if isinstance(j, dict) else []
            except Exception as e:
                falhas.append(f"{urlparse(url).path}: {str(e)[:40]}")
                continue
            respondeu = True
            if dados:
                break
    if not respondeu:
        raise RuntimeError("todas as rotas da Gupy falharam (" + "; ".join(falhas) + ")")
    out, fora_local, irrelevantes = [], 0, 0
    for d in dados:
        s_ = M.score(d.get("name"))
        if not s_:
            irrelevantes += 1
            continue
        remoto = d.get("isRemoteWork") or "remote" in str(d.get("workplaceType", "")).lower()
        loc = ", ".join(x for x in (d.get("city"), d.get("state"), "Brasil") if x) + (" (Remoto)" if remoto else "")
        if not local_ok(loc, local):
            fora_local += 1
            continue
        v = nova_vaga(d.get("name"), d.get("careerPageName") or d.get("companyName") or "Empresa Gupy", loc,
                      d.get("publishedDate"), d.get("jobUrl") or d.get("applicationUrl"), "Gupy", d.get("description"), s_)
        if v:
            out.append(v)
    nota(f"{len(dados)} itens brutos → {len(out)} aceitos ({irrelevantes} fora do cargo, {fora_local} fora de '{local}')")
    return out


@fonte("Sólides", "Brasil")
def solides(termo, local):
    # Parâmetros da v5 (funcionavam): page, take=14 (valores maiores dão 500) e title.
    M = matcher(termo)
    hdr = {"Origin": "https://vagas.solides.com.br", "Referer": "https://vagas.solides.com.br/", "Accept": "application/json"}

    def pagina(p):
        j = obter_json("https://vagas.solides.com.br/api/vacancies", params={"page": p, "take": 14, "title": termo},
                       headers=hdr, timeout=12)
        return j.get("data") or []

    out = []
    for lote in paralelo(pagina, [1, 2, 3]):
        for d in lote:
            if d.get("isHiddenJob"):
                continue
            s = M.score(d.get("title"))
            if not s:
                continue
            cidade = (d.get("city") or {}).get("name", "")
            est = d.get("state") or {}
            loc = ", ".join(x for x in (cidade, est.get("name") or est.get("code"), "Brasil") if x)
            if not local_ok(loc, local):
                continue
            link = d.get("redirectLink") or ""
            if not link.startswith("http") or "./" in link:
                link = f"https://vagas.solides.com.br/vagas/{d.get('id')}"
            v = nova_vaga(d.get("title"), d.get("companyName") or "Empresa no Sólides", loc,
                          d.get("publishedAt") or d.get("createdAt"), link, "Sólides", d.get("description"), s)
            if v:
                out.append(v)
    return out


def _cidade_slug(local):
    return "" if local_generico(local) else slug(re.split(r"[,\-/]", local)[0])


@fonte("Vagas.com.br", "Brasil")
def vagas_com(termo, local):
    cidade = _cidade_slug(local)
    base = f"https://www.vagas.com.br/vagas-de-{slug(termo) or 'vagas'}" + (f"-em-{cidade}" if cidade else "")

    def pagina(p):
        soup = obter_html(base + (f"?pagina={p}" if p > 1 else ""), timeout=10)
        out = []
        for item in soup.find_all("li", class_="vaga"):
            a = item.find("a", class_="link-detalhes-vaga")
            if not a:
                continue
            titulo = a.get("title") or a.get_text(strip=True)
            s = relevancia_vaga(titulo, termo)
            if not s:
                continue
            emp, loc, dt = (item.find("span", class_=c) for c in ("emprVaga", "vaga-local", "data-publicacao"))
            v = nova_vaga(titulo, emp.get_text(strip=True) if emp else "", loc.get_text(strip=True) if loc else local,
                          dt.get_text(strip=True) if dt else None, urljoin("https://www.vagas.com.br", a.get("href", "")),
                          "Vagas.com.br", "", s)
            if v:
                out.append(v)
        return out

    return [v for lote in paralelo(pagina, [1, 2]) for v in lote]


_RE_LOC = re.compile(r"((?:[A-ZÀ-Ú][\wÀ-ú']+\s){0,2}[A-ZÀ-Ú][\wÀ-ú']+)\s*[-–/]\s*([A-Z]{2})\b")


@fonte("Catho", "Brasil")
def catho(termo, local):
    cidade = _cidade_slug(local)
    urls = ([f"https://www.catho.com.br/vagas/{slug(termo)}/{cidade}/"] if cidade else []) + \
           [f"https://www.catho.com.br/vagas/{slug(termo)}/"]
    out = []
    for url in urls:  # a URL com cidade pode vir vazia; cai para a nacional e filtra pelo local do card
        arts = obter_html(url, timeout=10).find_all("article")
        nota(f"{len(arts)} <article> em …{url[-38:]}")
        for item in arts:
            h2 = item.find("h2")
            a = h2.find("a") if h2 else None
            if not a:
                continue
            titulo = a.get_text(strip=True)
            s_ = relevancia_vaga(titulo, termo)
            if not s_:
                continue
            m = _RE_LOC.search(item.get_text(" ", strip=True))
            loc = f"{m.group(1)} - {m.group(2)}" if m else (local or "Brasil")
            if m and not local_ok(loc, local):
                continue
            emp = item.find("span", class_=lambda c: c and "nomeEmpresa" in c)
            v = nova_vaga(titulo, emp.get_text(strip=True) if emp else "Confidencial", loc, None,
                          urljoin("https://www.catho.com.br", a.get("href", "")), "Catho", "", s_)
            if v:
                out.append(v)
        if out:
            break
    return out


def _cards_linkedin(soup, termo, local):
    out = []
    for card in soup.select("div.base-card") or soup.select("li.jobs-search-results__list-item"):
        a, t = card.select_one("a.base-card__full-link[href]"), card.select_one("h3.base-search-card__title")
        if not a or not t:
            continue
        titulo = limpa(t.get_text(" "))
        s = relevancia_vaga(titulo, termo)
        if not s:
            continue
        emp, loc, tm = (card.select_one(c) for c in ("h4.base-search-card__subtitle",
                                                      "span.job-search-card__location", "time"))
        v = nova_vaga(titulo, emp.get_text(" ") if emp else "", loc.get_text(" ") if loc else (local or "Brasil"),
                      tm.get("datetime") if tm else None, a.get("href"), "LinkedIn", "", s)
        if v:
            out.append(v)
    return out


@fonte("LinkedIn", "Brasil")
def linkedin(termo, local):
    q = {"keywords": termo, "location": local or "Brazil"}
    rotas = [q, {**q, "start": 25}, {**q, "start": 50}]  # as rotas "jobs-guest" retornam 404 (removidas)
    lotes = paralelo(lambda p: _cards_linkedin(obter_html("https://www.linkedin.com/jobs/search/", params=p, timeout=9),
                                               termo, local), rotas)
    return [v for lote in lotes for v in lote]


@fonte("BNE", "Brasil", beta=True)
def bne(termo, local):
    cidade, uf = cidade_uf(local)
    url = f"https://www.bne.com.br/vagas-de-emprego-para-{slug(termo)}" + (f"-em-{slug(cidade)}-{uf.lower()}" if cidade else "")
    nota(f"URL tentada: {url}")
    soup = obter_html(url, timeout=10)
    return extrair_generico(soup, "https://www.bne.com.br", "BNE", termo, local, ("/vaga-de-emprego",)) \
        or extrair_next_data(soup, "https://www.bne.com.br", "BNE", termo, local)


@fonte("InfoJobs", "Brasil", beta=True)
def infojobs(termo, local):
    cidade, uf = cidade_uf(local)
    url = f"https://www.infojobs.com.br/empregos-{slug(termo)}" + (f"-em-{slug(cidade)},-{uf.lower()}" if cidade else "") + ".aspx"
    nota(f"URL tentada: {url}")
    soup = obter_html(url, timeout=10)
    return extrair_generico(soup, "https://www.infojobs.com.br", "InfoJobs", termo, local, ("/vaga-de-", "/vaga/")) \
        or extrair_next_data(soup, "https://www.infojobs.com.br", "InfoJobs", termo, local)


@fonte("Trabalha Brasil", "Brasil", beta=True)
def trabalha_brasil(termo, local):
    # A v20 chamava "https://trabalhabrasil.com.br" (URL truncada, POST na home) → sempre 0.
    cidade, uf = cidade_uf(local)
    cands = []
    if cidade:
        cands.append(f"https://www.trabalhabrasil.com.br/vagas-empregos-em-{slug(cidade)}-{uf.lower()}/{slug(termo)}")
    cands.append(f"https://www.trabalhabrasil.com.br/vagas-empregos/{slug(termo)}")
    respondeu = False
    for url in cands:
        nota(f"URL tentada: {url}")
        try:
            soup = obter_html(url, timeout=10)
        except Exception as e:
            nota(f"falhou: {str(e)[:60]}")
            continue
        respondeu = True
        out = extrair_generico(soup, "https://www.trabalhabrasil.com.br", "Trabalha Brasil", termo, local,
                               ("/vaga", "/emprego")) \
            or extrair_next_data(soup, "https://www.trabalhabrasil.com.br", "Trabalha Brasil", termo, local)
        if out:
            return out
    if not respondeu:
        raise RuntimeError("nenhuma URL do Trabalha Brasil respondeu (ver notas)")
    return []


@fonte("Indeed (JobSpy)", "Brasil")
def indeed(termo, local):
    return _jobspy("indeed", termo, local, "Indeed")


@fonte("Glassdoor (JobSpy)", "Brasil", beta=True)
def glassdoor(termo, local):
    return _jobspy("glassdoor", termo, local, "Glassdoor")


@fonte("Google Jobs (JobSpy)", "Brasil", beta=True)
def google_jobs(termo, local):
    return _jobspy("google", termo, local, "Google Jobs")


def _jobspy(site, termo, local, origem):
    try:
        from jobspy import scrape_jobs
    except ImportError:
        raise RuntimeError("pacote python-jobspy não instalado")
    kw = dict(site_name=[site], search_term=termo, results_wanted=20, country_indeed="brazil", verbose=0)
    if site == "google":
        kw["google_search_term"] = f"{termo} vagas {local or 'Brasil'}"
    cidade, uf = cidade_uf(local)
    locais = [(local or "Brazil").strip()]
    if site == "glassdoor":  # "location not parsed": tenta "Cidade, UF" e depois o país
        locais = ([f"{cidade.title()}, {uf}"] if cidade else locais) + ["Brazil"]
    df = None
    for loc in dict.fromkeys(locais):
        try:
            df = scrape_jobs(**{**kw, "location": loc})
        except Exception as e:
            nota(f"jobspy/{site} '{loc}': {type(e).__name__}")
            continue
        nota(f"jobspy/{site} local '{loc}': {0 if df is None else len(df)} linhas")
        if df is not None and not df.empty:
            break
    out = []
    if df is None or df.empty:
        return out
    for _, row in df.iterrows():
        s_ = relevancia_vaga(row.get("title"), termo)
        loc_v = row.get("location") or "Brasil"
        if site != "indeed" and not local_ok(loc_v, local):
            continue
        v = nova_vaga(row.get("title"), row.get("company"), loc_v, row.get("date_posted"),
                      row.get("job_url"), origem, row.get("description"), s_)
        if v and s_:
            out.append(v)
    return out


@fonte("Adzuna", "Brasil", exige=("ADZUNA_APP_ID", "ADZUNA_APP_KEY"))
def adzuna(termo, local):
    p = {"app_id": os.getenv("ADZUNA_APP_ID"), "app_key": os.getenv("ADZUNA_APP_KEY"), "results_per_page": 50,
         "what": termo, "content-type": "application/json"}
    if not local_generico(local):
        p["where"] = local
    out = []
    for d in obter_json("https://api.adzuna.com/v1/api/jobs/br/search/1", params=p).get("results", []):
        s = relevancia_vaga(d.get("title"), termo)
        v = nova_vaga(d.get("title"), (d.get("company") or {}).get("display_name"), (d.get("location") or {}).get("display_name"),
                      d.get("created"), d.get("redirect_url"), "Adzuna", d.get("description"), s)
        if v and s:
            out.append(v)
    return out


@fonte("Jooble", "Brasil", exige=("JOOBLE_KEY",))
def jooble(termo, local):
    r = obter(f"https://jooble.org/api/{os.getenv('JOOBLE_KEY')}", metodo="POST",
              json_body={"keywords": termo, "location": "" if local_generico(local) else local, "page": 1})
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    out = []
    for d in r.json().get("jobs", []):
        s = relevancia_vaga(d.get("title"), termo)
        v = nova_vaga(d.get("title"), d.get("company"), d.get("location"), d.get("updated"), d.get("link"),
                      "Jooble", d.get("snippet"), s)
        if v and s:
            out.append(v)
    return out


# Quadros de vagas de empresas (APIs oficiais, JSON estável). EDITE as listas:
# slug = final da URL do quadro (boards.greenhouse.io/SLUG, jobs.lever.co/SLUG). Slug inválido é ignorado.
EMPRESAS_ATS = {
    "greenhouse": ["nubank", "gitlab", "stripe", "cloudflare", "datadog"],
    "lever": ["spotify", "palantir"],
}


@fonte("Empresas (Greenhouse/Lever)", "Empresas", beta=True)
def empresas_ats(termo, local):
    M = matcher(termo)
    tarefas = [(t, s) for t, lst in EMPRESAS_ATS.items() for s in lst]

    def quadro(ts):
        tipo, sl = ts
        chave = ("ats", tipo, sl)
        dados = cache_get(chave, ttl=900)
        if dados is None:
            url = (f"https://boards-api.greenhouse.io/v1/boards/{sl}/jobs" if tipo == "greenhouse"
                   else f"https://api.lever.co/v0/postings/{sl}?mode=json")
            r = obter(url, timeout=8)
            if r.status_code == 404:
                nota(f"slug inexistente: {tipo}/{sl}")
                return []
            if r.status_code != 200:
                raise RuntimeError(f"{sl}: HTTP {r.status_code}")
            j = r.json()
            dados = j.get("jobs", []) if tipo == "greenhouse" else j
            cache_set(chave, dados)
        emp, out = sl.replace("-", " ").title(), []
        for d in dados:
            if tipo == "greenhouse":
                titulo, loc = d.get("title"), (d.get("location") or {}).get("name", "")
                link, dt = d.get("absolute_url"), d.get("updated_at")
            else:
                titulo, loc = d.get("text"), (d.get("categories") or {}).get("location", "")
                link, dt = d.get("hostedUrl"), d.get("createdAt")
            s = M.score(titulo)
            if s and local_ok(loc, local):
                v = nova_vaga(titulo, emp, loc, dt, link, f"{emp} ({tipo.title()})", "", s)
                if v:
                    out.append(v)
        return out

    return [v for lote in paralelo(quadro, tarefas, workers=8) for v in lote]


# ======================================================================
# FONTES — GLOBAL / REMOTO
# ======================================================================
_TRAD = {"auditor interno": "internal auditor", "auditoria interna": "internal audit", "auditor": "auditor",
         "auditoria": "audit", "controles internos": "internal controls", "controller": "controller",
         "controladoria": "controller", "analista": "analyst", "gerente": "manager", "contador": "accountant"}


@fonte("Jobicy", "Global")
def jobicy(termo, local):
    termo_en = _TRAD.get(termo.lower().strip(), termo.lower().strip())
    url, jobs = "https://jobicy.com/api/v2/remote-jobs", []
    for tag in (termo_en, termo_en.split()[0]):
        j = obter_json(url, params={"count": 40, "tag": tag}, timeout=8)
        jobs = j.get("jobs", []) if isinstance(j, dict) else []
        if jobs:
            break
    out = []
    nota(f"{len(jobs)} itens brutos (tag '{termo_en}')")
    for d in jobs:
        s = max(relevancia_vaga(d.get("jobTitle"), termo), relevancia_vaga(d.get("jobTitle"), termo_en))
        v = nova_vaga(d.get("jobTitle"), d.get("companyName"), d.get("jobGeo") or "Global / Remoto", d.get("pubDate"),
                      d.get("url"), "Jobicy", d.get("jobDescription"), s)
        if v and s:
            out.append(v)
    return out


@fonte("Remotive", "Global")
def remotive(termo, local):
    termo_en = _TRAD.get(termo.lower().strip(), termo)
    out = []
    dados = obter_json("https://remotive.com/api/remote-jobs", params={"search": termo_en, "limit": 50}).get("jobs", [])
    nota(f"{len(dados)} itens brutos (busca '{termo_en}')")
    for d in dados:
        s = max(relevancia_vaga(d.get("title"), termo), relevancia_vaga(d.get("title"), termo_en))
        v = nova_vaga(d.get("title"), d.get("company_name"), d.get("candidate_required_location") or "Remoto",
                      d.get("publication_date"), d.get("url"), "Remotive", d.get("description"), s)
        if v and s:
            out.append(v)
    return out


@fonte("RemoteOK", "Global")
def remoteok(termo, local):
    termo_en = _TRAD.get(termo.lower().strip(), termo)
    out = []
    dados = [d for d in obter_json("https://remoteok.com/api", timeout=12) if isinstance(d, dict) and "position" in d]
    nota(f"{len(dados)} itens brutos")
    for d in dados:
        if False:
            continue
        s = max(relevancia_vaga(d.get("position"), termo), relevancia_vaga(d.get("position"), termo_en))
        v = nova_vaga(d.get("position"), d.get("company"), d.get("location") or "Remoto", d.get("date"), d.get("url"),
                      "RemoteOK", d.get("description"), s)
        if v and s:
            out.append(v)
    return out


@fonte("We Work Remotely", "Global")
def weworkremotely(termo, local):
    termo_en = _TRAD.get(termo.lower().strip(), termo)
    r = obter("https://weworkremotely.com/remote-jobs.rss", timeout=12)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    out = []
    itens_rss = list(ET.fromstring(r.content).iter("item"))
    nota(f"{len(itens_rss)} itens brutos")
    for it in itens_rss:
        bruto = limpa(it.findtext("title"))
        empresa, _, titulo = bruto.partition(": ") if ": " in bruto else ("", "", bruto)
        s = max(relevancia_vaga(titulo, termo), relevancia_vaga(titulo, termo_en))
        v = nova_vaga(titulo, empresa, it.findtext("region") or "Remoto / Global", it.findtext("pubDate"),
                      it.findtext("link"), "We Work Remotely", it.findtext("description"), s)
        if v and s:
            out.append(v)
    return out


@fonte("Arbeitnow", "Global")
def arbeitnow(termo, local):
    termo_en = _TRAD.get(termo.lower().strip(), termo)
    out = []
    dados = obter_json("https://www.arbeitnow.com/api/job-board-api", timeout=10).get("data", [])
    nota(f"{len(dados)} itens brutos")
    for d in dados:
        s = max(relevancia_vaga(d.get("title"), termo), relevancia_vaga(d.get("title"), termo_en))
        v = nova_vaga(d.get("title"), d.get("company_name"), d.get("location"), d.get("created_at"), d.get("url"),
                      "Arbeitnow", d.get("description"), s)
        if v and s:
            out.append(v)
    return out


@fonte("Remotar", "Global", beta=True)
def remotar(termo, local):
    # A v20 chamava "https://remotar.com.br" (sem caminho) e esperava JSON do WordPress → sempre 0.
    url = "https://remotar.com.br/search/jobs"
    nota(f"URL tentada: {url}?q={termo}")
    soup = obter_html(url, params={"q": termo}, timeout=10)
    out = extrair_next_data(soup, "https://remotar.com.br", "Remotar", termo, local)
    return out or extrair_generico(soup, "https://remotar.com.br", "Remotar", termo, local, ("/job/", "/jobs/", "/vaga"))
