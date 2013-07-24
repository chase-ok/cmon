
from shared import triggers
from os.path import join


EXCESS_POWER_ROOT = "/home/detchar/excesspower"
ER3_TRIGGERS_ROOT = join(EXCESS_POWER_ROOT, "ER3")
ER4_TRIGGERS_ROOT = join(EXCESS_POWER_ROOT, "ER4")
TRIGGERS_ROOT = ER3_TRIGGERS_ROOT
SPECTRA_ROOT = EXCESS_POWER_ROOT

triggers_source = triggers.Source(name='excesspower', root=TRIGGERS_ROOT)
triggers.add_source(triggers_source)

# TODO: move me to shared/spectra.py
def get_spectrum_directory(channel):
    return JOIN(SPECTRA_ROOT, 
                '{0.ifo}/{0.subsystem}/{0.name}/spectra'.format(channel)) 


