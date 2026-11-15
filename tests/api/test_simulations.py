import requests


def test_simulacao_rendimento_mensal_sucesso(
    base_url, auth_headers
):
    """
    Testa a simulação de rendimento mensal
    para um período de 12 meses.
    """

    # Dados enviados para a API
    payload = {
        "months": 12
    }

    # Envia a requisição POST
    response = requests.post(
        f"{base_url}/api/simulate/yield-monthly",
        json=payload,
        headers=auth_headers,
        timeout=30
    )

    # 1. Verifica se a requisição foi bem-sucedida primeiro
    assert response.status_code == 200, (
        f"Esperado HTTP 200, recebido "
        f"{response.status_code}. "
        f"Resposta: {response.text}"
    )

    # 2. Converte a resposta JSON para um dicionário
    resultado = response.json()

    # 3. Verifica se a resposta é um dicionário contendo a chave esperada
    assert isinstance(resultado, dict), "A resposta deveria ser um dicionário."
    assert "monthly_breakdown" in resultado, "A resposta deve conter 'monthly_breakdown'."

    # 4. Opcional: valida que o breakdown não está vazio
    assert len(resultado["monthly_breakdown"]) > 0, (
        "O detalhamento mensal (monthly_breakdown) veio vazio."
    )


def test_simular_resgate_otimizacao_fiscal(base_url, auth_headers):
    """
    Valida o cálculo e simulação de resgate com otimização fiscal.
    Endpoint: POST /api/simulations/tax-withdrawal
    """
    payload = {
        "investment_id": "12345",  # Ajuste o ID conforme necessário/esperado pela API
        "withdrawal_amount": 1000.00
    }

    # Requisição POST utilizando a fixture de autenticação
    response = requests.post(
        f"{base_url}/api/simulations/tax-withdrawal",
        json=payload,
        headers=auth_headers
    )
