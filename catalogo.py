"""Fonte comercial local explícita: nenhuma oferta sem revisão e hash aprovado."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

CAMPOS = ('id', 'servico', 'entrega', 'prazo', 'valor_brl', 'contratacao')

def resumo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ler(fonte: Path) -> list[dict]:
    if fonte.is_symlink() or not fonte.is_file() or fonte.stat().st_size > 100_000:
        raise ValueError('Fonte deve ser CSV local regular com ate 100 KB.')
    reader = csv.DictReader(io.StringIO(fonte.read_text(encoding='utf-8-sig')))
    if tuple(reader.fieldnames or ()) != CAMPOS:
        raise ValueError('Cabecalho comercial invalido.')
    itens, ids = [], set()
    for linha in reader:
        if None in linha or any(not (linha.get(k) or '').strip() for k in CAMPOS):
            raise ValueError('Preencha todos os campos sem colunas extras.')
        item = {k: linha[k].strip() for k in CAMPOS}
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}',item['id']) or item['id'] in ids:
            raise ValueError('ID comercial invalido ou duplicado.')
        if any(len(v)>1000 or any(ord(c)<32 for c in v) for v in item.values()):
            raise ValueError('Campo comercial longo ou com controles.')
        try:
            preco=Decimal(item['valor_brl'])
            if not preco.is_finite() or preco<=0 or preco.as_tuple().exponent < -2:
                raise InvalidOperation
        except InvalidOperation:
            raise ValueError('Valor deve ser positivo com ponto decimal e ate duas casas.') from None
        item['valor_brl']=format(preco,'.2f')
        ids.add(item['id']); itens.append(item)
    if not 1<=len(itens)<=50:
        raise ValueError('Informe de 1 a 50 servicos reais revisados; modelo vazio bloqueia atendimento.')
    return itens

def aprovar(pasta: Path, sha256: str) -> None:
    fonte=pasta/'servicos.csv'
    ler(fonte)
    if resumo(fonte)!=sha256.lower():
        raise ValueError('SHA256 divergente. Releia a fonte antes de aprovar.')
    fontes = _fontes(pasta)
    (pasta/'aprovacao.json').write_text(json.dumps({'sha256':sha256.lower(),'fontes':fontes,'escopo':'fonte comercial revisada; nao autoriza pareamento ou envio'}),encoding='utf-8')

def catalogo_aprovado(pasta: Path) -> list[dict]:
    fonte=pasta/'servicos.csv'
    aprovacao=json.loads((pasta/'aprovacao.json').read_text(encoding='utf-8'))
    if aprovacao.get('sha256')!=resumo(fonte):
        raise ValueError('Fonte alterada depois da revisao: atendimento bloqueado.')
    if aprovacao.get('fontes',{}) != _fontes(pasta):
        raise ValueError('Markdown revisado alterado: revisar e aprovar novamente.')
    return ler(fonte)


NOMES = ('servicos.md','precos_e_condicoes.md','tom_de_voz.md','perguntas_frequentes.md','memorias_e_decisoes.md','LEIA_PRIMEIRO.md')
def _fontes(pasta):
    originais=pasta/'originais'
    if not originais.exists(): return {}
    result={}
    for nome in NOMES:
        p=originais/nome
        if p.is_symlink() or not p.is_file() or p.stat().st_size>100_000:
            raise ValueError('Fonte Markdown ausente ou irregular.')
        result[nome]=resumo(p)
    return result

def contexto(pasta):
    catalogo_aprovado(pasta)
    originais=pasta/'originais'
    if not originais.exists(): return ''
    # Precos usam exclusivamente renderizacao do catalogo, nao estas notas livres.
    nomes=('tom_de_voz.md','perguntas_frequentes.md','memorias_e_decisoes.md')
    return json.dumps({n:(originais/n).read_text(encoding='utf-8-sig')[:12000] for n in nomes},ensure_ascii=False)
