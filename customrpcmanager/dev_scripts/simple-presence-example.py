from pypresence import Presence
import time

client_id = "xxx"  # from Discord Developer Portal
RPC = Presence(client_id)
RPC.connect()

RPC.update(
    name="test",
    details="test rpc",
    state="In Menu",
    large_image="icon",
    large_text="TEST RPC",
    start=time.time()
)

while True:
    time.sleep(15)
