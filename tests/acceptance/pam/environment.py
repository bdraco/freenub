import requests

from tests.acceptance import (
    CONTRACT_EXPECT_ENDPOINT,
    CONTRACT_INIT_ENDPOINT,
    MOCK_SERVER_URL,
)


def before_scenario(context, feature):
    for tag in feature.tags:
        if "contract" in tag:
            _, contract_name = tag.split("=")
            response = requests.get(
                MOCK_SERVER_URL + CONTRACT_INIT_ENDPOINT + contract_name
            )
            assert response


def after_scenario(context, feature):
    for tag in feature.tags:
        if "contract" in tag:
            response = requests.get(MOCK_SERVER_URL + CONTRACT_EXPECT_ENDPOINT)
            assert response

            response_json = response.json()

            assert not response_json["expectations"]["failed"]
            assert not response_json["expectations"]["pending"]
