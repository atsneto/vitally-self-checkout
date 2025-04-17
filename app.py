import flet as ft
import threading
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
    loading = ft.ProgressRing(visible=False)

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
                loading,
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

        # Agendar finalização após 3 segundos
        threading.Timer(3, finalizar_verificacao).start()

    def finalizar_verificacao():
        scan_animation.src = "images/success_checkmark.gif"
        status_text.value = "Verificação bem-sucedida!"
        progress.visible = False
        resultado.value = "Biometria validada com sucesso"
        resultado.color = ft.colors.GREEN
        pagina.update()
        
        # Agendar navegação após 2 segundos
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
    resultado = ft.Text(size=16, text_align=ft.TextAlign.CENTER)


    pagina.add(
        ft.Column(
            [
                header,
                ft.ElevatedButton(
                    "Registrar Temperatura",
                    on_click=registrar_temperatura,
                    icon=ft.icons.THERMOSTAT
                ),
                resultado,
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
    """Tela de registro de saturação de oxigênio"""
    pagina.clean()
    pagina.title = "Vitally - Saturação de Oxigênio"
    
    header = ft.Text(
        "Registro de Saturação de Oxigênio",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )

    saturacao_input = ft.TextField(
        label="Digite a saturação de oxigênio (%):",
        hint_text="Exemplo: 98",
        text_align=ft.TextAlign.CENTER,
        border_color="gray",
        border_radius=10,
        bgcolor="white",
        color="black",
        width=300
    )

    resultado = ft.Text(size=16, text_align=ft.TextAlign.CENTER)

    def registrar_saturacao(e):
        valor = saturacao_input.value.strip()
        if not valor.isdigit() or not (0 <= int(valor) <= 100):
            resultado.value = "Por favor, insira um valor válido entre 0 e 100."
            resultado.color = "red"
        else:
            resultado.value = f"Saturação registrada com sucesso: {valor}%"
            resultado.color = "green"
        pagina.update()

    pagina.add(
        ft.Column(
            [
                header,
                saturacao_input,
                ft.ElevatedButton(
                    "Registrar Saturação",
                    on_click=registrar_saturacao,
                    icon=ft.icons.HEALTH_AND_SAFETY
                ),
                resultado,
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

def main(pagina: ft.Page) -> None:
    """Função principal"""
    pagina.window_width = 800
    pagina.window_height = 600
    pagina.window_resizable = False
    pagina.theme_mode = ft.ThemeMode.LIGHT
    tela_inicial(pagina)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")