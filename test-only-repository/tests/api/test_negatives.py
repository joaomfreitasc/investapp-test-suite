import os
import pytest
import requests

TEST_USER = os.getenv("TEST_USER")


def test_acesso_nao_autorizado_sem_token(base_url):
    """Valida o acesso a um endpoint protegido sem o token Bearer (HTTP 401)."""
    response = requests.get(f"{base_url}/api/investments")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_acesso_com_token_invalido(base_url):
    """Valida o acesso com um token JWT malformado ou inválido (HTTP 401)."""
    headers = {"Authorization": "Bearer token_invalido_12345"}
    response = requests.get(f"{base_url}/api/investments", headers=headers)
    
    assert response.status_code == 401


def test_criar_investimento_payload_invalido_422(base_url, auth_headers):
    """Valida a rejeição por payload com tipos de dados incorretos ou campos faltando (HTTP 422)."""
    # Enviando 'amount' como string em vez de float/number
    payload = {
        "asset_name": "CDB",
        "amount": "valor_nao_numerico",
        "purchase_price": 1.00,
        "days_invested": 30,
        "planned_days": 365,
    }
    response = requests.post(f"{base_url}/api/investments", json=payload, headers=auth_headers)
    
    assert response.status_code == 422


def test_requisicao_bad_request_400(base_url, auth_headers):
    """Valida regra de negócio que resulta em requisição inválida/bad request (HTTP 400)."""
    # Exemplo tentando criar um investimento com valores logicamente proibidos (ex: quantidade negativa)
    payload = {
        "asset_name": "Ação XP",
        "amount": -500.00,
        "purchase_price": 10.00,
        "days_invested": 10,
        "planned_days": 100,
    }
    response = requests.post(f"{base_url}/api/investments", json=payload, headers=auth_headers)
    
    # Dependendo da validação da API, regras de negócio inválidas retornam 400 ou 422
    assert response.status_code in [400, 422]