import re
import traceback
import os

import pymem
import requests

PATTERN = br"authorization=Bearer ([a-zA-Z0-9=\._]{1,1000})"
QUERY = '''
            query getCurrentUser {
                me {
                    pd
                    personas {
                        psd
                        displayName
                        namespaceName
                    }
                }
            }
            '''
VERSION_DEFAULT = "13.128.0.5641"
LOG = r"%LocalAppData%\Electronic Arts\EA Desktop\Logs\EALauncher.log"
REG_EXP = r"\(eax::apps::utils::logAppInfo\)\s+Version:\s+(\d+\.\d+\.\d+[\-\.]\d+)"


def load_version():
    version = VERSION_DEFAULT
    try:
        with open(os.path.expandvars(LOG), encoding="utf-8") as f:
            for line in f:
                m = re.search(REG_EXP, line)
                if m is None:
                    continue
                version = m.group(1)
    except:
        pass

    return version.replace("-", ".")


def main():
    try:
        ea_app = pymem.Pymem("EADesktop.exe")
    except pymem.exception.ProcessNotFound:
        print("EA app process not found!")
        return

    offset = ea_app.pattern_scan_all(PATTERN)
    if offset is None:
        print("Access token not found, try again!")
        return

    data = ea_app.read_bytes(offset, 1021)
    match = re.match(PATTERN, data)
    token = match.group(1).decode()

    print("Got token!")

    version = load_version()

    r = requests.post(
        "https://service-aggregation-layer.juno.ea.com/graphql",
        headers={
            "User-Agent": f"EADesktop/{version}",
            "Authorization": f"Bearer {token}",
            "x-client-id": "EAX-JUNO-CLIENT",
            "Accept": "application/json",
        },
        json={"query": QUERY},
        timeout=15,
    )
    try:
        data = r.json()["data"]["me"]
        user_id = data["pd"]
    except (TypeError, KeyError):
        print(r.text)
        print("Something's wrong with the loaded profile, try again!")
        return

    print("Profile loaded!")

    username = None
    persona_id = None
    for persona in data["personas"]:
        if username is None or persona["namespaceName"] == "cem_ea_id":
            username = persona["displayName"]
            persona_id = persona["psd"]

            if persona["namespaceName"] == "cem_ea_id":
                break

    if username is None:
        print("Username not found!")
        return

    print("\nCopy these values:\n")
    print(token)
    print(username)
    print(user_id)
    print(persona_id)

    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exception(e)
    input("Press enter to exit.")
