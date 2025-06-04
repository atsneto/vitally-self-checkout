import time

import flet as ft
import threading
import random

import serial
from models import Pessoa, Paciente
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
        color=ft.Colors.BLUE_800
    )

    cpf_input = ft.TextField(
        hint_text="000.000.000-00",
        input_filter=ft.InputFilter(r"\d+"),
        max_length=11,
        text_align=ft.TextAlign.LEFT,
        width=300,
        border_radius=10,
        prefix_icon=ft.Icons.SEARCH
    )

    resultado = ft.Text(size=16, text_align=ft.TextAlign.CENTER)

    def consultar_cpf(e):
        global pessoa
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
                tela_biometria(pagina)

        except Exception as e:
            mostrar_erro(f"Erro de conexão: {str(e)}", pagina, resultado)

    btn_voltar = ft.TextButton(
        "Voltar",
        on_click=lambda e: tela_inicial(pagina),
        icon=ft.Icons.ARROW_BACK
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
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, padding=20)
                ),
                btn_voltar
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_biometria(pagina: ft.Page) -> None:
    """Tela de verificação biométrica"""
    pagina.clean()
    pagina.title = "Vitally - Biometria"

    header = ft.Text(
        "Verificação Biométrica",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    nome_pessoa = ft.Text(
        pessoa.name,
        size=20,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.BLUE_800
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
        nome_pessoa.visible = False
        e.control.visible = False
        pagina.update()

        threading.Timer(3, finalizar_verificacao).start()

    def finalizar_verificacao():
        scan_animation.src = "images/success_checkmark.gif"
        status_text.value = "Verificação bem-sucedida!"
        progress.visible = False
        resultado.value = "Biometria validada com sucesso"
        resultado.color = ft.Colors.GREEN
        pagina.update()

        threading.Timer(2, lambda: tela_temperatura(pagina)).start()

    pagina.add(
        ft.Column(
            [
                header,
                nome_pessoa,
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
                    icon=ft.Icons.ARROW_BACK
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()
valor_temperatura = None
def tela_temperatura(pagina: ft.Page) -> None:
    pagina.clean()
    pagina.title = "Vitally - Temperatura"

    header = ft.Text(
        "Medição de Temperatura",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    scan_animation = ft.Image(src="images/sensor_loading.gif", width=200, height=200, visible=False)
    status_text = ft.Text("Aguardando leitura do sensor...", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)

    leitura_ativa = False
    ser = None


    def ler_sensor():
        nonlocal leitura_ativa, ser
        global valor_temperatura
        try:
            ser = serial.Serial('COM3', 115200, timeout=120)
            leitura_ativa = True
            inicio = time.time()
            while leitura_ativa and (time.time() - inicio < 120):
                if ser.in_waiting:
                    linha = ser.readline().decode('utf-8').strip()
                    if linha:
                        valor_temperatura = linha
                        resultado.value = f"{linha} Cº"
                        resultado.color = ft.Colors.GREEN
                        status_text.value = "Dados recebidos do sensor"

                        pagina.update()
            parar_medicao()
            status_text.value = "Medição finalizada."
            print(valor_temperatura)
            pagina.update()
            time.sleep(6)  # pausa breve antes de transição

            tela_saturacao(pagina)  # redireciona após 2 minutos
        except Exception as e:
            status_text.value = f"Erro: {e}"
            pagina.update()

    def iniciar_medicao(e):
        nonlocal leitura_ativa
        scan_animation.visible = True
        status_text.value = "Lendo dados do sensor..."
        progress.visible = True
        e.control.visible = False
        pagina.update()

        thread = threading.Thread(target=ler_sensor, daemon=True)
        thread.start()

    def parar_medicao():
        nonlocal leitura_ativa
        leitura_ativa = False
        if ser and ser.is_open:
            ser.close()

    pagina.add(
        ft.Column(
            [
                header,
                scan_animation,
                status_text,
                progress,
                resultado,
                ft.ElevatedButton("Medir Temperatura", on_click=iniciar_medicao, icon=ft.Icons.THERMOSTAT),
                ft.TextButton("Voltar", on_click=lambda e: [parar_medicao(), tela_biometria(pagina, None)], icon=ft.Icons.ARROW_BACK)
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

# def tela_temperatura(pagina: ft.Page) -> None:
#     pagina.clean()
#     pagina.title = "Vitally - Temperatura"
#
#     header = ft.Text(
#         "Medição de Temperatura",
#         size=24,
#         weight=ft.FontWeight.BOLD,
#         color=ft.Colors.BLUE_800
#     )
#
#     scan_animation = ft.Image(src="images/sensor_loading.gif", width=200, height=200, visible=False)
#     status_text = ft.Text("Aguardando leitura...", size=16)
#     progress = ft.ProgressRing(visible=False)
#     resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)
#
#     def iniciar_medicao(e):
#         scan_animation.visible = True
#         status_text.value = "Lendo dados simulados..."
#         progress.visible = True
#         e.control.visible = False
#         pagina.update()
#
#         def finalizar_medicao():
#             scan_animation.visible = False
#             progress.visible = False
#             status_text.value = "Medição concluída!"
#             temp = round(random.uniform(36.0, 40.2), 1)
#             resultado.value = f"{temp} °C"
#             resultado.color = ft.Colors.GREEN
#             pagina.update()
#             threading.Timer(4, lambda: tela_saturacao(pagina)).start()
#
#         threading.Timer(4, finalizar_medicao).start()
#
#     pagina.add(
#         ft.Column(
#             [
#                 header,
#                 scan_animation,
#                 status_text,
#                 progress,
#                 resultado,
#                 ft.ElevatedButton("Medir Temperatura", on_click=iniciar_medicao, icon=ft.Icons.THERMOSTAT),
#                 ft.TextButton("Voltar", on_click=lambda e: tela_biometria(pagina), icon=ft.Icons.ARROW_BACK)
#             ],
#             spacing=25,
#             horizontal_alignment=ft.CrossAxisAlignment.CENTER,
#         )
#     )
#     pagina.update()
valor_saturacao = None
def tela_saturacao(pagina: ft.Page) -> None:
    """Tela de saturação de oxigênio"""
    pagina.clean()
    pagina.title = "Vitally - Saturação"
    global valor_saturacao


    header = ft.Text(
        "Medição de Saturação",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
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
            global valor_saturacao
            progress.visible = False
            status_text.value = "Medição concluída!"
            valor_saturacao = f"{random.randint(95, 100)}"
            text = " %"
            resultado.value = valor_saturacao + text
            resultado.color = ft.Colors.GREEN
            print(valor_saturacao)
            pagina.update()

            threading.Timer(4, lambda: tela_pressao(pagina)).start()

        threading.Timer(4, finalizar_medicao).start()

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
                    icon=ft.Icons.HEALTH_AND_SAFETY
                ),
                ft.TextButton(
                    "Voltar",
                    on_click=lambda e: tela_temperatura(pagina),
                    icon=ft.Icons.ARROW_BACK
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

valor_pressao = None
def tela_pressao(pagina: ft.Page) -> None:
    """Tela de pressão arterial"""
    pagina.clean()
    pagina.title = "Vitally - Pressão"
    global valor_pressao

    header = ft.Text(
        "Medição de Pressão Arterial",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    scan_animation = ft.Image(
        src="images/sensor_loading.gif",
        width=200,
        height=200,
        visible=False
    )

    status_text = ft.Text("Aguardando leitura do sensor...", size=16)
    progress = ft.ProgressRing(visible=False)
    resultado = ft.Text(size=24, weight=ft.FontWeight.BOLD)

    def gerar_pressao():
        global valor_pressao
        sistolica = random.randint(90, 180)
        diastolica = random.randint(60, 120)
        valor_pressao = f"{sistolica}/{diastolica}"
        return valor_pressao

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
            text = " mmHg"
            resultado.value = gerar_pressao() + text
            resultado.color = ft.Colors.GREEN
            print(valor_pressao)
            pagina.update()

        threading.Timer(4, finalizar_medicao).start()

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
                    icon=ft.Icons.MONITOR_HEART
                ),
                ft.TextButton(
                    "Finalizar",
                    on_click=lambda e: tela_sintomas(pagina),
                    icon=ft.Icons.CHECK_CIRCLE
                )
            ],
            spacing=25,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()

def tela_sintomas(pagina: ft.Page) -> None:
    """Tela de sintomas com classificação de risco considerando sinais vitais"""
    pagina.clean()
    pagina.title = "Vitally - Sintomas"

    header = ft.Text(
        "Selecione os sintomas apresentados",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    sintomas = [
        "Tosse", "Dor de cabeça", "Cansaço",
        "Dor no corpo", "Falta de ar", "Perda de olfato", "Dor de garganta"
    ]

    checkboxes = [ft.Checkbox(label=s) for s in sintomas]
    resultado = ft.Text()

    def confirmar(e):
        global selecionados
        selecionados = [cb.label for cb in checkboxes if cb.value]

        if not selecionados:
            resultado.value = "Nenhum sintoma selecionado."
            resultado.color = ft.Colors.GREY
            pagina.update()
            return

        resultado.value = "Sintomas selecionados:\n- " + "\n- ".join(selecionados)
        resultado.color = ft.Colors.GREEN
        pagina.update()

        # Sintomas graves definidos
        sintomas_graves = {"Falta de ar", "Febre", "Cansaço"}
        num_graves = len([s for s in selecionados if s in sintomas_graves])
        sintomas_criticos = "Falta de ar" in selecionados and "Febre" in selecionados and "Cansaço" in selecionados

        # Tratamento dos valores globais (todos strings)
        try:
            temp = float(valor_temperatura.replace(",", "."))
            saturacao = int(valor_saturacao.strip())
            sistolica, diastolica = map(int, valor_pressao.strip().split("/"))
        except Exception as ex:
            resultado.value = f"Erro ao interpretar sinais vitais: {ex}"
            resultado.color = ft.Colors.RED
            pagina.update()
            return

        # Verificações clínicas
        sinais_criticos = (
                temp < 34 or temp >= 40 or
                saturacao < 95 or
                sistolica < 90 or sistolica > 180 or
                diastolica < 60 or diastolica > 120
        )

        # Lógica de classificação
        if sintomas_criticos or sinais_criticos:
            cor = "vermelho"
        elif num_graves >= 2 or len(selecionados) >= 4:
            cor = "amarelo"
        else:
            cor = "verde"

        # Redireciona após 4 segundos
        threading.Timer(4, lambda: tela_classificacao(pagina, cor)).start()

    btn_confirmar = ft.ElevatedButton("Confirmar", on_click=confirmar)

    btn_voltar = ft.TextButton(
        "Voltar",
        on_click=lambda e: tela_pressao(pagina),
        icon=ft.Icons.ARROW_BACK
    )

    pagina.add(
        ft.Column(
            [
                header,
                *checkboxes,
                btn_confirmar,
                resultado,
                btn_voltar
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    pagina.update()


# NOVA FUNÇÃO ADICIONADA
def tela_classificacao(pagina: ft.Page, cor: str) -> None:
    """Tela de classificação de risco do paciente"""
    from models import Paciente
    from database import Session
    import datetime

    pagina.clean()
    pagina.title = "Vitally - Classificação de Risco"

    # Mapeamento da cor para o nível de risco
    cor_para_risco = {
        "verde": 1,
        "amarelo": 3,
        "vermelho": 5
    }
    risk_level = cor_para_risco.get(cor, 1)

    # Persistência do paciente
    try:
        with Session() as session:
            # Verifica se já existe um paciente para essa pessoa
            paciente = session.query(Paciente).filter_by(id=pessoa.id).first()
            selecionadosString = ", ".join(selecionados)
            if not paciente:
                paciente = Paciente(
                    id=pessoa.id,
                    description=selecionadosString,
                    temperatura=valor_temperatura,
                    saturacao=valor_saturacao,
                    pressao=valor_pressao,
                    risk_level=risk_level,
                    data_consulta=datetime.date.today(),
                    hora_consulta=datetime.datetime.now().time()
                )
                session.add(paciente)
            else:
                paciente.risk_level = risk_level
                paciente.data_consulta = datetime.date.today()
                paciente.hora_consulta = datetime.datetime.now().time()
            session.commit()
    except Exception as e:
        print(f"Erro ao salvar paciente: {e}")

    if cor == "verde":
        cor_texto = "Classificação Verde: Pouco Urgente"
        cor_corpo = ft.Colors.GREEN
    elif cor == "amarelo":
        cor_texto = "Classificação Amarela: Urgente"
        cor_corpo = ft.Colors.AMBER
    elif cor == "vermelho":
        cor_texto = "Classificação Vermelha: Emergência"
        cor_corpo = ft.Colors.RED
    else:
        cor_texto = "Classificação Desconhecida"
        cor_corpo = ft.Colors.GREY

    header = ft.Text(
        cor_texto,
        size=26,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER
    )

    instrucoes = ft.Text(
        "Por favor, retire sua ficha de espera e aguarde ser chamado.",
        size=18,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER
    )

    pagina.add(
        ft.Container(
            content=ft.Column(
                [
                    header,
                    instrucoes,
                    ft.Icon(name=ft.Icons.LOCAL_PRINTSHOP, size=64, color=ft.Colors.WHITE),
                    ft.TextButton(
                        "Voltar ao início",
                        on_click=lambda e: tela_inicial(pagina),
                        icon=ft.Icons.HOME
                    )
                ],
                spacing=30,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            bgcolor=cor_corpo,
            padding=50,
            expand=True
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