#!/usr/bin/env python3
"""Private read-only viewer. No gateway startup, pairing request, CLI login or send.
Launch from the integrated kit: python qr_viewer.py (no token/URL arguments).
"""
from __future__ import annotations

from pathlib import Path
import queue
import sys
import threading
import time

from viewer_core import DisplayGate, GatewayReader, POLL_INTERVAL, Result, ViewerError, load_token

ROOT = Path(__file__).resolve().parent
MESSAGES = {
    'connected': 'Conexão informada pelo gateway. QR removido. Nenhum envio foi autorizado aqui.',
    'starting': 'Gateway preparando a conexão. Nenhum QR disponível.',
    'pairing_in_progress': 'Pareamento em andamento. QR removido.',
    'disconnected': 'Gateway desconectado. QR removido; revise o terminal privado.',
    'consent_required': 'O gateway exige consentimento. Este visualizador não o concede.',
    'allowlist_required': 'Gateway sem allowlist. Nenhuma configuração foi alterada.',
    'session_review_required': 'A sessão precisa de revisão local. QR removido.',
    'restarting_transport': 'Gateway reiniciando o transporte autorizado. QR removido.',
    'startup_error': 'Gateway indisponível. QR removido.',
    'storage_error': 'Gateway com falha de armazenamento. QR removido.',
    'unauthorized': 'Acesso local recusado. Confira o .env privado; não cole o token em mensagens.',
    'transport_unavailable': 'Sem resposta local segura. QR oculto.',
    'slow_response': 'Resposta local demorou demais. QR descartado.',
    'expired': 'QR expirou ou a janela segura terminou. Aguardando quadro novo.',
}


class PrivateViewer:
    def __init__(self, root, reader):
        import tkinter as tk
        from tkinter import ttk
        self.root, self.reader = root, reader
        self.gate, self.results = DisplayGate(), queue.Queue(maxsize=1)
        self.enabled = self.busy = self.closed = False
        self.photo = None
        self.next_poll = 0.0
        root.title('QR privado — WhatsApp de laboratório')
        root.geometry('550x720')
        root.minsize(530, 680)
        wrapper = ttk.Frame(root, padding=18)
        wrapper.pack(fill='both', expand=True)
        ttk.Label(wrapper, text='PRIVADO — não compartilhe esta janela', font=('', 13, 'bold')).pack(pady=(0, 8))
        ttk.Label(wrapper, wraplength=475, text='Somente leitura do gateway local já autorizado. Este visualizador não inicia conexão, não confirma pareamento e não envia mensagens.').pack()
        self.image = ttk.Label(wrapper, text='QR oculto', anchor='center')
        self.image.pack(expand=True, fill='both', pady=12)
        self.lease = tk.StringVar(value='Sem QR vigente confirmado. A validade no WhatsApp não é garantida.')
        ttk.Label(wrapper, textvariable=self.lease, wraplength=475, anchor='center').pack(pady=4)
        self.message = tk.StringVar(value='Exiba somente em sua tela privada, sem projeção ou compartilhamento.')
        ttk.Label(wrapper, textvariable=self.message, wraplength=475, anchor='center').pack(pady=8)
        controls = ttk.Frame(wrapper)
        controls.pack(fill='x')
        ttk.Button(controls, text='Exibir nesta tela privada', command=self.resume).pack(side='left')
        ttk.Button(controls, text='Ocultar', command=self.pause).pack(side='right')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<FocusOut>', lambda _event: root.after_idle(self._check_focus))
        root.bind('<Unmap>', lambda event: self.pause() if event.widget is root else None)
        root.after(25, self.tick)

    def clear(self):
        self.image.configure(image='', text='QR oculto')
        self.photo = None
        self.lease.set('QR oculto. Aguardando verificação local; sem garantia de validade no WhatsApp.')

    def resume(self):
        if self.closed:
            return
        self.gate.hide()
        self.clear()
        self.enabled = True
        self.next_poll = 0.0
        self.message.set('Consultando somente o gateway 127.0.0.1…')

    def pause(self):
        if self.closed:
            return
        self.enabled = False
        self.gate.hide()
        self.clear()
        self.message.set('QR oculto. Clique em Exibir somente quando a tela estiver privada.')

    def _check_focus(self):
        if not self.closed and self.root.focus_displayof() is None:
            self.pause()

    def _fetch(self, serial):
        try:
            result = self.reader.fetch()
        except ViewerError as error:
            result = Result(str(error))  # our static codes, never an upstream body/error
        except Exception:
            result = Result('unavailable')
        try:
            self.results.put_nowait((serial, result))
        except queue.Full:
            pass

    def _show(self, frame):
        import tkinter as tk
        try:
            # Raw PNG remains in process memory. No browser, temporary SVG or image file.
            self.photo = tk.PhotoImage(data=frame.png, format='png', master=self.root)
            if not self.gate.visible(time.monotonic()):
                self.clear()
                return
            self.image.configure(image=self.photo, text='')
            remaining = max(0.0, frame.deadline - time.monotonic())
            self.lease.set(f'Verificação local: {remaining:.2f} s restantes · quadro {frame.generation}. Não é garantia de validade no WhatsApp.')
            self.message.set('Escaneie apenas no seu WhatsApp de teste consentido. QR se oculta durante verificações.')
        except Exception:
            self.gate.hide()
            self.clear()
            self.message.set('Não foi possível desenhar com segurança. QR oculto.')

    def tick(self):
        if self.closed:
            return
        now = time.monotonic()
        if not self.gate.visible(now) and self.photo is not None:
            self.clear()
        elif self.photo is not None and self.gate.frame:
            remaining = max(0.0, self.gate.frame.deadline - now)
            self.lease.set(f'Verificação local: {remaining:.2f} s restantes · quadro {self.gate.frame.generation}. Não é garantia de validade no WhatsApp.')
        try:
            serial, result = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            if self.enabled and serial == self.gate.serial:
                if self.gate.accept(serial, result, now):
                    self._show(self.gate.frame)
                else:
                    self.clear()
                    self.message.set(MESSAGES.get(result.state, 'Nenhum QR vigente confirmado. Aguardando.'))
        if self.enabled and not self.busy and now >= self.next_poll:
            # Invalidate first: never leave the previous QR visible while a refresh may fail.
            serial = self.gate.begin()
            self.clear()
            self.busy = True
            self.next_poll = now + POLL_INTERVAL
            threading.Thread(target=self._fetch, args=(serial,), daemon=True).start()
        self.root.after(25, self.tick)

    def close(self):
        self.closed = True
        self.enabled = False
        self.gate.close()
        self.clear()
        self.root.destroy()


def main():
    if len(sys.argv) != 1:
        print('Use apenas: python qr_viewer.py. Não passe token, URL ou caminho em argumentos.', file=sys.stderr)
        return 2
    try:
        token = load_token(ROOT / '.env')
        reader = GatewayReader(token)
        import tkinter as tk
        root = tk.Tk()
        PrivateViewer(root, reader)
        root.mainloop()
        return 0
    except ViewerError:
        print('Visualizador bloqueado: confira o .env privado existente, token único 64hex e permissões locais. Nenhuma configuração foi alterada.', file=sys.stderr)
        return 1
    except Exception:
        print('Janela privada indisponível. Confira Python com Tk/Tcl e a sessão gráfica local; não haverá fallback para navegador ou arquivo QR.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
