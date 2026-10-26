import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import catalogo
import importar_conhecimento as imp


class ImportacaoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.origem = self.raiz / 'conhecimento_agente'
        self.destino = self.raiz / 'fonte'
        self.origem.mkdir()
        texto = ('Serviço fictício\nEntrega demonstrativa\nPrazo demonstrativo\n'
                 'Valor total R$ 123,45\nContratação demonstrativa\n')
        for nome in imp.ARQUIVOS:
            (self.origem / nome).write_text(texto, encoding='utf-8')
        self.item = {'id': 'demo', 'servico': 'Serviço fictício', 'entrega': 'Entrega demonstrativa',
                     'prazo': 'Prazo demonstrativo', 'valor_brl': '123.45', 'contratacao': 'Contratação demonstrativa'}
        evidencias = [{'campo': k, 'arquivo': 'servicos.md', 'trecho': 'Valor total R$ 123,45' if k == 'valor_brl' else v}
                      for k, v in self.item.items() if k != 'id']
        self.proposta = {'servicos': [{**self.item, 'evidencias': evidencias}], 'pendencias': []}

    def rodar(self, proposta=None):
        with patch.object(imp, 'obter_decisao', return_value=copy.deepcopy(proposta or self.proposta)) as cli:
            resultado = imp.importar(self.origem, 'codex', self.destino)
            self.assertEqual(resultado, (self.destino / 'servicos.csv').exists())
        return cli

    def test_preserva_seis_originais_sha_e_exige_aprovacao_separada(self):
        antes = {n: (self.origem / n).read_bytes() for n in imp.ARQUIVOS}
        self.rodar()
        self.assertEqual(catalogo.ler(self.destino / 'servicos.csv'), [self.item])
        self.assertFalse((self.destino / 'aprovacao.json').exists())
        fontes = json.loads((self.destino / 'fontes.json').read_text(encoding='utf-8'))['arquivos']
        self.assertEqual(len(fontes), 6)
        for f in fontes:
            self.assertEqual((self.destino / 'originais' / f['arquivo']).read_bytes(), antes[f['arquivo']])
            self.assertEqual((self.origem / f['arquivo']).read_bytes(), antes[f['arquivo']])
            self.assertEqual(f['sha256'], hashlib.sha256(antes[f['arquivo']]).hexdigest())
        self.assertIn('linha 4', (self.destino / 'REVISAO.md').read_text(encoding='utf-8'))

    def test_preco_inventado_nao_cria_csv(self):
        self.proposta['servicos'][0]['valor_brl'] = '999.00'
        self.rodar()
        self.assertTrue((self.destino / 'PENDENCIAS.md').exists())
        self.assertFalse((self.destino / 'servicos.csv').exists())

    def test_evidencia_inventada_nao_cria_csv(self):
        self.proposta['servicos'][0]['evidencias'][0]['trecho'] = 'Não existe nos originais'
        self.rodar()
        self.assertFalse((self.destino / 'servicos.csv').exists())

    def test_parcela_sem_total_nao_vira_preco_total(self):
        arq = self.origem / 'servicos.md'
        arq.write_text(arq.read_text(encoding='utf-8').replace('Valor total R$ 123,45', '3x R$ 123,45'), encoding='utf-8')
        self.proposta['servicos'][0]['evidencias'][3]['trecho'] = 'R$ 123,45'
        self.rodar()
        self.assertFalse((self.destino / 'servicos.csv').exists())

    def test_pendencia_modelo_impede_catalogo(self):
        self.proposta['pendencias'] = ['Fonte comercial pode estar desatualizada.']
        self.rodar()
        self.assertTrue((self.destino / 'revisao.json').exists())
        self.assertFalse((self.destino / 'servicos.csv').exists())

    def test_nao_sobrescreve_csv_existente(self):
        self.destino.mkdir()
        arquivo = self.destino / 'servicos.csv'
        arquivo.write_text('PRESERVAR')
        with patch.object(imp, 'obter_decisao') as cli, self.assertRaises(FileExistsError):
            imp.importar(self.origem, 'codex', self.destino)
        self.assertEqual(arquivo.read_text(encoding='utf-8'), 'PRESERVAR')
        cli.assert_not_called()

    def test_arquivo_obrigatorio_ausente_bloqueia_sem_ia(self):
        (self.origem / 'LEIA_PRIMEIRO.md').unlink()
        with patch.object(imp, 'obter_decisao') as cli, self.assertRaises(ValueError):
            imp.importar(self.origem, 'codex', self.destino)
        cli.assert_not_called()
        self.assertFalse(self.destino.exists())

    def test_symlink_bloqueia_antes_da_ia(self):
        arq = self.origem / 'servicos.md'
        arq.unlink()
        alvo = self.raiz / 'fora.md'
        alvo.write_text('NAO LER')
        try:
            arq.symlink_to(alvo)
        except (OSError, NotImplementedError):
            self.skipTest('Sistema sem privilegio para criar symlink; teste de segredo continua independente.')
        with patch.object(imp, 'obter_decisao') as cli, self.assertRaises(ValueError):
            imp.importar(self.origem, 'codex', self.destino)
        cli.assert_not_called()

    def test_segredo_bloqueia_antes_da_ia(self):
        arq = self.origem / 'servicos.md'
        arq.write_text('API_KEY=SEGREDO_SINTETICO_NAO_REAL', encoding='utf-8')
        with patch.object(imp, 'obter_decisao') as cli, self.assertRaises(ValueError):
            imp.importar(self.origem, 'codex', self.destino)
        cli.assert_not_called()

    def test_falha_cli_gera_pendencia_sem_aprovacao(self):
        with patch.object(imp, 'obter_decisao', side_effect=imp.ErroCLI('limite')):
            self.assertFalse(imp.importar(self.origem, 'claude', self.destino))
        self.assertTrue((self.destino / 'PENDENCIAS.md').exists())
        self.assertFalse((self.destino / 'servicos.csv').exists())
        self.assertFalse((self.destino / 'aprovacao.json').exists())


if __name__ == '__main__':
    unittest.main()
