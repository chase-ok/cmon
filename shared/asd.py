
from shared import data, channels

H5_FILE = "asd.h5"
write_h5 = lambda: data.write_h5(H5_FILE)
read_h5 = lambda: data.read_h5(H5_FILE)

strain_asd = data.SpectralTable("asd", channels.strain)
