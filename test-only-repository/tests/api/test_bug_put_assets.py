import requests

TIMEOUT = 30
ASSET_NAME = "LCA"
TAXA_NOVA = 5.0


def listar_ativos(base_url, auth_headers):
    """Retorna a lista completa de ativos (GET /api/assets)."""
    response = requests.get(
        f"{base_url}/api/assets",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, response.text
    return response.json()


def registros_do_ativo(ativos, asset_name):
    """Retorna (posicao na lista, taxa) de cada registro com o nome dado.

    A API nao expoe um ID de ativo, entao a posicao na listagem e usada
    como identificador do registro.
    """
    return [
        (posicao, ativo["annual_rate"])
        for posicao, ativo in enumerate(ativos)
        if ativo["asset_name"] == asset_name
    ]


def taxa_do_investimento(base_url, auth_headers, investment_id):
    """Retorna a taxa anual atual de um investimento da carteira."""
    response = requests.get(
        f"{base_url}/api/investments",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, response.text
    for item in response.json():
        if item["id"] == investment_id:
            return item["annual_rate"]
    return None


def imprimir_registros(titulo, registros):
    print(f"\n{titulo}")
    for posicao, taxa in registros:
        print(f"  Registro (posicao na lista): {posicao} | Taxa: {taxa}%")


def test_put_ativo_deve_atualizar_em_vez_de_criar_novo(
    base_url, auth_headers
):
    """Evidencia o defeito do PUT /api/assets.

    Esperado: alterar a taxa de um ativo existente atualiza o registro.
    Defeito investigado: o PUT cria um novo registro e mantem o antigo.
    """
    print("\n" + "=" * 64)
    print(" EVIDENCIA - PUT /api/assets cria novo ativo em vez de atualizar")
    print("=" * 64)

    # 1. Estado ANTES do PUT
    ativos_antes = listar_ativos(base_url, auth_headers)
    registros_antes = registros_do_ativo(ativos_antes, ASSET_NAME)
    assert len(registros_antes) > 0, f"Ativo {ASSET_NAME} nao encontrado."

    # 2. Cria um investimento de R$ 1.000,00 no ativo
    response = requests.post(
        f"{base_url}/api/investments",
        json={
            "asset_name": ASSET_NAME,
            "amount": 1000.00,
            "purchase_price": 1.00,
            "days_invested": 30,
            "planned_days": 365,
        },
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert response.status_code == 201, response.text
    investimento = response.json()
    taxa_original = investimento["annual_rate"]

    try:
        print(f"\nATIVO: {ASSET_NAME}")
        print(
            f"INVESTIMENTO CRIADO: id={investimento['id']} | "
            f"valor={investimento['amount']} | "
            f"tipo={investimento['asset_type']} | "
            f"taxa={taxa_original}%"
        )
        imprimir_registros("ATIVO ANTES DO PUT:", registros_antes)
        print(
            f"QUANTIDADE DE REGISTROS DO ATIVO ANTES: {len(registros_antes)}"
        )
        print(f"TOTAL DE ATIVOS NA API ANTES: {len(ativos_antes)}")

        # 3. Simulacao de rentabilidade
        response = requests.post(
            f"{base_url}/api/simulate/yield-monthly",
            json={"months": 12},
            headers=auth_headers,
            timeout=TIMEOUT,
        )
        print(
            f"\nSIMULACAO DE RENTABILIDADE (12 meses): "
            f"HTTP {response.status_code} | {response.text[:300]}"
        )

        # 4. Simulacao de resgate
        response = requests.post(
            f"{base_url}/api/simulate/tax-withdrawal",
            json={"target_amount": 500.00},
            headers=auth_headers,
            timeout=TIMEOUT,
        )
        print(
            f"SIMULACAO DE RESGATE (R$ 500,00): "
            f"HTTP {response.status_code} | {response.text[:300]}"
        )

        # 5. Altera somente a taxa do ativo
        response = requests.put(
            f"{base_url}/api/assets",
            json={"asset_name": ASSET_NAME, "annual_rate": TAXA_NOVA},
            headers=auth_headers,
            timeout=TIMEOUT,
        )
        print(
            f"\nPUT /api/assets: taxa alterada de {taxa_original}% para "
            f"{TAXA_NOVA}% | HTTP {response.status_code} | {response.text}"
        )
        assert response.status_code == 200, response.text

        # 6. Estado DEPOIS do PUT
        ativos_depois = listar_ativos(base_url, auth_headers)
        registros_depois = registros_do_ativo(ativos_depois, ASSET_NAME)
        taxa_investimento_depois = taxa_do_investimento(
            base_url, auth_headers, investimento["id"]
        )

        imprimir_registros("ATIVOS DEPOIS DO PUT:", registros_depois)
        print(
            f"QUANTIDADE DE REGISTROS DO ATIVO DEPOIS: {len(registros_depois)}"
        )
        print(f"TOTAL DE ATIVOS NA API DEPOIS: {len(ativos_depois)}")
        print(
            f"TAXA DO INVESTIMENTO {investimento['id']} DEPOIS DO PUT: "
            f"{taxa_investimento_depois}%"
        )

        novos = [r for r in registros_depois if r not in registros_antes]
        criou_novo = len(registros_depois) > len(registros_antes)

        print(f"\nREGISTROS NOVOS OU ALTERADOS: {novos}")
        print("\nRESULTADO:")
        if criou_novo:
            print(
                "  FALHA - o PUT criou um novo ativo em vez de atualizar "
                "o ativo existente."
            )
        else:
            print("  OK - o PUT nao criou um novo registro.")
        print("=" * 64)
    finally:
        requests.delete(
            f"{base_url}/api/investments/{investimento['id']}",
            headers=auth_headers,
            timeout=TIMEOUT,
        )

    taxas_depois = [taxa for _, taxa in registros_depois]

    assert len(registros_depois) == len(registros_antes), (
        f"O PUT criou um novo registro de {ASSET_NAME}: "
        f"{len(registros_antes)} antes, {len(registros_depois)} depois. "
        f"Taxas: {taxas_depois}"
    )
    assert len(ativos_depois) == len(ativos_antes), (
        f"O total de ativos aumentou de {len(ativos_antes)} para "
        f"{len(ativos_depois)} apos o PUT."
    )
    assert TAXA_NOVA in taxas_depois, (
        f"Nenhum registro de {ASSET_NAME} ficou com a taxa {TAXA_NOVA}%. "
        f"Taxas encontradas: {taxas_depois}"
    )
