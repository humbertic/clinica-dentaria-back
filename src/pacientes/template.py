# src/pacientes/template.py

from typing import Literal, List
from pydantic import BaseModel

class Pergunta(BaseModel):
    id: str                    # chave única para o campo, ex. "estado_civil"
    label: str                 # texto a exibir no formulário
    type: Literal[
        "text",      # campo de texto simples
        "date",      # selecção de data
        "boolean",   # sim/não (checkbox ou switch)
        "textarea",  # área de texto multiline
        "object"     # objeto com subcampos (e.g. { 'sim': bool, 'detalhes': str })
    ]
    required: bool = False     # indica se o campo é obrigatório
    options: List[str] = []    # para selecções fixas (ex. sexo: ["M","F","Outro"])
    subfields: List[str] = []  # nomes de subcampos em type="object"

# -----------------------------------------------------------------------------
# Lista de perguntas do questionário de Ficha Clínica (fotográfico)
# -----------------------------------------------------------------------------
QUESTIONARIO: List[Pergunta] = [
    # — Cabeçalho —
    Pergunta(id="nome_paciente",     label="Paciente (nome completo)",         type="text",     required=True),
    Pergunta(id="data_nascimento",   label="Data de Nascimento",               type="date",     required=True),
    Pergunta(id="idade",             label="Idade",                            type="text",     required=False),
    Pergunta(id="sexo",              label="Género",                           type="text",     required=False, options=["M","F"]),
    Pergunta(id="estado_civil",      label="Estado Civil",                     type="text",     required=False),
    Pergunta(id="profissao",         label="Profissão",                        type="text",     required=False),
    Pergunta(id="endereco",          label="Endereço",                         type="textarea", required=False),
    Pergunta(id="telefone_residencial", label="Telefone Residencial",          type="text",     required=False),
    Pergunta(id="local_trabalho",    label="Local de Trabalho",                type="text",     required=False),
    Pergunta(id="telefone_trabalho", label="Telefone do Trabalho",             type="text",     required=False),
    Pergunta(id="tipo_beneficiario", label="Tipo de Beneficiário",             type="text",     required=False),
    Pergunta(id="numero_beneficiario", label="N.º de Beneficiário",            type="text",     required=False),
    Pergunta(id="recomendado_por",   label="Recomendado por",                  type="text",     required=False),
    Pergunta(id="data_questionario", label="Data do Questionário",            type="date",     required=False),

    # — Queixa Principal —
    Pergunta(id="queixa_principal",  label="1. Queixa Principal",              type="textarea", required=False),

    # — História Médica e Odontológica —
    Pergunta(
        id="tratamento_medico",
        label="Está em tratamento médico? Qual?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="medicamento",
        label="Toma algum medicamento? Qual?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="alergia_medicamento",
        label="Tem alergia a medicamento, alimento, anestésico ou outro?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="condicoes_sistêmicas",
        label="Apresenta diabetes, hemofilia, anemia, hipertensão, dermatológicas, cardíacas, hepáticas, renais ou outras?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="historico_familiar",
        label="Existem casos de diabetes, tuberculose ou cancro na família?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="sintomas_gerais",
        label="Apresenta sinais/sintomas: sede, urina frequente, febre, diarreia, cansaço, etc.?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="exames_dst",
        label="Já fez exames para DST (hepatite B/C, AIDS, gonorreia, sífilis)?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="historico_cirurgico",
        label="Já se submeteu a alguma cirurgia? Qual?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="febre_reumatica",
        label="Tem ou teve febre reumática, endocardite ou requer antibiótico antes de procedimento odontológico?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="fumante",
        label="É fumante? Qual a quantidade?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="alcool",
        label="Ingere bebidas alcoólicas? Qual frequência?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="desmaios",
        label="Já apresentou desmaios, ataques ou perda de consciência?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="hemorragia",
        label="Teve hemorragias ou distúrbios de coagulação?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="condicao_mulher",
        label="Para mulheres: grávida, menopausa ou usa anticoncepcionais orais?",
        type="object",
        required=False,
        subfields=["gravida", "menopausa", "anticoncepcionais"]
    ),
    Pergunta(
        id="tratamento_odontologico_previo",
        label="Já realizou tratamento odontológico? Qual tipo?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="sangramento_gengival",
        label="Apresenta sangramento gengival, mobilidade dentária, dor ou mau hábito?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),
    Pergunta(
        id="higiene_bucal",
        label="Já recebeu orientações sobre higiene bucal?",
        type="object",
        required=False,
        subfields=["sim", "detalhes"]
    ),

    # — Exame Clínico —
    Pergunta(
        id="exame_clinico",
        label="3. Exame Clínico (Extra/Intra bucal)",
        type="textarea",
        required=False
    ),

    # — Plano Geral de Tratamento —
    Pergunta(
        id="plano_geral",
        label="6. Plano Geral de Tratamento (mapa dentário e notas)",
        type="object",
        required=False,
        subfields=["mapa_dentario", "notas"]
    ),

    # — Observações Finais —
    Pergunta(
        id="observacoes_finais",
        label="Observações Finais",
        type="textarea",
        required=False
    ),
]
