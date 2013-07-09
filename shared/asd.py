
from shared import data, channels

H5_FILE = "asd.h5"
open_h5 = lambda mode=None: data.open_h5(H5_FILE, mode=mode)
use_h5 = data.use_h5(H5_FILE)

strain_asd = data.SpectralTable("asd", channels.strain)
