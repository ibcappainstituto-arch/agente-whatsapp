"""Metodo original preservado; precos/condicoes renderizados da fonte revisada."""
import re
from pathlib import Path
from catalogo import catalogo_aprovado

HUMANO = "Esse pedido precisa da revisão do responsável técnico. O atendimento automático ficará pausado; não posso confirmar preço, prazo ou conclusão fora do catálogo."


def _seguro(texto):
    return not re.search(r"R\s*\$|https?://|@|\d|garant|vai ganhar|vitória certa|reverter.*laudo|o juiz vai|sentença favorável|aguarde|vou.*retorn|\b(?:desconto|parcela|pagamento|pix|êxito|exito)\b",texto,re.I)


def _movimentos(decisao,conversa):
    entrada=next((t for p,t in reversed(conversa or []) if p=='user' and not t.startswith('(')),'')
    linhas=[l.strip() for l in decisao.get('mensagem','').splitlines() if l.strip()]
    espelho=decisao.get('espelho','').strip()
    if espelho and espelho.casefold() not in entrada.casefold():
        espelho=''
    if not espelho and entrada and '[enviou um anexo:' not in entrada:
        espelho=entrada.strip().split('\n')[0][:140]
    if re.search(r'https?://|R\s*\$|@',espelho,re.I):
        espelho=''
    sentido=decisao.get('sentido','').strip()
    if not sentido or '?' in sentido or len(sentido)>240 or not _seguro(sentido):
        sentido='O escopo técnico precisa corresponder à fase e à necessidade que você descreveu.'
    pergunta=decisao.get('pergunta_texto','').strip()
    if not pergunta and linhas and linhas[-1].endswith('?'):
        pergunta=linhas[-1]
    if pergunta.count('?')!=1 or not pergunta.endswith('?') or len(pergunta)>220 or not _seguro(pergunta):
        pergunta={'fase':'É uma demanda antes da ação, com perícia marcada ou com laudo apresentado?',
                  'prazo':'Qual é o prazo para essa demanda?',
                  'documentos':'Quais documentos você já possui para a avaliação técnica?',
                  'decisor':'Quem participa da decisão de contratação?'}.get(decisao.get('pergunta','fase'))
    espelho=espelho.replace('?','').rstrip('.! ”')
    return (f'“{espelho}”.' if espelho else ''),sentido,pergunta


def revisar(decisao: dict, pasta: Path, conversa=None) -> tuple[str,str]:
    servicos=catalogo_aprovado(pasta)
    acao=decisao.get('acao','qualificar')
    if acao=='humano' or decisao.get('avisar_perito'):
        return HUMANO,'Revisao humana solicitada.'
    if acao=='recusa':
        return 'Combinado, obrigado por avisar.',''
    espelho,sentido,pergunta=_movimentos(decisao,conversa)
    item=next((s for s in servicos if s['id']==decisao.get('servico')),None)
    respostas=sum(p=='assistant' for p,t in conversa or [])
    if acao=='qualificar' and respostas>=2:
        if item is None:
            return HUMANO,'Limite de diagnostico atingido sem servico adequado confirmado.'
        acao='ofertar'
    prefixo=[espelho] if espelho else []
    if acao in ('ofertar','valor'):
        if item is None:
            return HUMANO,'Servico fora do catalogo.'
        if acao=='ofertar':
            prazo_oferta=re.sub(r'\([^)]*R\$[^)]*\)','',item['prazo']).strip()
            linhas=prefixo+[sentido,f"O serviço {item['servico']} entrega {item['entrega']}",
                f"Prazo de referência: {prazo_oferta} A agenda precisa de confirmação do responsável.",
                'Faz sentido para você?']
        else:
            valor='R$ '+item['valor_brl']
            parcelado=re.search(r'(\d+x\s+de\s+R\$\s*[\d.,]+(?:\s*\([^)]*\))?)',valor,re.I)
            preco=f"{parcelado.group(1)}. Total: R$ {item['valor_brl']}." if parcelado else valor
            linhas=prefixo+[f"Condições aprovadas para {item['servico']}: {preco}",
                f"Como contratar: {item['contratacao']}", 'Ficou alguma dúvida para seguirmos com a contratação?']
        # Condicoes e valores sao copiados da fonte; nunca do texto gerado.
        return '\n'.join(linhas),''
    if acao in ('qualificar','objecao') and pergunta:
        if not decisao.get('mensagem') and not decisao.get('pergunta_texto'):
            return '',''
        return '\n'.join(prefixo+[sentido,pergunta]),''
    return HUMANO,'Saida fora das acoes permitidas.'
