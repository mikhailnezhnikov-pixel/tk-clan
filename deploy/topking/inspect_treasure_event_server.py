import importlib.util,json

server_path="/opt/hamsterking-license/server.py"
spec=importlib.util.spec_from_file_location("hk_server",server_path)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

print("RELEASE_VERSION",server.release_version())
print("MIN_SCRIPT_VERSION",server.MIN_SCRIPT_VERSION)
for version in ["1.17.24","1.17.81","1.17.82"]:
    plain=server.release_manifest(version)
    tokenized=server.release_manifest(version,"TEST_TOKEN")
    if tokenized.get("download_url"):
        tokenized["download_url"]=tokenized["download_url"].replace("TEST_TOKEN","[TOKEN]")
    print("UPDATE_MANIFEST",json.dumps({
        "version":version,
        "plain":plain,
        "tokenized":tokenized
    },ensure_ascii=False))
