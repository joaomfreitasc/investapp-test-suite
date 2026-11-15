import csv
import requests
import pytest
from pathlib import Path
# ---------------------------------------------------------------------
# Integrante 3 - Criacao de investimentos validos (POST /api/investments)
# ---------------------------------------------------------------------

CAMPOS_RESPOSTA = {
    "id",
    "user_id",
    "asset_name",
    "asset_type",
    "amount",
    "purchase_price",
    "days_invested",
    "planned_days",
    "annual_rate",
    "current_value",
    "future_value",
    "projected_profit",
}


# ---------------------------------------------------------------------
# GET /api/assets
# ---------------------------------------------------------------------

def buscar_ativo_existente(base_url, auth_headers):
    """Retorna o primeiro ativo cadastrado na API."""
    response = requests.get(
        f"{base_url}/api/assets",
        headers=auth_headers,
    )

    assert response.status_code == 200

    ativos = response.json()

    assert len(ativos) > 0, "Nenhum ativo cadastrado na API."

    return ativos[0]


def montar_payload(asset_name):
    """Monta um payload válido para criação de investimento."""
    return {
        "asset_name": asset_name,
        "amount": 1000.00,
        "purchase_price": 1.00,
        "days_invested": 30,
        "planned_days": 365,
    }


# ---------------------------------------------------------------------
# Fixture - cria investimento
# ---------------------------------------------------------------------

@pytest.fixture
def investimento_criado(base_url, auth_headers):
    """Cria um investimento válido."""

    ativo = buscar_ativo_existente(
        base_url,
        auth_headers,
    )

    payload = montar_payload(ativo["asset_name"])

    response = requests.post(
        f"{base_url}/api/investments",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201, (
        f"Falha ao criar investimento. "
        f"Resposta da API: {response.text}"
    )

    investimento = response.json()

    # Mostra o ID criado
    print("\n======================================")
    print("INVESTIMENTO CRIADO PELO FIXTURE")
    print("======================================")
    print(f"ID criado: {investimento['id']}")
    print(f"Ativo: {investimento['asset_name']}")
    print(f"Valor: {investimento['amount']}")
    print("======================================")

    yield ativo, payload, investimento

    # -------------------------------------------------------------
    # DELETE - limpeza após o teste
    # -------------------------------------------------------------

    print("\n--------------------------------------")
    print("LIMPANDO INVESTIMENTO DO FIXTURE")
    print("--------------------------------------")
    print(f"ID que será excluído: {investimento['id']}")

    delete_response = requests.delete(
        f"{base_url}/api/investments/{investimento['id']}",
        headers=auth_headers,
    )

    print(f"Status do DELETE: {delete_response.status_code}")

    assert delete_response.status_code == 200, (
        f"Falha ao excluir investimento criado pelo teste. "
        f"Resposta da API: {delete_response.text}"
    )

    print(f"✅ ID {investimento['id']} excluído com sucesso!")


# ---------------------------------------------------------------------
# TESTE POST - criação
# ---------------------------------------------------------------------

def test_criar_investimento_valido(investimento_criado):
    """Valida que a criação retorna 201 com os dados enviados."""

    _, payload, investimento = investimento_criado

    assert investimento["asset_name"] == payload["asset_name"]

    assert investimento["amount"] == pytest.approx(
        payload["amount"]
    )

    assert investimento["purchase_price"] == pytest.approx(
        payload["purchase_price"]
    )

    assert investimento["days_invested"] == payload["days_invested"]

    assert investimento["planned_days"] == payload["planned_days"]


# ---------------------------------------------------------------------
# TESTE POST - estrutura da resposta
# ---------------------------------------------------------------------

def test_criar_investimento_estrutura_da_resposta(
    investimento_criado
):
    """Valida que a resposta possui todos os campos do schema."""

    _, _, investimento = investimento_criado

    assert CAMPOS_RESPOSTA.issubset(
        investimento.keys()
    ), (
        f"Campos ausentes: "
        f"{CAMPOS_RESPOSTA - set(investimento.keys())}"
    )

    assert isinstance(investimento["id"], int)

    assert isinstance(investimento["user_id"], int)

    assert investimento["current_value"] is not None

    assert investimento["future_value"] is not None

    assert investimento["projected_profit"] is not None


# ---------------------------------------------------------------------
# TESTE POST - herança dos dados do ativo
# ---------------------------------------------------------------------

def test_criar_investimento_herda_dados_do_ativo(
    investimento_criado
):
    """Valida tipo e taxa anual preenchidos a partir do ativo."""

    ativo, _, investimento = investimento_criado

    assert investimento["asset_type"] == ativo["asset_type"]

    assert investimento["annual_rate"] == pytest.approx(
        ativo["annual_rate"]
    )


# ---------------------------------------------------------------------
# TESTE GET /api/investments
# ---------------------------------------------------------------------

def test_listar_investimentos(
    base_url,
    auth_headers,
    investimento_criado,
):
    """Valida que GET /api/investments retorna os investimentos."""

    _, _, investimento = investimento_criado

    response = requests.get(
        f"{base_url}/api/investments",
        headers=auth_headers,
    )

    assert response.status_code == 200

    investimentos = response.json()

    assert isinstance(investimentos, list)

    ids = [item["id"] for item in investimentos]

    assert investimento["id"] in ids


# ---------------------------------------------------------------------
# TESTE GET - estrutura da resposta
# ---------------------------------------------------------------------

def test_get_investimentos_estrutura(
    base_url,
    auth_headers,
):
    """Valida a estrutura retornada pelo GET."""

    response = requests.get(
        f"{base_url}/api/investments",
        headers=auth_headers,
    )

    assert response.status_code == 200

    investimentos = response.json()

    assert isinstance(investimentos, list)

    if len(investimentos) > 0:
        investimento = investimentos[0]

        assert CAMPOS_RESPOSTA.issubset(
            investimento.keys()
        ), (
            f"Campos ausentes: "
            f"{CAMPOS_RESPOSTA - set(investimento.keys())}"
        )


# ---------------------------------------------------------------------
# TESTE DELETE /api/investments/{investment_id}
# ---------------------------------------------------------------------


def test_deletar_investimento(
    base_url,
    auth_headers,
):
    """Cria um investimento e exclui vários IDs."""

    # 1. Busca um ativo
    ativo = buscar_ativo_existente(
        base_url,
        auth_headers,
    )

    # 2. Cria um investimento
    payload = montar_payload(ativo["asset_name"])

    create_response = requests.post(
        f"{base_url}/api/investments",
        json=payload,
        headers=auth_headers,
    )

    assert create_response.status_code == 201

    investimento = create_response.json()

    # ID criado automaticamente pela API
    id_criado = investimento["id"]

    print("\n======================================")
    print("TESTE DELETE - VÁRIOS IDs")
    print("======================================")
    print(f"ID criado pela API: {id_criado}")

    # 3. IDs que serão excluídos
    #
    # Os três primeiros são IDs definidos manualmente.
    # O último é o ID criado neste teste.
    ids_para_excluir = [
        id_criado,
    ]

    print("\nIDs que serão excluídos:")
    print(ids_para_excluir)

    # 4. Exclui cada ID
    for investment_id in ids_para_excluir:

        print("\n--------------------------------------")
        print(f"Tentando excluir ID: {investment_id}")
        print("--------------------------------------")

        delete_response = requests.delete(
            f"{base_url}/api/investments/{investment_id}",
            headers=auth_headers,
        )

        print(
            f"ID {investment_id} -> "
            f"Status: {delete_response.status_code}"
        )

        print(
            f"Resposta: {delete_response.text}"
        )

        # 200 = excluído
        # 404 = ID não existe
        assert delete_response.status_code in [200, 404]

        if delete_response.status_code == 200:
            print(
                f"✅ ID {investment_id} "
                "excluído com sucesso!"
            )
        elif delete_response.status_code == 404:
            print(
                f"⚠️ ID {investment_id} "
                "não foi encontrado."
            )

    print("\n======================================")
    print("FINALIZADO")
    print("======================================")



# ---------------------------------------------------------------------
# TESTE DELETE - verifica se realmente foi excluído
# ---------------------------------------------------------------------

def test_investimento_excluido_nao_aparece_na_listagem(
    base_url,
    auth_headers,
):
    """Valida que o investimento removido não aparece mais no GET."""

    # 1. Busca um ativo
    ativo = buscar_ativo_existente(
        base_url,
        auth_headers,
    )

    # 2. Cria investimento
    payload = montar_payload(ativo["asset_name"])

    create_response = requests.post(
        f"{base_url}/api/investments",
        json=payload,
        headers=auth_headers,
    )

    assert create_response.status_code == 201

    investimento = create_response.json()

    # Pega o ID criado
    investment_id = investimento["id"]

    print("\n======================================")
    print("VERIFICAÇÃO COMPLETA DO DELETE")
    print("======================================")
    print(f"ID criado: {investment_id}")

    # 3. DELETE
    print(f"\nExcluindo ID: {investment_id}")

    delete_response = requests.delete(
        f"{base_url}/api/investments/{investment_id}",
        headers=auth_headers,
    )

    print(f"Status do DELETE: {delete_response.status_code}")

    assert delete_response.status_code == 200

    # 4. GET
    print("\nConsultando investimentos novamente...")

    get_response = requests.get(
        f"{base_url}/api/investments",
        headers=auth_headers,
    )

    assert get_response.status_code == 200

    investimentos = get_response.json()

    ids = [item["id"] for item in investimentos]

    print(f"IDs existentes após DELETE: {ids}")

    # 5. O ID excluído não pode mais existir
    if investment_id not in ids:
        print(
            f"✅ CONFIRMADO: ID {investment_id} "
            "não existe mais na API."
        )
    else:
        print(
            f"❌ ERRO: ID {investment_id} "
            "ainda existe na API!"
        )

    assert investment_id not in ids


# ---------------------------------------------------------------------
# TESTE DELETE - ID inexistente
# ---------------------------------------------------------------------

def test_deletar_investimento_inexistente(
    base_url,
    auth_headers,
):
    """Valida que tentar excluir um investimento inexistente retorna 404."""

    id_inexistente = 999999999

    print("\n======================================")
    print("TESTE ID INEXISTENTE")
    print("======================================")
    print(f"ID utilizado: {id_inexistente}")

    response = requests.delete(
        f"{base_url}/api/investments/{id_inexistente}",
        headers=auth_headers,
    )

    print(f"Status retornado: {response.status_code}")
    print(f"Resposta: {response.text}")

    assert response.status_code == 404

    print("✅ API retornou 404 corretamente.")

# ---------------------------------------------------------------------
# Integrante 7 - Testes orientados a dados (DDT via CSV)
# ---------------------------------------------------------------------


def carregar_dados_investimentos_csv():
    """Lê dinamicamente o arquivo CSV localizado em tests/data/dados_investimentos.csv."""
    # .parent (api) -> .parent (tests) -> "data" / "dados_investimentos.csv"
    caminho_csv = Path(__file__).resolve().parent.parent / "data" / "dados_investimentos.csv"

    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo de massa CSV não encontrado em: {caminho_csv}")

    casos = []
    with open(caminho_csv, mode="r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            casos.append(
                (
                    linha["asset_name"],
                    float(linha["amount"]),
                    float(linha["purchase_price"]),
                    int(linha["days_invested"]),
                    int(linha["planned_days"]),
                    int(linha["status_esperado"]),
                )
            )
    return casos


@pytest.mark.parametrize(
    "asset, amount, price, days, planned, status_esperado",
    carregar_dados_investimentos_csv()
)
def test_criar_investimentos_ddt_csv(
    base_url, auth_headers, asset, amount, price, days, planned, status_esperado
):
    """Executa múltiplos cenários de criação de investimentos parametrizados via CSV."""
    payload = {
        "asset_name": asset,
        "amount": amount,
        "purchase_price": price,
        "days_invested": days,
        "planned_days": planned,
    }
    response = requests.post(f"{base_url}/api/investments", json=payload, headers=auth_headers)
    assert response.status_code == status_esperado