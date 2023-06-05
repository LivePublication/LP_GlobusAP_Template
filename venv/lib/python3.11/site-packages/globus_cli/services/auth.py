import uuid

import globus_sdk


def _is_uuid(s):
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


class CustomAuthClient(globus_sdk.AuthClient):
    def _lookup_identity_field(
        self, id_name=None, id_id=None, field="id", provision=False
    ):
        assert (id_name or id_id) and not (id_name and id_id)

        kw = dict(provision=provision)
        if id_name:
            kw.update({"usernames": id_name})
        else:
            kw.update({"ids": id_id})

        try:
            return self.get_identities(**kw)["identities"][0][field]
        except (IndexError, KeyError):
            # IndexError: identity does not exist and wasn't provisioned
            # KeyError: `field` does not exist for the requested identity
            return None

    def maybe_lookup_identity_id(self, identity_name, provision=False):
        if _is_uuid(identity_name):
            return identity_name
        else:
            return self._lookup_identity_field(
                id_name=identity_name, provision=provision
            )

    def lookup_identity_name(self, identity_id):
        return self._lookup_identity_field(id_id=identity_id, field="username")
