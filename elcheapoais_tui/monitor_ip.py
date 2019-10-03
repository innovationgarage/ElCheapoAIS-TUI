import subprocess

def get_ips():
    return [l.split("netmask")[0].strip()[5:]
            for l in subprocess.run(
                    "ifconfig", check=True, stdout=subprocess.PIPE
            ).stdout.decode("utf-8").split("\n")
            if "inet " in l]
