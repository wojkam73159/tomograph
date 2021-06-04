import math

import pydicom as pydicom
import streamlit as st
import numpy as np
import tomograf as tom
import matplotlib.pyplot as plt
import datetime
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom._storage_sopclass_uids import MRImageStorage


def save(img, name, comment, id_pacjenta, date, my_file):
    suffix = '.dcm'

    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.ImplementationClassUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(my_file, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.ImagesInAcquisition = "1"
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'

    ds.PixelRepresentation = 0

    savedImg = img / np.max(img) * (256 - 1)
    savedImg[savedImg < 0] = 0
    savedImg = savedImg.astype(np.uint16)
    ds.Rows, ds.Columns = savedImg.shape
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelData = (savedImg * 255).astype(np.uint16).tobytes()


    ds.PatientName = name
    ds.PatientID = id_pacjenta
    ds.StudyDescription = comment
    ds.StudyDate = date

    ds.is_little_endian = True
    ds.is_implicit_VR = True

    dt = datetime.datetime.now()
    ds.ContentDate = dt.strftime('%Y%m%d')
    time_str = dt.strftime('%H%M%S.%f')
    ds.ContentTime = time_str

    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRBigEndian

    pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
    ds.save_as('zdjęcia/' + my_file + suffix, write_like_original=False)


st.set_option('deprecation.showPyplotGlobalUse', False)  # disable warnings
num_of_scans = st.sidebar.number_input("#of scans", 1, 400, 50, 1)
num_of_detectors = st.sidebar.number_input("#of detectors", 1, 400, 20, 1)
beam_extent = st.sidebar.number_input("Beam Extent[Radians]", 0.0, 2*math.pi, math.pi / 2, 0.1)
use_filter = st.sidebar.checkbox('use filter')
show_steps = st.sidebar.checkbox('show steps')
which_plot = st.sidebar.slider('which step to show', min_value=1, max_value=num_of_scans//10)

status_text = st.sidebar.empty()

file = st.file_uploader("Upload Files")
ds = pydicom.dcmread(file)
image = ds.pixel_array
st.write("Input dicom:")
fig = plt.imshow(image, 'gray')
st.pyplot()


scanner = tom.Scanner(image, beam_extent=beam_extent, num_scans=num_of_scans, num_detectors=num_of_detectors)
sin = scanner.sinogram()
st.write("Sinogram:")
fig = plt.imshow(sin, 'gray')
st.pyplot()



reconstruct,to_plot = scanner.scan(use_filter=use_filter)
j=0
if show_steps:
    st.write("Step:{}".format(which_plot*10))
    plt.imshow(to_plot[which_plot-1], 'gray')
    #plt.colorbar()
    st.pyplot()
st.write("ostateczny wynik")
plt.imshow(reconstruct, 'gray')
st.pyplot()


st.write("wpisze dane pacjenta dla formatu dicom wynik w pliku \"{imie}{nazwisko}.dcm\"")
# dicom
imie_nazwisko = st.text_input('imie i nazwisko pacjenta')
temp=imie_nazwisko.split()
filename = "".join(temp)
plec = st.multiselect('plec', ["mezczyzna", "kobieta"])
data = st.date_input('data badania')

komentarz = st.text_input('komentarz lekarza')
identyfikator = st.text_input('identyfikator dicoma')



save(reconstruct, imie_nazwisko, komentarz, identyfikator, data, filename)
st.button("Re-run")



