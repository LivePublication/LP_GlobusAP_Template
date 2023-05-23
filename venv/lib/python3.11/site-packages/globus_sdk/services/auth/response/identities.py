from globus_sdk.response import IterableResponse


class GetIdentitiesResponse(IterableResponse):
    """
    Response class specific to the Get Identities API

    Provides iteration on the "identities" array in the response.
    """

    default_iter_key = "identities"
