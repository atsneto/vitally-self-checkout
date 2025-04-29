import flet as ft
import threading
import random
from models import Pessoa
from database import Session, Base, engine
import re

# Configuração do banco de dados
Base.metadata.create_all(engine)

# Funções utilitárias
def limpar_cpf(cpf: str) -> str:
    """Remove caracteres não numéricos do CPF"""
    return re.sub(r"\D", "", cpf)

def mostrar_erro(mensagem: str, pagina: ft.Page, controle: ft.Control) -> None:
    """Mostra mensagem de erro temporária"""
    controle.value = mensagem
    controle.color = "red"
    pagina.update()
    threading.Timer(2, lambda: limpar_erro(controle, pagina)).start()

def limpar_erro(controle: ft.Control, pagina: ft.Page) -> None:
    controle.value = ""
    pagina.update()

# Telas
def tela_inicial(pagina: ft.Page) -> None:
    """Tela inicial"""
    pagina.clean()
    pagina.title = "Vitally - Início"
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    logo = ft.Image(
        src="images/vitally_logo.png",
        width=400,
        height=400,
        fit=ft.ImageFit.CONTAIN
    )

    btn_iniciar = ft.ElevatedButton(
        "Iniciar Atendimento",
        style=ft.ButtonStyle(
            color="white",
            bgcolor="green",
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20
        ),
        on_click=lambda e: tela_consulta(pagina)
    )

    pagina.add(
        ft.Column(
            [logo, btn_iniciar],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=40
        )
    )
    pagina.update()

def tela_consulta(pagina: ft.Page) -> None:
    """Tela de consulta de CPF"""
    pagina.clean()
    pagina.title = "Vitally - Consulta CPF"
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    txt_titulo = ft.Text(
        "Digite seu CPF:",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    cpf_input = ft.TextField(
        hint_text="000.000.000-00",
        input_filter=ft.InputFilter(r"\d+"),
        max_length=11,
        text_align=ft.TextAlign.LEFT,
        width=300,
        border_radius=10,
        prefix_icon=ft.icons.SEARCH
    )

    resultado = ft.Text(size=16, text_align=ft.TextAlign.CENTER)

    def consultar_cpf(e):
        raw_cpf = limpar_cpf(cpf_input.value)

        if len(raw_cpf) != 11:
            mostrar_erro("CPF inválido! Deve conter 11 dígitos.", pagina, resultado)
            return

        try:
            with Session() as session:
                pessoa = session.query(Pessoa).filter_by(cpf=raw_cpf).first()

                if not pessoa:
                    mostrar_erro("CPF não encontrado!", pagina, resultado)
                    return

                resultado.value = ""
                pagina.update()
                tela_biometria(pagina, pessoa)

        except Exception as e:
            mostrar_erro(f"Erro de conexão: {str(e)}", pagina, resultado)

    btn_voltar = ft.TextButton(
        "Voltar",
        on_click=lambda e: tela_inicial(pagina),
        icon=ft.icons.ARROW_BACK
    )

    pagina.add(
        ft.Column(
            [
                txt_titulo,
                cpf_input,
                resultado,
                ft.ElevatedButton(
                    "Consultar",
                    on_click=consultar_cpf,
                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, padding=20)
                ),
                btn_voltar
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_biometria(pagina: ft.Page, pessoa: Pessoa) -> None:
    """Tela de verificação biométrica"""
    pagina.clean()
    pagina.title = "Vitally - Biometria"

    header = ft.Text(
        "Verificação Biométrica",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    scan_animation = ft.Image(
        src="images/biometriafacial.gif",
        width=300,
        height=300
    )

    status_text = ft.Text("Posicione seu rosto na câmera", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=16, text_align=ft.TextAlign.CENTER)

    def iniciar_verificacao(e):
        scan_animation.src = "images/scan_active.gif"
        status_text.value = "Analisando características faciais..."
        progress.visible = True
        header.visible = False
        e.control.visible = False
        pagina.update()

        threading.Timer(3, finalizar_verificacao).start()

    def finalizar_verificacao():
        scan_animation.src = "images/success_checkmark.gif"
        status_text.value = "Verificação bem-sucedida!"
        progress.visible = False
        resultado.value = "Biometria validada com sucesso"
        resultado.color = ft.colors.GREEN
        pagina.update()

        threading.Timer(2, lambda: tela_temperatura(pagina)).start()

    pagina.add(
        ft.Column(
            [
                header,
                scan_animation,
                status_text,
                progress,
                resultado,
                ft.ElevatedButton(
                    "Iniciar Verificação",
                    on_click=iniciar_verificacao
                ),
                ft.TextButton(
                    "Voltar",
                    on_click=lambda e: tela_consulta(pagina),
                    icon=ft.icons.ARROW_BACK
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_temperatura(pagina: ft.Page) -> None:
    """Tela de medição de temperatura"""
    pagina.clean()
    pagina.title = "Vitally - Temperatura"

    header = ft.Text(
        "Medição de Temperatura",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    scan_animation = ft.Image(
        src="images/sensor_loading.gif",
        width=200,
        height=200
    )

    status_text = ft.Text("Aguardando leitura do sensor...", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)

    def iniciar_medicao(e):
        scan_animation.visible = True
        status_text.value = "Lendo dados do sensor..."
        progress.visible = True
        e.control.visible = False
        pagina.update()

        def finalizar_medicao():
            scan_animation.visible = False
            progress.visible = False
            status_text.value = "Medição concluída!"
            resultado.value = f"{random.uniform(35.5, 37.5):.1f} °C"
            resultado.color = ft.colors.GREEN
            pagina.update()

            threading.Timer(2, lambda: tela_saturacao(pagina)).start()

        threading.Timer(3, finalizar_medicao).start()

    pagina.add(
        ft.Column(
            [
                header,
                scan_animation,
                status_text,
                progress,
                resultado,
                ft.ElevatedButton(
                    "Medir Temperatura",
                    on_click=iniciar_medicao,
                    icon=ft.icons.THERMOSTAT
                ),
                ft.TextButton(
                    "Voltar",
                    on_click=lambda e: tela_biometria(pagina, None),
                    icon=ft.icons.ARROW_BACK
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_saturacao(pagina: ft.Page) -> None:
    """Tela de saturação de oxigênio"""
    pagina.clean()
    pagina.title = "Vitally - Saturação"

    header = ft.Text(
        "Medição de Saturação",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    scan_animation = ft.Image(
        src="images/sensor_loading.gif",
        width=200,
        height=200
    )

    status_text = ft.Text("Aguardando leitura do sensor...", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)

    def iniciar_medicao(e):
        scan_animation.visible = True
        status_text.value = "Lendo dados do sensor..."
        progress.visible = True
        e.control.visible = False
        pagina.update()

        def finalizar_medicao():
            scan_animation.visible = False
            progress.visible = False
            status_text.value = "Medição concluída!"
            resultado.value = f"{random.randint(95, 100)}%"
            resultado.color = ft.colors.GREEN
            pagina.update()

            threading.Timer(2, lambda: tela_pressao(pagina)).start()

        threading.Timer(3, finalizar_medicao).start()

    pagina.add(
        ft.Column(
            [
                header,
                scan_animation,
                status_text,
                progress,
                resultado,
                ft.ElevatedButton(
                    "Medir Saturação",
                    on_click=iniciar_medicao,
                    icon=ft.icons.HEALTH_AND_SAFETY
                ),
                ft.TextButton(
                    "Voltar",
                    on_click=lambda e: tela_temperatura(pagina),
                    icon=ft.icons.ARROW_BACK
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_pressao(pagina: ft.Page) -> None:
    """Tela de pressão arterial"""
    pagina.clean()
    pagina.title = "Vitally - Pressão"

    header = ft.Text(
        "Medição de Pressão Arterial",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    scan_animation = ft.Image(
        src="images/sensor_loading.gif",
        width=200,
        height=200
    )

    status_text = ft.Text("Aguardando leitura do sensor...", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)

    def gerar_pressao():
        sistolica = random.randint(90, 180)
        diastolica = random.randint(60, 120)
        return f"{sistolica}/{diastolica} mmHg"

    def iniciar_medicao(e):
        scan_animation.visible = True
        status_text.value = "Lendo dados do sensor..."
        progress.visible = True
        e.control.visible = False
        pagina.update()

        def finalizar_medicao():
            scan_animation.visible = False
            progress.visible = False
            status_text.value = "Medição concluída!"
            resultado.value = gerar_pressao()
            resultado.color = ft.colors.GREEN
            pagina.update()

        threading.Timer(3, finalizar_medicao).start()

    pagina.add(
        ft.Column(
            [
                header,
                scan_animation,
                status_text,
                progress,
                resultado,
                ft.ElevatedButton(
                    "Medir Pressão",
                    on_click=iniciar_medicao,
                    icon=ft.icons.MONITOR_HEART
                ),
                ft.TextButton(
                    "Finalizar",
                    on_click=lambda e: tela_inicial(pagina),
                    icon=ft.icons.CHECK_CIRCLE
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def main(pagina: ft.Page) -> None:
    """Função principal"""
    pagina.window_width = 800
    pagina.window_height = 600
    pagina.window_resizable = False
    pagina.theme_mode = ft.ThemeMode.LIGHT
    tela_inicial(pagina)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")