import numpy
import scipy.io.wavfile
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.utils import shuffle

from scipy.fftpack import dct

#file_address = './data/0_jackson_0.wav'
frame_size = 0.025  # number of seconds of each frame
frame_stride = 0.01  # size of stride between two frames (frame_size - frame_stride = overlap between frames)
nfilt = 40  # No. triangular filters converting from Hz to Mel
frame_limit = 63  # No. frames limited, about 0.6 seconds


def mfcc_calc(file_address, frame_size=frame_size, frame_stride=frame_stride, nfilt=nfilt, frame_limit=frame_limit):
    sample_rate, signal = scipy.io.wavfile.read(file_address) # sample_rate: number of samples per second
                                                              # signal: 1D vector of audio data

    # create shorter-term frame for signal

    frame_length, frame_step = frame_size * sample_rate, frame_stride * sample_rate
    signal_length = len(signal)
    frame_length = int(round(frame_length))
    frame_step = int(round(frame_step))
    if (signal_length > frame_length):
        num_steps = int(numpy.ceil(float(signal_length - frame_length) / frame_step))
    else:
        num_steps = 1
    num_frames = num_steps + 1
    pad_signal_length = num_steps * frame_step + frame_length # number of zeros to pad at the end of signal
    pad_vector = numpy.zeros((pad_signal_length - signal_length))
    pad_signal = numpy.append(signal, pad_vector)
    indices = numpy.tile(numpy.arange(0, frame_length), (num_frames, 1)) + \
                numpy.tile(numpy.arange(0, num_frames * frame_step, frame_step), (frame_length, 1)).T
              # indices in signal to slice to form frames
    frames = pad_signal[indices.astype(numpy.int32, copy=False)]

    # apply hamming function for FFT
    frames *= numpy.hamming(frame_length)

    #Report some values
    #print('sample_rate: ', sample_rate)
    #print('frame_length: ', frame_length)
    #print('frame_step: ', frame_step)
    #print('signal_length: ', signal_length)
    #print('num_frames: ', num_frames)
    #print('pad_signal_length: ', pad_signal_length)
    #print('frames: ', frames)

    # Fourier Transform and Power Spectrum
    NFFT = 512
    mag_frames = numpy.absolute(numpy.fft.rfft(frames, NFFT))  # Magnitude of the FFT
    pow_frames = ((1.0 / NFFT) * ((mag_frames) ** 2))  # Power Spectrum

    #Report some values
    #print('mag_frames: ', numpy.shape(mag_frames))
    #print('pow_frames: ', numpy.shape(pow_frames))

    # apply triangular filter

    low_freq_mel = 0
    high_freq_mel = (2595 * numpy.log10(1 + (sample_rate / 2) / 700))  # Convert Hz to Mel
    mel_points = numpy.linspace(low_freq_mel, high_freq_mel, nfilt + 2)  # Equally spaced in Mel scale (incl. low&high freq)
    hz_points = (700 * (10**(mel_points / 2595) - 1))  # Convert Mel to Hz
    bin = numpy.floor((NFFT + 1) * hz_points / sample_rate)

    fbank = numpy.zeros((nfilt, int(numpy.floor(NFFT / 2 + 1))))
    for m in range(1, nfilt + 1):
        f_m_minus = int(bin[m - 1])   # left
        f_m = int(bin[m])			 # center
        f_m_plus = int(bin[m + 1])	# right

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin[m - 1]) / (bin[m] - bin[m - 1])
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin[m + 1] - k) / (bin[m + 1] - bin[m])
    filter_banks = numpy.dot(pow_frames, fbank.T)
    filter_banks = numpy.where(filter_banks == 0, numpy.finfo(float).eps, filter_banks)  # Numerical Stability
    filter_banks = 20 * numpy.log10(filter_banks)  # dB

    # Report some values
    #print('high_freq_mel: ', high_freq_mel)
    #print('mel_points: ', mel_points.shape)
    #print('hz_points: ', hz_points.shape)
    #print('bin: ', bin.shape)
    #print('fbank: ', fbank.shape)
    #print('filter_banks: ', filter_banks.shape)

    num_ceps = 12
    mfcc = dct(filter_banks, type=2, axis=1, norm='ortho')[:, 1 : (num_ceps + 1)] # Keep 2-13


    cep_lifter = 23
    (nframes, ncoeff) = mfcc.shape
    n = numpy.arange(ncoeff)
    lift = 1 + (cep_lifter / 2) * numpy.sin(numpy.pi * n / cep_lifter)
    mfcc *= lift

    # mean normalization
    mfcc -= (numpy.mean(mfcc, axis=0))

    mfcc_result = numpy.zeros((frame_limit,num_ceps))
    dim1 = len(mfcc)
    if (dim1 <= frame_limit):
        mfcc_result[:dim1, :] = mfcc
    else:
        mfcc_result[:,:] = mfcc[:frame_limit, :]

        # Report some values
    #print('dim1: ', dim1)
    #print('mfcc_result: ', mfcc_result.shape)
    #plt.imshow(mfcc_result, cmap='hot')
    #plt.show()

    #print(numpy.shape(mfcc_result.T.reshape(1,-1)))
    return mfcc_result.T.reshape(1,-1)


def clf_SVM(X, Y):
    X, Y = shuffle(X, Y)
    train_size = int(len(X) * 0.02)
    X_train, Y_train = X[:train_size], Y[:train_size]
    X_test, Y_test = X[train_size:], Y[train_size:]
    parameters = {'C': [10, 1, 1e-1, 1e-2, 1e-3]}
    svc = SVC(kernel='linear')
    clf = GridSearchCV(svc, parameters, cv=2, return_train_score=False, iid=False)
    clf.fit(X_train, Y_train)
    results = clf.cv_results_
    opt_index = clf.best_index_
    testing_score = clf.best_estimator_.fit(X_train, Y_train).score(X_test, Y_test)
    return clf.best_estimator_, testing_score