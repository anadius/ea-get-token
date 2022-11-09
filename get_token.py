import sys
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
VERSION_DEFAULT = "12.38.0.5295"
VERSION_FILE = "version.txt"


if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
elif __file__:
    os.chdir(os.path.dirname(__file__))


def load_version():
    try:
        with open(VERSION_FILE) as f:
            version = f.read().strip()
        if re.match(r"^\d+\.\d+\.\d+\.\d+$") is None:
            return VERSION_DEFAULT
    except:
        return VERSION_DEFAULT


def save_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version)


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

    old_version = load_version()
    print("EA app saved version:", old_version)
    r = requests.get(
        "https://autopatch.juno.ea.com/autopatch/upgrade/buckets/85",
        headers={"User-Agent": f"EADesktop/{old_version}"},
        timeout=15,
    )
    data = r.json()
    version = data["recommended"]["version"]

    print("EA app current version:", version)

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
    if old_version != version:
        save_version(version)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exception(e)
    input("Press enter to exit.")
