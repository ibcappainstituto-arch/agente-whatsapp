import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import agente
import catalogo
import comercial

class Runtime(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); (self.root/'fonte_comercial').mkdir()
        (self.root/'METODO.md').write_text('Espelho sentido pergunta.',encoding='utf-8')
        self.source=self.root/'fonte_comercial'/'servicos.csv'
        with self.source.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(catalogo.CAMPOS);w.writerow(['demo','Servico SINTETICO','Entrega ficticia','Prazo sujeito a confirmacao','123.45','Nenhum pagamento: teste sintetico'])
        catalogo.aprovar(self.source.parent,catalogo.resumo(self.source))
        self.patch=patch.object(agente,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.db=agente.banco(self.root/'dados'/'teste.sqlite3');self.addCleanup(self.db.close)
        # Numero sintetico usado apenas como string; nenhum canal/rede e acionado.
        self.c={'motor':'codex','nome':'Responsavel Ficticio','allowlist':['99999999999']}
        self.e={'id':'sintetico-1','chat_id':'99999999999@s.whatsapp.net','text':'Tenho um laudo apresentado','timestamp':1000}
        self.g=Mock();self.g.chamar.return_value={'state':'sent','message_id':'recibo-sintetico'}
        self.d={'acao':'qualificar','pergunta':'prazo','espelho':'laudo apresentado','sentido':'O escopo técnico precisa corresponder à fase descrita.','pergunta_texto':'Qual prazo você recebeu?','mensagem':'resposta','avisar_perito':False,'servico':'demo'}
        self.ia=Mock(return_value=self.d)
    def go(self,e=None): return agente.processar(self.db,self.c,self.g,e or self.e,self.ia,agora=1001)
    def test_resposta_sintetica_com_recibo(self):
        self.assertEqual(self.go(),'aceito_gateway');self.g.chamar.assert_called_once()
        self.assertIn('Sou o assistente virtual',self.g.chamar.call_args[0][2]['text'])
    def test_duplicado_nao_reenvia(self):
        self.go();self.assertEqual(self.go(),'duplicado');self.g.chamar.assert_called_once()
    def test_numero_fora_da_lista(self):
        self.e['chat_id']='88888888888@s.whatsapp.net';self.assertEqual(self.go(),'fora_allowlist');self.ia.assert_not_called()
    def test_allowlist_vazia_bloqueia(self):
        self.c['allowlist']=[];self.assertEqual(self.go(),'fora_allowlist');self.g.chamar.assert_not_called()
    def test_grupo_bloqueado(self):
        self.e['chat_id']='99999999999@g.us';self.assertEqual(self.go(),'fora_allowlist')
    def test_lid_bloqueado(self):
        self.e['chat_id']='99999999999@lid';self.assertEqual(self.go(),'fora_allowlist')
    def test_antiga_e_futura_bloqueadas(self):
        self.e['timestamp']=100;self.assertEqual(self.go(),'ignorado')
        self.e['timestamp']=2000;self.assertEqual(self.go(),'ignorado')
    def test_recusa_pausa_sem_ia(self):
        self.e['text']='Não quero mais mensagens';self.assertEqual(self.go(),'recusa');self.ia.assert_not_called();self.g.chamar.assert_not_called()
        self.e['id']='nova';self.e['text']='Oi';self.assertEqual(self.go(),'pausado')
    def test_pedido_humano_pausa(self):
        self.e['text']='Quero uma pessoa real';self.assertEqual(self.go(),'humano');self.ia.assert_not_called()
    def test_manual_pausa(self):
        self.e['kind']='human_takeover';self.assertEqual(self.go(),'pausado_humano');self.ia.assert_not_called()
    def test_timeout_envio_nao_repete(self):
        self.g.chamar.side_effect=TimeoutError();self.assertEqual(self.go(),'revisao_necessaria')
        self.assertEqual(self.go(),'duplicado');self.g.chamar.assert_called_once()
    def test_recibo_vazio_pausa(self):
        self.g.chamar.return_value={};self.assertEqual(self.go(),'revisao_necessaria')
    def test_falha_ia_pausa_sem_envio(self):
        self.ia.side_effect=RuntimeError();self.assertEqual(self.go(),'revisao_necessaria');self.g.chamar.assert_not_called()
    def test_fonte_alterada_bloqueia(self):
        self.source.write_text(self.source.read_text()+'\n',encoding='utf-8')
        self.assertEqual(self.go(),'revisao_necessaria');self.ia.assert_not_called();self.g.chamar.assert_not_called()
    def test_valor_vem_da_fonte_nao_ia(self):
        self.d.update(acao='valor',mensagem='Custa R$ 1 com desconto',espelho='')
        self.go();s=self.g.chamar.call_args[0][2]['text'];self.assertIn('R$ 123.45',s);self.assertNotIn('com desconto',s)
    def test_inventar_servico_pausa(self):
        self.d.update(acao='ofertar',servico='inventado');self.assertEqual(self.go(),'sem_envio');self.g.chamar.assert_not_called()
    def test_terceira_resposta_oferece(self):
        for _ in range(2):self.db.execute("INSERT INTO historico(chat,papel,texto) VALUES (?,'assistant','Pergunta?')",(self.e['chat_id'],))
        self.go();self.assertIn('Servico SINTETICO',self.g.chamar.call_args[0][2]['text'])
    def test_espelho_fabricado_nao_sai(self):
        self.d['espelho']='O juiz garantiu minha vitória';self.go();self.assertNotIn('garantiu',self.g.chamar.call_args[0][2]['text'])
    def test_numero_config_estrito(self):
        for x in ('','*','todos','999; curl segredo'):
            with self.assertRaises(ValueError):agente.numero(x)
    def test_md_alterado_bloqueia(self):
        orig=self.source.parent/'originais';orig.mkdir()
        for n in catalogo.NOMES:(orig/n).write_text('Fonte sintetica.',encoding='utf-8')
        catalogo.aprovar(self.source.parent,catalogo.resumo(self.source))
        (orig/'tom_de_voz.md').write_text('Alterado',encoding='utf-8')
        with self.assertRaises(ValueError):catalogo.catalogo_aprovado(self.source.parent)

if __name__=='__main__':unittest.main()
