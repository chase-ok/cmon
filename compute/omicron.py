
from shared.omicron import triggers_source
from compute import triggers

def triggers_process():
    #triggers.update_channels(triggers_source)
    #triggers.setup_tables(triggers_source)
    triggers.sync_triggers_process(triggers_source)

if __name__ == "__main__":
    triggers_process()
