
from shared import triggers
from os.path import join


OMICRON_ROOT = "/home/detchar/triggers"
POSTER3_TRIGGERS_ROOT = join(OMICRON_ROOT, "POSTER3")
ER4_TRIGGERS_ROOT = join(OMICRON_ROOT, "ER4")
TRIGGERS_ROOT = ER4_TRIGGERS_ROOT

triggers_source = triggers.Source(name='omicron', root=TRIGGERS_ROOT)
triggers.add_source(triggers_source)
